"""Settings window."""

import logging
import threading
import numpy as np
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from whispa.config.settings import Settings
from whispa.config.manager import ConfigManager
from whispa.core.controller import AppController
from whispa.audio.capture import AudioCapture
from whispa.transcription.model_manager import AVAILABLE_MODELS, detect_gpu

logger = logging.getLogger(__name__)


class SettingsWindow(QDialog):
    """Settings configuration window."""

    # Signals for thread-safe UI updates
    _download_progress = pyqtSignal(float, str)
    _transcription_result = pyqtSignal(str)

    def __init__(
        self,
        controller: AppController,
        config_manager: ConfigManager,
        parent: Optional[QWidget] = None,
    ):
        """Initialize settings window.

        Args:
            controller: Application controller
            config_manager: Configuration manager
            parent: Parent widget
        """
        super().__init__(parent)

        self.controller = controller
        self.config_manager = config_manager

        self.setWindowTitle("Whispa Settings")
        self.setMinimumSize(550, 500)

        self._volume_meter = None  # Will be created in _create_audio_tab
        self._is_test_recording = False
        self._test_audio_buffer = []

        self._setup_ui()
        self._load_settings()
        self._update_model_status()

        # Connect signals
        self.controller.events.audio_level_changed.connect(self._on_audio_level_changed)
        self._download_progress.connect(self._on_download_progress)
        self._transcription_result.connect(self._on_transcription_result)

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "General")
        tabs.addTab(self._create_audio_tab(), "Audio")
        tabs.addTab(self._create_transcription_tab(), "Transcription")
        tabs.addTab(self._create_text_processing_tab(), "Text Processing")
        tabs.addTab(self._create_hotkeys_tab(), "Hotkeys")

        layout.addWidget(tabs)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_defaults)

        buttons_layout.addWidget(reset_btn)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # UI group
        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout(ui_group)

        self._show_overlay = QCheckBox()
        ui_layout.addRow("Show recording overlay:", self._show_overlay)

        self._overlay_opacity = QSlider(Qt.Orientation.Horizontal)
        self._overlay_opacity.setRange(50, 100)
        self._overlay_opacity.setTickInterval(10)
        ui_layout.addRow("Overlay opacity:", self._overlay_opacity)

        self._start_minimized = QCheckBox()
        ui_layout.addRow("Start minimized:", self._start_minimized)

        self._start_with_windows = QCheckBox()
        ui_layout.addRow("Start with Windows:", self._start_with_windows)

        layout.addWidget(ui_group)

        # Output group
        output_group = QGroupBox("Text Output")
        output_layout = QFormLayout(output_group)

        self._output_method = QComboBox()
        self._output_method.addItems(["clipboard", "keyboard"])
        output_layout.addRow("Injection method:", self._output_method)

        self._add_trailing_space = QCheckBox()
        output_layout.addRow("Add trailing space:", self._add_trailing_space)

        layout.addWidget(output_group)

        layout.addStretch()
        return widget

    def _create_audio_tab(self) -> QWidget:
        """Create audio settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Device group
        device_group = QGroupBox("Input Device")
        device_layout = QFormLayout(device_group)

        self._audio_device = QComboBox()
        self._audio_device.addItem("Default")
        for device in AudioCapture.list_devices():
            self._audio_device.addItem(device.name)
        device_layout.addRow("Microphone:", self._audio_device)

        self._volume_meter = QProgressBar()
        self._volume_meter.setRange(0, 100)
        self._volume_meter.setValue(0)
        self._volume_meter.setTextVisible(False)
        self._volume_meter.setFixedHeight(20)
        self._volume_meter.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        device_layout.addRow("Input Level:", self._volume_meter)

        layout.addWidget(device_group)

        # VAD group
        vad_group = QGroupBox("Voice Activity Detection")
        vad_layout = QFormLayout(vad_group)

        self._vad_threshold = QDoubleSpinBox()
        self._vad_threshold.setRange(0.1, 0.9)
        self._vad_threshold.setSingleStep(0.1)
        self._vad_threshold.setDecimals(1)
        vad_layout.addRow("VAD threshold:", self._vad_threshold)

        self._vad_min_speech = QSpinBox()
        self._vad_min_speech.setRange(100, 1000)
        self._vad_min_speech.setSuffix(" ms")
        vad_layout.addRow("Min speech duration:", self._vad_min_speech)

        self._vad_min_silence = QSpinBox()
        self._vad_min_silence.setRange(100, 1000)
        self._vad_min_silence.setSuffix(" ms")
        vad_layout.addRow("Min silence duration:", self._vad_min_silence)

        self._pre_roll = QSpinBox()
        self._pre_roll.setRange(0, 1000)
        self._pre_roll.setSuffix(" ms")
        vad_layout.addRow("Pre-roll buffer:", self._pre_roll)

        layout.addWidget(vad_group)

        layout.addStretch()
        return widget

    def _create_transcription_tab(self) -> QWidget:
        """Create transcription settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Model group
        model_group = QGroupBox("Model")
        model_layout = QFormLayout(model_group)

        self._model_size = QComboBox()
        for name, info in AVAILABLE_MODELS.items():
            self._model_size.addItem(f"{name} ({info.size_mb} MB)", name)
        self._model_size.currentIndexChanged.connect(self._update_model_status)
        model_layout.addRow("Model:", self._model_size)

        # Model status row
        status_layout = QHBoxLayout()
        self._model_status_label = QLabel("Checking...")
        self._download_btn = QPushButton("Download")
        self._download_btn.clicked.connect(self._download_model)
        self._download_btn.setFixedWidth(100)
        status_layout.addWidget(self._model_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self._download_btn)
        model_layout.addRow("Status:", status_layout)

        # Download progress bar (hidden by default)
        self._download_progress_bar = QProgressBar()
        self._download_progress_bar.setRange(0, 100)
        self._download_progress_bar.setVisible(False)
        model_layout.addRow("", self._download_progress_bar)

        # Device detection
        cuda_available, device_name = detect_gpu()
        self._device = QComboBox()
        self._device.addItems(["auto", "cuda", "cpu"])
        if not cuda_available:
            self._device.setCurrentText("cpu")
        device_label = QLabel(f"Detected: {device_name}")
        device_label.setStyleSheet("color: gray;")
        model_layout.addRow("Compute device:", self._device)
        model_layout.addRow("", device_label)

        self._compute_type = QComboBox()
        self._compute_type.addItems(["float16", "float32", "int8"])
        model_layout.addRow("Compute type:", self._compute_type)

        layout.addWidget(model_group)

        # Language group
        lang_group = QGroupBox("Language")
        lang_layout = QFormLayout(lang_group)

        self._language = QComboBox()
        self._language.addItem("Auto-detect", "auto")
        self._language.addItem("English", "en")
        self._language.addItem("Spanish", "es")
        self._language.addItem("French", "fr")
        self._language.addItem("German", "de")
        self._language.addItem("Italian", "it")
        self._language.addItem("Portuguese", "pt")
        self._language.addItem("Russian", "ru")
        self._language.addItem("Japanese", "ja")
        self._language.addItem("Chinese", "zh")
        lang_layout.addRow("Language:", self._language)

        self._beam_size = QSpinBox()
        self._beam_size.setRange(1, 10)
        lang_layout.addRow("Beam size:", self._beam_size)

        self._initial_prompt = QLineEdit()
        self._initial_prompt.setPlaceholderText("Optional prompt to guide transcription")
        lang_layout.addRow("Initial prompt:", self._initial_prompt)

        layout.addWidget(lang_group)

        # Test transcription group
        test_group = QGroupBox("Test Transcription")
        test_layout = QVBoxLayout(test_group)

        # Test controls
        test_controls = QHBoxLayout()
        self._test_record_btn = QPushButton("Hold to Record")
        self._test_record_btn.pressed.connect(self._start_test_recording)
        self._test_record_btn.released.connect(self._stop_test_recording)
        self._test_volume_meter = QProgressBar()
        self._test_volume_meter.setRange(0, 100)
        self._test_volume_meter.setValue(0)
        self._test_volume_meter.setTextVisible(False)
        self._test_volume_meter.setFixedHeight(20)
        self._test_volume_meter.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        test_controls.addWidget(self._test_record_btn)
        test_controls.addWidget(self._test_volume_meter, 1)
        test_layout.addLayout(test_controls)

        # Transcription output
        self._test_output = QTextEdit()
        self._test_output.setReadOnly(True)
        self._test_output.setPlaceholderText("Transcription results will appear here...")
        self._test_output.setMaximumHeight(80)
        test_layout.addWidget(self._test_output)

        layout.addWidget(test_group)

        return widget

    def _create_text_processing_tab(self) -> QWidget:
        """Create text processing settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filler words group
        filler_group = QGroupBox("Filler Words")
        filler_layout = QVBoxLayout(filler_group)

        self._remove_fillers = QCheckBox("Remove filler words")
        filler_layout.addWidget(self._remove_fillers)

        filler_layout.addWidget(QLabel("Filler words (comma-separated):"))
        self._filler_words = QPlainTextEdit()
        self._filler_words.setMaximumHeight(80)
        filler_layout.addWidget(self._filler_words)

        layout.addWidget(filler_group)

        # Formatting group
        format_group = QGroupBox("Formatting")
        format_layout = QFormLayout(format_group)

        self._auto_capitalize = QCheckBox()
        format_layout.addRow("Auto-capitalize:", self._auto_capitalize)

        self._voice_commands = QCheckBox()
        format_layout.addRow("Voice commands:", self._voice_commands)

        layout.addWidget(format_group)

        layout.addStretch()
        return widget

    def _create_hotkeys_tab(self) -> QWidget:
        """Create hotkeys settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Mode group
        mode_group = QGroupBox("Activation Mode")
        mode_layout = QFormLayout(mode_group)

        self._hotkey_mode = QComboBox()
        self._hotkey_mode.addItems(["toggle", "hold"])
        mode_layout.addRow("Mode:", self._hotkey_mode)

        layout.addWidget(mode_group)

        # Hotkeys group
        hotkeys_group = QGroupBox("Hotkeys")
        hotkeys_layout = QFormLayout(hotkeys_group)

        self._activate_hotkey = QLineEdit()
        self._activate_hotkey.setPlaceholderText("e.g., ctrl+shift+space")
        hotkeys_layout.addRow("Activate:", self._activate_hotkey)

        self._cancel_hotkey = QLineEdit()
        self._cancel_hotkey.setPlaceholderText("e.g., escape")
        hotkeys_layout.addRow("Cancel:", self._cancel_hotkey)

        layout.addWidget(hotkeys_group)

        # Help text
        help_label = QLabel(
            "Modifier keys: ctrl, shift, alt, win\n"
            "Special keys: space, enter, tab, escape, f1-f12\n"
            "Example: ctrl+shift+space"
        )
        help_label.setStyleSheet("color: gray;")
        layout.addWidget(help_label)

        layout.addStretch()
        return widget

    def _load_settings(self) -> None:
        """Load current settings into UI."""
        settings = self.config_manager.settings

        # General
        self._show_overlay.setChecked(settings.ui.show_overlay)
        self._overlay_opacity.setValue(int(settings.ui.overlay_opacity * 100))
        self._start_minimized.setChecked(settings.ui.start_minimized)
        self._start_with_windows.setChecked(settings.ui.start_with_windows)
        self._output_method.setCurrentText(settings.output.method)
        self._add_trailing_space.setChecked(settings.output.add_trailing_space)

        # Audio
        device = settings.audio.input_device
        if device == "default":
            self._audio_device.setCurrentIndex(0)
        else:
            idx = self._audio_device.findText(device)
            if idx >= 0:
                self._audio_device.setCurrentIndex(idx)
        self._vad_threshold.setValue(settings.audio.vad_threshold)
        self._vad_min_speech.setValue(settings.audio.vad_min_speech_ms)
        self._vad_min_silence.setValue(settings.audio.vad_min_silence_ms)
        self._pre_roll.setValue(settings.audio.pre_roll_ms)

        # Transcription
        model_idx = self._model_size.findData(settings.transcription.model_size)
        if model_idx >= 0:
            self._model_size.setCurrentIndex(model_idx)
        self._device.setCurrentText(settings.transcription.device)
        self._compute_type.setCurrentText(settings.transcription.compute_type)
        lang_idx = self._language.findData(settings.transcription.language)
        if lang_idx >= 0:
            self._language.setCurrentIndex(lang_idx)
        self._beam_size.setValue(settings.transcription.beam_size)
        self._initial_prompt.setText(settings.transcription.initial_prompt)

        # Text processing
        self._remove_fillers.setChecked(settings.text_processing.remove_filler_words)
        self._filler_words.setPlainText(", ".join(settings.text_processing.filler_words))
        self._auto_capitalize.setChecked(settings.text_processing.auto_capitalize)
        self._voice_commands.setChecked(settings.text_processing.voice_commands_enabled)

        # Hotkeys
        self._hotkey_mode.setCurrentText(settings.hotkeys.mode)
        self._activate_hotkey.setText(settings.hotkeys.activate)
        self._cancel_hotkey.setText(settings.hotkeys.cancel)

    def _save_settings(self) -> None:
        """Save settings from UI."""
        settings = self.config_manager.settings

        # General
        settings.ui.show_overlay = self._show_overlay.isChecked()
        settings.ui.overlay_opacity = self._overlay_opacity.value() / 100.0
        settings.ui.start_minimized = self._start_minimized.isChecked()
        settings.ui.start_with_windows = self._start_with_windows.isChecked()
        settings.output.method = self._output_method.currentText()
        settings.output.add_trailing_space = self._add_trailing_space.isChecked()

        # Audio
        device = self._audio_device.currentText()
        settings.audio.input_device = "default" if device == "Default" else device
        settings.audio.vad_threshold = self._vad_threshold.value()
        settings.audio.vad_min_speech_ms = self._vad_min_speech.value()
        settings.audio.vad_min_silence_ms = self._vad_min_silence.value()
        settings.audio.pre_roll_ms = self._pre_roll.value()

        # Transcription
        settings.transcription.model_size = self._model_size.currentData()
        settings.transcription.device = self._device.currentText()
        settings.transcription.compute_type = self._compute_type.currentText()
        settings.transcription.language = self._language.currentData()
        settings.transcription.beam_size = self._beam_size.value()
        settings.transcription.initial_prompt = self._initial_prompt.text()

        # Text processing
        settings.text_processing.remove_filler_words = self._remove_fillers.isChecked()
        filler_text = self._filler_words.toPlainText()
        settings.text_processing.filler_words = [
            w.strip() for w in filler_text.split(",") if w.strip()
        ]
        settings.text_processing.auto_capitalize = self._auto_capitalize.isChecked()
        settings.text_processing.voice_commands_enabled = self._voice_commands.isChecked()

        # Hotkeys
        settings.hotkeys.mode = self._hotkey_mode.currentText()
        settings.hotkeys.activate = self._activate_hotkey.text()
        settings.hotkeys.cancel = self._cancel_hotkey.text()

        # Apply settings
        self.controller.update_settings(settings)

        QMessageBox.information(self, "Settings", "Settings saved successfully.")
        self.close()

    def _reset_defaults(self) -> None:
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.reset_to_defaults()
            self._load_settings()

    def _on_audio_level_changed(self, level: float) -> None:
        """Update volume meter with current audio level.

        Args:
            level: Audio level from 0.0 to 1.0
        """
        level_int = int(level * 100)
        if self._volume_meter is not None:
            self._volume_meter.setValue(level_int)
        if hasattr(self, '_test_volume_meter') and self._test_volume_meter is not None:
            self._test_volume_meter.setValue(level_int)

    def _update_model_status(self) -> None:
        """Update the model status indicator."""
        if not hasattr(self, '_model_status_label'):
            return

        model_size = self._model_size.currentData()
        if model_size is None:
            return

        # Check if model is available by checking huggingface cache
        try:
            from huggingface_hub import scan_cache_dir
            cache_info = scan_cache_dir()
            model_downloaded = any(
                model_size in repo.repo_id
                for repo in cache_info.repos
            )
        except Exception:
            # Fallback: assume not downloaded
            model_downloaded = False

        if model_downloaded:
            self._model_status_label.setText("Ready")
            self._model_status_label.setStyleSheet("color: green; font-weight: bold;")
            self._download_btn.setText("Re-download")
            self._download_btn.setEnabled(True)
        else:
            self._model_status_label.setText("Not downloaded")
            self._model_status_label.setStyleSheet("color: orange; font-weight: bold;")
            self._download_btn.setText("Download")
            self._download_btn.setEnabled(True)

    def _download_model(self) -> None:
        """Start model download in background thread."""
        model_size = self._model_size.currentData()
        if model_size is None:
            return

        self._download_btn.setEnabled(False)
        self._download_progress_bar.setVisible(True)
        self._download_progress_bar.setValue(0)
        self._model_status_label.setText("Downloading...")
        self._model_status_label.setStyleSheet("color: blue;")

        def download_thread():
            try:
                self._download_progress.emit(0.1, "Loading model (downloading if needed)...")
                from faster_whisper import WhisperModel

                # This triggers the download
                _ = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                )
                self._download_progress.emit(1.0, "Complete")
            except Exception as e:
                self._download_progress.emit(-1.0, str(e))

        threading.Thread(target=download_thread, daemon=True).start()

    def _on_download_progress(self, progress: float, message: str) -> None:
        """Handle download progress update from background thread."""
        if progress < 0:
            # Error
            self._download_progress_bar.setVisible(False)
            self._model_status_label.setText(f"Error: {message[:30]}...")
            self._model_status_label.setStyleSheet("color: red;")
            self._download_btn.setEnabled(True)
            QMessageBox.warning(self, "Download Error", f"Failed to download model:\n{message}")
        elif progress >= 1.0:
            # Complete
            self._download_progress_bar.setValue(100)
            self._download_progress_bar.setVisible(False)
            self._model_status_label.setText("Ready")
            self._model_status_label.setStyleSheet("color: green; font-weight: bold;")
            self._download_btn.setText("Re-download")
            self._download_btn.setEnabled(True)
        else:
            # In progress
            self._download_progress_bar.setValue(int(progress * 100))

    def _capture_audio_chunk(self, audio) -> None:
        """Capture audio chunk for test recording."""
        if self._is_test_recording:
            self._test_audio_chunks.append(audio.copy())

    def _start_test_recording(self) -> None:
        """Start test recording."""
        self._is_test_recording = True
        self._test_audio_chunks = []
        self._test_record_btn.setText("Recording...")
        self._test_record_btn.setStyleSheet("background-color: #ff6b6b;")
        self._test_output.setPlainText("Recording... (speak now)")

        # Register as audio listener
        self.controller.add_audio_listener(self._capture_audio_chunk)

    def _stop_test_recording(self) -> None:
        """Stop test recording and transcribe."""
        if not self._is_test_recording:
            return

        self._is_test_recording = False
        self._test_record_btn.setText("Hold to Record")
        self._test_record_btn.setStyleSheet("")
        self._test_output.setPlainText("Transcribing...")

        # Unregister audio listener
        self.controller.remove_audio_listener(self._capture_audio_chunk)

        # Combine captured audio chunks
        if not self._test_audio_chunks:
            self._test_output.setPlainText("No audio captured. Try again.")
            return

        audio = np.concatenate(self._test_audio_chunks)
        self._test_audio_chunks = []

        if len(audio) < 8000:  # Less than 0.5 seconds
            self._test_output.setPlainText(f"Recording too short ({len(audio)/16000:.1f}s). Hold longer.")
            return

        self._test_output.setPlainText(f"Transcribing {len(audio)/16000:.1f}s of audio...")

        # Transcribe in background thread
        def transcribe_thread():
            try:
                result = self.controller.transcription_engine.transcribe(
                    audio,
                    sample_rate=self.controller.settings.audio.sample_rate,
                    language=self.controller.settings.transcription.language,
                )
                if result and result.text:
                    self._transcription_result.emit(result.text)
                else:
                    self._transcription_result.emit("[No speech detected]")
            except Exception as e:
                self._transcription_result.emit(f"[Error: {e}]")

        threading.Thread(target=transcribe_thread, daemon=True).start()

    def _on_transcription_result(self, text: str) -> None:
        """Handle transcription result from background thread."""
        self._test_output.setPlainText(text)
