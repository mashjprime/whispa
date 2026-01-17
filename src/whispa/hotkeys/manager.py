"""Global hotkey manager using pynput."""

import logging
import threading
from typing import Callable, Optional, Set, Tuple
from pynput import keyboard

from whispa.hotkeys.parser import parse_hotkey, format_hotkey, is_modifier

logger = logging.getLogger(__name__)


class HotkeyManager:
    """Manages global hotkeys using pynput."""

    def __init__(self):
        """Initialize hotkey manager."""
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        self._lock = threading.Lock()

        # Current pressed keys
        self._pressed_keys: Set = set()
        self._pressed_modifiers: Set = set()

        # Registered hotkeys: {name: (modifiers, key, on_press, on_release)}
        self._hotkeys: dict = {}

        # Track which hotkeys are currently "active" (pressed)
        self._active_hotkeys: Set[str] = set()

        # Callback for when any key is pressed (for recording hotkeys)
        self._key_capture_callback: Optional[Callable] = None

    def register_hotkey(
        self,
        name: str,
        hotkey_str: str,
        on_press: Callable[[], None],
        on_release: Optional[Callable[[], None]] = None,
    ) -> bool:
        """Register a hotkey.

        Args:
            name: Unique name for the hotkey
            hotkey_str: Hotkey string like "ctrl+shift+space" or "ctrl+win"
            on_press: Function to call when hotkey is pressed
            on_release: Function to call when hotkey is released (for hold mode)

        Returns:
            True if registered successfully
        """
        try:
            modifiers, key = parse_hotkey(hotkey_str)

            # For modifier-only hotkeys (like ctrl+win), key will be None
            # In that case, we trigger on the last modifier press

            with self._lock:
                self._hotkeys[name] = (modifiers, key, on_press, on_release)

            logger.info("Registered hotkey '%s': %s", name, hotkey_str)
            return True

        except Exception as e:
            logger.error("Failed to register hotkey '%s': %s", name, e)
            return False

    def unregister_hotkey(self, name: str) -> bool:
        """Unregister a hotkey.

        Args:
            name: Name of hotkey to unregister

        Returns:
            True if unregistered
        """
        with self._lock:
            if name in self._hotkeys:
                del self._hotkeys[name]
                self._active_hotkeys.discard(name)
                logger.info("Unregistered hotkey: %s", name)
                return True
        return False

    def start(self) -> bool:
        """Start listening for hotkeys.

        Returns:
            True if started successfully
        """
        with self._lock:
            if self._running:
                return True

            try:
                self._listener = keyboard.Listener(
                    on_press=self._on_key_press,
                    on_release=self._on_key_release,
                )
                self._listener.start()
                self._running = True
                logger.info("Hotkey listener started")
                return True

            except Exception as e:
                logger.error("Failed to start hotkey listener: %s", e)
                return False

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        with self._lock:
            if self._listener is not None:
                try:
                    self._listener.stop()
                except Exception as e:
                    logger.warning("Error stopping listener: %s", e)
                finally:
                    self._listener = None

            self._running = False
            self._pressed_keys.clear()
            self._pressed_modifiers.clear()
            self._active_hotkeys.clear()
            logger.info("Hotkey listener stopped")

    def _on_key_press(self, key) -> None:
        """Handle key press event."""
        # Normalize key
        normalized = self._normalize_key(key)

        if is_modifier(normalized):
            self._pressed_modifiers.add(normalized)
        else:
            self._pressed_keys.add(normalized)

        # Check for key capture mode
        if self._key_capture_callback is not None:
            self._key_capture_callback(
                self._pressed_modifiers.copy(), normalized
            )
            return

        # Check registered hotkeys for press
        self._check_hotkeys_press(normalized)

    def _on_key_release(self, key) -> None:
        """Handle key release event."""
        normalized = self._normalize_key(key)

        # Check for hotkey release BEFORE updating pressed keys
        self._check_hotkeys_release(normalized)

        if is_modifier(normalized):
            self._pressed_modifiers.discard(normalized)
        else:
            self._pressed_keys.discard(normalized)

    def _normalize_key(self, key):
        """Normalize a key (convert right modifiers to left)."""
        # Map right modifiers to left
        if key == keyboard.Key.ctrl_r:
            return keyboard.Key.ctrl_l
        elif key == keyboard.Key.shift_r:
            return keyboard.Key.shift_l
        elif key == keyboard.Key.alt_r:
            return keyboard.Key.alt_l
        return key

    def _check_hotkeys_press(self, key) -> None:
        """Check if any registered hotkey matches current state for press."""
        with self._lock:
            for name, (modifiers, hotkey_key, on_press, on_release) in self._hotkeys.items():
                if name in self._active_hotkeys:
                    continue  # Already active

                if self._hotkey_matches(modifiers, hotkey_key, key):
                    logger.debug("Hotkey pressed: %s", name)
                    self._active_hotkeys.add(name)
                    # Run callback in separate thread to not block listener
                    threading.Thread(
                        target=self._run_callback,
                        args=(on_press,),
                        daemon=True,
                    ).start()

    def _check_hotkeys_release(self, key) -> None:
        """Check if any active hotkey should be released."""
        with self._lock:
            to_release = []

            for name in list(self._active_hotkeys):
                if name not in self._hotkeys:
                    continue

                modifiers, hotkey_key, on_press, on_release = self._hotkeys[name]

                # Check if the released key is part of this hotkey
                is_part_of_hotkey = False

                if is_modifier(key) and key in modifiers:
                    is_part_of_hotkey = True
                elif hotkey_key is not None and self._key_equals(hotkey_key, key):
                    is_part_of_hotkey = True

                if is_part_of_hotkey:
                    to_release.append((name, on_release))

            for name, on_release in to_release:
                logger.debug("Hotkey released: %s", name)
                self._active_hotkeys.discard(name)
                if on_release is not None:
                    threading.Thread(
                        target=self._run_callback,
                        args=(on_release,),
                        daemon=True,
                    ).start()

    def _hotkey_matches(self, required_modifiers: Set, required_key, pressed_key) -> bool:
        """Check if pressed keys match required hotkey."""
        # Check modifiers match exactly
        if required_modifiers != self._pressed_modifiers:
            return False

        # If no main key required (modifier-only hotkey), match when all modifiers are pressed
        if required_key is None:
            # Trigger when the last required modifier is pressed
            return is_modifier(pressed_key) and pressed_key in required_modifiers

        # Check main key
        return self._key_equals(required_key, pressed_key)

    def _key_equals(self, key1, key2) -> bool:
        """Check if two keys are equal."""
        if hasattr(key1, "char") and hasattr(key2, "char"):
            return key1.char == key2.char
        return key1 == key2

    def _run_callback(self, callback: Callable) -> None:
        """Run a hotkey callback safely."""
        if callback is None:
            return
        try:
            callback()
        except Exception as e:
            logger.error("Hotkey callback error: %s", e)

    def start_key_capture(self, callback: Callable[[Set, any], None]) -> None:
        """Start capturing key presses for hotkey recording.

        Args:
            callback: Function called with (modifiers, key) on each key press
        """
        self._key_capture_callback = callback
        logger.debug("Key capture mode enabled")

    def stop_key_capture(self) -> None:
        """Stop key capture mode."""
        self._key_capture_callback = None
        logger.debug("Key capture mode disabled")

    @property
    def is_running(self) -> bool:
        """Check if listener is running."""
        with self._lock:
            return self._running
