import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askokcancel
from threading import Thread

from config import Config
from data import *
def time_to_str(time: float) -> str:
    secs = int(time % 60)
    mins_tot = int(time // 60)
    mins = mins_tot % 60
    hours = mins_tot // 60
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

class TimeWidget:
    def __init__(self, app: "App", root: tk.Tk, program_data: ProgramData = DEFAULT_PROGRAM_DATA):
        self.app = app
        self.root = root
        self.frame = tk.Frame(master = root)
        self.data = program_data
        self.selected = self.data.id == self.app.profile.selected_program.id

        # Widgets & Variables
        self.hide_button = ttk.Button(master = self.frame, text = "Hide", command = self.hide_program, style = "Danger.TButton")
        self.label_text = tk.StringVar(value = time_to_str(program_data.time))
        self.label = ttk.Label(master = self.frame, textvariable = self.label_text, font = app.config.label_font)
        self.button_text = tk.StringVar(value = program_data.id)
        self.task_button = ttk.Button(self.frame, textvariable = self.button_text, command = self.set_task)
        self.pinned_var = tk.BooleanVar(value = program_data.visibility == P_VIS_PINNED)
        self.pin_checkbox = ttk.Checkbutton(self.frame, text = "Pin", variable = self.pinned_var, command=self.set_pinned)
        self.type_var = tk.StringVar(value = program_data.category)
        self.type_combobox = ttk.Combobox(self.frame, textvariable = self.type_var, values = app.config.categories, state = "readonly")
        self.type_combobox.bind("<<ComboboxSelected>>", self.set_ptype)

        # Structure
        self.hide_button.pack(side = 'left', padx = 10)
        self.task_button.pack(side = 'left', padx = 10)
        self.label.pack(side = 'left', padx = 10)
        self.pin_checkbox.pack(side = 'left', padx = 10)
        self.type_combobox.pack(side = 'left', padx = 10)
        self.frame.pack()

        # Style initialization
        self.set_highlight(self.selected)

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

    def set_ptype(self, _evt):
        self.data.category = self.type_var.get()
        self.app.update_view()

    def update_program(self, data: ProgramData):
        self.data = data
        self.set_highlight(self.data.id == self.app.profile.selected_program.id)

        self.label_text.set(time_to_str(data.time))
        self.button_text.set(data.id)
        self.pinned_var.set(data.visibility == P_VIS_PINNED)
        self.type_var.set(data.category)

    def set_highlight(self, selected: bool):
        if self.selected == selected: return
        self.selected = selected
        color = self.app.config.get_color("active" if selected else "unselected")
        self.frame.configure(bg = color)
        self.label.configure(background = color)

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

        # Structure
        self.session_timer_label.pack()
        self.timer_label.pack()
        self.frame.pack()

        # Event handlers
        self.window.protocol("WM_DELETE_WINDOW", self.app.handle_close)

    def set_task(self, task: ProgramData):
        self.app.profile.selected_program = task
        self.update()

    def update(self):
        task = self.app.profile.selected_program
        bg_color = self.app.config.get_color("active" if self.app.active_window == task.id else "idle", "#ffffff") 
        self.session_timer_label.configure(background=bg_color, text=time_to_str(task.session_time))
        self.timer_label.configure(background=bg_color, text=f"({time_to_str(task.time)})")
        self.window.configure(bg=bg_color)
        self.frame.configure(bg=bg_color)

class CategoryInfoWidget:
    def __init__(self, app: "App", root: tk.Tk, category: str):
        self.app = app
        self.category = category
        self.root = root
        self.frame = tk.Frame(master = root)
        self.title_label = ttk.Label(master = self.frame, text = category or "Total", font = app.config.label_font_mini)
        self.time_var = tk.StringVar(value = f"{app.profile.get_category_time(category)}")
        self.time_session_var = tk.StringVar(value = f"({app.profile.get_category_session_time(category)})")
        self.timer_label = ttk.Label(master = self.frame, textvariable = self.time_var, font = app.config.label_font)
        self.session_timer_label = ttk.Label(master = self.frame, textvariable = self.time_session_var, font = app.config.label_font_mini)

        # Structure
        self.title_label.pack()
        self.timer_label.pack()
        self.session_timer_label.pack()
        self.frame.pack(side='left', padx=10, fill="x")

    def update(self):
        self.time_var.set(f"{time_to_str(self.app.profile.get_category_time(self.category))}")
        self.time_session_var.set(f"({time_to_str(self.app.profile.get_category_session_time(self.category))})")

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
        self.category_widgets = {
            category: CategoryInfoWidget(self, self.category_panel, category) for category in self.config.categories + [""]
        }
        self.active_window = None

        # Event handlers
        self.window.protocol("WM_DELETE_WINDOW", self.handle_close)

        # Structure
        self.category_panel.pack(side = 'top')

        # Styling
        danger_btn_style = ttk.Style()
        danger_btn_style.configure("Danger.TButton", background="#ff8888")

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
            self.data_widgets.append(TimeWidget(self, self.window))
        while len(self.data_widgets) > len(keys):
            self.data_widgets.pop().frame.destroy()
        for k,widget in zip(keys,self.data_widgets):
            widget.update_program(self.profile.programs[k])
