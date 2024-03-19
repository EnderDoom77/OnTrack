import pygetwindow as gw
import psutil as ps
import win32process as wproc

def get_active_pid() -> int | None:
    win = gw.getActiveWindow()
    if not win:
        return
    tId, pId = wproc.GetWindowThreadProcessId(win._hWnd)
    return pId

def try_get_proc_name(pid, dropExtension):
    try:
        proc = ps.Process(pid)
        pname = proc.name()
        last_dot = pname.find(".")
        if (dropExtension and last_dot > 0): # if a file starts with a ".", or doesn't contain a "." keep it as-is
            pname = pname[:last_dot]
        return pname
    except:
        return None