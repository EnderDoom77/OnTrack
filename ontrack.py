import pygetwindow as gw
import asyncio
import json
import time
from collections import defaultdict

from config import Config
import gui

all_data = defaultdict(float)
last_checked = time.time()
active_window = None

config = Config.load()
config.save() # ensure all fields are in the file and the file is generated if it doesn't exist

async def main():
    autosave_time = 0
    update_time = 0
    app = gui.App(config)
    while True:
        app.window.update()
        t = time.time()
        if t > update_time:
            add_data()
            update_time = t + config.update_interval
            app.update_data(all_data, active_window)
            app.timer_window.update(all_data)
        if t > autosave_time:
            autosave()
            autosave_time = t + config.autosave_interval

def autosave():
    write_data(all_data)

def add_data():
    global all_data
    global last_checked
    global active_window
    win = gw.getActiveWindow()
    if not win:
        return
    win_title : str = win.title
    win_app = win_title.split("-")[-1].strip()
    active_window = win_app
    now = time.time()
    all_data[win_app] += now - last_checked
    last_checked = now 
    
DB_FILE = "db.json"
def load_data() -> dict:
    try:
        with open(DB_FILE) as f:
            all_data = json.load(f)
    except:
        write_data({})
    else:
        return all_data
    return {}
def write_data(data: dict):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)


saved_data = load_data()
for k,v in saved_data.items():
    all_data[k] = v

asyncio.run(main())
