"""Repository for snippet storage."""

import logging
from typing import List, Optional
from whispa.data.database import Database
from whispa.text_processing.snippets import Snippet

logger = logging.getLogger(__name__)


class SnippetsRepository:
    """CRUD operations for snippets."""

    def __init__(self, database: Database):
        """Initialize repository.

        Args:
            database: Database instance
        """
        self.db = database

    def get_all(self) -> List[Snippet]:
        """Get all snippets.

        Returns:
            List of snippets
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, trigger, expansion, category, description FROM snippets"
                )
                rows = cursor.fetchall()
                return [
                    Snippet(
                        id=row["id"],
                        trigger=row["trigger"],
                        expansion=row["expansion"],
                        category=row["category"] or "",
                        description=row["description"] or "",
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error("Failed to get snippets: %s", e)
            return []

    def get_by_id(self, snippet_id: int) -> Optional[Snippet]:
        """Get a snippet by ID.

        Args:
            snippet_id: Snippet ID

        Returns:
            Snippet or None
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, trigger, expansion, category, description "
                    "FROM snippets WHERE id = ?",
                    (snippet_id,),
                )
                row = cursor.fetchone()
                if row:
                    return Snippet(
                        id=row["id"],
                        trigger=row["trigger"],
                        expansion=row["expansion"],
                        category=row["category"] or "",
                        description=row["description"] or "",
                    )
                return None
        except Exception as e:
            logger.error("Failed to get snippet %d: %s", snippet_id, e)
            return None

    def get_by_trigger(self, trigger: str) -> Optional[Snippet]:
        """Get a snippet by trigger.

        Args:
            trigger: Snippet trigger

        Returns:
            Snippet or None
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, trigger, expansion, category, description "
                    "FROM snippets WHERE trigger = ?",
                    (trigger,),
                )
                row = cursor.fetchone()
                if row:
                    return Snippet(
                        id=row["id"],
                        trigger=row["trigger"],
                        expansion=row["expansion"],
                        category=row["category"] or "",
                        description=row["description"] or "",
                    )
                return None
        except Exception as e:
            logger.error("Failed to get snippet by trigger '%s': %s", trigger, e)
            return None

    def get_by_category(self, category: str) -> List[Snippet]:
        """Get snippets by category.

        Args:
            category: Category name

        Returns:
            List of snippets
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT id, trigger, expansion, category, description "
                    "FROM snippets WHERE category = ?",
                    (category,),
                )
                rows = cursor.fetchall()
                return [
                    Snippet(
                        id=row["id"],
                        trigger=row["trigger"],
                        expansion=row["expansion"],
                        category=row["category"] or "",
                        description=row["description"] or "",
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error("Failed to get snippets by category '%s': %s", category, e)
            return []

    def create(
        self,
        trigger: str,
        expansion: str,
        category: str = "",
        description: str = "",
    ) -> Optional[Snippet]:
        """Create a new snippet.

        Args:
            trigger: Trigger phrase
            expansion: Expanded text
            category: Category name
            description: Description

        Returns:
            Created snippet or None
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO snippets (trigger, expansion, category, description) "
                    "VALUES (?, ?, ?, ?)",
                    (trigger, expansion, category, description),
                )
                return Snippet(
                    id=cursor.lastrowid,
                    trigger=trigger,
                    expansion=expansion,
                    category=category,
                    description=description,
                )
        except Exception as e:
            logger.error("Failed to create snippet: %s", e)
            return None

    def update(self, snippet: Snippet) -> bool:
        """Update a snippet.

        Args:
            snippet: Snippet with updated values

        Returns:
            True if updated
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "UPDATE snippets SET trigger = ?, expansion = ?, "
                    "category = ?, description = ?, updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = ?",
                    (
                        snippet.trigger,
                        snippet.expansion,
                        snippet.category,
                        snippet.description,
                        snippet.id,
                    ),
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error("Failed to update snippet %d: %s", snippet.id, e)
            return False

    def delete(self, snippet_id: int) -> bool:
        """Delete a snippet.

        Args:
            snippet_id: ID of snippet to delete

        Returns:
            True if deleted
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error("Failed to delete snippet %d: %s", snippet_id, e)
            return False

    def get_categories(self) -> List[str]:
        """Get all unique categories.

        Returns:
            List of category names
        """
        try:
            with self.db.cursor() as cursor:
                cursor.execute(
                    "SELECT DISTINCT category FROM snippets WHERE category != ''"
                )
                return [row["category"] for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Failed to get categories: %s", e)
            return []

    def import_snippets(self, snippets: List[dict]) -> int:
        """Import snippets from a list of dicts.

        Args:
            snippets: List of snippet dicts

        Returns:
            Number of imported snippets
        """
        count = 0
        for data in snippets:
            snippet = self.create(
                trigger=data.get("trigger", ""),
                expansion=data.get("expansion", ""),
                category=data.get("category", ""),
                description=data.get("description", ""),
            )
            if snippet:
                count += 1
        return count

    def export_snippets(self) -> List[dict]:
        """Export all snippets as dicts.

        Returns:
            List of snippet dicts
        """
        snippets = self.get_all()
        return [
            {
                "trigger": s.trigger,
                "expansion": s.expansion,
                "category": s.category,
                "description": s.description,
            }
            for s in snippets
        ]
