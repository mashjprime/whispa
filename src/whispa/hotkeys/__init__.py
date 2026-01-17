"""Global hotkey module."""

from whispa.hotkeys.manager import HotkeyManager
from whispa.hotkeys.parser import parse_hotkey, format_hotkey

__all__ = ["HotkeyManager", "parse_hotkey", "format_hotkey"]
