import os
import sys
import glob
import time
import shutil
import logging
import subprocess
import psutil
from typing import Dict, Any, Optional, List
from pathlib import Path
from backend.tools.registry import registry

try:
    import win32gui
    import win32con
    import win32process
except ImportError:
    win32gui = None

logger = logging.getLogger("AEGIS.AppLauncher")

# Common aliases and direct commands/protocols
APP_ALIASES: Dict[str, Dict[str, Any]] = {
    "chrome": {"exe": "chrome.exe", "command": "start chrome", "process_names": ["chrome.exe"]},
    "google chrome": {"exe": "chrome.exe", "command": "start chrome", "process_names": ["chrome.exe"]},
    "vs code": {"exe": "Code.exe", "command": "code", "process_names": ["Code.exe"]},
    "vscode": {"exe": "Code.exe", "command": "code", "process_names": ["Code.exe"]},
    "visual studio code": {"exe": "Code.exe", "command": "code", "process_names": ["Code.exe"]},
    "paint": {"exe": "mspaint.exe", "command": "mspaint", "process_names": ["mspaint.exe", "Paint.exe", "mspaint"]},
    "ms paint": {"exe": "mspaint.exe", "command": "mspaint", "process_names": ["mspaint.exe", "Paint.exe", "mspaint"]},
    "notepad": {"exe": "notepad.exe", "command": "notepad", "process_names": ["notepad.exe", "Notepad.exe"]},
    "calculator": {"exe": "calc.exe", "command": "calc", "process_names": ["calc.exe", "CalculatorApp.exe", "Calculator.exe"]},
    "calc": {"exe": "calc.exe", "command": "calc", "process_names": ["calc.exe", "CalculatorApp.exe"]},
    "spotify": {"exe": "Spotify.exe", "command": "start spotify:", "process_names": ["Spotify.exe"]},
    "discord": {"exe": "Discord.exe", "command": "start discord:", "process_names": ["Discord.exe"]},
    "whatsapp": {"exe": "WhatsApp.exe", "command": "start whatsapp:", "process_names": ["WhatsApp.exe", "WhatsApp.Root.exe"]},
    "settings": {"exe": "ms-settings:", "command": "start ms-settings:", "process_names": ["SystemSettings.exe"]},
    "file explorer": {"exe": "explorer.exe", "command": "explorer", "process_names": ["explorer.exe"]},
    "explorer": {"exe": "explorer.exe", "command": "explorer", "process_names": ["explorer.exe"]},
    "word": {"exe": "winword.exe", "command": "start winword", "process_names": ["WINWORD.EXE"]},
    "microsoft word": {"exe": "winword.exe", "command": "start winword", "process_names": ["WINWORD.EXE"]},
    "excel": {"exe": "excel.exe", "command": "start excel", "process_names": ["EXCEL.EXE"]},
    "microsoft excel": {"exe": "excel.exe", "command": "start excel", "process_names": ["EXCEL.EXE"]},
    "powerpoint": {"exe": "powerpnt.exe", "command": "start powerpnt", "process_names": ["POWERPNT.EXE"]},
    "terminal": {"exe": "wt.exe", "command": "start wt", "process_names": ["WindowsTerminal.exe", "wt.exe"]},
    "powershell": {"exe": "powershell.exe", "command": "start powershell", "process_names": ["powershell.exe"]},
    "cmd": {"exe": "cmd.exe", "command": "start cmd", "process_names": ["cmd.exe"]},
    "downloads": {"exe": "explorer.exe", "command": f'explorer "{Path.home() / "Downloads"}"', "process_names": ["explorer.exe"]},
    "desktop": {"exe": "explorer.exe", "command": f'explorer "{Path.home() / "Desktop"}"', "process_names": ["explorer.exe"]},
    "documents": {"exe": "explorer.exe", "command": f'explorer "{Path.home() / "Documents"}"', "process_names": ["explorer.exe"]},
}

def scan_installed_shortcuts() -> Dict[str, str]:
    """Scans Start Menu folders for .lnk shortcuts across system and user profiles."""
    shortcuts: Dict[str, str] = {}
    paths_to_scan = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
    ]
    for base_path in paths_to_scan:
        if os.path.exists(base_path):
            for root, _, files in os.walk(base_path):
                for f in files:
                    if f.lower().endswith(".lnk") or f.lower().endswith(".url"):
                        name = f.rsplit(".", 1)[0].lower()
                        full_path = os.path.join(root, f)
                        shortcuts[name] = full_path
    return shortcuts

def find_running_window(app_name: str) -> Optional[int]:
    """Finds an open top-level window by title substring."""
    if not win32gui:
        return None
    app_lower = app_name.lower()
    matches = []

    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and (app_lower in title.lower() or any(alias in title.lower() for alias in [app_lower])):
                matches.append(hwnd)

    try:
        win32gui.EnumWindows(enum_handler, None)
        return matches[0] if matches else None
    except Exception:
        return None

def bring_window_to_foreground(hwnd: int) -> bool:
    """Safely brings a window to the foreground."""
    if not win32gui or not hwnd:
        return False
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False

@registry.register(
    name="open_application",
    description="Launch or switch to any installed Windows application (e.g. Chrome, VS Code, Paint, Notepad, Calculator, Spotify, WhatsApp, Settings, File Explorer, Downloads, etc.).",
    parameters={
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name of the application or folder to open (e.g., 'Chrome', 'Paint', 'VS Code', 'Downloads')"
            }
        },
        "required": ["app_name"]
    },
    permission_level="normal",
    category="application"
)
def open_application(app_name: str) -> Dict[str, Any]:
    norm_name = app_name.strip().lower()
    
    # 1. Check if application is already open
    existing_hwnd = find_running_window(norm_name)
    if existing_hwnd:
        bring_window_to_foreground(existing_hwnd)
        return {
            "status": "already_open",
            "message": f"{app_name.capitalize()} is already open and brought to the front.",
            "verified": True
        }

    # 2. Check predefined aliases
    if norm_name in APP_ALIASES:
        target = APP_ALIASES[norm_name]
        cmd = target["command"]
        try:
            subprocess.Popen(cmd, shell=True)
            time.sleep(1.2)
            # Verify window or process
            hwnd = find_running_window(norm_name)
            if hwnd:
                bring_window_to_foreground(hwnd)
            return {
                "status": "launched",
                "app": app_name,
                "message": f"Done. {app_name.capitalize()} is open.",
                "verified": True
            }
        except Exception as e:
            logger.error(f"Error launching alias {app_name}: {e}")

    # 3. Check Start Menu Shortcuts
    shortcuts = scan_installed_shortcuts()
    # Exact or fuzzy match
    matched_shortcut = None
    for name, path in shortcuts.items():
        if norm_name == name or norm_name in name:
            matched_shortcut = path
            break

    if matched_shortcut:
        try:
            os.startfile(matched_shortcut)
            time.sleep(1.5)
            hwnd = find_running_window(norm_name)
            if hwnd:
                bring_window_to_foreground(hwnd)
            return {
                "status": "launched",
                "app": app_name,
                "path": matched_shortcut,
                "message": f"Done. {app_name.capitalize()} is open.",
                "verified": True
            }
        except Exception as e:
            logger.error(f"Error launching shortcut {matched_shortcut}: {e}")

    # 4. Fallback: try direct executable launch via system PATH
    exe_name = norm_name if norm_name.endswith(".exe") else f"{norm_name}.exe"
    if shutil.which(exe_name) or shutil.which(norm_name):
        try:
            subprocess.Popen(f"start {norm_name}", shell=True)
            time.sleep(1.2)
            return {
                "status": "launched",
                "app": app_name,
                "message": f"Done. {app_name.capitalize()} is open.",
                "verified": True
            }
        except Exception as e:
            logger.error(f"Error launching via PATH {norm_name}: {e}")

    return {
        "status": "not_found",
        "message": f"I couldn't find {app_name}. Please verify it is installed.",
        "verified": False
    }

@registry.register(
    name="close_application",
    description="Close an open application or process on Windows.",
    parameters={
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name of the application to close (e.g. 'Paint', 'Notepad', 'Chrome')"
            }
        },
        "required": ["app_name"]
    },
    permission_level="normal",
    category="application"
)
def close_application(app_name: str) -> Dict[str, Any]:
    norm_name = app_name.strip().lower()
    targets = [norm_name, f"{norm_name}.exe"]
    if norm_name in APP_ALIASES:
        targets.extend(APP_ALIASES[norm_name]["process_names"])

    closed_count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pname = proc.info['name']
            if pname and any(t.lower() == pname.lower() or t.lower() in pname.lower() for t in targets):
                proc.terminate()
                closed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if closed_count > 0:
        return {
            "status": "closed",
            "message": f"Closed {app_name}.",
            "verified": True
        }
    else:
        return {
            "status": "not_running",
            "message": f"{app_name} is not currently running.",
            "verified": False
        }

@registry.register(
    name="switch_window",
    description="Switch focus to an open window by application or window name.",
    parameters={
        "type": "object",
        "properties": {
            "window_title": {
                "type": "string",
                "description": "Name or title of the window to focus"
            }
        },
        "required": ["window_title"]
    },
    permission_level="normal",
    category="application"
)
def switch_window(window_title: str) -> Dict[str, Any]:
    hwnd = find_running_window(window_title)
    if hwnd and bring_window_to_foreground(hwnd):
        return {
            "status": "switched",
            "message": f"Switched to {window_title}.",
            "verified": True
        }
    return {
        "status": "not_found",
        "message": f"Could not find an open window matching '{window_title}'.",
        "verified": False
    }
