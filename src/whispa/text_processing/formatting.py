"""Text formatting utilities."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TextFormatter:
    """Handles text formatting operations."""

    def __init__(self, auto_capitalize: bool = True):
        """Initialize formatter.

        Args:
            auto_capitalize: Whether to auto-capitalize
        """
        self.auto_capitalize = auto_capitalize

    def format(self, text: str) -> str:
        """Apply all formatting to text.

        Args:
            text: Input text

        Returns:
            Formatted text
        """
        if not text:
            return text

        result = text.strip()

        # Clean whitespace
        result = self._clean_whitespace(result)

        # Fix punctuation spacing
        result = self._fix_punctuation(result)

        # Auto-capitalize
        if self.auto_capitalize:
            result = self._capitalize(result)

        return result

    def _clean_whitespace(self, text: str) -> str:
        """Clean up whitespace."""
        # Multiple spaces to single
        text = re.sub(r" +", " ", text)

        # Remove spaces at start/end of lines
        text = re.sub(r"^ +| +$", "", text, flags=re.MULTILINE)

        return text

    def _fix_punctuation(self, text: str) -> str:
        """Fix spacing around punctuation."""
        # Remove space before punctuation
        text = re.sub(r"\s+([.,!?;:)])", r"\1", text)

        # Remove space after opening brackets
        text = re.sub(r"([(])\s+", r"\1", text)

        # Ensure space after punctuation (except at end)
        text = re.sub(r"([.,!?;:])([A-Za-z])", r"\1 \2", text)

        # Fix multiple punctuation
        text = re.sub(r"([.!?]){2,}", r"\1", text)

        return text

    def _capitalize(self, text: str) -> str:
        """Auto-capitalize sentences."""
        if not text:
            return text

        # Capitalize first character
        if text[0].isalpha():
            text = text[0].upper() + text[1:]

        # Capitalize after sentence endings
        def capitalize_match(m):
            return m.group(1) + " " + m.group(2).upper()

        text = re.sub(r"([.!?])\s+([a-z])", capitalize_match, text)

        # Capitalize "I" standalone
        text = re.sub(r"\bi\b", "I", text)

        return text

    def append_to_existing(
        self, existing: str, new_text: str, add_space: bool = True
    ) -> str:
        """Append new text to existing text intelligently.

        Args:
            existing: Existing text
            new_text: New text to append
            add_space: Whether to add space between

        Returns:
            Combined text
        """
        if not existing:
            return new_text

        if not new_text:
            return existing

        # Check if existing ends with space
        has_trailing_space = existing.endswith(" ")

        # Check if new starts with punctuation
        starts_with_punct = new_text[0] in ".,!?;:"

        if starts_with_punct:
            # No space before punctuation
            result = existing.rstrip() + new_text
        elif has_trailing_space or not add_space:
            result = existing + new_text
        else:
            result = existing + " " + new_text

        return result
