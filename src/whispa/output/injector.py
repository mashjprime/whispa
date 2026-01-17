"""Text injection strategy selection."""

import logging
from typing import Literal, Optional

from whispa.output.clipboard import ClipboardInjector
from whispa.output.keyboard import KeyboardInjector

logger = logging.getLogger(__name__)


class TextInjector:
    """Main text injector that selects the appropriate method."""

    def __init__(
        self,
        method: Literal["clipboard", "keyboard"] = "clipboard",
        restore_clipboard: bool = True,
        add_trailing_space: bool = True,
    ):
        """Initialize text injector.

        Args:
            method: Injection method to use
            restore_clipboard: Whether to restore clipboard after injection
            add_trailing_space: Whether to add trailing space after text
        """
        self.method = method
        self.add_trailing_space = add_trailing_space

        self._clipboard = ClipboardInjector(restore_clipboard=restore_clipboard)
        self._keyboard = KeyboardInjector()

    def inject(self, text: str) -> bool:
        """Inject text using the configured method.

        Args:
            text: Text to inject

        Returns:
            True if successful
        """
        if not text:
            return True

        # Add trailing space if configured
        if self.add_trailing_space and not text.endswith((" ", "\n", "\t")):
            text = text + " "

        # Try primary method
        if self.method == "clipboard":
            if self._clipboard.inject(text):
                return True
            logger.warning("Clipboard injection failed, trying keyboard fallback")
            return self._keyboard.inject(text)
        else:
            if self._keyboard.inject(text):
                return True
            logger.warning("Keyboard injection failed, trying clipboard fallback")
            return self._clipboard.inject(text)

    def set_method(self, method: Literal["clipboard", "keyboard"]) -> None:
        """Set the injection method.

        Args:
            method: New injection method
        """
        self.method = method
        logger.info("Text injection method set to: %s", method)

    def test_injection(self) -> bool:
        """Test if text injection is working.

        Note: This will inject a test character and immediately backspace.

        Returns:
            True if injection works
        """
        try:
            # Try to inject and delete
            if self._clipboard.inject(""):
                return True
            return False
        except Exception as e:
            logger.error("Injection test failed: %s", e)
            return False
