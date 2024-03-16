import tkinter as tk
from tkinter import ttk
from threading import Thread

from config import Config

def time_to_str(time: float) -> str:
    secs = int(time % 60)
    mins_tot = int(time // 60)
    mins = mins_tot % 60
    hours = mins_tot // 60
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

class TimeWidget:
    def __init__(self, app: "App", root: tk.Tk, name: str, time: float, font:str = "Calibri 24"):
        def set_task():
            app.set_task(name)
        self.root = root
        self.frame = ttk.Frame(master = root)
        self.name = name
        self.time = time
        self.task_button = ttk.Button(self.frame, text = name, command = set_task)
        time_str = time_to_str(time)
        self.label = ttk.Label(master = self.frame, text=f"{time_str}", font=font)
        self.task_button.pack(side = 'left')
        self.label.pack(side = 'left', padx = 10)
        self.frame.pack()

    def update_label(self):
        self.label

class TimerWindow:
    def __init__(self, app: "App", key: str):
        self.app = app
        self.window = tk.Tk()
        self.window.lift()
        self.window.attributes("-topmost", True)
        self.window.geometry("250x50")
        self.window.title("Timer - OnTrack")
        self.key = key
        self.label = ttk.Label(master = self.window, text="00:00:00", font="Calibri 24")
        self.label.pack()

    def update(self, data: dict):
        if self.key not in data:
            return

        bg_color = self.app.config.get_color("active" if self.app.active_window == self.key else "idle", "#ffffff") 
        self.label.destroy()
        self.label = ttk.Label(master = self.window, text = time_to_str(data[self.key]), background=bg_color, font="Calibri 24")
        self.label.pack()
        self.window.configure(bg=bg_color)

class App:    
    def __init__(self, config: Config):
        self.config = config
        self.window = tk.Tk()
        self.timer_window = TimerWindow(self, "Visual Studio Code")
        self.window.title("OnTrack")
        self.window.geometry('300x150')
        self.data_widgets : list[TimeWidget] = []
        self.active_window = None

    def set_task(self, name):
        self.timer_window.key = name

    def update_data(self, data: dict, active_window: str | None):
        self.active_window = active_window
        for dw in self.data_widgets:
            dw.frame.destroy()
        self.data_widgets = []
        keys = sorted(data.keys(), key = lambda i: -data[i])
        for k in keys:
            time_widget = TimeWidget(self, self.window, k, data[k])
            self.data_widgets.append(time_widget)