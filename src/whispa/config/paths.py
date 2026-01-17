"""Application paths for Whispa."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_app_paths: Optional["AppPaths"] = None


@dataclass
class AppPaths:
    """Application directory paths."""

    base_dir: Path
    config_file: Path
    database_file: Path
    log_file: Path
    models_dir: Path
    cache_dir: Path

    def ensure_directories(self) -> None:
        """Create all required directories."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Ensure parent directories for files exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)


def get_app_paths() -> AppPaths:
    """Get application paths, using %APPDATA%/Whispa on Windows.

    Returns:
        AppPaths instance with all configured paths
    """
    global _app_paths

    if _app_paths is not None:
        return _app_paths

    # Use APPDATA on Windows, fallback to home directory
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base_dir = Path(appdata) / "Whispa"
        else:
            base_dir = Path.home() / ".whispa"
    else:
        base_dir = Path.home() / ".whispa"

    _app_paths = AppPaths(
        base_dir=base_dir,
        config_file=base_dir / "config.json",
        database_file=base_dir / "whispa.db",
        log_file=base_dir / "logs" / "whispa.log",
        models_dir=base_dir / "models",
        cache_dir=base_dir / "cache",
    )

    return _app_paths


def reset_app_paths() -> None:
    """Reset cached paths (for testing)."""
    global _app_paths
    _app_paths = None
