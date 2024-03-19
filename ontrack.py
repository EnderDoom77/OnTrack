import pygetwindow as gw
import asyncio
import time

from config import Config
from data import Profile, ProgramData
import gui

last_checked = time.time()
active_window = None

data = Profile.load()
data.save() # ensure we have at least a blank database file
config = Config.load()
config.save() # ensure all fields are in the file and the file is generated if it doesn't exist

async def main():
    autosave_time = 0
    update_time = 0
    app = gui.App(config, data)
    while True:
        app.window.update()
        t = time.time()
        if t > update_time:
            add_data()
            update_time = t + config.update_interval
            app.update_data(active_window)
            app.timer_window.update()
        if t > autosave_time:
            data.save()
            autosave_time = t + config.autosave_interval

def add_data():
    global data
    global last_checked
    global active_window
    win = gw.getActiveWindow()
    if not win:
        return
    win_title : str = win.title
    win_app = win_title.split("-")[-1].strip()
    active_window = win_app
    now = time.time()
    
    for ss in config.banner_substrings:
        if ss in win_title:
            break
    else:
        data.get_program(win_app).time += now - last_checked
    
    last_checked = now

asyncio.run(main())
