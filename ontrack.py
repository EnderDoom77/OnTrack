import pygetwindow as gw
import asyncio
import time
import psutil
import win32process as wproc

from config import Config
from data import Profile, ProgramData
import gui
from lib.processes import get_active_pid, try_get_proc_name

last_checked = time.time()
active_window = None

config = Config.load()
config.save() # ensure all fields are in the file and the file is generated if it doesn't exist
data = Profile.load(config)
data.save() # ensure we have at least a blank database file

async def main():
    autosave_time = 0
    update_time = 0
    app = gui.App(config, data)
    while True:
        app.window.update()
        if app.has_quit: break
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

    # timer update
    now = time.time()
    delta_time = now - last_checked
    last_checked = now

    pid = get_active_pid()
    if (pid == None): return
    app_name = try_get_proc_name(pid, True)
    if (app_name == None): return
    active_window = app_name
    
    program = data.get_program(app_name)
    if (program != None):
        program.time += delta_time
        program.session_time += delta_time

asyncio.run(main())
