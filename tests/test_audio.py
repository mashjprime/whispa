"""Tests for audio module."""

import pytest
import numpy as np

from whispa.audio.buffer import AudioBuffer


class TestAudioBuffer:
    """Tests for AudioBuffer."""

    def test_init(self):
        """Test buffer initialization."""
        buffer = AudioBuffer(sample_rate=16000, pre_roll_ms=300)

        assert buffer.sample_rate == 16000
        assert buffer.pre_roll_samples == 4800  # 16000 * 0.3
        assert not buffer.is_recording

    def test_pre_roll(self):
        """Test pre-roll buffer."""
        buffer = AudioBuffer(sample_rate=16000, pre_roll_ms=100)

        # Add some audio to pre-roll
        audio = np.ones(1600, dtype=np.float32) * 0.5
        buffer.add_to_pre_roll(audio)

        # Start recording - should include pre-roll
        buffer.start_recording()
        assert buffer.is_recording

        # Add more audio
        audio2 = np.ones(1600, dtype=np.float32) * 0.8
        buffer.add_samples(audio2)

        # Stop and get audio
        result = buffer.stop_recording()

        assert result is not None
        assert len(result) > 1600  # Should include pre-roll

    def test_recording_cycle(self):
        """Test full recording cycle."""
        buffer = AudioBuffer(sample_rate=16000, pre_roll_ms=0)

        # Not recording initially
        assert not buffer.is_recording

        # Start recording
        buffer.start_recording()
        assert buffer.is_recording

        # Add samples
        audio = np.random.randn(3200).astype(np.float32)
        buffer.add_samples(audio)

        # Stop recording
        result = buffer.stop_recording()

        assert not buffer.is_recording
        assert result is not None
        assert len(result) == 3200

    def test_max_duration(self):
        """Test max duration limit."""
        buffer = AudioBuffer(sample_rate=16000, pre_roll_ms=0, max_duration_s=1.0)

        buffer.start_recording()

        # Add audio within limit
        audio = np.ones(8000, dtype=np.float32)
        assert buffer.add_samples(audio) is True

        # Try to exceed limit
        audio2 = np.ones(16000, dtype=np.float32)
        assert buffer.add_samples(audio2) is False

    def test_duration_tracking(self):
        """Test duration tracking."""
        buffer = AudioBuffer(sample_rate=16000, pre_roll_ms=0)

        buffer.start_recording()

        # Add 1 second of audio (16000 samples)
        audio = np.ones(16000, dtype=np.float32)
        buffer.add_samples(audio)

        assert buffer.duration_ms == 1000

    def test_clear(self):
        """Test buffer clearing."""
        buffer = AudioBuffer(sample_rate=16000, pre_roll_ms=100)

        # Add pre-roll
        buffer.add_to_pre_roll(np.ones(1600, dtype=np.float32))

        # Start recording
        buffer.start_recording()
        buffer.add_samples(np.ones(1600, dtype=np.float32))

        # Clear
        buffer.clear()

        assert not buffer.is_recording
        assert buffer.duration_ms == 0

    def test_stop_without_start(self):
        """Test stopping without starting returns None."""
        buffer = AudioBuffer(sample_rate=16000)

        result = buffer.stop_recording()

        assert result is None

    def test_add_samples_when_not_recording(self):
        """Test adding samples when not recording returns False."""
        buffer = AudioBuffer(sample_rate=16000)

        audio = np.ones(1600, dtype=np.float32)
        result = buffer.add_samples(audio)

        assert result is False
