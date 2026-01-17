"""Recording overlay indicator."""

import logging
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QCursor, QPainter, QColor, QBrush, QPen

logger = logging.getLogger(__name__)


class RecordingOverlay(QWidget):
    """Small overlay window shown near cursor during recording."""

    def __init__(self, opacity: float = 0.9, parent: Optional[QWidget] = None):
        """Initialize overlay.

        Args:
            opacity: Window opacity (0.0-1.0)
            parent: Parent widget
        """
        super().__init__(parent)

        self._audio_level = 0.0

        # Window flags for overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )

        # Make window transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(opacity)

        # Fixed size
        self.setFixedSize(80, 80)

        # Animation timer
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_value = 0.0
        self._pulse_direction = 1

    def show_at_cursor(self) -> None:
        """Show overlay near the current cursor position."""
        cursor_pos = QCursor.pos()

        # Offset from cursor
        offset_x = 20
        offset_y = 20

        self.move(cursor_pos.x() + offset_x, cursor_pos.y() + offset_y)
        self.show()
        self._pulse_timer.start(50)

    def hide(self) -> None:
        """Hide the overlay."""
        self._pulse_timer.stop()
        super().hide()

    def set_audio_level(self, level: float) -> None:
        """Set the current audio level.

        Args:
            level: Audio level (0.0-1.0)
        """
        self._audio_level = max(0.0, min(1.0, level))
        self.update()

    def _pulse(self) -> None:
        """Animate the pulse effect."""
        self._pulse_value += 0.1 * self._pulse_direction
        if self._pulse_value >= 1.0:
            self._pulse_direction = -1
        elif self._pulse_value <= 0.0:
            self._pulse_direction = 1
        self.update()

    def paintEvent(self, event) -> None:
        """Paint the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2

        # Background circle (semi-transparent)
        bg_color = QColor(40, 40, 40, 200)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(5, 5, width - 10, height - 10)

        # Outer ring (pulse effect)
        pulse_alpha = int(100 + 100 * self._pulse_value)
        ring_color = QColor(255, 0, 0, pulse_alpha)
        pen = QPen(ring_color, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(8, 8, width - 16, height - 16)

        # Inner recording indicator (red dot)
        inner_size = 20 + int(self._audio_level * 15)
        inner_x = center_x - inner_size // 2
        inner_y = center_y - inner_size // 2

        # Glow effect based on audio level
        if self._audio_level > 0.1:
            glow_size = inner_size + 10
            glow_color = QColor(255, 0, 0, int(80 * self._audio_level))
            painter.setBrush(QBrush(glow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            glow_x = center_x - glow_size // 2
            glow_y = center_y - glow_size // 2
            painter.drawEllipse(glow_x, glow_y, glow_size, glow_size)

        # Red recording dot
        dot_color = QColor(255, 50, 50)
        painter.setBrush(QBrush(dot_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(inner_x, inner_y, inner_size, inner_size)

        painter.end()
