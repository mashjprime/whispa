"""Tests for configuration module."""

import pytest
import json
import tempfile
from pathlib import Path

from whispa.config.settings import Settings, HotkeySettings, TranscriptionSettings
from whispa.config.manager import ConfigManager


class TestSettings:
    """Tests for Settings dataclass."""

    def test_default_settings(self):
        """Test default settings creation."""
        settings = Settings()

        assert settings.hotkeys.mode == "toggle"
        assert settings.hotkeys.activate == "ctrl+shift+space"
        assert settings.transcription.model_size == "large-v3-turbo"
        assert settings.transcription.device == "cuda"
        assert settings.audio.sample_rate == 16000
        assert settings.text_processing.remove_filler_words is True
        assert settings.output.method == "clipboard"

    def test_settings_to_dict(self):
        """Test settings serialization to dict."""
        settings = Settings()
        data = settings.to_dict()

        assert "hotkeys" in data
        assert "transcription" in data
        assert "audio" in data
        assert "text_processing" in data
        assert "output" in data
        assert "ui" in data

        assert data["hotkeys"]["mode"] == "toggle"
        assert data["transcription"]["model_size"] == "large-v3-turbo"

    def test_settings_from_dict(self):
        """Test settings deserialization from dict."""
        data = {
            "hotkeys": {
                "mode": "hold",
                "activate": "f5",
            },
            "transcription": {
                "model_size": "small",
                "device": "cpu",
            },
        }

        settings = Settings.from_dict(data)

        assert settings.hotkeys.mode == "hold"
        assert settings.hotkeys.activate == "f5"
        assert settings.transcription.model_size == "small"
        assert settings.transcription.device == "cpu"
        # Defaults for unspecified
        assert settings.audio.sample_rate == 16000

    def test_settings_roundtrip(self):
        """Test settings can be serialized and deserialized."""
        original = Settings()
        original.hotkeys.mode = "hold"
        original.transcription.model_size = "medium"

        data = original.to_dict()
        restored = Settings.from_dict(data)

        assert restored.hotkeys.mode == original.hotkeys.mode
        assert restored.transcription.model_size == original.transcription.model_size


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_file)

            settings = manager.load()

            assert settings.hotkeys.mode == "toggle"

    def test_save_and_load(self):
        """Test saving and loading settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_file)

            # Modify and save
            settings = manager.settings
            settings.hotkeys.mode = "hold"
            settings.transcription.model_size = "small"
            manager.save(settings)

            # Load in new manager
            manager2 = ConfigManager(config_file)
            loaded = manager2.load()

            assert loaded.hotkeys.mode == "hold"
            assert loaded.transcription.model_size == "small"

    def test_save_creates_directory(self):
        """Test save creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "subdir" / "config.json"
            manager = ConfigManager(config_file)

            manager.save(Settings())

            assert config_file.exists()

    def test_reset_to_defaults(self):
        """Test reset to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_file)

            # Modify
            settings = manager.settings
            settings.hotkeys.mode = "hold"
            manager.save(settings)

            # Reset
            settings = manager.reset_to_defaults()

            assert settings.hotkeys.mode == "toggle"
