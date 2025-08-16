import cv2
import numpy as np
import time
import math

TOP_LEFT = 0
TOP_RIGHT = 1
BOT_RIGHT = 3
BOT_LEFT = 2

def scanForNonZeroHorizontal(input_frame, start_x, start_y, stop_x, stop_y, step_x, step_y, step_multiplier, debug_frame):
    for y in range(start_y, stop_y, step_y * step_multiplier):

        a, b = calculate_ab_line(start_x, start_y, stop_x, y)
        for px in range(start_x, stop_x, step_x):
            py = int(a * px + b) if a != 0 else y
            if debug_frame is not None:
                debug_frame[py, px] = [0, 0, 230]

            if input_frame[py,px] != 0:
                dx, dy = scanBackwardsHorizontal(input_frame, start_x, start_y, stop_x, y, step_x, -step_y, px, py, debug_frame)  
                return (dx, dy)
    return None, None
            

def scanBackwardsHorizontal(input_frame, start_x, start_y, stop_x, stop_y, step_x, step_y, detected_x, detected_y, debug_frame):
    dx, dy = detected_x, detected_y
    for y in range(stop_y, start_y, step_y):

        found_pixel = False
        a, b = calculate_ab_line(start_x, start_y, stop_x, y)
        for px in range(start_x, stop_x, step_x):
            py = int(a * px + b) if a != 0 else y
            if debug_frame is not None:
                debug_frame[py, px] = [230, 0, 230]

            if input_frame[py,px] != 0:  
                found_pixel = True
                dx, dy = px, py
                break
        if not found_pixel:
            return dx, dy
    return None, None


def scanForNonZeroVertical(input_frame, start_x, start_y, stop_x, stop_y, step_x, step_y, step_multiplier, debug_frame):

    for x in range(start_x, stop_x, step_x * step_multiplier):

        a, b = calculate_ab_line(start_x, start_y, x, stop_y)
        for py in range(start_y, stop_y, step_y):
            px = int((py - b) / a) if a != 0 else x
            if debug_frame is not None:
                debug_frame[py, px] = [0, 230, 0]
            if input_frame[py,px] != 0:
                dx, dy = scanBackwardsVertical(input_frame, start_x, start_y, x, stop_y, -step_x, step_y, px, py, debug_frame)
                return dx, dy
    return None, None

def scanBackwardsVertical(input_frame, start_x, start_y, stop_x, stop_y, step_x, step_y, detected_x, detected_y, debug_frame):
    dx, dy = detected_x, detected_y
    for x in range(stop_x, start_x, step_x):

        found_pixel = False
        for py in range(start_y, stop_y, step_y):
            a, b = calculate_ab_line(start_x, start_y, x, stop_y)
            px = int((py - b) / a) if a != 0 else x

            if debug_frame is not None:
                debug_frame[py, px] = [150, 230, 150]

            if input_frame[py,px] != 0:  
                found_pixel = True
                dx, dy = px, py
                break    
        if not found_pixel:
            return dx, dy
    return None, None
            
def detectCornersHorizontal(input_frame, debug_frame, step_multiplier:int):

    width = input_frame.shape[1]
    height = input_frame.shape[0]
    corners = []
    px, py = scanForNonZeroHorizontal(input_frame, int(width / 2), 1, 1, height, -1, 1, step_multiplier, debug_frame)
    corners.append(['top-left', px, py])

    px, py = scanForNonZeroHorizontal(input_frame, int(width / 2), 1, width, height, 1, 1, step_multiplier, debug_frame)
    corners.append(['top-right', px, py])

    px, py = scanForNonZeroHorizontal(input_frame, int(width / 2), height-1, width-1, 1, 1, -1, step_multiplier, debug_frame)
    corners.append(['bot-right', px, py])

    px, py = scanForNonZeroHorizontal(input_frame, int(width / 2), height -1, 1, 1, -1, -1, step_multiplier, debug_frame)
    corners.append(['bot-left', px, py])

    return corners

def detectCornersVertical(input_frame, debug_frame, step_multiplier:int):
    width = input_frame.shape[1]
    height = input_frame.shape[0]

    corners = []
    px, py = scanForNonZeroVertical(input_frame, 0, int(height / 2), width - 1, 0, 1, -1, step_multiplier, debug_frame)
    corners.append(['top-left', px, py])

    px, py = scanForNonZeroVertical(input_frame, width - 1, int(height / 2), 0, 0, -1, -1, step_multiplier, debug_frame)
    corners.append(['top-right', px, py])

    px, py = scanForNonZeroVertical(input_frame, 0, int(height / 2), width - 1, height - 1, 1, 1, step_multiplier, debug_frame)
    corners.append(['bot-left', px, py])

    px, py = scanForNonZeroVertical(input_frame, width - 1, int(height / 2), 0, height - 1, -1, 1, step_multiplier, debug_frame)
    corners.append(['bot-right', px, py])
    return corners

def find_intersection_from_corners(corners):

    for c in corners:
        if c[1] is None or c[2] is None:
            return None, None

    #print(corners)

    a1, b1 = calculate_ab_line(corners[0][1], corners[0][2], corners[2][1], corners[2][2])
    a2, b2 = calculate_ab_line(corners[1][1], corners[1][2], corners[3][1], corners[3][2])
    x, y = find_intersection_from_ab(a1, b1, a2, b2)
    if x is None or y is None:
        return None, None
    return int(x), int(y)


def find_intersection_from_ab(a1, b1, a2, b2):

    if a1 - a2 == 0:
        print("ALARM ALARM", a1, a2)
        return None, None

    x = (b2 - b1) / (a1 - a2)
    y = a1 * x + b1
    return x, y
    

def calculate_ab_line(x1, y1, x2, y2):
    a = None
    if x2 - x1 == 0:
        a = 1000
    elif y2 - y1 == 0:
        a = 0
    else:
        a = (y2 - y1) / (x2 - x1)
    b = y1 - a * x1
    return a, b

def ab_value(x, a, b):
    return a * x + b

def calculate_tilt(x1, y1, x2, y2):

    if x1 is None or x2 is None or y1 is None or y2 is None:
        print("CHUJ DUPA")
        return None

    dy = y2 - y1
    dx = x2 - x1
    theta = math.atan2(dy, dx)
    theta *= 180 / math.pi
    return theta

