import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import ImageTk, Image
from matplotlib import pyplot as plt
from tkcalendar import Calendar, DateEntry
from tkinter.messagebox import askokcancel
from threading import Thread
from typing import Any
from datetime import datetime, date

from config import Config
from data import *
from lib import graphs
from lib.errors import GraphingError
from lib.mathlib import time_to_str, clamp
from lib.components import ScrollableFrame, ProgramSetSelector

class TimeWidget:
    def __init__(self, app: "App", root: tk.Tk, program_data: ProgramData = DEFAULT_PROGRAM_DATA):
        self.app = app
        self.root = root
        self.frame = tk.Frame(master = root, bg = app.config.get_color("unselected"), border=1, relief="solid")
        self.data = program_data
        self.selected = None # temporary

        # Widgets & Variables
        self.hide_button = ttk.Button(master = self.frame, text = "Hide", command = self.hide_program, style = "Danger.TButton")
        self.label_text = tk.StringVar(value = time_to_str(program_data.time))
        self.label = ttk.Label(master = self.frame, textvariable = self.label_text, font = app.config.label_font, background=app.config.get_color("unselected"))
        self.button_text = tk.StringVar(value = program_data.id)
        self.task_button = ttk.Button(self.frame, textvariable = self.button_text, command = self.set_task, width=app.config.button_width)
        self.pinned_var = tk.BooleanVar(value = program_data.visibility == P_VIS_PINNED)
        self.pin_checkbox = ttk.Checkbutton(self.frame, text = "Pin", variable = self.pinned_var, command=self.set_pinned)
        self.type_var = tk.StringVar(value = program_data.category)
        self.type_combobox = ttk.Combobox(self.frame, textvariable = self.type_var, values = app.config.categories, state = "readonly")
        self.type_combobox.bind("<<ComboboxSelected>>", self.set_ptype)
        self.afk_var = tk.BooleanVar(value = program_data.afk_sensitive)
        self.afk_checkbox = ttk.Checkbutton(self.frame, text = "Can AFK?", variable = self.afk_var, command=self.set_afk)
        self.graph_button = ttk.Button(self.frame, text = "Graph", command = lambda: self.app.show_graph_window([self.data]))

        # Structure
        self.hide_button.pack(side = 'left', padx = 10)
        self.task_button.pack(side = 'left', padx = 10)
        self.label.pack(side = 'left', padx = 10)
        self.pin_checkbox.pack(side = 'left', padx = 10)
        self.afk_checkbox.pack(side = 'left', padx = 10)
        self.type_combobox.pack(side = 'left', padx = 10)
        self.graph_button.pack(side = 'left', padx = 10)
        self.frame.pack(side='top', fill='x', expand=True)

        # Style initialization
        self.set_highlight(self.data.id == self.app.profile.selected_program.get_id())

    def set_task(self):
        self.app.set_task(self.data)

    def hide_program(self):
        confirmation = askokcancel("Hide program", f"Are you sure you want to hide {self.data.display_name}?")
        if (confirmation):
            self.data.visibility = P_VIS_HIDDEN
            self.app.update_view()

    def set_pinned(self):
        pinned = self.pinned_var.get()
        self.data.visibility = P_VIS_PINNED if pinned else P_VIS_DEFAULT
        self.app.update_view()
    def set_afk(self):
        afk = self.afk_var.get()
        self.data.afk_sensitive = afk
        print(f"Setting afk sensitivity for {self.data.display_name} to {afk}")
        self.app.update_view()

    def set_ptype(self, _evt):
        self.data.category = self.type_var.get()
        self.app.update_view()

    def update_program(self, data: ProgramData):
        self.data = data
        self.set_highlight(self.data.id == self.app.profile.selected_program.get_id())

        self.label_text.set(time_to_str(data.time))
        self.button_text.set(data.id)
        self.pinned_var.set(data.visibility == P_VIS_PINNED)
        self.type_var.set(data.category)
        self.afk_var.set(data.afk_sensitive)

    def set_highlight(self, selected: bool):
        if self.selected == selected: return
        self.selected = selected
        color = self.app.config.get_color("active" if selected else "unselected")
        self.frame.configure(bg = color)
        self.label.configure(background = color)
        # self.afk_checkbox.configure(bg = color)
        # self.pin_checkbox.configure(bg = color)

class TimerWindow:
    def __init__(self, app: "App"):
        self.app = app
        self.window = tk.Tk()
        self.window.lift()
        self.window.attributes("-topmost", True)
        self.window.geometry("200x75")
        self.window.title("Timer - OnTrack")

        # Widgets
        self.frame = tk.Frame(master = self.window)
        self.session_timer_label = ttk.Label(master = self.frame, text="00:00:00", font=app.config.label_font)
        self.timer_label = ttk.Label(master = self.frame, text="(00:00:00)", font=app.config.label_font_mini)
        self.info_label = ttk.Label(master = self.frame, text=self.get_info_text(self.app.profile.selected_program), font=app.config.label_font_mini)

        # Structure
        self.session_timer_label.pack()
        self.timer_label.pack()
        self.frame.pack()
        self.info_label.pack()

        # Event handlers
        self.window.protocol("WM_DELETE_WINDOW", self.app.handle_close)

    def set_task(self, task: ITask | None):
        self.app.profile.selected_program = task
        self.update()

    def get_info_text(self, task: ITask | None):
        if task is None: return "No task selected"
        return task.get_name()
    
    def update(self):
        task = self.app.profile.selected_program
        color = "idle"
        if self.app.profile.afk_time >= self.app.config.afk_timeout: color = "afk"
        
        active_program: ProgramData | None = self.app.profile.get_program(self.app.active_window)
        if  isinstance(task, TotalTask) or \
            isinstance(task, CategoryTask) and active_program and task.category == active_program.category or \
            isinstance(task, ProgramData) and active_program and task.get_id() == active_program.id: 
            color = "active"

        bg_color = self.app.config.get_color(color, "#ffffff") 
        self.session_timer_label.configure(background=bg_color, text=time_to_str(task.get_session_time()))
        self.timer_label.configure(background=bg_color, text=f"({time_to_str(task.get_time())})")
        self.info_label.configure(background=bg_color, text=self.get_info_text(task))
        self.window.configure(bg=bg_color)
        self.frame.configure(bg=bg_color)

class CategoryInfoWidget:
    def __init__(self, app: "App", root: tk.Tk, category: str):
        self.app = app
        self.category = category
        self.root = root
        self.frame = tk.Frame(master = root)
        self.task = CategoryTask(category, app.profile) if category else TotalTask(app.profile)
        self.title_button = ttk.Button(master = self.frame, text = self.task.get_name(), command=lambda: app.set_task(self.task))
        self.time_session_var = tk.StringVar(value = f"({app.profile.get_category_session_time(category)})")
        self.time_var = tk.StringVar(value = f"{app.profile.get_category_time(category)}")
        self.session_timer_label = ttk.Label(master = self.frame, textvariable = self.time_session_var, font = app.config.label_font)
        self.timer_label = ttk.Label(master = self.frame, textvariable = self.time_var, font = app.config.label_font_mini)

        # Structure
        self.title_button.pack()
        self.session_timer_label.pack()
        self.timer_label.pack()
        self.frame.pack(side='left', padx=10, fill="x")

    def update(self):
        bg_color = self.app.config.get_color("unselected")
        if self.app.profile.selected_program == self.task:
            bg_color = self.app.config.get_color("active")
        self.frame.configure(bg = bg_color)
        self.time_session_var.set(f"{time_to_str(self.app.profile.get_category_session_time(self.category))}")
        self.time_var.set(f"({time_to_str(self.app.profile.get_category_time(self.category))})")
        self.session_timer_label.configure(background = bg_color)
        self.timer_label.configure(background = bg_color)

class StatisticsWindow:
    def __init__(self, app: "App", selected_programs: list[ProgramData] = []):
        # Local data and variables
        self.app = app
        self.selected_timestep = 3600 * 24
        self.timestep_options = [(3600, "hourly"), (3600 * 24, "daily"), (3600 * 24 * 7, "weekly")]
        self.graph_image: ImageTk.PhotoImage | None = None

        self.window = tk.Toplevel(app.window)
        self.window.wait_visibility()
        self.window.grab_set()
        self.window.transient(app.window)
        self.window.title("Statistics - OnTrack")
        self.window.geometry("960x580")

        self.display_options = {
            "Time Chart": ("Bar", False, False),
            "Time Chart by Category": ("Bar", True, False),
            "Time Chart by Program (Unified)": ("Bar", False, True),
            "Time Chart by Program (Split)": ("Bar", True, True),
            "Pie Chart": ("Pie", False, None),
            "Pie Chart by Category": ("Pie", True, None),
        }
        
        self.option_frame = tk.Frame(master = self.window)
        self.time_start_selector = DateEntry(master = self.option_frame, date_pattern="YYYY-MM-dd")
        self.time_start_selector.bind("<<DateEntrySelected>>", self._update_t_start)
        self.time_start_clear = ttk.Button(master = self.option_frame, text = "X", width=3, command = self._reset_t_start)
        self.time_end_selector = DateEntry(master = self.option_frame, date_pattern="YYYY-MM-dd")
        self.time_end_selector.bind("<<DateEntrySelected>>", self._update_t_end)
        self.time_end_clear = ttk.Button(master = self.option_frame, text = "X", width=3, command = self._reset_t_end)
        self.refresh_button = ttk.Button(master = self.option_frame, text = "Refresh", command = self.update_graph)
        self.timestep_buttons: list[ttk.Button] = []
        for timestep, label in self.timestep_options:
            self.timestep_buttons.append(ttk.Button(master = self.option_frame, text = label, command = lambda t=timestep: self.set_timestep(t)))

        self.display_mode_var = tk.StringVar(value = "Time Chart")
        self.display_mode_selector = ttk.Combobox(master = self.option_frame, textvariable=self.display_mode_var, values = list(self.display_options.keys()), state = "readonly")
        self.display_mode_selector.bind("<<ComboboxSelected>>", self.update_graph)
        self.program_selector = ProgramSetSelector(self.window, app.config, app.profile, selected_programs = selected_programs)

        self.canvas = tk.Canvas(self.window, bg = "#ffffff")
        self._reset_t_end(None, False) # must be done first
        self._reset_t_start(None, False)

        # Structure
        self.program_selector.pack(side = 'left', fill="y")
        self.refresh_button.pack(side = 'left')
        self.display_mode_selector.pack(side = 'left')
        for btn in self.timestep_buttons:
            btn.pack(side = 'left')
        self.time_start_selector.pack(side = 'left')
        self.time_start_clear.pack(side = 'left')
        self.time_end_selector.pack(side = 'left')
        self.time_end_clear.pack(side = 'left')

        self.option_frame.pack(side = 'top', fill='x')
        self.canvas.pack(fill = "both", expand = True)
        self.update_graph()

    def update_graph(self, _evt = None):
        display_mode = self.display_mode_var.get()
        graphtype, split_by_categories, split_by_programs = self.display_options[display_mode]
        selected_programs = self.program_selector.get_checked()
        timestamp_stop = self.timestamp_end + self.selected_timestep
        try:
            if graphtype == "Bar":
                figure, _ = graphs.build_activity_graph(self.app.profile, self.app.config, self.timestamp_start, timestamp_stop, self.selected_timestep, split_by_categories, split_by_programs, selected_programs)
            elif graphtype == "Pie":
                figure, _ = graphs.build_pie_chart(self.app.profile, self.app.config, self.timestamp_start, timestamp_stop, split_by_categories, selected_programs)
        except GraphingError as e:
            messagebox.showerror("Graphing Error", f"{e}")
            return
        TEMP_FILENAME = "temp_graph.png"
        figure.savefig(TEMP_FILENAME)
        plt.close(figure)
        # with open(TEMP_FILENAME, "rb") as f:
            # img = Image.open(f)
            # img = img.resize((800, 600), resample=Image.Resampling.BICUBIC)
        self.graph_image = ImageTk.PhotoImage(Image.open(TEMP_FILENAME))
        self.canvas.create_image(20, 20, image = self.graph_image, anchor = "nw")
        self.canvas.image = self.graph_image # keep a reference to the image

    def _reset_t_start(self, _evt = None, update = True):
        self.timestamp_start = self.app.profile.get_first_timestamp()
        # Show at most a month by default
        if (self.timestamp_start < self.timestamp_end - 30 * 86400):
            self.timestamp_start = self.timestamp_end - 30 * 86400
        self.time_start_selector.set_date(datetime.fromtimestamp(self.timestamp_start))
        if update: self.update_graph()
    def _reset_t_end(self, _evt = None, update = True):
        self.timestamp_end = self.app.profile.get_last_timestamp()
        self.time_end_selector.set_date(datetime.fromtimestamp(self.timestamp_end))
        if update: self.update_graph()
    def _update_t_start(self, _evt = None, update = True):
        d: date = self.time_start_selector.get_date()
        self.timestamp_start = datetime(d.year, d.month, d.day).timestamp()
        if update: self.update_graph()
    def _update_t_end(self, _evt = None, update = True):
        d: date = self.time_end_selector.get_date()
        self.timestamp_end = datetime(d.year, d.month, d.day).timestamp() + 86400
        if update: self.update_graph()
    def set_timestep(self, timestep: int):
        self.selected_timestep = timestep
        self.update_graph()

class App:    
    def __init__(self, config: Config, data: Profile):
        self.has_quit = False
        self.config = config
        self.window = tk.Tk()
        self.profile = data

        self.timer_window = TimerWindow(self)
        self.window.title("OnTrack")
        self.window.geometry('800x600')
        self.data_widgets : list[TimeWidget] = []
        self.category_panel = tk.Frame(master = self.window)
        self.timer_panel = ScrollableFrame(self.window)
        self.category_widgets = {
            category: CategoryInfoWidget(self, self.category_panel, category) for category in self.config.categories + [""]
        }
        self.active_window = None
        self.graph_frame = tk.Frame(master = self.window)
        self.open_graph_window_button = ttk.Button(master = self.graph_frame, text = "Statistics", command = self.show_graph_window)

        # Event handlers
        self.window.protocol("WM_DELETE_WINDOW", self.handle_close)

        # Structure
        self.category_panel.pack(side = 'top')
        self.open_graph_window_button.pack(side = 'left')
        self.graph_frame.pack(side = 'top')
        self.timer_panel.pack(side = 'top', fill = 'both', expand = True)
        
        # Styling
        danger_btn_style = ttk.Style()
        danger_btn_style.configure("Danger.TButton", background="#ff8888")

    def show_graph_window(self, programs: list[ProgramData] = []):
        self.graph_window = StatisticsWindow(self, programs)
        # self.window.wait_window(self.graph_window.window)

    def set_task(self, task: ProgramData):
        if self.has_quit: return
        self.timer_window.set_task(task)

    def update_data(self, active_window: str | None):
        if self.has_quit: return
        self.active_window = active_window
        self.update_view()
        for widget in self.category_widgets.values():
            widget.update()

    def handle_close(self):
        if (self.has_quit): return
        self.has_quit = True
        self.profile.save()
        if self.timer_window.window:
            self.timer_window.window.destroy()
        if self.window:
            self.window.destroy()
        exit(0)
    
    def update_view(self):
        if self.has_quit: return
        eligible_keys = [k for k in self.profile.programs.keys() if self.profile.programs[k].is_visible()]
        keys = sorted(eligible_keys, key = lambda i: (self.profile.programs[i].sortkey()))
        while len(self.data_widgets) < len(keys):
            self.data_widgets.append(TimeWidget(self, self.timer_panel.frame))
        while len(self.data_widgets) > len(keys):
            self.data_widgets.pop().frame.destroy()
        for k,widget in zip(keys,self.data_widgets):
            widget.update_program(self.profile.programs[k])
