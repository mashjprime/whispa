"""Clipboard-based text injection."""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ClipboardInjector:
    """Injects text via clipboard and Ctrl+V."""

    def __init__(self, restore_clipboard: bool = True):
        """Initialize clipboard injector.

        Args:
            restore_clipboard: Whether to restore original clipboard after injection
        """
        self.restore_clipboard = restore_clipboard

    def inject(self, text: str) -> bool:
        """Inject text via clipboard.

        Args:
            text: Text to inject

        Returns:
            True if successful
        """
        if not text:
            return True

        try:
            import pyperclip
            import pydirectinput

            # Save original clipboard if needed
            original = None
            if self.restore_clipboard:
                try:
                    original = pyperclip.paste()
                except Exception:
                    pass

            # Set clipboard to our text
            pyperclip.copy(text)

            # Small delay to ensure clipboard is set
            time.sleep(0.05)

            # Send Ctrl+V
            pydirectinput.keyDown("ctrl")
            pydirectinput.press("v")
            pydirectinput.keyUp("ctrl")

            # Small delay before restoring
            time.sleep(0.1)

            # Restore original clipboard
            if self.restore_clipboard and original is not None:
                try:
                    pyperclip.copy(original)
                except Exception:
                    pass

            logger.debug("Injected %d characters via clipboard", len(text))
            return True

        except ImportError as e:
            logger.error("Missing dependency for clipboard injection: %s", e)
            return False
        except Exception as e:
            logger.error("Clipboard injection failed: %s", e)
            return False

    def get_clipboard(self) -> Optional[str]:
        """Get current clipboard contents.

        Returns:
            Clipboard text or None
        """
        try:
            import pyperclip

            return pyperclip.paste()
        except Exception as e:
            logger.warning("Failed to get clipboard: %s", e)
            return None

    def set_clipboard(self, text: str) -> bool:
        """Set clipboard contents.

        Args:
            text: Text to set

        Returns:
            True if successful
        """
        try:
            import pyperclip

            pyperclip.copy(text)
            return True
        except Exception as e:
            logger.warning("Failed to set clipboard: %s", e)
            return False
