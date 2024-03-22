import math

def distance2d(x: tuple[float, float], y: tuple[float, float]):
    return math.sqrt((x[0] - y[0])**2 + (x[1] - y[1])**2)