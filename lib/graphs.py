import math
from matplotlib import axes, pyplot as plt
from matplotlib.figure import Figure

from config import Config
from data import Profile, ProgramData, get_time_key_pretty
from lib.errors import GraphingError
from lib.mathlib import add_to_list
import numpy as np

def timespan_to_str(time: float) -> str:
    if time < 3600:
        if time < 60:
            return f"{int(time):d}s"
        return f"{int(time // 60):d}m {int(time % 60):d}s"
    secs = int(time % 60)
    mins_tot = int(time // 60)
    mins = mins_tot % 60
    hours = mins_tot // 60
    return f"{hours:d}h {mins:d}m {secs:d}s"

def plot_bar_timegraph(times, values, config: Config, title: str = "Time Graph", x_label: str = "Date", y_label: str = "Time Spent", labelx_rotation: float = 45) -> tuple[Figure, axes.Axes]:
    (fig, ax) = plt.subplots()
    ax : plt.Axes = ax
    ax.bar(times, values)
    ax.set_title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=labelx_rotation)
    ax.set_yticks(ax.get_yticks())
    ax.set_yticklabels([timespan_to_str(v) for v in ax.get_yticks()])
    fig.tight_layout()

    reduce_xaxis_labels(ax, config.max_plot_labels)

    return fig, ax

def reduce_xaxis_labels(ax: axes.Axes, max_labels: int = 10):
    xlabels = ax.get_xticklabels()
    if len(xlabels) > max_labels:
        for i in range(len(xlabels)):
            if i % (len(xlabels) // max_labels) != 0:
                xlabels[i].set_visible(False)

def plot_app_times(data: ProgramData, start: float | None = None, end: float | None = None, bucket_size: int = 60 * 60, num_buckets: float | None = None, only_show_days: bool = False) -> tuple[Figure, axes.Axes]:
    if start is None:
        start = data.get_first_timestamp()
    if end is None:
        end = data.get_last_timestamp() + 1
    if num_buckets is not None:
        bucket_size = math.ceil((end - start) / num_buckets)
    hist = data.get_bucketed_time(start, end, bucket_size)
    times = [get_time_key_pretty(start + i * bucket_size, only_show_days) for i in range(len(hist))]
    return plot_bar_timegraph(times, hist, data.config, f"Time Spent in {data.display_name}", "Date", "Time Spent")

def plot_tagged_series(x: list, data: dict[str, list[float]], config: Config, xlabel_rotation: float = 45) -> tuple[Figure, axes.Axes]:
    fig, ax = plt.subplots(layout='constrained')
    ax: plt.Axes = ax

    x_range = np.arange(len(x))
    width = 0.8 / len(data)
    multiplier = 0
    for k,v in data.items():
        offset = width * multiplier
        rects = ax.bar(x_range + offset, v, width, label=k, color=config.get_color(k.lower()))
        ax.bar_label(rects, padding=3, rotation=90, fmt=lambda x: timespan_to_str(x))
        multiplier += 1

    ax.set_ylabel('Time Spent')
    ax.set_title('Time Spent by Category')
    ax.set_xticks(x_range + width, x, rotation=xlabel_rotation)
    ax.set_yticks(ax.get_yticks())
    ax.set_yticklabels([timespan_to_str(v) for v in ax.get_yticks()])
    ax.legend()
    
    reduce_xaxis_labels(ax, config.max_plot_labels)

    return fig, ax

def plot_category_times(data: Profile, config: Config, start: float | None = None, end: float | None = None, bucket_size: int = 60 * 60, num_buckets: float | None = None, only_show_days: bool = False, label_xrotation: float = 45, programs: list[ProgramData] = []) -> tuple[Figure, axes.Axes]:
    if start is None:
        start = data.get_first_timestamp()
    if end is None:
        end = data.get_last_timestamp() + 1
    if num_buckets is not None:
        bucket_size = math.ceil((end - start) / num_buckets)
    if len(programs) == 0:
        programs = [p for p in data.programs.values() if p.is_visible()]
    num_buckets = math.ceil((end - start) / bucket_size)
    values = {category: [0 for _ in range(num_buckets)] for category in config.categories}    
    for prog in programs:
        add_to_list(values[prog.category], prog.get_bucketed_time(start, end, bucket_size))
    times = [get_time_key_pretty(start + i * bucket_size, only_show_days) for i in range(num_buckets)]
    return plot_tagged_series(times, values, config, label_xrotation)

def plot_mixed_times(data: Profile, config: Config, start: float | None = None, end: float | None = None, bucket_size: int = 60, num_buckets: float | None = None, only_show_days: bool = False, label_xrotation: float = 45, programs: list[ProgramData] = []) -> tuple[Figure, axes.Axes]:
    if start is None:
        start = data.get_first_timestamp()
    if end is None:
        end = data.get_last_timestamp() + 1
    if num_buckets is not None:
        bucket_size = math.ceil((end - start) / num_buckets)
    if len(programs) == 0:
        programs = [p for p in data.programs.values() if p.is_visible()]
    num_buckets = math.ceil((end - start) / bucket_size)
    values = [0 for _ in range(num_buckets)]
    for prog in programs:
        add_to_list(values, prog.get_bucketed_time(start, end, bucket_size))
    times = [get_time_key_pretty(start + i * bucket_size, only_show_days) for i in range(num_buckets)]
    return plot_bar_timegraph(times, values, config, "Activity Over Time", labelx_rotation=label_xrotation)

def build_activity_graph(profile: Profile, config: Config, timestamp_start: float, timestamp_end: float, selected_timestep: float, split_by_categories: bool = True, selected_programs: list = []) -> tuple[Figure, axes.Axes]:
    if len(selected_programs) == 0:
        selected_programs = [p for p in profile.programs.values() if p.is_visible()]
    if timestamp_end <= timestamp_start:
        raise GraphingError("End time must be after start time")
    show_time = selected_timestep < 60 * 60 * 24
    num_buckets = math.ceil((timestamp_end - timestamp_start) / selected_timestep)
    if num_buckets > config.max_plot_buckets:
        raise GraphingError(f"Too many buckets: ({num_buckets} > {config.max_plot_buckets})")
    # <= 4 -> 45 degrees
    # 6 buckets - 60 degrees
    # 8 buckets - 67.5 degrees
    # ...
    label_rotation = max(90 - (180 / num_buckets), 45)
    if split_by_categories:
        return plot_category_times(profile, config, timestamp_start, timestamp_end, selected_timestep, only_show_days=not show_time, programs = selected_programs, label_xrotation=label_rotation)
    return plot_mixed_times(profile, config, timestamp_start, timestamp_end, selected_timestep, only_show_days=not show_time, programs = selected_programs, label_xrotation=label_rotation)

