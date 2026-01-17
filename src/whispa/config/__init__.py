"""Configuration module for Whispa."""

from whispa.config.settings import Settings
from whispa.config.manager import ConfigManager
from whispa.config.paths import get_app_paths, AppPaths

__all__ = ["Settings", "ConfigManager", "get_app_paths", "AppPaths"]
