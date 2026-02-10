# Whispa Development Progress

## Project Overview
Local Whisper voice dictation application for Windows with push-to-talk activation.

## Current Status: Working MVP
The application runs and is functional. Basic dictation works.

---

## Completed Features

### Phase 1: Foundation ✅
- Project structure with `src/whispa/` layout
- `pyproject.toml` and `requirements.txt`
- Logging system with rotation
- App paths (`%APPDATA%/Whispa`)
- Single-instance lock using Windows mutex

### Phase 2: Core Transcription ✅
- **faster-whisper** integration
- Model manager with download support
- GPU detection (falls back to CPU if no CUDA)
- Post-processor for text cleanup
- **Silero-VAD** for voice activity detection
- Ring buffer with pre-roll support

### Phase 3: System Integration ✅
- **pynput** global hotkey manager
- Support for modifier-only hotkeys (e.g., `ctrl+win`)
- Hold mode (hold to record, release to transcribe)
- Toggle mode support
- Clipboard text injection with `pyperclip`
- Keyboard fallback with `PyDirectInput`

### Phase 4: User Interface ✅
- **PyQt6** system tray icon with status colors
  - Gray = Idle
  - Red = Recording
  - Orange = Processing
- Recording overlay near cursor with audio level visualization
- Settings window with tabs for all configuration
- Snippets management window
- Dictionary management window

### Phase 5: Data & Text Processing ✅
- SQLite database for snippets and dictionary
- Voice commands (period, comma, new line, etc.)
- Filler word removal (um, uh, like, etc.)
- Auto-capitalization
- Snippet expansion
- Dictionary corrections

### Phase 6: Core Controller ✅
- State machine (IDLE → LISTENING → PROCESSING → IDLE)
- Event system with Qt signals
- Orchestration of all components

---

## Bug Fixes Applied

1. **Deadlock in state machine** - Changed `threading.Lock()` to `threading.RLock()` in `state_machine.py` because `can_transition_to()` was called inside `transition_to()`, both using the same lock.

2. **Qt signal emission before event loop** - Modified `_on_state_changed()` in `controller.py` to check if `QApplication.instance()` exists before emitting signals.

3. **Hotkey manager for hold mode** - Rewrote `hotkeys/manager.py` to support:
   - Separate `on_press` and `on_release` callbacks
   - Modifier-only hotkeys (like `ctrl+win`)
   - Proper tracking of active hotkeys

---

## Current Configuration

```json
{
  "hotkeys": {
    "mode": "hold",
    "activate": "ctrl+win",
    "cancel": "escape"
  },
  "transcription": {
    "model_size": "large-v3-turbo",
    "device": "cuda",
    "compute_type": "float16"
  }
}
```

**Note:** On current test system, CUDA was not available, so it falls back to CPU.

---

## Known Issues / TODO

1. **First transcription downloads model** - The first time you record, it downloads ~1.6GB model which can take several minutes. App appears stuck during this.

2. **Model download progress** - No UI feedback during model download (shows as "processing").

3. **CUDA detection** - On test system, CUDA wasn't detected despite having GPU. May need to install CUDA-enabled PyTorch:
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```

4. **Settings persistence** - Config file gets recreated with defaults each run (may need to check why it's not persisting).

---

## File Structure

```
whispa/
├── src/whispa/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py                 # Entry point with single-instance lock
│   ├── config/
│   │   ├── settings.py         # Settings dataclasses
│   │   ├── manager.py          # JSON config load/save
│   │   └── paths.py            # App directory paths
│   ├── audio/
│   │   ├── capture.py          # sounddevice wrapper
│   │   ├── buffer.py           # Ring buffer with pre-roll
│   │   └── vad.py              # Silero-VAD wrapper
│   ├── transcription/
│   │   ├── engine.py           # faster-whisper wrapper
│   │   ├── model_manager.py    # Model download/cache
│   │   └── post_processor.py   # Text cleanup
│   ├── text_processing/
│   │   ├── commands.py         # Voice commands
│   │   ├── filler_words.py     # Filler removal
│   │   ├── formatting.py       # Auto-capitalization
│   │   ├── snippets.py         # Snippet expansion
│   │   └── dictionary.py       # Word corrections
│   ├── output/
│   │   ├── injector.py         # Strategy selection
│   │   ├── clipboard.py        # Clipboard + Ctrl+V
│   │   └── keyboard.py         # Direct typing
│   ├── hotkeys/
│   │   ├── manager.py          # Global hotkey listener
│   │   └── parser.py           # Hotkey string parsing
│   ├── ui/
│   │   ├── app.py              # Main application
│   │   ├── tray.py             # System tray icon
│   │   ├── overlay.py          # Recording indicator
│   │   ├── settings_window.py  # Settings dialog
│   │   ├── snippets_window.py  # Snippets manager
│   │   ├── dictionary_window.py # Dictionary manager
│   │   └── model_download.py   # Download progress
│   ├── data/
│   │   ├── database.py         # SQLite connection
│   │   ├── snippets_repo.py    # Snippet CRUD
│   │   └── dictionary_repo.py  # Dictionary CRUD
│   ├── core/
│   │   ├── controller.py       # Main orchestrator
│   │   ├── state_machine.py    # App state management
│   │   └── events.py           # Qt signals
│   └── utils/
│       ├── logging.py          # Log setup
│       ├── single_instance.py  # Mutex lock
│       └── threading.py        # Thread helpers
├── tests/
│   ├── test_config.py
│   ├── test_text_processing.py
│   ├── test_audio.py
│   ├── test_state_machine.py
│   └── test_hotkeys.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## How to Run

```bash
cd C:\AI\whispa
pip install -e .
python -m whispa
```

---

## How to Use

1. **Hold `Ctrl+Win`** to start recording
2. **Speak** into microphone
3. **Release `Ctrl+Win`** to transcribe and inject text
4. **Press `Escape`** to cancel recording

---

## Next Steps (Suggested)

1. Add model download progress UI
2. Fix CUDA detection / provide better error messages
3. Add "test microphone" button in settings
4. Add notification when model is ready
5. Consider adding a "warm up" on startup to pre-load model
