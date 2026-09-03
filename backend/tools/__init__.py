# Import all tools to trigger registry decorators
import backend.tools.system_tools
import backend.tools.math_tools
import backend.tools.app_launcher
import backend.tools.browser_tools
import backend.tools.file_tools
import backend.tools.computer_tools
import backend.tools.reminder_tools
import backend.tools.flight_tools

from backend.tools.registry import registry

__all__ = ["registry"]
