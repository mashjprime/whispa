# Whispa - Local Whisper Voice Dictation

A Windows voice dictation application using local Whisper models. Similar to Wispr Flow but fully offline with push-to-talk activation, system-wide text injection, and intelligent text processing.

## Features

- **Local Speech Recognition**: Uses faster-whisper for fast, accurate transcription on your GPU
- **Push-to-Talk**: Toggle mode with customizable hotkey (default: Ctrl+Shift+Space)
- **System-Wide**: Works in any Windows application via clipboard injection
- **Voice Activity Detection**: Silero-VAD filters silence to prevent hallucinations
- **Text Processing**:
  - Automatic filler word removal (um, uh, like, etc.)
  - Voice commands (period, comma, new line, etc.)
  - Auto-capitalization
- **Personal Dictionary**: Custom word corrections (teh → the, api → API)
- **Snippets**: Voice-triggered text expansion (my email → user@example.com)
- **Recording Overlay**: Visual indicator when recording with audio level display

## Requirements

- Windows 10/11
- Python 3.10+
- NVIDIA GPU with 6GB+ VRAM (recommended for large-v3-turbo model)
- CUDA 11.x or 12.x

## Installation

1. Clone or download the repository:
```bash
git clone https://github.com/yourusername/whispa.git
cd whispa
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install PyTorch with CUDA support:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

4. Install Whispa:
```bash
pip install -e .
```

## Usage

### Starting Whispa

```bash
# Run as module
python -m whispa

# Or use the installed command
whispa
```

Whispa runs in the system tray. Look for the circular icon.

### Basic Usage

1. Press **Ctrl+Shift+Space** to start recording
2. Speak your text
3. Press **Ctrl+Shift+Space** again to stop and transcribe
4. Text is automatically typed at your cursor position

Press **Escape** to cancel recording without transcription.

### Voice Commands

Say these words to insert punctuation and control formatting:

| Command | Result |
|---------|--------|
| "period" | . |
| "comma" | , |
| "question mark" | ? |
| "exclamation mark" | ! |
| "new line" | Line break |
| "new paragraph" | Double line break |
| "open quote" / "close quote" | " |
| "colon" | : |
| "semicolon" | ; |

### Configuration

Access settings by double-clicking the tray icon or right-click → Settings.

**Audio Settings:**
- Select input device
- Adjust VAD threshold (speech detection sensitivity)
- Configure pre-roll buffer

**Transcription Settings:**
- Choose Whisper model size
- Select compute device (CUDA/CPU)
- Set language (auto-detect or specific)

**Hotkeys:**
- Customize activation hotkey
- Toggle vs hold mode

**Text Processing:**
- Enable/disable filler word removal
- Customize filler word list
- Toggle voice commands

### Personal Dictionary

Add custom word corrections:
1. Right-click tray → Dictionary
2. Add entries like: `teh` → `the`, `api` → `API`

### Snippets

Create voice-triggered text expansions:
1. Right-click tray → Snippets
2. Add entries like: `my email` → `user@example.com`

## Whisper Models

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | ~1GB | Fastest | Low |
| base | ~1GB | Fast | Low |
| small | ~2GB | Medium | Good |
| medium | ~5GB | Slow | Better |
| large-v3-turbo | ~6GB | Medium | Best |
| large-v3 | ~10GB | Slowest | Best |

The default **large-v3-turbo** model provides the best balance of speed and accuracy for GPUs with 6GB+ VRAM.

## File Locations

Configuration and data are stored in:
```
%APPDATA%\Whispa\
├── config.json      # Settings
├── whispa.db        # Snippets and dictionary
├── logs\            # Log files
└── models\          # Downloaded Whisper models
```

## Troubleshooting

### No audio detected
- Check microphone permissions in Windows Settings
- Verify correct input device in Whispa settings
- Increase VAD threshold if speech not detected

### Slow transcription
- Ensure CUDA is being used (check logs)
- Try a smaller model
- Update GPU drivers

### Text not appearing
- Some apps block clipboard paste - try keyboard injection mode
- Run Whispa as administrator for protected apps

### Model download fails
- Check internet connection
- Try manual download from Hugging Face
- Check disk space

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Project Structure

```
whispa/
├── src/whispa/
│   ├── audio/          # Audio capture and VAD
│   ├── config/         # Settings management
│   ├── core/           # App controller and state machine
│   ├── data/           # SQLite repositories
│   ├── hotkeys/        # Global hotkey handling
│   ├── output/         # Text injection
│   ├── text_processing/ # Post-processing pipeline
│   ├── transcription/  # Whisper integration
│   ├── ui/             # PyQt6 windows
│   └── utils/          # Helpers
└── tests/              # Unit tests
```

## License

MIT License

## Acknowledgments

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Fast Whisper implementation
- [Silero VAD](https://github.com/snakers4/silero-vad) - Voice activity detection
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - UI framework
- [pynput](https://github.com/moses-palmer/pynput) - Global hotkeys
