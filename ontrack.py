import keyboard
import pygetwindow as gw
import asyncio
import time

from config import Config
from data import Profile, ProgramData
import gui
from lib.processes import get_active_pid, try_get_proc_name
from lib.mathlib import distance2d

last_checked = time.time()
active_window = None

config = Config.load()
config.save() # ensure all fields are in the file and the file is generated if it doesn't exist
data = Profile.load(config)
data.save() # ensure we have at least a blank database file
frame_rate = 60
frame_time = 1 / frame_rate

async def main():
    autosave_time = 0
    update_time = 0
    next_refresh = time.time()
    app = gui.App(config, data)
    keyboard.hook(handle_keypress)
    # app.window.bind('<Motion>', handle_mouse)
    while True:
        app.window.update()
        now = time.time()
        await asyncio.sleep(next_refresh - now)
        next_refresh += frame_time
        if app.has_quit: break
        t = time.time()
        if t > update_time:
            handle_mouse(app.window.winfo_pointerx(), app.window.winfo_pointery())
            add_data()
            update_time = t + config.update_interval
            data.afk_time += config.update_interval
            app.update_data(active_window)
            app.timer_window.update()
        if t > autosave_time:
            data.save()
            autosave_time = t + config.autosave_interval

def handle_keypress(_evt: keyboard.KeyboardEvent):
    data.afk_time = 0
    # print("Detected keypress, resetting AFK timer.")
mouse_px = 0
mouse_py = 0
def handle_mouse(px, py):
    global mouse_px, mouse_py
    if (distance2d((mouse_px, mouse_py), (px, py)) < 1): return
    (mouse_px, mouse_py) = (px, py)
    data.afk_time = 0
    # print("Detected mouse movement, resetting AFK timer.")

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
        if (program.has_afk_timer() and data.afk_time >= config.afk_timeout):
            return
        program.add_time(delta_time)
        
asyncio.run(main())
