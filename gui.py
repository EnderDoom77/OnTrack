import tkinter as tk
from tkinter import ttk
from threading import Thread

from config import Config
from data import *

def time_to_str(time: float) -> str:
    secs = int(time % 60)
    mins_tot = int(time // 60)
    mins = mins_tot % 60
    hours = mins_tot // 60
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

DEFAULT_PROGRAM_DATA = ProgramData("")
class TimeWidget:
    def __init__(self, app: "App", root: tk.Tk, program_data: ProgramData = DEFAULT_PROGRAM_DATA):
        self.app = app
        self.root = root
        self.frame = ttk.Frame(master = root)
        self.data = program_data

        # Widgets & Variables
        self.label_text = tk.StringVar(value = time_to_str(program_data.time))
        self.label = ttk.Label(master = self.frame, textvariable = self.label_text, font = app.config.label_font)
        self.button_text = tk.StringVar(value = program_data.id)
        self.task_button = ttk.Button(self.frame, textvariable = self.button_text, command = self.set_task)
        self.pinned_var = tk.BooleanVar(value = program_data.visibility == P_VIS_PINNED)
        self.pin_checkbox = ttk.Checkbutton(self.frame, text = "Pin", variable = self.pinned_var, command=self.set_pinned)
        
        # Structure
        self.task_button.pack(side = 'left')
        self.label.pack(side = 'left', padx = 10)
        self.pin_checkbox.pack(side = 'left', padx = 10)
        self.frame.pack()

    def set_task(self):
        self.app.set_task(self.data)

    def set_pinned(self):
        pinned = self.pinned_var.get()
        self.data.visibility = P_VIS_PINNED if pinned else P_VIS_DEFAULT
        self.app.update_view()

    def update_program(self, data: ProgramData):
        self.data = data
        self.label_text.set(time_to_str(data.time))
        self.button_text.set(data.id)
        self.pinned_var.set(data.visibility == P_VIS_PINNED)

class TimerWindow:
    def __init__(self, app: "App", task: ProgramData = DEFAULT_PROGRAM_DATA):
        self.app = app
        self.window = tk.Tk()
        self.window.lift()
        self.window.attributes("-topmost", True)
        self.window.geometry("276x50")
        self.window.title("Timer - OnTrack")
        self.task = task

        self.frame = ttk.Frame(master = self.window)
        self.label = ttk.Label(master = self.frame, text="00:00:00", font=app.config.label_font)
        self.label.pack()
        self.frame.pack()

    def set_task(self, task: ProgramData):
        self.task = task
        self.update()

    def update(self):
        bg_color = self.app.config.get_color("active" if self.app.active_window == self.task.id else "idle", "#ffffff") 
        self.label.configure(background=bg_color, text=time_to_str(self.task.time))
        self.window.configure(bg=bg_color)

class App:    
    def __init__(self, config: Config, data: Profile):
        self.config = config
        self.window = tk.Tk()
        self.profile = data

        self.timer_window = TimerWindow(self)
        self.window.title("OnTrack")
        self.window.geometry('800x600')
        self.data_widgets : list[TimeWidget] = []
        self.active_window = None

    def set_task(self, task: ProgramData):
        self.timer_window.set_task(task)

    def update_data(self, active_window: str | None):
        self.active_window = active_window
        self.update_view()
    
    def update_view(self):
        eligible_keys = [k for k in self.profile.programs.keys() if self.profile.programs[k].is_visible()]
        keys = sorted(eligible_keys, key = lambda i: (self.profile.programs[i].sortkey()))
        while len(self.data_widgets) < len(keys):
            self.data_widgets.append(TimeWidget(self, self.window))
        while len(self.data_widgets) > len(keys):
            self.data_widgets.pop().frame.destroy()
        for k,widget in zip(keys,self.data_widgets):
            widget.update_program(self.profile.programs[k])