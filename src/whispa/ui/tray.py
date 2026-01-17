"""System tray icon and menu."""

import logging
from typing import Optional

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PyQt6.QtCore import pyqtSignal, QObject

from whispa.core.controller import AppController
from whispa.core.state_machine import AppState

logger = logging.getLogger(__name__)


class SystemTrayIcon(QObject):
    """System tray icon with context menu."""

    # Signals
    settings_requested = pyqtSignal()
    snippets_requested = pyqtSignal()
    dictionary_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    # Icon colors
    COLOR_IDLE = QColor(100, 100, 100)  # Gray
    COLOR_LISTENING = QColor(255, 0, 0)  # Red
    COLOR_PROCESSING = QColor(255, 165, 0)  # Orange

    def __init__(self, controller: AppController, parent: QApplication):
        """Initialize system tray.

        Args:
            controller: Application controller
            parent: Parent application
        """
        super().__init__(parent)

        self.controller = controller
        self._tray = QSystemTrayIcon(parent)

        # Create icons
        self._icon_idle = self._create_icon(self.COLOR_IDLE)
        self._icon_listening = self._create_icon(self.COLOR_LISTENING)
        self._icon_processing = self._create_icon(self.COLOR_PROCESSING)

        self._tray.setIcon(self._icon_idle)
        self._tray.setToolTip("Whispa - Voice Dictation")

        # Create context menu
        self._create_menu()

        # Connect state changes
        controller.events.state_changed.connect(self._on_state_changed)

    def _create_icon(self, color: QColor) -> QIcon:
        """Create a simple colored circle icon.

        Args:
            color: Icon color

        Returns:
            QIcon instance
        """
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(color)
        painter.setPen(QColor(255, 255, 255))
        painter.drawEllipse(4, 4, size - 8, size - 8)
        painter.end()

        return QIcon(pixmap)

    def _create_menu(self) -> None:
        """Create context menu."""
        menu = QMenu()

        # Status (disabled, just for display)
        self._status_action = menu.addAction("Status: Idle")
        self._status_action.setEnabled(False)

        menu.addSeparator()

        # Settings
        settings_action = menu.addAction("Settings...")
        settings_action.triggered.connect(self.settings_requested.emit)

        # Snippets
        snippets_action = menu.addAction("Snippets...")
        snippets_action.triggered.connect(self.snippets_requested.emit)

        # Dictionary
        dictionary_action = menu.addAction("Dictionary...")
        dictionary_action.triggered.connect(self.dictionary_requested.emit)

        menu.addSeparator()

        # Quit
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_requested.emit)

        self._tray.setContextMenu(menu)

        # Double-click to open settings
        self._tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation.

        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()

    def _on_state_changed(self, old_state: AppState, new_state: AppState) -> None:
        """Handle state change.

        Args:
            old_state: Previous state
            new_state: New state
        """
        if new_state == AppState.IDLE:
            self._tray.setIcon(self._icon_idle)
            self._status_action.setText("Status: Idle")
            self._tray.setToolTip("Whispa - Ready")
        elif new_state == AppState.LISTENING:
            self._tray.setIcon(self._icon_listening)
            self._status_action.setText("Status: Recording")
            self._tray.setToolTip("Whispa - Recording...")
        elif new_state == AppState.PROCESSING:
            self._tray.setIcon(self._icon_processing)
            self._status_action.setText("Status: Processing")
            self._tray.setToolTip("Whispa - Processing...")

    def set_recording(self, recording: bool) -> None:
        """Update recording state display.

        Args:
            recording: Whether currently recording
        """
        if recording:
            self._tray.setIcon(self._icon_listening)
        else:
            self._tray.setIcon(self._icon_idle)

    def show_notification(self, title: str, message: str) -> None:
        """Show a notification.

        Args:
            title: Notification title
            message: Notification message
        """
        self._tray.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000,  # 3 seconds
        )

    def show(self) -> None:
        """Show the tray icon."""
        self._tray.show()

    def hide(self) -> None:
        """Hide the tray icon."""
        self._tray.hide()
