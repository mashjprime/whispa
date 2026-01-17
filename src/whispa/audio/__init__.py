"""Audio capture and processing module."""

from whispa.audio.capture import AudioCapture
from whispa.audio.buffer import AudioBuffer
from whispa.audio.vad import VoiceActivityDetector

__all__ = ["AudioCapture", "AudioBuffer", "VoiceActivityDetector"]
