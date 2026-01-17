"""Personal dictionary for word corrections."""

import re
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DictionaryEntry:
    """A dictionary entry for word correction."""

    id: int
    original: str
    replacement: str
    case_sensitive: bool
    whole_word: bool


class DictionaryCorrector:
    """Applies personal dictionary corrections."""

    def __init__(self, enabled: bool = True):
        """Initialize dictionary corrector.

        Args:
            enabled: Whether correction is enabled
        """
        self.enabled = enabled
        self._entries: Dict[str, DictionaryEntry] = {}
        self._patterns: Dict[str, re.Pattern] = {}

    def load_entries(self, entries: List[DictionaryEntry]) -> None:
        """Load dictionary entries.

        Args:
            entries: List of entries to load
        """
        self._entries.clear()
        self._patterns.clear()

        for entry in entries:
            key = entry.original if entry.case_sensitive else entry.original.lower()
            self._entries[key] = entry
            self._patterns[key] = self._build_pattern(entry)

    def _build_pattern(self, entry: DictionaryEntry) -> re.Pattern:
        """Build regex pattern for an entry.

        Args:
            entry: Dictionary entry

        Returns:
            Compiled regex pattern
        """
        escaped = re.escape(entry.original)

        if entry.whole_word:
            pattern = r"\b" + escaped + r"\b"
        else:
            pattern = escaped

        flags = 0 if entry.case_sensitive else re.IGNORECASE
        return re.compile(pattern, flags)

    def correct(self, text: str) -> tuple[str, int]:
        """Apply dictionary corrections to text.

        Args:
            text: Input text

        Returns:
            Tuple of (corrected_text, correction_count)
        """
        if not self.enabled or not self._entries or not text:
            return text, 0

        result = text
        count = 0

        for key, entry in self._entries.items():
            pattern = self._patterns[key]

            def replace(match):
                nonlocal count
                count += 1
                original = match.group(0)

                # Preserve case if not case-sensitive
                if not entry.case_sensitive:
                    return self._match_case(original, entry.replacement)
                return entry.replacement

            result = pattern.sub(replace, result)

        return result, count

    def _match_case(self, original: str, replacement: str) -> str:
        """Match the case of replacement to original.

        Args:
            original: Original text
            replacement: Replacement text

        Returns:
            Case-matched replacement
        """
        if original.isupper():
            return replacement.upper()
        elif original.islower():
            return replacement.lower()
        elif original[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement

    def add_entry(self, entry: DictionaryEntry) -> None:
        """Add a dictionary entry.

        Args:
            entry: Entry to add
        """
        key = entry.original if entry.case_sensitive else entry.original.lower()
        self._entries[key] = entry
        self._patterns[key] = self._build_pattern(entry)

    def remove_entry(self, original: str, case_sensitive: bool = False) -> bool:
        """Remove a dictionary entry.

        Args:
            original: Original text of entry
            case_sensitive: Whether to match case

        Returns:
            True if removed
        """
        key = original if case_sensitive else original.lower()
        if key in self._entries:
            del self._entries[key]
            del self._patterns[key]
            return True
        return False

    def get_entry(self, original: str) -> Optional[DictionaryEntry]:
        """Get an entry by original text.

        Args:
            original: Original text

        Returns:
            Entry or None
        """
        # Try case-sensitive first, then case-insensitive
        if original in self._entries:
            return self._entries[original]
        return self._entries.get(original.lower())

    def get_all_entries(self) -> List[DictionaryEntry]:
        """Get all dictionary entries."""
        return list(self._entries.values())
