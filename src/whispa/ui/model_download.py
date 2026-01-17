"""Model download progress dialog."""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread

from whispa.transcription.model_manager import ModelManager

logger = logging.getLogger(__name__)


class DownloadWorker(QThread):
    """Worker thread for model download."""

    progress = pyqtSignal(float, str)
    finished = pyqtSignal(bool)

    def __init__(self, model_manager: ModelManager, model_size: str):
        super().__init__()
        self.model_manager = model_manager
        self.model_size = model_size
        self._cancelled = False

    def run(self):
        """Run the download."""

        def progress_callback(progress: float, message: str):
            if not self._cancelled:
                self.progress.emit(progress, message)

        success = self.model_manager.download_model(
            self.model_size, progress_callback=progress_callback
        )
        self.finished.emit(success)

    def cancel(self):
        """Cancel the download."""
        self._cancelled = True


class ModelDownloadDialog(QDialog):
    """Dialog showing model download progress."""

    def __init__(
        self,
        model_manager: ModelManager,
        model_size: str,
        parent: Optional[QWidget] = None,
    ):
        """Initialize download dialog.

        Args:
            model_manager: Model manager instance
            model_size: Model size to download
            parent: Parent widget
        """
        super().__init__(parent)

        self.model_manager = model_manager
        self.model_size = model_size
        self._worker: Optional[DownloadWorker] = None

        self.setWindowTitle("Downloading Model")
        self.setModal(True)
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Model info
        self._model_label = QLabel(f"Downloading: {self.model_size}")
        self._model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._model_label)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        # Status label
        self._status_label = QLabel("Preparing download...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._cancel)
        layout.addWidget(self._cancel_btn)

    def start_download(self) -> None:
        """Start the download."""
        self._worker = DownloadWorker(self.model_manager, self.model_size)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, progress: float, message: str) -> None:
        """Handle progress update.

        Args:
            progress: Progress value (0.0-1.0)
            message: Status message
        """
        self._progress.setValue(int(progress * 100))
        self._status_label.setText(message)

    def _on_finished(self, success: bool) -> None:
        """Handle download finished.

        Args:
            success: Whether download was successful
        """
        if success:
            self._status_label.setText("Download complete!")
            self._cancel_btn.setText("Close")
            self._cancel_btn.clicked.disconnect()
            self._cancel_btn.clicked.connect(self.accept)
        else:
            self._status_label.setText("Download failed or cancelled.")
            self._cancel_btn.setText("Close")
            self._cancel_btn.clicked.disconnect()
            self._cancel_btn.clicked.connect(self.reject)

    def _cancel(self) -> None:
        """Cancel the download."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()
        self.reject()

    def closeEvent(self, event) -> None:
        """Handle window close."""
        self._cancel()
        event.accept()
