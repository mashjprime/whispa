"""Qt signals for cross-thread communication."""

from PyQt6.QtCore import QObject, pyqtSignal
from whispa.core.state_machine import AppState


class AppEvents(QObject):
    """Qt signals for application events."""

    # State changes
    state_changed = pyqtSignal(AppState, AppState)  # old_state, new_state

    # Audio events
    audio_level_changed = pyqtSignal(float)  # level 0.0-1.0
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()

    # Transcription events
    transcription_started = pyqtSignal()
    transcription_completed = pyqtSignal(str)  # transcribed text
    transcription_error = pyqtSignal(str)  # error message

    # Text injection events
    text_injected = pyqtSignal(str)  # injected text

    # Model events
    model_loading = pyqtSignal()
    model_loaded = pyqtSignal()
    model_download_progress = pyqtSignal(float, str)  # progress 0-1, message

    # Error events
    error_occurred = pyqtSignal(str)  # error message

    # UI events
    settings_changed = pyqtSignal()
    show_notification = pyqtSignal(str, str)  # title, message

    def __init__(self, parent=None):
        super().__init__(parent)
