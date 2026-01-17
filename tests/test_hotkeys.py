"""Tests for hotkey module."""

import pytest

from whispa.hotkeys.parser import parse_hotkey, format_hotkey, is_modifier
from pynput import keyboard


class TestHotkeyParser:
    """Tests for hotkey parsing."""

    def test_parse_simple_hotkey(self):
        """Test parsing simple hotkey."""
        modifiers, key = parse_hotkey("ctrl+a")

        assert keyboard.Key.ctrl_l in modifiers
        assert key is not None

    def test_parse_multiple_modifiers(self):
        """Test parsing multiple modifiers."""
        modifiers, key = parse_hotkey("ctrl+shift+space")

        assert keyboard.Key.ctrl_l in modifiers
        assert keyboard.Key.shift_l in modifiers
        assert key == keyboard.Key.space

    def test_parse_function_key(self):
        """Test parsing function key."""
        modifiers, key = parse_hotkey("f5")

        assert len(modifiers) == 0
        assert key == keyboard.Key.f5

    def test_parse_with_modifier_function_key(self):
        """Test parsing modifier with function key."""
        modifiers, key = parse_hotkey("ctrl+f5")

        assert keyboard.Key.ctrl_l in modifiers
        assert key == keyboard.Key.f5

    def test_parse_special_keys(self):
        """Test parsing special keys."""
        _, key = parse_hotkey("escape")
        assert key == keyboard.Key.esc

        _, key = parse_hotkey("enter")
        assert key == keyboard.Key.enter

        _, key = parse_hotkey("tab")
        assert key == keyboard.Key.tab

    def test_parse_case_insensitive(self):
        """Test case insensitive parsing."""
        modifiers1, key1 = parse_hotkey("CTRL+SHIFT+A")
        modifiers2, key2 = parse_hotkey("ctrl+shift+a")

        assert modifiers1 == modifiers2

    def test_format_hotkey(self):
        """Test hotkey formatting."""
        modifiers = {keyboard.Key.ctrl_l, keyboard.Key.shift_l}
        key = keyboard.Key.space

        result = format_hotkey(modifiers, key)

        assert "Ctrl" in result
        assert "Shift" in result
        assert "Space" in result

    def test_format_function_key(self):
        """Test formatting function key."""
        modifiers = set()
        key = keyboard.Key.f5

        result = format_hotkey(modifiers, key)

        assert result == "F5"


class TestIsModifier:
    """Tests for modifier detection."""

    def test_ctrl_is_modifier(self):
        """Test Ctrl is detected as modifier."""
        assert is_modifier(keyboard.Key.ctrl_l) is True
        assert is_modifier(keyboard.Key.ctrl_r) is True

    def test_shift_is_modifier(self):
        """Test Shift is detected as modifier."""
        assert is_modifier(keyboard.Key.shift_l) is True
        assert is_modifier(keyboard.Key.shift_r) is True

    def test_alt_is_modifier(self):
        """Test Alt is detected as modifier."""
        assert is_modifier(keyboard.Key.alt_l) is True
        assert is_modifier(keyboard.Key.alt_r) is True

    def test_regular_key_not_modifier(self):
        """Test regular keys are not modifiers."""
        assert is_modifier(keyboard.Key.space) is False
        assert is_modifier(keyboard.Key.enter) is False
        assert is_modifier(keyboard.Key.f5) is False
