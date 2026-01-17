"""Audio capture using sounddevice."""

import numpy as np
import sounddevice as sd
import threading
import logging
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AudioDevice:
    """Audio device information."""

    index: int
    name: str
    channels: int
    sample_rate: float
    is_default: bool


class AudioCapture:
    """Real-time audio capture using sounddevice."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration_ms: int = 30,
        device: Optional[str] = None,
    ):
        """Initialize audio capture.

        Args:
            sample_rate: Sample rate in Hz
            channels: Number of channels (1 for mono)
            chunk_duration_ms: Duration of each audio chunk in ms
            device: Device name or None for default
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        self.device_name = device

        self._stream: Optional[sd.InputStream] = None
        self._callback: Optional[Callable[[np.ndarray], None]] = None
        self._running = False
        self._lock = threading.Lock()

    @staticmethod
    def list_devices() -> List[AudioDevice]:
        """List available input devices.

        Returns:
            List of AudioDevice objects
        """
        devices = []
        try:
            default_device = sd.default.device[0]
            for i, dev in enumerate(sd.query_devices()):
                if dev["max_input_channels"] > 0:
                    devices.append(
                        AudioDevice(
                            index=i,
                            name=dev["name"],
                            channels=dev["max_input_channels"],
                            sample_rate=dev["default_samplerate"],
                            is_default=(i == default_device),
                        )
                    )
        except Exception as e:
            logger.error("Failed to list audio devices: %s", e)
        return devices

    @staticmethod
    def get_device_index(name: Optional[str]) -> Optional[int]:
        """Get device index by name.

        Args:
            name: Device name or None/default for default device

        Returns:
            Device index or None for default
        """
        if name is None or name.lower() == "default":
            return None

        devices = AudioCapture.list_devices()
        for dev in devices:
            if name.lower() in dev.name.lower():
                return dev.index

        logger.warning("Device '%s' not found, using default", name)
        return None

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info: Any, status: sd.CallbackFlags
    ) -> None:
        """Internal callback for sounddevice stream."""
        if status:
            logger.warning("Audio callback status: %s", status)

        if self._callback is not None:
            # Convert to float32 and flatten to mono
            audio = indata.flatten().astype(np.float32)
            self._callback(audio)

    def start(self, callback: Callable[[np.ndarray], None]) -> bool:
        """Start audio capture.

        Args:
            callback: Function to call with audio chunks

        Returns:
            True if started successfully
        """
        with self._lock:
            if self._running:
                logger.warning("Audio capture already running")
                return True

            try:
                device_index = self.get_device_index(self.device_name)
                self._callback = callback

                self._stream = sd.InputStream(
                    device=device_index,
                    channels=self.channels,
                    samplerate=self.sample_rate,
                    blocksize=self.chunk_size,
                    dtype=np.float32,
                    callback=self._audio_callback,
                )
                self._stream.start()
                self._running = True

                logger.info(
                    "Started audio capture: %d Hz, %d ch, device=%s",
                    self.sample_rate,
                    self.channels,
                    self.device_name or "default",
                )
                return True

            except Exception as e:
                logger.error("Failed to start audio capture: %s", e)
                self._stream = None
                self._callback = None
                return False

    def stop(self) -> None:
        """Stop audio capture."""
        with self._lock:
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.warning("Error stopping audio stream: %s", e)
                finally:
                    self._stream = None

            self._callback = None
            self._running = False
            logger.info("Stopped audio capture")

    @property
    def is_running(self) -> bool:
        """Check if capture is running."""
        with self._lock:
            return self._running

    def get_input_level(self) -> float:
        """Get current input level (0.0 - 1.0).

        Note: This is a placeholder; actual level tracking would need
        to be implemented in the callback.
        """
        return 0.0
