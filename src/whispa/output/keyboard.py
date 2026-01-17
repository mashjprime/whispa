"""Keyboard-based text injection using PyDirectInput."""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KeyboardInjector:
    """Injects text by simulating keyboard input."""

    def __init__(self, typing_delay: float = 0.01):
        """Initialize keyboard injector.

        Args:
            typing_delay: Delay between keystrokes in seconds
        """
        self.typing_delay = typing_delay

    def inject(self, text: str) -> bool:
        """Inject text by typing.

        Args:
            text: Text to inject

        Returns:
            True if successful
        """
        if not text:
            return True

        try:
            import pydirectinput

            # Type each character
            for char in text:
                if char == "\n":
                    pydirectinput.press("enter")
                elif char == "\t":
                    pydirectinput.press("tab")
                else:
                    # pydirectinput.write handles special characters
                    pydirectinput.write(char, interval=0)

                if self.typing_delay > 0:
                    time.sleep(self.typing_delay)

            logger.debug("Typed %d characters", len(text))
            return True

        except ImportError as e:
            logger.error("Missing dependency for keyboard injection: %s", e)
            return False
        except Exception as e:
            logger.error("Keyboard injection failed: %s", e)
            return False

    def press_key(self, key: str) -> bool:
        """Press a single key.

        Args:
            key: Key name (e.g., "enter", "tab", "a")

        Returns:
            True if successful
        """
        try:
            import pydirectinput

            pydirectinput.press(key)
            return True
        except Exception as e:
            logger.error("Failed to press key '%s': %s", key, e)
            return False

    def hotkey(self, *keys: str) -> bool:
        """Press a hotkey combination.

        Args:
            *keys: Keys to press together (e.g., "ctrl", "a")

        Returns:
            True if successful
        """
        try:
            import pydirectinput

            pydirectinput.hotkey(*keys)
            return True
        except Exception as e:
            logger.error("Failed to press hotkey %s: %s", keys, e)
            return False
