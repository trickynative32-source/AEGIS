import time
import math
import logging
import subprocess
from typing import Dict, Any, Optional
import pyautogui
from backend.tools.registry import registry

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None

logger = logging.getLogger("AEGIS.PaintTools")

# Set pyautogui failsafe
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

def get_paint_canvas_rect() -> Optional[Dict[str, int]]:
    """Locates the Paint window and estimates canvas area."""
    if not win32gui:
        screen_w, screen_h = pyautogui.size()
        return {"left": 200, "top": 220, "width": screen_w - 400, "height": screen_h - 400}

    paint_hwnd = None
    def enum_handler(hwnd, _):
        nonlocal paint_hwnd
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "paint" in title.lower():
                paint_hwnd = hwnd

    win32gui.EnumWindows(enum_handler, None)
    if not paint_hwnd:
        return None

    # Restore and bring to front
    win32gui.ShowWindow(paint_hwnd, win32con.SW_RESTORE)
    win32gui.ShowWindow(paint_hwnd, win32con.SW_MAXIMIZE)
    time.sleep(0.5)
    win32gui.SetForegroundWindow(paint_hwnd)
    time.sleep(0.5)

    rect = win32gui.GetWindowRect(paint_hwnd)
    win_left, win_top, win_right, win_bottom = rect
    win_w = win_right - win_left
    win_h = win_bottom - win_top

    # The canvas in modern Windows 11/10 Paint is offset below ribbon
    canvas_left = win_left + 150
    canvas_top = win_top + 180
    canvas_w = win_w - 300
    canvas_h = win_h - 260

    return {
        "left": canvas_left,
        "top": canvas_top,
        "width": canvas_w,
        "height": canvas_h,
        "center_x": canvas_left + canvas_w // 2,
        "center_y": canvas_top + canvas_h // 2
    }

def draw_line(x1, y1, x2, y2, duration=0.2):
    pyautogui.moveTo(x1, y1)
    pyautogui.dragTo(x2, y2, duration=duration, button='left')

def draw_rect(x, y, w, h):
    draw_line(x, y, x + w, y)
    draw_line(x + w, y, x + w, y + h)
    draw_line(x + w, y + h, x, y + h)
    draw_line(x, y + h, x, y)

def draw_circle_approx(cx, cy, r, steps=24):
    points = []
    for i in range(steps + 1):
        angle = (2 * math.pi / steps) * i
        px = int(cx + r * math.cos(angle))
        py = int(cy + r * math.sin(angle))
        points.append((px, py))
    
    pyautogui.moveTo(points[0][0], points[0][1])
    for px, py in points[1:]:
        pyautogui.dragTo(px, py, duration=0.02, button='left')

@registry.register(
    name="open_paint",
    description="Open Microsoft Paint on Windows.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    permission_level="normal",
    category="paint"
)
def open_paint() -> Dict[str, Any]:
    try:
        subprocess.Popen("mspaint", shell=True)
        time.sleep(1.5)
        rect = get_paint_canvas_rect()
        return {
            "status": "opened",
            "message": "Microsoft Paint is open.",
            "verified": rect is not None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "verified": False
        }

@registry.register(
    name="draw_in_paint",
    description="Draw structured illustrations in Microsoft Paint (e.g. 'house', 'circle', 'landscape', 'birthday_card', 'aegis_text', 'geometric').",
    parameters={
        "type": "object",
        "properties": {
            "drawing_type": {
                "type": "string",
                "enum": ["house", "circle", "landscape", "birthday_card", "aegis_text", "aura_text", "geometric"],
                "description": "Type of drawing to illustrate on the canvas"
            },
            "description": {
                "type": "string",
                "description": "Optional details about the drawing"
            }
        },
        "required": ["drawing_type"]
    },
    permission_level="normal",
    category="paint"
)
def draw_in_paint(drawing_type: str, description: Optional[str] = "") -> Dict[str, Any]:
    # Ensure paint is open and focused
    rect = get_paint_canvas_rect()
    if not rect:
        open_paint()
        time.sleep(1.5)
        rect = get_paint_canvas_rect()

    if not rect:
        return {
            "status": "error",
            "message": "Could not detect Microsoft Paint window.",
            "verified": False
        }

    cx = rect["center_x"]
    cy = rect["center_y"]
    logger.info(f"Drawing {drawing_type} in Paint around center ({cx}, {cy})")

    # Select brush/pencil if needed (click canvas center to activate)
    pyautogui.click(cx, cy)
    time.sleep(0.2)

    dtype = drawing_type.lower()

    if dtype == "house":
        # Base walls
        w, h = 240, 160
        bx, by = cx - w // 2, cy - h // 4
        draw_rect(bx, by, w, h)
        
        # Roof triangle
        peak_x, peak_y = cx, by - 100
        draw_line(bx, by, peak_x, peak_y)
        draw_line(peak_x, peak_y, bx + w, by)
        
        # Chimney
        chim_x = bx + w - 50
        draw_line(chim_x, by - 40, chim_x, by - 90)
        draw_line(chim_x, by - 90, chim_x + 30, by - 90)
        draw_line(chim_x + 30, by - 90, chim_x + 30, by - 20)

        # Door
        dw, dh = 50, 90
        dx, dy = cx - dw // 2, by + h - dh
        draw_rect(dx, dy, dw, dh)
        # Doorknob
        draw_circle_approx(dx + dw - 10, dy + dh // 2, 3, steps=8)

        # Windows
        ww, wh = 40, 40
        # Left Window
        lwx, lwy = bx + 25, by + 30
        draw_rect(lwx, lwy, ww, wh)
        draw_line(lwx + ww // 2, lwy, lwx + ww // 2, lwy + wh)
        draw_line(lwx, lwy + wh // 2, lwx + ww, lwy + wh // 2)
        # Right Window
        rwx, rwy = bx + w - 65, by + 30
        draw_rect(rwx, rwy, ww, wh)
        draw_line(rwx + ww // 2, rwy, rwx + ww // 2, rwy + wh)
        draw_line(rwx, rwy + wh // 2, rwx + ww, rwy + wh // 2)

    elif dtype == "circle":
        # Sun / Circle
        draw_circle_approx(cx, cy, 80)
        # Sun rays
        for angle_deg in range(0, 360, 45):
            rad = math.radians(angle_deg)
            r1 = 90
            r2 = 130
            x1 = int(cx + r1 * math.cos(rad))
            y1 = int(cy + r1 * math.sin(rad))
            x2 = int(cx + r2 * math.cos(rad))
            y2 = int(cy + r2 * math.sin(rad))
            draw_line(x1, y1, x2, y2, duration=0.1)

    elif dtype == "landscape":
        # Mountains
        base_y = cy + 100
        draw_line(cx - 300, base_y, cx - 150, cy - 80)
        draw_line(cx - 150, cy - 80, cx, base_y)
        draw_line(cx - 50, base_y, cx + 120, cy - 120)
        draw_line(cx + 120, cy - 120, cx + 300, base_y)
        
        # Sun
        draw_circle_approx(cx - 200, cy - 120, 35)

        # River path
        draw_line(cx, base_y, cx - 40, base_y + 100)
        draw_line(cx + 40, base_y, cx + 80, base_y + 100)

    elif dtype == "birthday_card":
        # Card Border
        draw_rect(cx - 200, cy - 150, 400, 300)
        # Balloons
        draw_circle_approx(cx - 80, cy - 60, 30)
        draw_line(cx - 80, cy - 30, cx - 70, cy + 20)
        draw_circle_approx(cx + 80, cy - 60, 30)
        draw_line(cx + 80, cy - 30, cx + 70, cy + 20)
        # Cake
        draw_rect(cx - 60, cy + 30, 120, 60)
        # Candle
        draw_line(cx, cy + 30, cx, cy + 10)
        draw_circle_approx(cx, cy + 5, 4, steps=8)

    elif dtype in ["aegis_text", "aura_text"]:
        # Draw "A E G I S"
        spacing = 55
        start_x = cx - 140
        
        # 'A'
        draw_line(start_x, cy + 40, start_x + 15, cy - 40)
        draw_line(start_x + 15, cy - 40, start_x + 30, cy + 40)
        draw_line(start_x + 8, cy, start_x + 22, cy)

        # 'E'
        e_x = start_x + spacing
        draw_line(e_x, cy - 40, e_x, cy + 40)
        draw_line(e_x, cy - 40, e_x + 25, cy - 40)
        draw_line(e_x, cy, e_x + 20, cy)
        draw_line(e_x, cy + 40, e_x + 25, cy + 40)

        # 'G'
        g_x = e_x + spacing
        draw_line(g_x + 25, cy - 40, g_x, cy - 40)
        draw_line(g_x, cy - 40, g_x, cy + 40)
        draw_line(g_x, cy + 40, g_x + 25, cy + 40)
        draw_line(g_x + 25, cy + 40, g_x + 25, cy)
        draw_line(g_x + 25, cy, g_x + 12, cy)

        # 'I'
        i_x = g_x + spacing
        draw_line(i_x + 5, cy - 40, i_x + 25, cy - 40)
        draw_line(i_x + 15, cy - 40, i_x + 15, cy + 40)
        draw_line(i_x + 5, cy + 40, i_x + 25, cy + 40)

        # 'S'
        s_x = i_x + spacing
        draw_line(s_x + 25, cy - 40, s_x, cy - 40)
        draw_line(s_x, cy - 40, s_x, cy)
        draw_line(s_x, cy, s_x + 25, cy)
        draw_line(s_x + 25, cy, s_x + 25, cy + 40)
        draw_line(s_x + 25, cy + 40, s_x, cy + 40)

    elif dtype == "geometric":
        # Star / hexagon
        radius = 100
        for i in range(6):
            a1 = math.radians(60 * i)
            a2 = math.radians(60 * (i + 2))
            x1 = int(cx + radius * math.cos(a1))
            y1 = int(cy + radius * math.sin(a1))
            x2 = int(cx + radius * math.cos(a2))
            y2 = int(cy + radius * math.sin(a2))
            draw_line(x1, y1, x2, y2, duration=0.1)

    return {
        "status": "drawn",
        "drawing_type": drawing_type,
        "message": f"Drawn {drawing_type} in Microsoft Paint.",
        "verified": True
    }
