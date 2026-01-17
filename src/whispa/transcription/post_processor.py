"""Post-processing for transcribed text."""

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class PostProcessor:
    """Post-processes transcribed text."""

    def __init__(
        self,
        filler_words: Optional[List[str]] = None,
        remove_fillers: bool = True,
        auto_capitalize: bool = True,
    ):
        """Initialize post-processor.

        Args:
            filler_words: List of filler words to remove
            remove_fillers: Whether to remove filler words
            auto_capitalize: Whether to auto-capitalize sentences
        """
        self.filler_words = filler_words or [
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
        ]
        self.remove_fillers = remove_fillers
        self.auto_capitalize = auto_capitalize

        # Build regex pattern for filler words
        self._filler_pattern = self._build_filler_pattern()

    def _build_filler_pattern(self) -> re.Pattern:
        """Build regex pattern for filler word removal."""
        # Sort by length (longest first) to match longer phrases first
        sorted_fillers = sorted(self.filler_words, key=len, reverse=True)

        # Escape special characters and join with |
        escaped = [re.escape(f) for f in sorted_fillers]
        pattern = r"\b(" + "|".join(escaped) + r")\b[,]?\s*"

        return re.compile(pattern, re.IGNORECASE)

    def process(self, text: str) -> str:
        """Process transcribed text.

        Args:
            text: Raw transcribed text

        Returns:
            Processed text
        """
        if not text:
            return text

        result = text.strip()

        # Remove filler words
        if self.remove_fillers:
            result = self._remove_filler_words(result)

        # Clean up whitespace
        result = self._clean_whitespace(result)

        # Auto-capitalize
        if self.auto_capitalize:
            result = self._auto_capitalize(result)

        return result

    def _remove_filler_words(self, text: str) -> str:
        """Remove filler words from text."""
        result = self._filler_pattern.sub("", text)

        # Clean up any double spaces or leading commas
        result = re.sub(r"\s+", " ", result)
        result = re.sub(r"^\s*,\s*", "", result)
        result = re.sub(r"\s*,\s*,", ",", result)

        return result.strip()

    def _clean_whitespace(self, text: str) -> str:
        """Clean up whitespace in text."""
        # Remove multiple spaces
        text = re.sub(r" +", " ", text)

        # Fix spacing around punctuation
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        text = re.sub(r"([.,!?;:])\s*([A-Za-z])", r"\1 \2", text)

        return text.strip()

    def _auto_capitalize(self, text: str) -> str:
        """Auto-capitalize sentence starts."""
        if not text:
            return text

        # Capitalize first character
        result = text[0].upper() + text[1:] if len(text) > 1 else text.upper()

        # Capitalize after sentence-ending punctuation
        result = re.sub(
            r"([.!?])\s+([a-z])",
            lambda m: m.group(1) + " " + m.group(2).upper(),
            result,
        )

        return result

    def update_filler_words(self, filler_words: List[str]) -> None:
        """Update the list of filler words.

        Args:
            filler_words: New list of filler words
        """
        self.filler_words = filler_words
        self._filler_pattern = self._build_filler_pattern()
