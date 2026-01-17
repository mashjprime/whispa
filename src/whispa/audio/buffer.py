"""Ring buffer for audio with pre-roll support."""

import numpy as np
import threading
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AudioBuffer:
    """Thread-safe ring buffer for audio samples with pre-roll."""

    def __init__(self, sample_rate: int = 16000, pre_roll_ms: int = 300, max_duration_s: float = 60.0):
        """Initialize audio buffer.

        Args:
            sample_rate: Audio sample rate in Hz
            pre_roll_ms: Pre-roll duration in milliseconds
            max_duration_s: Maximum recording duration in seconds
        """
        self.sample_rate = sample_rate
        self.pre_roll_samples = int(sample_rate * pre_roll_ms / 1000)
        self.max_samples = int(sample_rate * max_duration_s)

        # Pre-roll buffer (circular)
        self._pre_roll = np.zeros(self.pre_roll_samples, dtype=np.float32)
        self._pre_roll_pos = 0

        # Main recording buffer
        self._buffer: list[np.ndarray] = []
        self._total_samples = 0

        self._lock = threading.Lock()
        self._recording = False

    def add_to_pre_roll(self, audio: np.ndarray) -> None:
        """Add audio to pre-roll buffer (always running).

        Args:
            audio: Audio samples to add
        """
        with self._lock:
            samples = audio.flatten().astype(np.float32)

            for sample in samples:
                self._pre_roll[self._pre_roll_pos] = sample
                self._pre_roll_pos = (self._pre_roll_pos + 1) % self.pre_roll_samples

    def start_recording(self) -> None:
        """Start recording, capturing pre-roll."""
        with self._lock:
            self._buffer.clear()
            self._total_samples = 0

            # Copy pre-roll to start of recording
            pre_roll = np.concatenate([
                self._pre_roll[self._pre_roll_pos:],
                self._pre_roll[:self._pre_roll_pos]
            ])
            self._buffer.append(pre_roll)
            self._total_samples = len(pre_roll)
            self._recording = True
            logger.debug("Started recording with %d samples pre-roll", len(pre_roll))

    def add_samples(self, audio: np.ndarray) -> bool:
        """Add audio samples to the recording buffer.

        Args:
            audio: Audio samples to add

        Returns:
            True if samples added, False if max duration exceeded
        """
        with self._lock:
            if not self._recording:
                return False

            samples = audio.flatten().astype(np.float32)

            if self._total_samples + len(samples) > self.max_samples:
                logger.warning("Max recording duration exceeded")
                return False

            self._buffer.append(samples)
            self._total_samples += len(samples)
            return True

    def stop_recording(self) -> Optional[np.ndarray]:
        """Stop recording and return the audio.

        Returns:
            Recorded audio as numpy array, or None if not recording
        """
        with self._lock:
            if not self._recording:
                return None

            self._recording = False

            if not self._buffer:
                return None

            audio = np.concatenate(self._buffer)
            self._buffer.clear()
            self._total_samples = 0

            logger.debug("Stopped recording, %d samples captured", len(audio))
            return audio

    def clear(self) -> None:
        """Clear all buffers."""
        with self._lock:
            self._buffer.clear()
            self._total_samples = 0
            self._pre_roll.fill(0)
            self._pre_roll_pos = 0
            self._recording = False

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        with self._lock:
            return self._recording

    @property
    def duration_ms(self) -> int:
        """Get current recording duration in milliseconds."""
        with self._lock:
            return int(self._total_samples * 1000 / self.sample_rate)
