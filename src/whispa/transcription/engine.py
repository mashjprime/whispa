"""Transcription engine using faster-whisper."""

import numpy as np
import logging
import threading
from typing import Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from whispa.config.settings import TranscriptionSettings
from whispa.transcription.model_manager import ModelManager, detect_gpu

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result of a transcription."""

    text: str
    language: str
    language_probability: float
    duration_seconds: float
    segments: list


class TranscriptionEngine:
    """Transcription engine using faster-whisper."""

    def __init__(self, settings: TranscriptionSettings, models_dir: Path):
        """Initialize transcription engine.

        Args:
            settings: Transcription settings
            models_dir: Directory for model storage
        """
        self.settings = settings
        self.models_dir = models_dir
        self.model_manager = ModelManager(models_dir)

        self._model = None
        self._lock = threading.Lock()
        self._loaded = False

    def load_model(self) -> bool:
        """Load the Whisper model.

        Returns:
            True if loaded successfully
        """
        with self._lock:
            if self._loaded:
                return True

            try:
                from faster_whisper import WhisperModel

                # Determine device and compute type
                device = self.settings.device
                compute_type = self.settings.compute_type

                # Always validate CUDA availability
                cuda_available, gpu_name = detect_gpu()

                if device == "auto":
                    device = "cuda" if cuda_available else "cpu"
                elif device == "cuda" and not cuda_available:
                    logger.warning("CUDA requested but not available, falling back to CPU")
                    device = "cpu"

                # Adjust compute type for CPU
                if device == "cpu":
                    compute_type = "int8"

                logger.info(
                    "Loading model %s on %s with %s",
                    self.settings.model_size,
                    device,
                    compute_type,
                )

                self._model = WhisperModel(
                    self.settings.model_size,
                    device=device,
                    compute_type=compute_type,
                    download_root=str(self.models_dir),
                )

                self._loaded = True
                logger.info("Model loaded successfully")
                return True

            except Exception as e:
                logger.error("Failed to load model: %s", e)
                return False

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        with self._lock:
            if self._model is not None:
                del self._model
                self._model = None
                self._loaded = False

                # Force garbage collection
                import gc

                gc.collect()

                try:
                    import torch

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass

                logger.info("Model unloaded")

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> Optional[TranscriptionResult]:
        """Transcribe audio.

        Args:
            audio: Audio samples (float32, mono)
            sample_rate: Sample rate in Hz
            language: Language code or None for auto-detect

        Returns:
            TranscriptionResult or None if failed
        """
        if not self._loaded:
            if not self.load_model():
                return None

        try:
            with self._lock:
                # Ensure audio is correct format
                if audio.dtype != np.float32:
                    audio = audio.astype(np.float32)

                # Resample if needed
                if sample_rate != 16000:
                    audio = self._resample(audio, sample_rate, 16000)

                # Determine language
                lang = language
                if lang == "auto" or lang is None:
                    lang = None  # Let Whisper auto-detect

                # Get initial prompt
                initial_prompt = self.settings.initial_prompt or None

                # Transcribe
                segments, info = self._model.transcribe(
                    audio,
                    language=lang,
                    beam_size=self.settings.beam_size,
                    initial_prompt=initial_prompt,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=300,
                        speech_pad_ms=200,
                    ),
                )

                # Collect segments
                segment_list = []
                text_parts = []

                for segment in segments:
                    segment_list.append(
                        {
                            "start": segment.start,
                            "end": segment.end,
                            "text": segment.text,
                        }
                    )
                    text_parts.append(segment.text.strip())

                full_text = " ".join(text_parts)

                return TranscriptionResult(
                    text=full_text,
                    language=info.language,
                    language_probability=info.language_probability,
                    duration_seconds=info.duration,
                    segments=segment_list,
                )

        except Exception as e:
            logger.error("Transcription failed: %s", e)
            return None

    def _resample(
        self, audio: np.ndarray, orig_sr: int, target_sr: int
    ) -> np.ndarray:
        """Resample audio to target sample rate.

        Args:
            audio: Input audio
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled audio
        """
        if orig_sr == target_sr:
            return audio

        # Simple linear interpolation resampling
        duration = len(audio) / orig_sr
        target_length = int(duration * target_sr)
        indices = np.linspace(0, len(audio) - 1, target_length)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        with self._lock:
            return self._loaded

    def update_settings(self, settings: TranscriptionSettings) -> None:
        """Update transcription settings (may require model reload).

        Args:
            settings: New settings
        """
        need_reload = (
            settings.model_size != self.settings.model_size
            or settings.device != self.settings.device
            or settings.compute_type != self.settings.compute_type
        )

        self.settings = settings

        if need_reload and self._loaded:
            logger.info("Settings changed, reloading model")
            self.unload_model()
            self.load_model()
