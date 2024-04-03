import math
from matplotlib import axes, pyplot as plt
from matplotlib.figure import Figure

from config import Config
from data import Profile, ProgramData, get_time_key_pretty
from lib.data_management import bucket_into_other, sort_dict_by_value
from lib.errors import GraphingError
from lib.mathlib import add_to_list
from lib.constants import GROUPING_OTHER, GROUPING_OTHER_DISPLAY
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

def shorten_name(name: str, max_len: int = 20, exceptions = {GROUPING_OTHER, GROUPING_OTHER_DISPLAY}) -> str:
    if name in exceptions:
        return name
    if len(name) <= max_len:
        return name
    return name[:max_len]

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
        # ax.bar_label(rects, padding=3, rotation=90, fmt=lambda x: timespan_to_str(x))
        multiplier += 1

    ax.set_ylabel('Time Spent')
    ax.set_title('Time Spent by Category')
    ax.set_xticks(x_range + width, x, rotation=xlabel_rotation)
    ax.set_yticks(ax.get_yticks())
    ax.set_yticklabels([timespan_to_str(v) for v in ax.get_yticks()])
    ax.legend()
    
    reduce_xaxis_labels(ax, config.max_plot_labels)

    return fig, ax

def advanced_time_plot(x: list, x_subdivs: list[str], data: dict[str, tuple[str,list[float]]], config: Config, xlabel_rotation: float = 45):
    fig, ax = plt.subplots(layout='constrained')
    ax: plt.Axes = ax

    effective_bar_count = len(x) * len(x_subdivs)
    width = 0.8 / len(x_subdivs)

    # Each position in the xlabel is defined by a number of subdivisions (or categories)
    # Each subdivision, simultaneously, has a number of programs with an associated time
    segmented_data: list[dict[str,dict[str,float]]] = [{x_subdiv: {} for x_subdiv in x_subdivs} for _ in range(effective_bar_count)]
    for pname, (cat, vals) in data.items():
        for i, v in enumerate(vals):
            segmented_data[i][cat][pname] = v
        
    # Now we just compactify the data to ignore categories, pretend each subdivision is an additional tick in the x axis
    segmented_data_effective_bars : list[dict[str, float]] = []
    for vals in segmented_data:
        for subdiv in x_subdivs:
            segmented_data_effective_bars.append(vals[subdiv])

    effective_offsets = []
    for i in range(len(x)):
        for j in range(len(x_subdivs)):
            effective_offsets.append(i + j * width)

    keys = list(data.keys()) + [GROUPING_OTHER]
    sizes_per_program = {pname: [] for pname in keys}
    offsets_per_program = {pname: [] for pname in keys}
    bottoms_per_program = {pname: [] for pname in keys}
    # Then, we need to sort each individual subdivision and lump certain programs into a new "other" category
    for i,vals in enumerate(segmented_data_effective_bars):
        total = sum(vals.values())
        bucketed = bucket_into_other(vals, config.min_piece_fraction_bars * total, GROUPING_OTHER)
        # Reverse is false because we want to create the bar plot starting from the bottom
        sorted_keys, sorted_vals = sort_dict_by_value(bucketed, reverse=False, force_min_key=GROUPING_OTHER)
        bot = 0
        for pname, val in zip(sorted_keys, sorted_vals):
            if val == 0:
                continue
            sizes_per_program[pname].append(val)
            offsets_per_program[pname].append(effective_offsets[i])
            bottoms_per_program[pname].append(bot)
            bot += val

    prog_colors = {}
    prog_totals = {pname: sum(sizes) for pname, sizes in sizes_per_program.items()}
    color_gen = config.color_generator()
    for pname in sort_dict_by_value(prog_totals, reverse=True)[0]:
        if pname == GROUPING_OTHER:
            prog_colors[pname] = config.get_color("miscellaneous")
            continue
        prog_colors[pname] = next(color_gen)

    for pname in keys:
        offsets = offsets_per_program[pname]
        if (len(offsets) == 0):
            continue
        sizes = sizes_per_program[pname]
        bottoms = bottoms_per_program[pname]
        color = prog_colors[pname]
        rects = ax.bar(offsets, sizes, width, bottoms, label=shorten_name(pname), color=color)
        # ax.bar_label(rects, padding=3, rotation=90, fmt=lambda x: timespan_to_str(x))

    x_range = np.arange(len(x))
    ax.set_ylabel('Time Spent')
    ax.set_title('Time Spent by Category')
    ax.set_xticks(x_range + (0.4 - width / 2), x, rotation=xlabel_rotation)
    ax.set_yticks(ax.get_yticks())
    ax.set_yticklabels([timespan_to_str(v) for v in ax.get_yticks()])
    ax.legend()
    
    reduce_xaxis_labels(ax, config.max_plot_labels)

    return fig, ax

def plot_category_times(data: Profile, config: Config, start: float | None = None, end: float | None = None, bucket_size: int = 60 * 60, num_buckets: float | None = None, only_show_days: bool = False, label_xrotation: float = 45, programs: list[ProgramData] = []) -> tuple[Figure, axes.Axes]:
    if start is None:
        start = data.get_first_timestamp()
    if end is None:
        end = data.get_last_timestamp() + bucket_size
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

def build_activity_graph(profile: Profile, config: Config, timestamp_start: float, timestamp_end: float, selected_timestep: float, split_by_categories: bool = True, show_individual_programs: bool = False, selected_programs: list[ProgramData] = []) -> tuple[Figure, axes.Axes]:
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
    if not show_individual_programs:
        if split_by_categories:
            return plot_category_times(profile, config, timestamp_start, timestamp_end, selected_timestep, only_show_days=not show_time, programs = selected_programs, label_xrotation=label_rotation)
        return plot_mixed_times(profile, config, timestamp_start, timestamp_end, selected_timestep, only_show_days=not show_time, programs = selected_programs, label_xrotation=label_rotation)
    else:
        formatted_data = {}
        categories = [""]
        if split_by_categories:
            formatted_data = {prog.display_name: (prog.category, prog.get_bucketed_time(timestamp_start, timestamp_end, selected_timestep)) for prog in selected_programs}
            categories = config.categories
        else:
            formatted_data = {prog.display_name: ("", prog.get_bucketed_time(timestamp_start, timestamp_end, selected_timestep)) for prog in selected_programs}
        x_labels = [get_time_key_pretty(timestamp_start + i * selected_timestep, not show_time) for i in range(num_buckets)]
        return advanced_time_plot(x_labels, categories, formatted_data, config, label_rotation)

##############
# PIE CHARTS #
##############

def plot_pie_chart(keys: list[str], values: list[float], config: Config, title: str = "Time Spent by Category") -> tuple[Figure, axes.Axes]:
    fig, ax = plt.subplots()
    misc_color_gen = config.color_generator()
    colors = []
    explodes = []
    labels = []
    other_color = config.get_color("miscellaneous")
    for k,v in zip(keys, values):
        e = 0
        c = other_color
        if k in config.categories:
            c = config.get_color(k.lower())
        elif k != GROUPING_OTHER:
            c = next(misc_color_gen)
        else:
            e = 0.1
        colors.append(c)
        explodes.append(e)
        labels.append(f"{k} ({timespan_to_str(v)})")
    ax: plt.Axes = ax
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, explode=explodes)
    ax.axis('equal')
    ax.set_title(title)
    return fig, ax

def build_pie_chart(profile: Profile, config: Config, timestamp_start: float, timestamp_end: float, split_by_categories: bool = True, selected_programs: list[ProgramData] = []) -> tuple[Figure, axes.Axes]:
    if len(selected_programs) == 0:
        selected_programs = [p for p in profile.programs.values() if p.is_visible()]
    if timestamp_end <= timestamp_start:
        raise GraphingError("End time must be after start time")
    
    if split_by_categories:
        data = {category: 0 for category in config.categories}
        for prog in selected_programs:
            data[prog.category] += prog.get_timeframe_time(timestamp_start, timestamp_end)
    else:
        data = {prog.display_name: prog.get_timeframe_time(timestamp_start, timestamp_end) for prog in selected_programs}

    total = sum(data.values())
    data = bucket_into_other(data, config.min_piece_fraction * total)
    keys, values = sort_dict_by_value(data, reverse=False)
    return plot_pie_chart(keys, values, config, f"Task Distribution from {get_time_key_pretty(timestamp_start, True)} to {get_time_key_pretty(timestamp_end, True)}")
    