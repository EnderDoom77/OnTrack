import yaml

CONFIG_FILE = "config.yaml"
DEFAULT_COLORS = { 
  "active": "#55ff55",
  "idle": "#ff7777",
  "text": "#000000"
}
class Config:
    autosave_interval : float
    update_interval: float
    def __init__(self, autosave_interval: float = 60, update_interval: float = 1, colors: dict[str,str] = DEFAULT_COLORS):
        self.autosave_interval = autosave_interval
        self.update_interval = update_interval
        self.colors = colors

    def get_color(self, name: str, default: str = "#000000"):
        if name in self.colors:
            return self.colors[name]
        return default
    
    @staticmethod
    def from_dict(data: dict) -> "Config":
        if data is None: data = {}
        return Config(**data)
    def to_dict(self) -> dict:
        return {
            "autosave_interval": self.autosave_interval,
            "update_interval": self.update_interval,
            "colors": self.colors
        }
    @staticmethod
    def load():
        try:
            with open(CONFIG_FILE) as f:
                return Config.from_dict(yaml.load(f, yaml.SafeLoader))
        except:
            return Config.from_dict({})
    def save(self):
        with open(CONFIG_FILE, "w") as f:
            yaml.safe_dump(self.to_dict(), f)