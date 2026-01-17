"""Voice Activity Detection using Silero-VAD."""

import numpy as np
import logging
import threading
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """Voice Activity Detection using Silero-VAD model."""

    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000):
        """Initialize VAD.

        Args:
            threshold: Speech probability threshold (0.0-1.0)
            sample_rate: Audio sample rate (must be 16000 for Silero)
        """
        self.threshold = threshold
        self.sample_rate = sample_rate
        self._model = None
        self._get_speech_timestamps = None
        self._lock = threading.Lock()
        self._loaded = False

    def load(self) -> bool:
        """Load the Silero-VAD model.

        Returns:
            True if loaded successfully
        """
        with self._lock:
            if self._loaded:
                return True

            try:
                import torch

                # Load Silero VAD from torch hub
                model, utils = torch.hub.load(
                    repo_or_dir="snakers4/silero-vad",
                    model="silero_vad",
                    force_reload=False,
                    onnx=False,
                    trust_repo=True,
                )

                self._model = model
                (
                    self._get_speech_timestamps,
                    _,
                    self._read_audio,
                    *_,
                ) = utils

                self._loaded = True
                logger.info("Silero-VAD model loaded successfully")
                return True

            except Exception as e:
                logger.error("Failed to load Silero-VAD: %s", e)
                return False

    def is_speech(self, audio: np.ndarray) -> Tuple[bool, float]:
        """Check if audio chunk contains speech.

        Args:
            audio: Audio samples (float32, 16kHz)

        Returns:
            Tuple of (is_speech, probability)
        """
        if not self._loaded:
            if not self.load():
                return False, 0.0

        try:
            import torch

            with self._lock:
                # Ensure audio is the right format
                if audio.dtype != np.float32:
                    audio = audio.astype(np.float32)

                # Convert to tensor
                tensor = torch.from_numpy(audio)

                # Get speech probability
                prob = self._model(tensor, self.sample_rate).item()

                is_speech = prob >= self.threshold
                return is_speech, prob

        except Exception as e:
            logger.error("VAD inference error: %s", e)
            return False, 0.0

    def reset(self) -> None:
        """Reset VAD state (for new utterance)."""
        with self._lock:
            if self._model is not None:
                try:
                    self._model.reset_states()
                except Exception:
                    pass

    def get_speech_segments(
        self, audio: np.ndarray, min_speech_ms: int = 250, min_silence_ms: int = 300
    ) -> list:
        """Get speech segments from audio.

        Args:
            audio: Complete audio recording
            min_speech_ms: Minimum speech duration in ms
            min_silence_ms: Minimum silence to split segments

        Returns:
            List of (start_sample, end_sample) tuples
        """
        if not self._loaded:
            if not self.load():
                return [(0, len(audio))]

        try:
            import torch

            with self._lock:
                tensor = torch.from_numpy(audio.astype(np.float32))

                timestamps = self._get_speech_timestamps(
                    tensor,
                    self._model,
                    threshold=self.threshold,
                    sampling_rate=self.sample_rate,
                    min_speech_duration_ms=min_speech_ms,
                    min_silence_duration_ms=min_silence_ms,
                )

                if not timestamps:
                    return [(0, len(audio))]

                return [(ts["start"], ts["end"]) for ts in timestamps]

        except Exception as e:
            logger.error("Failed to get speech segments: %s", e)
            return [(0, len(audio))]
