import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pyautogui
import mss
from PIL import Image
from backend.tools.registry import registry
from backend.config import settings

logger = logging.getLogger("AEGIS.ComputerTools")

pyautogui.FAILSAFE = True

@registry.register(
    name="take_screenshot",
    description="Capture the current computer screen and save as an image for inspection.",
    parameters={
        "type": "object",
        "properties": {
            "save_name": {
                "type": "string",
                "description": "Optional name for the screenshot file (e.g. 'screen_capture.png')",
                "default": "screenshot.png"
            }
        },
        "required": []
    },
    permission_level="normal",
    category="computer"
)
def take_screenshot(save_name: Optional[str] = "screenshot.png") -> Dict[str, Any]:
    try:
        temp_dir = Path(settings.BASE_DIR) / "data" / "screenshots"
        temp_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = temp_dir / save_name

        with mss.mss() as sct:
            sct.shot(mon=-1, output=str(screenshot_path))

        return {
            "status": "captured",
            "filepath": str(screenshot_path),
            "message": "Screenshot captured.",
            "verified": screenshot_path.exists()
        }
    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}")
        return {
            "status": "error",
            "error": str(e),
            "verified": False
        }

@registry.register(
    name="mouse_click",
    description="Click at specific screen coordinates or current cursor location.",
    parameters={
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X coordinate on screen"},
            "y": {"type": "integer", "description": "Y coordinate on screen"},
            "clicks": {"type": "integer", "description": "Number of clicks (1 for single, 2 for double)", "default": 1},
            "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"}
        },
        "required": ["x", "y"]
    },
    permission_level="normal",
    category="computer"
)
def mouse_click(x: int, y: int, clicks: int = 1, button: str = "left") -> Dict[str, Any]:
    try:
        pyautogui.click(x=x, y=y, clicks=clicks, button=button)
        return {
            "status": "clicked",
            "x": x,
            "y": y,
            "clicks": clicks,
            "button": button,
            "verified": True
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "verified": False}

@registry.register(
    name="keyboard_type",
    description="Type text using the keyboard.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text string to type out"}
        },
        "required": ["text"]
    },
    permission_level="normal",
    category="computer"
)
def keyboard_type(text: str) -> Dict[str, Any]:
    try:
        pyautogui.write(text, interval=0.02)
        return {"status": "typed", "text_length": len(text), "verified": True}
    except Exception as e:
        return {"status": "error", "error": str(e), "verified": False}

@registry.register(
    name="keyboard_hotkey",
    description="Press a combination of keys simultaneously (e.g. ['ctrl', 'c'], ['alt', 'tab'], ['win', 'd'], ['enter']).",
    parameters={
        "type": "object",
        "properties": {
            "keys": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of key names to press together (e.g. ['ctrl', 's'])"
            }
        },
        "required": ["keys"]
    },
    permission_level="normal",
    category="computer"
)
def keyboard_hotkey(keys: List[str]) -> Dict[str, Any]:
    try:
        pyautogui.hotkey(*keys)
        return {"status": "pressed", "keys": keys, "verified": True}
    except Exception as e:
        return {"status": "error", "error": str(e), "verified": False}

@registry.register(
    name="scroll",
    description="Scroll up or down on the active window.",
    parameters={
        "type": "object",
        "properties": {
            "amount": {
                "type": "integer",
                "description": "Positive integer to scroll up, negative to scroll down (e.g. -5 for down, 5 for up)"
            }
        },
        "required": ["amount"]
    },
    permission_level="normal",
    category="computer"
)
def scroll(amount: int) -> Dict[str, Any]:
    try:
        pyautogui.scroll(amount * 100)
        return {"status": "scrolled", "amount": amount, "verified": True}
    except Exception as e:
        return {"status": "error", "error": str(e), "verified": False}
