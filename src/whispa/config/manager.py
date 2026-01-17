"""Configuration manager for loading and saving settings."""

import json
import logging
from pathlib import Path
from typing import Optional

from whispa.config.settings import Settings

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages loading and saving application configuration."""

    def __init__(self, config_file: Path):
        """Initialize config manager.

        Args:
            config_file: Path to the JSON config file
        """
        self.config_file = config_file
        self._settings: Optional[Settings] = None

    @property
    def settings(self) -> Settings:
        """Get current settings, loading from file if needed."""
        if self._settings is None:
            self._settings = self.load()
        return self._settings

    def load(self) -> Settings:
        """Load settings from file.

        Returns:
            Settings instance (defaults if file doesn't exist)
        """
        if not self.config_file.exists():
            logger.info("Config file not found, using defaults")
            return Settings()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Loaded config from %s", self.config_file)
            return Settings.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in config file: %s", e)
            return Settings()
        except Exception as e:
            logger.error("Failed to load config: %s", e)
            return Settings()

    def save(self, settings: Optional[Settings] = None) -> bool:
        """Save settings to file.

        Args:
            settings: Settings to save (uses current if None)

        Returns:
            True if saved successfully
        """
        if settings is not None:
            self._settings = settings

        if self._settings is None:
            self._settings = Settings()

        try:
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._settings.to_dict(), f, indent=2)
            logger.info("Saved config to %s", self.config_file)
            return True
        except Exception as e:
            logger.error("Failed to save config: %s", e)
            return False

    def reset_to_defaults(self) -> Settings:
        """Reset settings to defaults.

        Returns:
            Default settings
        """
        self._settings = Settings()
        self.save()
        return self._settings

    def update(self, **kwargs) -> Settings:
        """Update specific settings.

        Args:
            **kwargs: Settings to update (nested with dots, e.g., 'hotkeys.mode')

        Returns:
            Updated settings
        """
        settings = self.settings

        for key, value in kwargs.items():
            parts = key.split(".")
            obj = settings
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)

        self.save()
        return settings
