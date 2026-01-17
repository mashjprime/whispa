"""Data storage module with SQLite."""

from whispa.data.database import Database
from whispa.data.snippets_repo import SnippetsRepository
from whispa.data.dictionary_repo import DictionaryRepository

__all__ = ["Database", "SnippetsRepository", "DictionaryRepository"]
