"""Settings dataclass for Whispa configuration."""

from dataclasses import dataclass, field
from typing import List, Literal


@dataclass
class HotkeySettings:
    """Hotkey configuration."""

    mode: Literal["toggle", "hold"] = "hold"
    activate: str = "ctrl+win"
    cancel: str = "escape"


@dataclass
class TranscriptionSettings:
    """Transcription engine configuration."""

    model_size: str = "large-v3-turbo"
    device: Literal["cuda", "cpu", "auto"] = "auto"
    compute_type: str = "float16"
    language: str = "auto"
    beam_size: int = 5
    initial_prompt: str = ""


@dataclass
class AudioSettings:
    """Audio capture configuration."""

    input_device: str = "default"
    sample_rate: int = 16000
    vad_threshold: float = 0.5
    vad_min_speech_ms: int = 250
    vad_min_silence_ms: int = 300
    pre_roll_ms: int = 300


@dataclass
class TextProcessingSettings:
    """Text processing configuration."""

    remove_filler_words: bool = True
    filler_words: List[str] = field(
        default_factory=lambda: ["um", "uh", "er", "ah", "like", "you know", "basically", "actually"]
    )
    auto_capitalize: bool = True
    voice_commands_enabled: bool = True


@dataclass
class OutputSettings:
    """Text output configuration."""

    method: Literal["clipboard", "keyboard"] = "clipboard"
    add_trailing_space: bool = True


@dataclass
class UISettings:
    """UI configuration."""

    show_overlay: bool = True
    overlay_opacity: float = 0.9
    start_minimized: bool = False
    start_with_windows: bool = False


@dataclass
class Settings:
    """Application settings."""

    hotkeys: HotkeySettings = field(default_factory=HotkeySettings)
    transcription: TranscriptionSettings = field(default_factory=TranscriptionSettings)
    audio: AudioSettings = field(default_factory=AudioSettings)
    text_processing: TextProcessingSettings = field(default_factory=TextProcessingSettings)
    output: OutputSettings = field(default_factory=OutputSettings)
    ui: UISettings = field(default_factory=UISettings)

    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            "hotkeys": {
                "mode": self.hotkeys.mode,
                "activate": self.hotkeys.activate,
                "cancel": self.hotkeys.cancel,
            },
            "transcription": {
                "model_size": self.transcription.model_size,
                "device": self.transcription.device,
                "compute_type": self.transcription.compute_type,
                "language": self.transcription.language,
                "beam_size": self.transcription.beam_size,
                "initial_prompt": self.transcription.initial_prompt,
            },
            "audio": {
                "input_device": self.audio.input_device,
                "sample_rate": self.audio.sample_rate,
                "vad_threshold": self.audio.vad_threshold,
                "vad_min_speech_ms": self.audio.vad_min_speech_ms,
                "vad_min_silence_ms": self.audio.vad_min_silence_ms,
                "pre_roll_ms": self.audio.pre_roll_ms,
            },
            "text_processing": {
                "remove_filler_words": self.text_processing.remove_filler_words,
                "filler_words": self.text_processing.filler_words,
                "auto_capitalize": self.text_processing.auto_capitalize,
                "voice_commands_enabled": self.text_processing.voice_commands_enabled,
            },
            "output": {
                "method": self.output.method,
                "add_trailing_space": self.output.add_trailing_space,
            },
            "ui": {
                "show_overlay": self.ui.show_overlay,
                "overlay_opacity": self.ui.overlay_opacity,
                "start_minimized": self.ui.start_minimized,
                "start_with_windows": self.ui.start_with_windows,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """Create settings from dictionary."""
        settings = cls()

        if "hotkeys" in data:
            h = data["hotkeys"]
            settings.hotkeys = HotkeySettings(
                mode=h.get("mode", settings.hotkeys.mode),
                activate=h.get("activate", settings.hotkeys.activate),
                cancel=h.get("cancel", settings.hotkeys.cancel),
            )

        if "transcription" in data:
            t = data["transcription"]
            settings.transcription = TranscriptionSettings(
                model_size=t.get("model_size", settings.transcription.model_size),
                device=t.get("device", settings.transcription.device),
                compute_type=t.get("compute_type", settings.transcription.compute_type),
                language=t.get("language", settings.transcription.language),
                beam_size=t.get("beam_size", settings.transcription.beam_size),
                initial_prompt=t.get("initial_prompt", settings.transcription.initial_prompt),
            )

        if "audio" in data:
            a = data["audio"]
            settings.audio = AudioSettings(
                input_device=a.get("input_device", settings.audio.input_device),
                sample_rate=a.get("sample_rate", settings.audio.sample_rate),
                vad_threshold=a.get("vad_threshold", settings.audio.vad_threshold),
                vad_min_speech_ms=a.get("vad_min_speech_ms", settings.audio.vad_min_speech_ms),
                vad_min_silence_ms=a.get("vad_min_silence_ms", settings.audio.vad_min_silence_ms),
                pre_roll_ms=a.get("pre_roll_ms", settings.audio.pre_roll_ms),
            )

        if "text_processing" in data:
            tp = data["text_processing"]
            settings.text_processing = TextProcessingSettings(
                remove_filler_words=tp.get(
                    "remove_filler_words", settings.text_processing.remove_filler_words
                ),
                filler_words=tp.get("filler_words", settings.text_processing.filler_words),
                auto_capitalize=tp.get(
                    "auto_capitalize", settings.text_processing.auto_capitalize
                ),
                voice_commands_enabled=tp.get(
                    "voice_commands_enabled", settings.text_processing.voice_commands_enabled
                ),
            )

        if "output" in data:
            o = data["output"]
            settings.output = OutputSettings(
                method=o.get("method", settings.output.method),
                add_trailing_space=o.get(
                    "add_trailing_space", settings.output.add_trailing_space
                ),
            )

        if "ui" in data:
            u = data["ui"]
            settings.ui = UISettings(
                show_overlay=u.get("show_overlay", settings.ui.show_overlay),
                overlay_opacity=u.get("overlay_opacity", settings.ui.overlay_opacity),
                start_minimized=u.get("start_minimized", settings.ui.start_minimized),
                start_with_windows=u.get("start_with_windows", settings.ui.start_with_windows),
            )

        return settings
