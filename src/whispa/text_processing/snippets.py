"""Snippet expansion for voice-triggered text insertion."""

import re
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Snippet:
    """A text snippet for expansion."""

    id: int
    trigger: str
    expansion: str
    category: str
    description: str


class SnippetExpander:
    """Expands voice-triggered snippets."""

    def __init__(self, enabled: bool = True):
        """Initialize snippet expander.

        Args:
            enabled: Whether expansion is enabled
        """
        self.enabled = enabled
        self._snippets: Dict[str, Snippet] = {}
        self._pattern: Optional[re.Pattern] = None

    def load_snippets(self, snippets: List[Snippet]) -> None:
        """Load snippets.

        Args:
            snippets: List of snippets to load
        """
        self._snippets.clear()
        for snippet in snippets:
            self._snippets[snippet.trigger.lower()] = snippet
        self._build_pattern()

    def _build_pattern(self) -> None:
        """Build regex pattern for snippet matching."""
        if not self._snippets:
            self._pattern = None
            return

        # Sort triggers by length (longest first)
        triggers = sorted(self._snippets.keys(), key=len, reverse=True)

        # Escape and join
        escaped = [re.escape(t) for t in triggers]
        pattern = r"\b(" + "|".join(escaped) + r")\b"

        self._pattern = re.compile(pattern, re.IGNORECASE)

    def expand(self, text: str) -> tuple[str, bool]:
        """Expand snippets in text.

        Args:
            text: Input text

        Returns:
            Tuple of (expanded_text, had_expansions)
        """
        if not self.enabled or not self._pattern or not text:
            return text, False

        had_expansions = False
        result = text

        def replace_snippet(match):
            nonlocal had_expansions
            trigger = match.group(1).lower()
            if trigger in self._snippets:
                had_expansions = True
                return self._snippets[trigger].expansion
            return match.group(0)

        result = self._pattern.sub(replace_snippet, result)
        return result, had_expansions

    def add_snippet(self, snippet: Snippet) -> None:
        """Add a snippet.

        Args:
            snippet: Snippet to add
        """
        self._snippets[snippet.trigger.lower()] = snippet
        self._build_pattern()

    def remove_snippet(self, trigger: str) -> bool:
        """Remove a snippet by trigger.

        Args:
            trigger: Trigger of snippet to remove

        Returns:
            True if removed
        """
        trigger_lower = trigger.lower()
        if trigger_lower in self._snippets:
            del self._snippets[trigger_lower]
            self._build_pattern()
            return True
        return False

    def get_snippet(self, trigger: str) -> Optional[Snippet]:
        """Get a snippet by trigger.

        Args:
            trigger: Snippet trigger

        Returns:
            Snippet or None
        """
        return self._snippets.get(trigger.lower())

    def get_all_snippets(self) -> List[Snippet]:
        """Get all snippets."""
        return list(self._snippets.values())

    def get_by_category(self, category: str) -> List[Snippet]:
        """Get snippets by category.

        Args:
            category: Category name

        Returns:
            List of snippets in category
        """
        return [s for s in self._snippets.values() if s.category == category]

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return list(set(s.category for s in self._snippets.values()))
