import json

from config import Config

DB_FILE = "db.json"
CURRENT_SCHEMA_VERSION = 1
P_VIS_DEFAULT = "default"
P_VIS_PINNED = "pinned"
P_VIS_HIDDEN = "hidden"
valid_visibilities = {P_VIS_DEFAULT, P_VIS_PINNED, P_VIS_HIDDEN}
class Profile:
    def __init__(self, config: Config, programs: dict = {}, selected_program = "", **kwargs):
        self.programs: dict[str, ProgramData] = {k: ProgramData.from_dict(config, k,v) for k,v in programs.items()}
        self.session_data: dict[str, ProgramData] = {}
        self.other_params = kwargs
        self.selected_program: ProgramData = self.programs.get(selected_program, DEFAULT_PROGRAM_DATA)
        self.config = config

    def to_dict(self):
        return {
            "version": CURRENT_SCHEMA_VERSION,
            "programs": {k: v.to_dict() for k,v in self.programs.items()},
            "selected_program": self.selected_program.id
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
    
class ProgramData:
    def __init__(self, config: Config, id: str, time: float = 0, visibility: str = P_VIS_DEFAULT, program_type: str = None, display_name: str | None = None, afk_sensitive: bool = True):
        self.config = config
        if program_type is None:
            program_type = config.default_category
        self.id = id
        self.time = time
        self.session_time = 0
        self.display_name = self.id if not display_name else display_name
        self.visibility = visibility if visibility in valid_visibilities else P_VIS_DEFAULT
        self.category = program_type if program_type in config.categories else config.default_category
        self.afk_sensitive = afk_sensitive

    def to_dict(self):
        result = {
            "time": self.time,
        }
        if self.visibility != P_VIS_DEFAULT:
            result["visibility"] = self.visibility
        if self.category != self.config.default_category:
            result["program_type"] = self.category
        if self.display_name != self.id:
            result["display_name"] = self.display_name
        if not self.afk_sensitive:
            result["afk_sensitive"] = False
        
        return result
    
    def __repr__(self) -> str:
        return f"ProgramData({self.id}, {self.time}, {self.visibility}, {self.category})"

    @staticmethod
    def from_dict(config: Config, key: str, data: dict):
        return ProgramData(config, key, **data)
    
    def is_visible(self):
        return self.visibility != P_VIS_HIDDEN
    def has_afk_timer(self):
        return self.afk_sensitive

    def sortkey(self):
        return (0 if self.visibility == P_VIS_PINNED else 1, -self.time)

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