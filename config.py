import yaml

CONFIG_FILE = "config.yaml"
class Config:
    autosave_interval : float
    update_interval: float
    def __init__(self, autosave_interval: float = 60, update_interval: float = 1):
        self.autosave_interval = autosave_interval
        self.update_interval = update_interval
    @staticmethod
    def from_dict(data: dict) -> "Config":
        if data is None: data = {}
        return Config(**data)
    def to_dict(self) -> dict:
        return {
            "autosave_interval": self.autosave_interval,
            "update_interval": self.update_interval
        }
    @staticmethod
    def load():
        with open(CONFIG_FILE) as f:
            return Config.from_dict(yaml.load(f, yaml.SafeLoader))
    def save(self):
        with open(CONFIG_FILE, "w") as f:
            yaml.safe_dump(self.to_dict())