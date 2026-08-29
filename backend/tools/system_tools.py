import datetime
import os
import platform
import psutil
from typing import Dict, Any
from backend.tools.registry import registry

@registry.register(
    name="get_system_time",
    description="Get the exact current local system time from the real Windows system clock.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    permission_level="normal",
    category="system"
)
def get_system_time() -> Dict[str, Any]:
    now = datetime.datetime.now()
    hour = int(now.strftime("%I"))
    minute = now.strftime("%M")
    ampm = now.strftime("%p")
    time_str = f"{hour}:{minute} {ampm}"  # e.g., "12:07 AM", "5:30 PM"
    return {
        "time": time_str,
        "raw_time": now.strftime("%H:%M:%S"),
        "timezone": str(datetime.datetime.now().astimezone().tzinfo),
        "message": f"The current time is {time_str}."
    }

@registry.register(
    name="get_system_date",
    description="Get the exact current date, day of the week, and year from the real Windows system clock.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    permission_level="normal",
    category="system"
)
def get_system_date() -> Dict[str, Any]:
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")  # e.g. "Thursday, August 27, 2026"
    return {
        "date": date_str,
        "day": now.strftime("%A"),
        "month": now.strftime("%B"),
        "day_number": now.day,
        "year": now.year,
        "message": f"Today is {date_str}."
    }

@registry.register(
    name="get_system_info",
    description="Get current computer hardware and OS telemetry (CPU, RAM, Battery, OS).",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    permission_level="normal",
    category="system"
)
def get_system_info() -> Dict[str, Any]:
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    
    battery_info = "No battery detected (Desktop)"
    if battery:
        battery_info = f"{battery.percent}% ({'Plugged in' if battery.power_plugged else 'On Battery'})"

    return {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu_usage": f"{cpu_percent}%",
        "ram_usage": f"{ram.percent}% (Used: {ram.used // (1024**2)} MB / Total: {ram.total // (1024**2)} MB)",
        "battery": battery_info,
        "hostname": platform.node(),
        "username": os.getlogin() if hasattr(os, "getlogin") else "User"
    }

@registry.register(
    name="set_volume",
    description="Adjust system volume level or mute/unmute.",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["up", "down", "mute", "unmute"],
                "description": "Volume action to perform"
            }
        },
        "required": ["action"]
    },
    permission_level="normal",
    category="system"
)
def set_volume(action: str) -> Dict[str, Any]:
    import pyautogui
    if action == "up":
        pyautogui.press("volumeup", presses=5)
        return {"status": "Volume increased"}
    elif action == "down":
        pyautogui.press("volumedown", presses=5)
        return {"status": "Volume decreased"}
    elif action in ["mute", "unmute"]:
        pyautogui.press("volumemute")
        return {"status": "Volume toggle mute"}
    return {"status": "Unknown volume action"}
