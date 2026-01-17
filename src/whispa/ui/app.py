"""Main Qt application."""

import sys
import logging
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from whispa.config.paths import get_app_paths
from whispa.config.manager import ConfigManager
from whispa.core.controller import AppController
from whispa.ui.tray import SystemTrayIcon
from whispa.ui.overlay import RecordingOverlay
from whispa.ui.settings_window import SettingsWindow
from whispa.ui.snippets_window import SnippetsWindow
from whispa.ui.dictionary_window import DictionaryWindow

logger = logging.getLogger(__name__)


class WhispaApplication:
    """Main application class."""

    def __init__(self, argv: list):
        """Initialize application.

        Args:
            argv: Command line arguments
        """
        # Enable high DPI support
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        self.app = QApplication(argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("Whispa")
        self.app.setOrganizationName("Whispa")

        # Get paths and config
        self.paths = get_app_paths()
        self.config_manager = ConfigManager(self.paths.config_file)

        # Initialize controller
        self.controller: Optional[AppController] = None
        self.tray: Optional[SystemTrayIcon] = None
        self.overlay: Optional[RecordingOverlay] = None
        self.settings_window: Optional[SettingsWindow] = None
        self.snippets_window: Optional[SnippetsWindow] = None
        self.dictionary_window: Optional[DictionaryWindow] = None

    def run(self) -> int:
        """Run the application.

        Returns:
            Exit code
        """
        try:
            # Initialize controller
            self.controller = AppController(self.paths, self.config_manager)
            if not self.controller.initialize():
                logger.error("Failed to initialize controller")
                return 1

            # Create UI components
            self._create_ui()

            # Connect signals
            self._connect_signals()

            # Start controller
            if not self.controller.start():
                logger.error("Failed to start controller")
                return 1

            logger.info("Application started")

            # Run event loop
            return self.app.exec()

        except Exception as e:
            logger.exception("Application error: %s", e)
            return 1

        finally:
            self._cleanup()

    def _create_ui(self) -> None:
        """Create UI components."""
        # System tray
        self.tray = SystemTrayIcon(self.controller, self.app)
        self.tray.show()

        # Recording overlay
        if self.controller.settings.ui.show_overlay:
            self.overlay = RecordingOverlay(
                opacity=self.controller.settings.ui.overlay_opacity
            )

        # Settings window (created but not shown)
        self.settings_window = SettingsWindow(
            self.controller,
            self.config_manager,
        )

        # Snippets window (created but not shown)
        self.snippets_window = SnippetsWindow(self.controller)

        # Dictionary window (created but not shown)
        self.dictionary_window = DictionaryWindow(self.controller)

        # Connect tray actions
        self.tray.settings_requested.connect(self._show_settings)
        self.tray.snippets_requested.connect(self._show_snippets)
        self.tray.dictionary_requested.connect(self._show_dictionary)
        self.tray.quit_requested.connect(self._quit)

    def _connect_signals(self) -> None:
        """Connect controller signals to UI."""
        events = self.controller.events

        # Recording state
        events.recording_started.connect(self._on_recording_started)
        events.recording_stopped.connect(self._on_recording_stopped)

        # Transcription
        events.transcription_completed.connect(self._on_transcription_completed)
        events.transcription_error.connect(self._on_transcription_error)

        # Audio level
        events.audio_level_changed.connect(self._on_audio_level_changed)

    def _on_recording_started(self) -> None:
        """Handle recording started."""
        if self.overlay:
            self.overlay.show_at_cursor()
        if self.tray:
            self.tray.set_recording(True)

    def _on_recording_stopped(self) -> None:
        """Handle recording stopped."""
        if self.overlay:
            self.overlay.hide()
        if self.tray:
            self.tray.set_recording(False)

    def _on_transcription_completed(self, text: str) -> None:
        """Handle transcription completed."""
        if self.tray and len(text) > 0:
            preview = text[:50] + "..." if len(text) > 50 else text
            self.tray.show_notification("Transcribed", preview)

    def _on_transcription_error(self, error: str) -> None:
        """Handle transcription error."""
        if self.tray:
            self.tray.show_notification("Error", error)

    def _on_audio_level_changed(self, level: float) -> None:
        """Handle audio level change."""
        if self.overlay and self.overlay.isVisible():
            self.overlay.set_audio_level(level)

    def _show_settings(self) -> None:
        """Show settings window."""
        if self.settings_window:
            self.settings_window.show()
            self.settings_window.activateWindow()

    def _show_snippets(self) -> None:
        """Show snippets window."""
        if self.snippets_window:
            self.snippets_window.show()
            self.snippets_window.activateWindow()

    def _show_dictionary(self) -> None:
        """Show dictionary window."""
        if self.dictionary_window:
            self.dictionary_window.show()
            self.dictionary_window.activateWindow()

    def _quit(self) -> None:
        """Quit the application."""
        logger.info("Quit requested")
        self._cleanup()
        self.app.quit()

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.controller:
            self.controller.stop()

        if self.overlay:
            self.overlay.close()

        if self.settings_window:
            self.settings_window.close()

        if self.snippets_window:
            self.snippets_window.close()

        if self.dictionary_window:
            self.dictionary_window.close()
