"""Hotkey string parsing and formatting."""

import logging
from typing import Set, Optional, Tuple
from pynput import keyboard

logger = logging.getLogger(__name__)

# Mapping from string names to pynput keys
KEY_NAMES = {
    # Modifiers
    "ctrl": keyboard.Key.ctrl_l,
    "control": keyboard.Key.ctrl_l,
    "shift": keyboard.Key.shift_l,
    "alt": keyboard.Key.alt_l,
    "win": keyboard.Key.cmd,
    "cmd": keyboard.Key.cmd,
    "super": keyboard.Key.cmd,
    # Function keys
    "f1": keyboard.Key.f1,
    "f2": keyboard.Key.f2,
    "f3": keyboard.Key.f3,
    "f4": keyboard.Key.f4,
    "f5": keyboard.Key.f5,
    "f6": keyboard.Key.f6,
    "f7": keyboard.Key.f7,
    "f8": keyboard.Key.f8,
    "f9": keyboard.Key.f9,
    "f10": keyboard.Key.f10,
    "f11": keyboard.Key.f11,
    "f12": keyboard.Key.f12,
    # Special keys
    "space": keyboard.Key.space,
    "enter": keyboard.Key.enter,
    "return": keyboard.Key.enter,
    "tab": keyboard.Key.tab,
    "backspace": keyboard.Key.backspace,
    "delete": keyboard.Key.delete,
    "escape": keyboard.Key.esc,
    "esc": keyboard.Key.esc,
    "home": keyboard.Key.home,
    "end": keyboard.Key.end,
    "pageup": keyboard.Key.page_up,
    "pagedown": keyboard.Key.page_down,
    "up": keyboard.Key.up,
    "down": keyboard.Key.down,
    "left": keyboard.Key.left,
    "right": keyboard.Key.right,
    "insert": keyboard.Key.insert,
    "capslock": keyboard.Key.caps_lock,
    "numlock": keyboard.Key.num_lock,
    "scrolllock": keyboard.Key.scroll_lock,
    "printscreen": keyboard.Key.print_screen,
    "pause": keyboard.Key.pause,
}

# Reverse mapping for formatting
KEY_DISPLAY_NAMES = {
    keyboard.Key.ctrl_l: "Ctrl",
    keyboard.Key.ctrl_r: "Ctrl",
    keyboard.Key.shift_l: "Shift",
    keyboard.Key.shift_r: "Shift",
    keyboard.Key.alt_l: "Alt",
    keyboard.Key.alt_r: "Alt",
    keyboard.Key.cmd: "Win",
    keyboard.Key.space: "Space",
    keyboard.Key.enter: "Enter",
    keyboard.Key.tab: "Tab",
    keyboard.Key.backspace: "Backspace",
    keyboard.Key.delete: "Delete",
    keyboard.Key.esc: "Escape",
    keyboard.Key.home: "Home",
    keyboard.Key.end: "End",
    keyboard.Key.page_up: "PageUp",
    keyboard.Key.page_down: "PageDown",
    keyboard.Key.up: "Up",
    keyboard.Key.down: "Down",
    keyboard.Key.left: "Left",
    keyboard.Key.right: "Right",
    keyboard.Key.insert: "Insert",
    keyboard.Key.caps_lock: "CapsLock",
    keyboard.Key.num_lock: "NumLock",
    keyboard.Key.scroll_lock: "ScrollLock",
    keyboard.Key.print_screen: "PrintScreen",
    keyboard.Key.pause: "Pause",
}

# Add function keys
for i in range(1, 13):
    KEY_DISPLAY_NAMES[getattr(keyboard.Key, f"f{i}")] = f"F{i}"


def parse_hotkey(hotkey_str: str) -> Tuple[Set, Optional[keyboard.Key]]:
    """Parse a hotkey string into modifiers and key.

    Args:
        hotkey_str: Hotkey string like "ctrl+shift+space"

    Returns:
        Tuple of (modifier_set, key)
    """
    modifiers = set()
    main_key = None

    parts = [p.strip().lower() for p in hotkey_str.split("+")]

    for part in parts:
        if part in ("ctrl", "control"):
            modifiers.add(keyboard.Key.ctrl_l)
        elif part == "shift":
            modifiers.add(keyboard.Key.shift_l)
        elif part == "alt":
            modifiers.add(keyboard.Key.alt_l)
        elif part in ("win", "cmd", "super"):
            modifiers.add(keyboard.Key.cmd)
        elif part in KEY_NAMES:
            main_key = KEY_NAMES[part]
        elif len(part) == 1:
            # Single character
            main_key = keyboard.KeyCode.from_char(part)
        else:
            logger.warning("Unknown key: %s", part)

    return modifiers, main_key


def format_hotkey(modifiers: Set, key) -> str:
    """Format a hotkey combination as a string.

    Args:
        modifiers: Set of modifier keys
        key: Main key

    Returns:
        Formatted string like "Ctrl+Shift+Space"
    """
    parts = []

    # Add modifiers in standard order
    if keyboard.Key.ctrl_l in modifiers or keyboard.Key.ctrl_r in modifiers:
        parts.append("Ctrl")
    if keyboard.Key.alt_l in modifiers or keyboard.Key.alt_r in modifiers:
        parts.append("Alt")
    if keyboard.Key.shift_l in modifiers or keyboard.Key.shift_r in modifiers:
        parts.append("Shift")
    if keyboard.Key.cmd in modifiers:
        parts.append("Win")

    # Add main key
    if key is not None:
        if key in KEY_DISPLAY_NAMES:
            parts.append(KEY_DISPLAY_NAMES[key])
        elif hasattr(key, "char") and key.char:
            parts.append(key.char.upper())
        else:
            parts.append(str(key))

    return "+".join(parts)


def is_modifier(key) -> bool:
    """Check if a key is a modifier.

    Args:
        key: Key to check

    Returns:
        True if modifier
    """
    modifier_keys = {
        keyboard.Key.ctrl_l,
        keyboard.Key.ctrl_r,
        keyboard.Key.shift_l,
        keyboard.Key.shift_r,
        keyboard.Key.alt_l,
        keyboard.Key.alt_r,
        keyboard.Key.cmd,
    }
    return key in modifier_keys
