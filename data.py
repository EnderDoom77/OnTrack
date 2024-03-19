import json

DB_FILE = "db.json"
CURRENT_SCHEMA_VERSION = 1
class Profile:
    def __init__(self, programs: dict = {}, **kwargs):
        self.programs = {k: ProgramData.from_dict(k,v) for k,v in programs.items()}
        self.other_params = kwargs

    def to_dict(self):
        return {
            "version": CURRENT_SCHEMA_VERSION,
            "programs": {k: v.to_dict() for k,v in self.programs.items()}
        }
    
    @staticmethod
    def from_dict(data: dict):
        version = data.get("version", 0)
        if version != CURRENT_SCHEMA_VERSION:
            return read_old_profile(data, version)
        return Profile(**data)
    
    @staticmethod
    def load() -> "Profile":
        try:
            with open(DB_FILE) as f:
                return Profile.from_dict(json.load(f))
        except Exception as e:
            print(f"Error loading profile: {e}")
            return Profile.from_dict({})
    def save(self):
        with open(DB_FILE, "w") as f:
            json.dump(self.to_dict(), f, indent = 2)

    def get_program(self, key: str) -> "ProgramData":
        if not key in self.programs:
            self.programs[key] = ProgramData(key)
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
    def __init__(self, id: str, time: float = 0, visibility: str = P_VIS_DEFAULT, program_type: str = P_TYPE_DEFAULT):
        self.id = id
        self.time = time
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

def read_old_profile(data: dict, version: int) -> Profile:
    print(f"Converting old profile version {version}")
    if version == 0:
        # schema is dict[str, float]
        print(data)
        return Profile(
            programs = {k: ProgramData(k, time=v).to_dict() for k,v in data.items()}
        )
    raise ValueError(f"Unknown schema version {version}")