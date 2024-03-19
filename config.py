import yaml

CONFIG_FILE = "config.yaml"
DEFAULT_COLORS = { 
  "active": "#55ff55",
  "idle": "#ff7777",
  "text": "#000000"
}
class Config:
    def __init__(self, 
        autosave_interval: float = 60, 
        update_interval: float = 1, 
        colors: dict[str,str] = DEFAULT_COLORS, 
        afk_timeout: float = 300, 
        label_font: str = "Calibri 24",
        banned_substrings: list[str] = ["C:\\"]
    ):        
        self.autosave_interval = autosave_interval
        self.update_interval = update_interval
        self.colors = colors
        self.afk_timeout = afk_timeout
        self.label_font = label_font
        self.banner_substrings = banned_substrings

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
            "afk_timeout": self.afk_timeout,
            "colors": self.colors,
            "label_font": self.label_font,
            "banned_substrings": self.banner_substrings
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