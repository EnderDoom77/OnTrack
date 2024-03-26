import math

def distance2d(x: tuple[float, float], y: tuple[float, float]):
    return math.sqrt((x[0] - y[0])**2 + (x[1] - y[1])**2)

def time_to_str(time: float) -> str:
    secs = int(time % 60)
    mins_tot = int(time // 60)
    mins = mins_tot % 60
    hours = mins_tot // 60
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

def clamp(x, a, b):
    return max(a, min(b, x))