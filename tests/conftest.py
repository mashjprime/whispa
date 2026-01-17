"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Provide a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config_file(temp_dir):
    """Provide a temporary config file path."""
    return temp_dir / "config.json"


@pytest.fixture
def db_file(temp_dir):
    """Provide a temporary database file path."""
    return temp_dir / "test.db"
