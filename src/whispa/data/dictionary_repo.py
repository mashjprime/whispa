"""Repository for dictionary entries."""

import logging
from typing import List, Optional
from whispa.data.database import Database
from whispa.text_processing.dictionary import DictionaryEntry

logger = logging.getLogger(__name__)


class DictionaryRepository:
    """CRUD operations for dictionary entries."""

    def __init__(self, database: Database):
        """Initialize repository.

        Args:
            database: Database instance
        """
        self.db = database

    def get_all(self) -> List[DictionaryEntry]:
        """Get all dictionary entries.

        Returns:
            List of entries
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, original, replacement, case_sensitive, whole_word "
                    "FROM dictionary"
                )
                rows = cursor.fetchall()
                return [
                    DictionaryEntry(
                        id=row["id"],
                        original=row["original"],
                        replacement=row["replacement"],
                        case_sensitive=bool(row["case_sensitive"]),
                        whole_word=bool(row["whole_word"]),
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error("Failed to get dictionary entries: %s", e)
            return []

    def get_by_id(self, entry_id: int) -> Optional[DictionaryEntry]:
        """Get an entry by ID.

        Args:
            entry_id: Entry ID

        Returns:
            Entry or None
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, original, replacement, case_sensitive, whole_word "
                    "FROM dictionary WHERE id = ?",
                    (entry_id,),
                )
                row = cursor.fetchone()
                if row:
                    return DictionaryEntry(
                        id=row["id"],
                        original=row["original"],
                        replacement=row["replacement"],
                        case_sensitive=bool(row["case_sensitive"]),
                        whole_word=bool(row["whole_word"]),
                    )
                return None
        except Exception as e:
            logger.error("Failed to get dictionary entry %d: %s", entry_id, e)
            return None

    def get_by_original(
        self, original: str, case_sensitive: bool = False
    ) -> Optional[DictionaryEntry]:
        """Get an entry by original text.

        Args:
            original: Original text
            case_sensitive: Whether to match case

        Returns:
            Entry or None
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, original, replacement, case_sensitive, whole_word "
                    "FROM dictionary WHERE original = ? AND case_sensitive = ?",
                    (original, int(case_sensitive)),
                )
                row = cursor.fetchone()
                if row:
                    return DictionaryEntry(
                        id=row["id"],
                        original=row["original"],
                        replacement=row["replacement"],
                        case_sensitive=bool(row["case_sensitive"]),
                        whole_word=bool(row["whole_word"]),
                    )
                return None
        except Exception as e:
            logger.error("Failed to get dictionary entry '%s': %s", original, e)
            return None

    def create(
        self,
        original: str,
        replacement: str,
        case_sensitive: bool = False,
        whole_word: bool = True,
    ) -> Optional[DictionaryEntry]:
        """Create a new dictionary entry.

        Args:
            original: Original text
            replacement: Replacement text
            case_sensitive: Whether match should be case sensitive
            whole_word: Whether to match whole words only

        Returns:
            Created entry or None
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO dictionary "
                    "(original, replacement, case_sensitive, whole_word) "
                    "VALUES (?, ?, ?, ?)",
                    (original, replacement, int(case_sensitive), int(whole_word)),
                )
                return DictionaryEntry(
                    id=cursor.lastrowid,
                    original=original,
                    replacement=replacement,
                    case_sensitive=case_sensitive,
                    whole_word=whole_word,
                )
        except Exception as e:
            logger.error("Failed to create dictionary entry: %s", e)
            return None

    def update(self, entry: DictionaryEntry) -> bool:
        """Update a dictionary entry.

        Args:
            entry: Entry with updated values

        Returns:
            True if updated
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "UPDATE dictionary SET original = ?, replacement = ?, "
                    "case_sensitive = ?, whole_word = ? WHERE id = ?",
                    (
                        entry.original,
                        entry.replacement,
                        int(entry.case_sensitive),
                        int(entry.whole_word),
                        entry.id,
                    ),
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error("Failed to update dictionary entry %d: %s", entry.id, e)
            return False

    def delete(self, entry_id: int) -> bool:
        """Delete a dictionary entry.

        Args:
            entry_id: ID of entry to delete

        Returns:
            True if deleted
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute("DELETE FROM dictionary WHERE id = ?", (entry_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error("Failed to delete dictionary entry %d: %s", entry_id, e)
            return False

    def import_entries(self, entries: List[dict]) -> int:
        """Import entries from a list of dicts.

        Args:
            entries: List of entry dicts

        Returns:
            Number of imported entries
        """
        count = 0
        for data in entries:
            entry = self.create(
                original=data.get("original", ""),
                replacement=data.get("replacement", ""),
                case_sensitive=data.get("case_sensitive", False),
                whole_word=data.get("whole_word", True),
            )
            if entry:
                count += 1
        return count

    def export_entries(self) -> List[dict]:
        """Export all entries as dicts.

        Returns:
            List of entry dicts
        """
        entries = self.get_all()
        return [
            {
                "original": e.original,
                "replacement": e.replacement,
                "case_sensitive": e.case_sensitive,
                "whole_word": e.whole_word,
            }
            for e in entries
        ]
