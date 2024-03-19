import json

from config import Config

DB_FILE = "db.json"
CURRENT_SCHEMA_VERSION = 1
class Profile:
    def __init__(self, config: Config, programs: dict = {}, **kwargs):
        self.programs: dict[str, ProgramData] = {k: ProgramData.from_dict(k,v) for k,v in programs.items()}
        self.session_data: dict[str, ProgramData] = {}
        self.other_params = kwargs
        self.config = config

    def to_dict(self):
        return {
            "version": CURRENT_SCHEMA_VERSION,
            "programs": {k: v.to_dict() for k,v in self.programs.items()}
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
            self.programs[key] = ProgramData(key, visibility = P_VIS_HIDDEN if autohide else P_VIS_DEFAULT)
        return self.programs[key]
    
P_VIS_DEFAULT = "default"
P_VIS_PINNED = "pinned"
P_VIS_HIDDEN = "hidden"
valid_visibilities = {P_VIS_DEFAULT, P_VIS_PINNED, P_VIS_HIDDEN}
P_TYPE_DEFAULT = "default"
P_TYPE_ENTERTAINMENT = "entertainment"
P_TYPE_PRODUCTIVITY = "productivity"
valid_ptypes = {P_TYPE_DEFAULT, P_TYPE_ENTERTAINMENT, P_TYPE_PRODUCTIVITY}
class ProgramData:
    def __init__(self, id: str, time: float = 0, visibility: str = P_VIS_DEFAULT, program_type: str = P_TYPE_DEFAULT, display_name: str | None = None):
        self.id = id
        self.time = time
        self.session_time = 0
        self.display_name = self.id if not display_name else display_name
        self.visibility = visibility if visibility in valid_visibilities else P_VIS_DEFAULT
        self.program_type = program_type if program_type in valid_ptypes else P_TYPE_DEFAULT

    def to_dict(self):
        result = {
            "time": self.time,
        }
        if self.visibility != P_VIS_DEFAULT:
            result["visibility"] = self.visibility
        if self.program_type != P_TYPE_DEFAULT:
            result["program_type"] = self.program_type
        if self.display_name != self.id:
            result["display_name"] = self.display_name
        return result
    
    def __repr__(self) -> str:
        return f"ProgramData({self.id}, {self.time}, {self.visibility}, {self.program_type})"

    @staticmethod
    def from_dict(key: str, data: dict):
        return ProgramData(key, **data)
    
    def is_visible(self):
        return self.visibility != P_VIS_HIDDEN
    def has_afk_timer(self):
        return self.program_type == P_TYPE_PRODUCTIVITY

    def sortkey(self):
        return (0 if self.visibility == P_VIS_PINNED else 1, -self.time)

def read_old_profile(config: Config, data: dict, version: int) -> Profile:
    print(f"Converting old profile version {version}")
    if version == 0:
        # schema is dict[str, float]
        return Profile(
            config,
            programs = {k: ProgramData(k, time=v).to_dict() for k,v in data.items()}
        )
    raise ValueError(f"Unknown schema version {version}")