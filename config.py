from typing import Generator, NoReturn
import yaml

CONFIG_FILE = "config.yaml"
DEFAULT_COLORS = { 
    "active": "#55ff55",
    "idle": "#ff7777",
    "afk": "#55a0ff",
    "unselected": "#dddddd",
    "text": "#000000",
    "social": "#88ff88",
    "productivity": "#ff8888",
    "entertainment": "#8888ff",
    "miscellaneous": "#aaaaaa"
}
DEFAULT_MISC_COLORS = [
    "#faedcb",
    "#c9e4d3",
    "#c6def1",
    "#dbcdf0",
    "#f2c6de",
    "#f7d9c4",
    "#f2da3d",
    "#39a862",
    "#327ab3",
    "#583191",
    "#992c68",
    "#c97132",
    "#664a00",
    "#003614",
    "#002f54",
    "#1e004a",
    "#4a0028",
    "#3d1900"
]
class Config:
    def __init__(self, 
        autosave_interval: float = 60, 
        update_interval: float = 1, 
        colors: dict[str,str] = DEFAULT_COLORS, 
        afk_timeout: float = 60, 
        button_width: int = 20,
        label_font: str = "Calibri 24",
        label_font_mini: str = "Calibri 16",
        autohide_substrings: list[str] = ["C:\\"],
        categories: list[str] = ["Productivity", "Entertainment", "Social", "Miscellaneous"],
        default_category: str = "Miscellaneous",
        max_plot_buckets = 100,
        max_plot_labels = 10,
        min_piece_fraction = 0.05,
        misc_colors = DEFAULT_MISC_COLORS,
        **kwargs
    ):        
        self.autosave_interval = autosave_interval
        self.update_interval = update_interval
        self.colors = colors
        self.button_width = button_width
        for k in DEFAULT_COLORS:
            if not k in self.colors:
                self.colors[k] = DEFAULT_COLORS[k]
        self.afk_timeout = afk_timeout
        self.label_font = label_font
        self.label_font_mini = label_font_mini
        self.autohide_substrings = autohide_substrings
        self.categories = categories
        self.default_category = default_category
        self.max_plot_buckets = max_plot_buckets
        self.max_plot_labels = max_plot_labels
        self.misc_colors = misc_colors
        self.min_piece_fraction = min_piece_fraction
        # Might make this a separate configurable value, forward compatibility!
        self.min_piece_fraction_bars = min_piece_fraction
        if len(kwargs) != 0:
            print(f"[WARNING] unknown fields during config parsing: {kwargs}")

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
            "button_width": self.button_width,
            "colors": self.colors,
            "label_font": self.label_font,
            "label_font_mini": self.label_font_mini,
            "autohide_substrings": self.autohide_substrings,
            "categories": self.categories,
            "default_category": self.default_category,
            "max_plot_buckets": self.max_plot_buckets,
            "max_plot_labels": self.max_plot_labels,
            "misc_colors": self.misc_colors,
            "min_piece_fraction": self.min_piece_fraction,
        }
    
    @staticmethod
    def load():
        try:
            with open(CONFIG_FILE) as f:
                r = Config.from_dict(yaml.load(f, yaml.SafeLoader))
                print("Successfully loaded config")
                return r
        except Exception as e:
            print(f"Error loading config: {e}")
            return Config.from_dict({})
    def save(self):
        with open(CONFIG_FILE, "w") as f:
            yaml.safe_dump(self.to_dict(), f)

    def should_autohide(self, key: str) -> bool:
        for ss in self.autohide_substrings:
            if ss in key:
                return True
        return False
    
    def color_generator(self) -> Generator[str, None, NoReturn]:
        colors = self.misc_colors
        while True:
            for c in colors:
                yield c