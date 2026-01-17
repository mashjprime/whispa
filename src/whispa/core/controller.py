"""Main application controller."""

import logging
import threading
import numpy as np
from typing import Optional
from pathlib import Path

from whispa.config.settings import Settings
from whispa.config.manager import ConfigManager
from whispa.config.paths import AppPaths

from whispa.core.state_machine import AppState, StateMachine
from whispa.core.events import AppEvents

from whispa.audio.capture import AudioCapture
from whispa.audio.buffer import AudioBuffer
from whispa.audio.vad import VoiceActivityDetector

from whispa.transcription.engine import TranscriptionEngine
from whispa.transcription.post_processor import PostProcessor

from whispa.text_processing.commands import VoiceCommandProcessor
from whispa.text_processing.filler_words import FillerWordRemover
from whispa.text_processing.formatting import TextFormatter
from whispa.text_processing.snippets import SnippetExpander
from whispa.text_processing.dictionary import DictionaryCorrector

from whispa.output.injector import TextInjector
from whispa.hotkeys.manager import HotkeyManager

from whispa.data.database import Database
from whispa.data.snippets_repo import SnippetsRepository
from whispa.data.dictionary_repo import DictionaryRepository

logger = logging.getLogger(__name__)


class AppController:
    """Main application controller that orchestrates all components."""

    def __init__(self, paths: AppPaths, config_manager: ConfigManager):
        """Initialize controller.

        Args:
            paths: Application paths
            config_manager: Configuration manager
        """
        self.paths = paths
        self.config_manager = config_manager
        self.settings = config_manager.settings

        # Core components
        self.state_machine = StateMachine()
        self.events = AppEvents()

        # Audio components
        self.audio_capture: Optional[AudioCapture] = None
        self.audio_buffer: Optional[AudioBuffer] = None
        self.vad: Optional[VoiceActivityDetector] = None

        # Transcription components
        self.transcription_engine: Optional[TranscriptionEngine] = None
        self.post_processor: Optional[PostProcessor] = None

        # Text processing components
        self.voice_commands: Optional[VoiceCommandProcessor] = None
        self.filler_remover: Optional[FillerWordRemover] = None
        self.formatter: Optional[TextFormatter] = None
        self.snippet_expander: Optional[SnippetExpander] = None
        self.dictionary_corrector: Optional[DictionaryCorrector] = None

        # Output components
        self.text_injector: Optional[TextInjector] = None
        self.hotkey_manager: Optional[HotkeyManager] = None

        # Data components
        self.database: Optional[Database] = None
        self.snippets_repo: Optional[SnippetsRepository] = None
        self.dictionary_repo: Optional[DictionaryRepository] = None

        # Internal state
        self._lock = threading.Lock()
        self._is_recording = False
        self._speech_detected = False
        self._audio_level = 0.0
        self._audio_listeners = []  # Additional callbacks for audio chunks
        self._listeners_lock = threading.Lock()  # Lock for audio listeners
        self._recorded_chunks = []  # Audio chunks collected during recording
        self._chunks_lock = threading.Lock()  # Lock for recorded chunks

    def initialize(self) -> bool:
        """Initialize all components.

        Returns:
            True if successful
        """
        logger.info("Initializing application controller...")

        try:
            # Initialize database
            self.database = Database(self.paths.database_file)
            if not self.database.initialize():
                raise RuntimeError("Failed to initialize database")

            self.snippets_repo = SnippetsRepository(self.database)
            self.dictionary_repo = DictionaryRepository(self.database)

            # Initialize audio components
            self.audio_capture = AudioCapture(
                sample_rate=self.settings.audio.sample_rate,
                device=self.settings.audio.input_device,
            )
            self.audio_buffer = AudioBuffer(
                sample_rate=self.settings.audio.sample_rate,
                pre_roll_ms=self.settings.audio.pre_roll_ms,
            )
            self.vad = VoiceActivityDetector(
                threshold=self.settings.audio.vad_threshold,
                sample_rate=self.settings.audio.sample_rate,
            )
            # Pre-load VAD model to avoid blocking during first recording
            self.vad.load()

            # Initialize transcription components
            self.transcription_engine = TranscriptionEngine(
                self.settings.transcription,
                self.paths.models_dir,
            )
            self.post_processor = PostProcessor(
                filler_words=self.settings.text_processing.filler_words,
                remove_fillers=self.settings.text_processing.remove_filler_words,
                auto_capitalize=self.settings.text_processing.auto_capitalize,
            )

            # Initialize text processing components
            self.voice_commands = VoiceCommandProcessor(
                enabled=self.settings.text_processing.voice_commands_enabled
            )
            self.filler_remover = FillerWordRemover(
                filler_words=self.settings.text_processing.filler_words,
                enabled=self.settings.text_processing.remove_filler_words,
            )
            self.formatter = TextFormatter(
                auto_capitalize=self.settings.text_processing.auto_capitalize
            )
            self.snippet_expander = SnippetExpander(enabled=True)
            self.dictionary_corrector = DictionaryCorrector(enabled=True)

            # Load snippets and dictionary from database
            self._load_data_from_database()

            # Initialize output components
            self.text_injector = TextInjector(
                method=self.settings.output.method,
                add_trailing_space=self.settings.output.add_trailing_space,
            )

            # Initialize hotkey manager
            self.hotkey_manager = HotkeyManager()

            # Register hotkeys
            self._register_hotkeys()

            # Connect state machine to events
            logger.debug("Adding state listener...")
            self.state_machine.add_listener(self._on_state_changed)

            # Transition to idle
            logger.debug("Transitioning to IDLE state...")
            self.state_machine.transition_to(AppState.IDLE)
            logger.debug("State transition complete")

            logger.info("Application controller initialized")
            return True

        except Exception as e:
            logger.error("Failed to initialize controller: %s", e)
            self.state_machine.force_state(AppState.ERROR)
            return False

    def _load_data_from_database(self) -> None:
        """Load snippets and dictionary from database."""
        # Load snippets
        snippets = self.snippets_repo.get_all()
        self.snippet_expander.load_snippets(snippets)
        logger.info("Loaded %d snippets", len(snippets))

        # Load dictionary
        entries = self.dictionary_repo.get_all()
        self.dictionary_corrector.load_entries(entries)
        logger.info("Loaded %d dictionary entries", len(entries))

    def _register_hotkeys(self) -> None:
        """Register global hotkeys."""
        if self.settings.hotkeys.mode == "hold":
            # Hold mode: start recording on press, stop on release
            self.hotkey_manager.register_hotkey(
                "activate",
                self.settings.hotkeys.activate,
                on_press=self._start_recording,
                on_release=self._stop_recording,
            )
        else:
            # Toggle mode: toggle recording on each press
            self.hotkey_manager.register_hotkey(
                "activate",
                self.settings.hotkeys.activate,
                on_press=self._on_activate_hotkey,
            )

        # Cancel hotkey (same for both modes)
        self.hotkey_manager.register_hotkey(
            "cancel",
            self.settings.hotkeys.cancel,
            on_press=self._on_cancel_hotkey,
        )

    def start(self) -> bool:
        """Start the controller (begin listening for hotkeys).

        Returns:
            True if started
        """
        logger.info("Starting controller...")

        # Start hotkey listener
        if not self.hotkey_manager.start():
            logger.error("Failed to start hotkey manager")
            return False

        # Start audio capture (always running for pre-roll)
        if not self.audio_capture.start(self._on_audio_chunk):
            logger.error("Failed to start audio capture")
            return False

        logger.info("Controller started")
        return True

    def stop(self) -> None:
        """Stop the controller."""
        logger.info("Stopping controller...")

        self.state_machine.transition_to(AppState.SHUTDOWN)

        # Stop audio capture
        if self.audio_capture:
            self.audio_capture.stop()

        # Stop hotkey listener
        if self.hotkey_manager:
            self.hotkey_manager.stop()

        # Unload model to free memory
        if self.transcription_engine:
            self.transcription_engine.unload_model()

        # Close database
        if self.database:
            self.database.close()

        logger.info("Controller stopped")

    def _on_activate_hotkey(self) -> None:
        """Handle activate/toggle hotkey press."""
        logger.debug("Activate hotkey pressed")

        current_state = self.state_machine.state

        if current_state == AppState.IDLE:
            self._start_recording()
        elif current_state == AppState.LISTENING:
            self._stop_recording()
        # Ignore if processing

    def _on_cancel_hotkey(self) -> None:
        """Handle cancel hotkey press."""
        logger.debug("Cancel hotkey pressed")

        current_state = self.state_machine.state

        if current_state == AppState.LISTENING:
            # Cancel recording without transcription
            self.audio_buffer.stop_recording()
            self.audio_buffer.clear()
            self.state_machine.transition_to(AppState.IDLE)
            logger.info("Recording cancelled")

    def _start_recording(self) -> None:
        """Start recording audio."""
        if not self.state_machine.transition_to(AppState.LISTENING):
            return

        # Clear and start collecting audio chunks
        with self._chunks_lock:
            self._recorded_chunks.clear()
        self._is_recording = True
        self._speech_detected = False

        self.events.recording_started.emit()
        logger.info("Recording started")

    def _stop_recording(self) -> None:
        """Stop recording and process audio."""
        if not self.state_machine.transition_to(AppState.PROCESSING):
            return

        # Stop collecting first
        self._is_recording = False

        # Combine collected chunks with lock
        with self._chunks_lock:
            if not self._recorded_chunks:
                logger.warning("No audio chunks captured")
                self.state_machine.transition_to(AppState.IDLE)
                return

            audio = np.concatenate(self._recorded_chunks)
            self._recorded_chunks.clear()

        self.events.recording_stopped.emit()
        logger.info("Recording stopped, %d samples captured", len(audio))

        if len(audio) < 8000:  # Less than 0.5 seconds
            logger.warning("Recording too short (%d samples), skipping transcription", len(audio))
            self.state_machine.transition_to(AppState.IDLE)
            return

        # Process in background thread
        threading.Thread(
            target=self._process_audio,
            args=(audio,),
            daemon=True,
        ).start()

    def _on_audio_chunk(self, audio: np.ndarray) -> None:
        """Handle incoming audio chunk from capture.

        Args:
            audio: Audio samples
        """
        # Calculate audio level
        self._audio_level = float(np.abs(audio).mean())
        self.events.audio_level_changed.emit(min(1.0, self._audio_level * 10))

        # Always add to pre-roll buffer
        self.audio_buffer.add_to_pre_roll(audio)

        # If recording, collect audio directly
        if self._is_recording:
            with self._chunks_lock:
                self._recorded_chunks.append(audio.copy())

            # Check VAD for speech detection (ignore errors)
            try:
                is_speech, prob = self.vad.is_speech(audio)
                if is_speech:
                    self._speech_detected = True
            except Exception:
                pass  # VAD errors shouldn't stop recording

        # Notify any additional audio listeners
        with self._listeners_lock:
            listeners = self._audio_listeners.copy()
        for listener in listeners:
            try:
                listener(audio)
            except Exception as e:
                logger.warning("Audio listener error: %s", e)

    def add_audio_listener(self, callback) -> None:
        """Add a callback to receive audio chunks.

        Args:
            callback: Function that takes audio numpy array
        """
        with self._listeners_lock:
            if callback not in self._audio_listeners:
                self._audio_listeners.append(callback)

    def remove_audio_listener(self, callback) -> None:
        """Remove an audio listener callback.

        Args:
            callback: Callback to remove
        """
        with self._listeners_lock:
            if callback in self._audio_listeners:
                self._audio_listeners.remove(callback)

    def _process_audio(self, audio: np.ndarray) -> None:
        """Process recorded audio (background thread).

        Args:
            audio: Recorded audio samples
        """
        try:
            self.events.transcription_started.emit()

            # Transcribe
            result = self.transcription_engine.transcribe(
                audio,
                sample_rate=self.settings.audio.sample_rate,
                language=self.settings.transcription.language,
            )

            if result is None or not result.text:
                logger.warning("No transcription result")
                self.state_machine.transition_to(AppState.IDLE)
                return

            text = result.text
            logger.info("Transcribed: %s", text[:100])

            # Apply post-processing
            text = self._process_text(text)

            if not text:
                logger.warning("Text empty after processing")
                self.state_machine.transition_to(AppState.IDLE)
                return

            # Inject text
            self.text_injector.inject(text)
            self.events.transcription_completed.emit(text)
            self.events.text_injected.emit(text)

            logger.info("Injected text: %s", text[:100])

        except Exception as e:
            logger.error("Audio processing failed: %s", e)
            self.events.transcription_error.emit(str(e))

        finally:
            self.state_machine.transition_to(AppState.IDLE)

    def _process_text(self, text: str) -> str:
        """Apply all text processing to transcribed text.

        Args:
            text: Raw transcribed text

        Returns:
            Processed text
        """
        # Remove filler words
        text = self.filler_remover.remove(text)

        # Apply voice commands
        text, _ = self.voice_commands.process(text)

        # Apply dictionary corrections
        text, _ = self.dictionary_corrector.correct(text)

        # Expand snippets
        text, _ = self.snippet_expander.expand(text)

        # Apply formatting
        text = self.formatter.format(text)

        return text

    def _on_state_changed(self, old_state: AppState, new_state: AppState) -> None:
        """Handle state machine state change.

        Args:
            old_state: Previous state
            new_state: New state
        """
        try:
            from PyQt6.QtWidgets import QApplication
            if QApplication.instance() is not None:
                self.events.state_changed.emit(old_state, new_state)
        except Exception:
            pass  # Qt not ready yet

    def update_settings(self, settings: Settings) -> None:
        """Update application settings.

        Args:
            settings: New settings
        """
        self.settings = settings
        self.config_manager.save(settings)

        # Update components with new settings
        if self.audio_capture:
            # Would need to restart audio capture for device change
            pass

        if self.transcription_engine:
            self.transcription_engine.update_settings(settings.transcription)

        if self.post_processor:
            self.post_processor.filler_words = settings.text_processing.filler_words
            self.post_processor.remove_fillers = settings.text_processing.remove_filler_words
            self.post_processor.auto_capitalize = settings.text_processing.auto_capitalize

        if self.filler_remover:
            self.filler_remover.set_filler_words(settings.text_processing.filler_words)
            self.filler_remover.enabled = settings.text_processing.remove_filler_words

        if self.voice_commands:
            self.voice_commands.enabled = settings.text_processing.voice_commands_enabled

        if self.formatter:
            self.formatter.auto_capitalize = settings.text_processing.auto_capitalize

        if self.text_injector:
            self.text_injector.method = settings.output.method
            self.text_injector.add_trailing_space = settings.output.add_trailing_space

        # Re-register hotkeys
        if self.hotkey_manager:
            self.hotkey_manager.unregister_hotkey("activate")
            self.hotkey_manager.unregister_hotkey("cancel")
            self._register_hotkeys()

        self.events.settings_changed.emit()
        logger.info("Settings updated")

    def reload_data(self) -> None:
        """Reload snippets and dictionary from database."""
        self._load_data_from_database()

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording

    @property
    def audio_level(self) -> float:
        """Get current audio level."""
        return self._audio_level
