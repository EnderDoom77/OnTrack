from abc import abstractmethod
from datetime import datetime
import json
import math
import time

from config import Config

DB_FILE = "db.json"
CURRENT_SCHEMA_VERSION = 1
P_VIS_DEFAULT = "default"
P_VIS_PINNED = "pinned"
P_VIS_HIDDEN = "hidden"
valid_visibilities = {P_VIS_DEFAULT, P_VIS_PINNED, P_VIS_HIDDEN}

def get_time_key(time: float, only_show_day: bool = False) -> str:
    fmt_str = "%Y-%m-%dT%H:00:00" if not only_show_day else "%Y-%m-%d"
    return datetime.fromtimestamp(time).strftime(fmt_str)
def get_time_key_pretty(time: float, only_show_day: bool = False) -> str:
    fmt_str = "%b %d %I%p" if not only_show_day else "%b %d"
    return datetime.fromtimestamp(time).strftime(fmt_str)

def get_time_from_key(key: str) -> float:
    return datetime.strptime(key, "%Y-%m-%dT%H:%M:%S").timestamp()

def time_to_date_str(time: float, fmt: str = "%Y-%m-%d") -> str:
    return datetime.fromtimestamp(time).strftime(fmt)

class Profile:
    def __init__(self, config: Config, programs: dict = {}, selected_program = "", **kwargs):
        self.programs: dict[str, ProgramData] = {k: ProgramData.from_dict(config, k,v) for k,v in programs.items()}
        self.session_data: dict[str, ProgramData] = {}
        self.other_params = kwargs
        self.selected_program: ITask = None
        if selected_program.startswith("CATEGORY_"):
            self.selected_program: ITask = CategoryTask(selected_program[9:], self)
        else:
            self.selected_program: ITask = self.programs.get(selected_program, DEFAULT_PROGRAM_DATA)
        self.config = config
        self.afk_time : float = 0

    def to_dict(self):
        return {
            "version": CURRENT_SCHEMA_VERSION,
            "programs": {k: v.to_dict() for k,v in self.programs.items()},
            "selected_program": self.selected_program.get_id(),
        }
    
    @staticmethod
    def from_dict(config: Config, data: dict):
        version = data.get("version", 0)
        if version != CURRENT_SCHEMA_VERSION:
            return read_old_profile(config, data, version)
        return Profile(config, **data)
    
    @staticmethod
    def load(config: Config) -> "Profile":
        try:
            with open(DB_FILE) as f:
                return Profile.from_dict(config, json.load(f))
        except Exception as e:
            print(f"Error loading profile: {e}")
            return Profile.from_dict(config, {})
    def save(self):
        with open(DB_FILE, "w") as f:
            json.dump(self.to_dict(), f, indent = 2)

    def get_program(self, key: str) -> "ProgramData | None":
        if not key in self.programs:
            autohide = key.isspace() or self.config.should_autohide(key)
            self.programs[key] = ProgramData(self.config, key, visibility = P_VIS_HIDDEN if autohide else P_VIS_DEFAULT)
        return self.programs[key]
    
    def get_category_time(self, category: str) -> float:
        if category == "":
            return self.get_total_time()
        return sum(p.time for p in self.programs.values() if p.category == category and p.is_visible())
    def get_category_session_time(self, category: str) -> float:
        if category == "":
            return self.get_total_session_time()
        return sum(p.session_time for p in self.programs.values() if p.category == category and p.is_visible())
    def get_total_time(self) -> float:
        return sum(p.time for p in self.programs.values() if p.is_visible())
    def get_total_session_time(self) -> float:
        return sum(p.session_time for p in self.programs.values() if p.is_visible())
    
    def get_first_timekey(self):
        return min(p.get_first_timekey() for p in self.programs.values())
    def get_last_timekey(self):
        return max(p.get_last_timekey() for p in self.programs.values())
    def get_first_timestamp(self):
        return get_time_from_key(self.get_first_timekey())
    def get_last_timestamp(self):
        return get_time_from_key(self.get_last_timekey())
    
class ITask:
    @abstractmethod
    def get_id(self) -> str: pass
    @abstractmethod
    def get_name(self) -> str: pass

    @abstractmethod
    def get_time(self) -> float: pass
    @abstractmethod
    def get_session_time(self) -> float: pass
    @abstractmethod
    def get_timeframe_time(self, start: float, end: float) -> float: pass
    @abstractmethod
    def get_first_timekey(self): pass
    @abstractmethod
    def get_last_timekey(self): pass
    @abstractmethod
    def get_first_timestamp(self): pass
    @abstractmethod
    def get_last_timestamp(self): pass

class ProgramData(ITask):
    def __init__(self, config: Config, id: str, time: float = 0, time_series: dict[str,float] = {}, visibility: str = P_VIS_DEFAULT, program_type: str = None, display_name: str | None = None, afk_sensitive: bool = True):
        self.config = config
        if program_type is None:
            program_type = config.default_category
        self.id = id
        self.time = time
        self.time_series = time_series
        self.session_time = 0
        self.display_name = self.id.title() if not display_name else display_name
        self.visibility = visibility if visibility in valid_visibilities else P_VIS_DEFAULT
        self.category = program_type if program_type in config.categories else config.default_category
        self.afk_sensitive = afk_sensitive

    def to_dict(self):
        result = {
            "time": self.time,
            "time_series": self.time_series,
        }
        if self.visibility != P_VIS_DEFAULT:
            result["visibility"] = self.visibility
        if self.category != self.config.default_category:
            result["program_type"] = self.category
        if self.display_name != self.id.title():
            result["display_name"] = self.display_name
        if not self.afk_sensitive:
            result["afk_sensitive"] = False
        
        return result
    
    def __repr__(self) -> str:
        return f"ProgramData({self.id}, {self.time}, {self.visibility}, {self.category})"

    @staticmethod
    def from_dict(config: Config, key: str, data: dict):
        return ProgramData(config, key, **data)
    
    def get_id(self) -> str:
        return self.id
    def get_name(self) -> str:
        return self.display_name
    
    # Fulfill ITask interface
    def get_time(self) -> float:
        return self.time
    def get_session_time(self) -> float:
        return self.session_time

    def is_visible(self):
        return self.visibility != P_VIS_HIDDEN
    def has_afk_timer(self):
        return self.afk_sensitive

    def sortkey(self):
        return (0 if self.visibility == P_VIS_PINNED else 1, -self.time)
    
    def add_time(self, delta: float, now: float = time.time()):
        self.time += delta
        self.session_time += delta
        time_key = get_time_key(now)
        if not time_key in self.time_series:
            self.time_series[time_key] = 0
        # print(f"Adding {delta:.3f} to {self.display_name} at {time_key}")
        self.time_series[time_key] += delta
        # print("  New value:" , self.time_series[time_key])

    def get_bucketed_time(self, start: float, end: float | None = None, bucket_size = 60 * 60) -> list[float]:
        if end is None:
            end = start + bucket_size
        num_buckets = math.ceil((end - start) / bucket_size)
        result = [0 for _ in range(num_buckets)]
        for k,v in self.time_series.items():
            time = get_time_from_key(k)
            if time < start or time >= end:
                continue
            idx = int((time - start) / bucket_size)
            result[idx] += v
        return result
    
    def get_timeframe_time(self, start: float, end: float) -> float:
        return sum(v for k,v in self.time_series.items() if start <= get_time_from_key(k) < end)
    
    def get_first_timekey(self):
        return min(self.time_series.keys(), default = get_time_key(time.time()))
    def get_last_timekey(self):
        return max(self.time_series.keys(), default = get_time_key(time.time()))
    def get_first_timestamp(self):
        return get_time_from_key(self.get_first_timekey())
    def get_last_timestamp(self):
        return get_time_from_key(self.get_last_timekey())

class CategoryTask(ITask):
    def __init__(self, category: str, profile: Profile):
        self.category = category
        self.profile = profile

    def get_id(self) -> str:
        return f"CATEGORY_{self.category}"
    def get_name(self) -> str:
        return self.category

    def get_time(self) -> float:
        return self.profile.get_category_time(self.category)
    def get_session_time(self) -> float:
        return self.profile.get_category_session_time(self.category)
    
    def get_timeframe_time(self, start: float, end: float) -> float:
        return sum(p.get_timeframe_time(start, end) for p in self.profile.programs.values() if p.category == self.category and p.is_visible())
    
    def get_first_timekey(self):
        return min(p.get_first_timekey() for p in self.profile.programs.values() if p.category == self.category and p.is_visible())
    def get_last_timekey(self):
        return max(p.get_last_timekey() for p in self.profile.programs.values() if p.category == self.category and p.is_visible())
    def get_first_timestamp(self):
        return get_time_from_key(self.get_first_timekey())
    def get_last_timestamp(self):
        return get_time_from_key(self.get_last_timekey())

class TotalTask(ITask):
    def __init__(self, profile: Profile):
        self.profile = profile

    def get_id(self) -> str:
        return "Total"
    def get_name(self) -> str:
        return "Total"

    def get_time(self) -> float:
        return self.profile.get_total_time()
    def get_session_time(self) -> float:
        return self.profile.get_total_session_time()
    
    def get_timeframe_time(self, start: float, end: float) -> float:
        return sum(p.get_timeframe_time(start, end) for p in self.profile.programs.values() if p.is_visible())
    
    def get_first_timekey(self):
        return min(p.get_first_timekey() for p in self.profile.programs.values() if p.is_visible())
    def get_last_timekey(self):
        return max(p.get_last_timekey() for p in self.profile.programs.values() if p.is_visible())
    def get_first_timestamp(self):
        return get_time_from_key(self.get_first_timekey())
    def get_last_timestamp(self):
        return get_time_from_key(self.get_last_timekey())

DEFAULT_PROGRAM_DATA = ProgramData(Config(), "")
def read_old_profile(config: Config, data: dict, version: int) -> Profile:
    print(f"Converting old profile version {version}")
    if version == 0:
        # schema is dict[str, float]
        return Profile(
            config,
            programs = {k: ProgramData(config, k, time=v).to_dict() for k,v in data.items()}
        )
    raise ValueError(f"Unknown schema version {version}")
