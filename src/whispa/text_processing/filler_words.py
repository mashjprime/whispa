"""Filler word removal."""

import re
import logging
from typing import List, Set

logger = logging.getLogger(__name__)


class FillerWordRemover:
    """Removes filler words from transcribed text."""

    DEFAULT_FILLERS = [
        "um",
        "uh",
        "er",
        "ah",
        "like",
        "you know",
        "basically",
        "actually",
        "i mean",
        "sort of",
        "kind of",
        "well",
        "so",
        "right",
        "okay",
    ]

    def __init__(self, filler_words: List[str] = None, enabled: bool = True):
        """Initialize filler word remover.

        Args:
            filler_words: Custom list of filler words
            enabled: Whether removal is enabled
        """
        self.enabled = enabled
        self._filler_words: Set[str] = set()
        self._pattern: re.Pattern = None

        self.set_filler_words(filler_words or self.DEFAULT_FILLERS)

    def set_filler_words(self, filler_words: List[str]) -> None:
        """Set the list of filler words.

        Args:
            filler_words: List of filler words/phrases
        """
        self._filler_words = set(word.lower().strip() for word in filler_words)
        self._build_pattern()

    def _build_pattern(self) -> None:
        """Build regex pattern for filler word matching."""
        if not self._filler_words:
            self._pattern = None
            return

        # Sort by length (longest first) for proper matching
        sorted_fillers = sorted(self._filler_words, key=len, reverse=True)

        # Escape special characters
        escaped = [re.escape(f) for f in sorted_fillers]

        # Build pattern that matches fillers with optional trailing comma
        pattern = r"(?<!\w)(" + "|".join(escaped) + r")(?:,)?\s*(?!\w)"

        self._pattern = re.compile(pattern, re.IGNORECASE)

    def remove(self, text: str) -> str:
        """Remove filler words from text.

        Args:
            text: Input text

        Returns:
            Text with filler words removed
        """
        if not self.enabled or not self._pattern or not text:
            return text

        # Remove filler words
        result = self._pattern.sub(" ", text)

        # Clean up extra whitespace
        result = re.sub(r"\s+", " ", result)
        result = re.sub(r"^\s*,\s*", "", result)
        result = re.sub(r"\s*,\s*,", ",", result)

        return result.strip()

    def add_filler_word(self, word: str) -> None:
        """Add a filler word.

        Args:
            word: Word to add
        """
        self._filler_words.add(word.lower().strip())
        self._build_pattern()

    def remove_filler_word(self, word: str) -> None:
        """Remove a filler word.

        Args:
            word: Word to remove
        """
        self._filler_words.discard(word.lower().strip())
        self._build_pattern()

    @property
    def filler_words(self) -> List[str]:
        """Get current filler words list."""
        return sorted(self._filler_words)
