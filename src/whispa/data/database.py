"""SQLite database connection and management."""

import sqlite3
import logging
import threading
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Path):
        """Initialize database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()
        self._initialized = False

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    @contextmanager
    def connection(self):
        """Context manager for database connection."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    @contextmanager
    def cursor(self):
        """Context manager for database cursor."""
        with self.connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def initialize(self) -> bool:
        """Initialize database schema.

        Returns:
            True if successful
        """
        if self._initialized:
            return True

        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            with self.cursor() as cursor:
                # Create schema version table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY
                    )
                """)

                # Check current version
                cursor.execute("SELECT version FROM schema_version LIMIT 1")
                row = cursor.fetchone()
                current_version = row[0] if row else 0

                # Apply migrations
                if current_version < self.SCHEMA_VERSION:
                    self._migrate(cursor, current_version)

                    # Update version
                    cursor.execute("DELETE FROM schema_version")
                    cursor.execute(
                        "INSERT INTO schema_version (version) VALUES (?)",
                        (self.SCHEMA_VERSION,),
                    )

            self._initialized = True
            logger.info("Database initialized at %s", self.db_path)
            return True

        except Exception as e:
            logger.error("Failed to initialize database: %s", e)
            return False

    def _migrate(self, cursor: sqlite3.Cursor, from_version: int) -> None:
        """Apply database migrations.

        Args:
            cursor: Database cursor
            from_version: Current schema version
        """
        if from_version < 1:
            # Initial schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snippets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger TEXT NOT NULL UNIQUE,
                    expansion TEXT NOT NULL,
                    category TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dictionary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original TEXT NOT NULL,
                    replacement TEXT NOT NULL,
                    case_sensitive INTEGER DEFAULT 0,
                    whole_word INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(original, case_sensitive)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snippets_trigger
                ON snippets(trigger)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snippets_category
                ON snippets(category)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_dictionary_original
                ON dictionary(original)
            """)

            logger.info("Applied migration to schema version 1")

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            try:
                self._local.connection.close()
            except Exception:
                pass
            finally:
                self._local.connection = None
