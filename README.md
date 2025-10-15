# SwiftF0 Real-Time Vocal-to-Audio System

**Real-time humming → timbre transformation → speaker output with optional auto-tune**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

---

## Project Status

**Author**: Adrian  
**Phase**: Mac desktop prototype (production-ready)  
**Core Pipeline**: Mic → Pitch Detection → MIDI Events → FluidSynth → Audio Output  
**Latency**: ~22ms (256 samples @ 44.1kHz synthesis + 16ms @ 16kHz detection)

---

## Quick Start

### 1. Install Dependencies

```bash
# System dependencies (macOS)
brew install fluid-synth

# Python packages
pip install -e .
pip install pyfluidsynth sounddevice
```

### 2. Download SoundFont (Automatic)

```bash
# Download GeneralUser GS (30MB, recommended)
cd soundfonts/
curl -L http://www.schristiancollins.com/generaluser.php -o GeneralUser-GS.zip
unzip GeneralUser-GS.zip
mv GeneralUser\ GS\ 1.471/GeneralUser\ GS.sf2 GeneralUser-GS.sf2
rm -rf GeneralUser-GS.zip "GeneralUser GS 1.471"
cd ..
```

The system will automatically find `.sf2` files in `soundfonts/` directory.

### 3. Run Real-Time Demo

```bash
# Basic usage (auto-detects SoundFont, oboe timbre)
python examples/streaming/realtime_demo.py --audio

# Specific SoundFont and instrument
python examples/streaming/realtime_demo.py \
    --audio \
    --sf2 soundfonts/GeneralUser-GS.sf2 \
    --instrument 68

# With auto-tune (trumpet timbre)
python examples/streaming/realtime_demo.py \
    --audio \
    --instrument 56 \
    --autotune \
    --autotune-strength 0.8
```

**Stop**: Press `Ctrl+C`

---

## Architecture Overview

```
Microphone Input (16kHz mono)
    ↓
┌─────────────────────────────────────────────────┐
│ SwiftF0Streamer (sliding window inference)      │
│ - 1024-sample window, 256-sample hop            │
│ - ONNX model @ 16kHz                             │
│ - Output: PitchFrame (Hz, confidence, timestamp) │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ RealtimeNoteSegmenter (state machine)            │
│ - States: IDLE → TENTATIVE_START → ACTIVE        │
│ - Grace period for note end detection           │
│ - Output: NoteEvent (note_on/off, MIDI note)    │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ OnlineKeyTracker (optional, K-S algorithm)       │
│ - 10s sliding window pitch class histogram      │
│ - 24-key correlation (12 major + 12 minor)      │
│ - Output: (key_name, mode, correlation)         │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ AutoTuneQuantizer (optional)                     │
│ - Quantize note_on events to detected key scale │
│ - Adjustable strength [0.0, 1.0]                │
│ - Fallback to C major if confidence < 0.3       │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ RealtimeAudioSink (FluidSynth + sounddevice)     │
│ - Thread-safe MIDI → audio synthesis            │
│ - 44.1kHz stereo output, 256-sample buffer      │
│ - Supports 128 GM instruments                    │
└─────────────────────────────────────────────────┘
    ↓
Speaker Output (real-time)
```

---

## Project Structure

```
swift-f0/
├── swift_f0/                      # Core library
│   ├── core.py                    # Pitch detection (ONNX)
│   ├── music_theory.py            # Music theory constants (DRY)
│   ├── music_enhanced.py          # Offline MIDI export
│   └── streaming/                 # Real-time framework
│       ├── audio.py               # Audio sources (mic/file)
│       ├── inference.py           # Sliding window inference
│       ├── notes.py               # Note segmentation
│       ├── key_detection.py       # Online key tracking
│       ├── autotune.py            # Pitch quantization
│       ├── synthesis.py           # FluidSynth backend
│       ├── soundfont_utils.py     # SoundFont discovery
│       └── pipeline.py            # Orchestration
│
├── soundfonts/                    # SoundFont files (.sf2/.sf3)
│   └── README.md                  # Download instructions
│
├── examples/streaming/            # Demo scripts
│   ├── realtime_demo.py           # Mic → Audio (main demo)
│   └── run_pipeline.py            # WAV → MIDI (offline)
│
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── examples/                  # Example-based tests
│
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md            # System architecture
│   ├── streaming/                 # Streaming pipeline docs
│   └── archive/                   # Archived docs
│
└── README.md                      # This file
```

---

## Module Reference

### Core Library

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `swift_f0/core.py` | Pitch detection (ONNX inference) | `SwiftF0` |
| `swift_f0/music_theory.py` | Music theory constants (DRY principle) | `GM_INSTRUMENTS`, `KEY_NAMES`, profiles |
| `swift_f0/music_enhanced.py` | Offline MIDI export with timbre/auto-tune | `export_to_midi_enhanced()`, `detect_key()` |

### Streaming Framework

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `streaming/audio.py` | Audio sources (mic/file) | `MicSource`, `WavFileSource` |
| `streaming/inference.py` | Sliding window pitch detection | `SwiftF0Streamer` |
| `streaming/notes.py` | Real-time note segmentation | `RealtimeNoteSegmenter` |
| `streaming/key_detection.py` | Online key tracking (K-S algorithm) | `OnlineKeyTracker` |
| `streaming/autotune.py` | Pitch quantization to scale | `AutoTuneQuantizer` |
| `streaming/synthesis.py` | FluidSynth audio synthesis | `FluidSynthBackend`, `RealtimeAudioSink` |
| `streaming/soundfont_utils.py` | SoundFont discovery | `find_soundfonts()`, `get_default_soundfont()` |
| `streaming/midi.py` | MIDI output (file/virtual port) | `FileMIDISink`, `RealtimeMIDISink` |
| `streaming/pipeline.py` | Orchestration | `StreamingPipeline` |

---

## Configuration Options

### Audio Synthesis (`--audio` mode)

```bash
--sf2 PATH              # SoundFont file path (auto-detected if omitted)
--instrument INT/NAME   # GM program 0-127 or name (default: 68=oboe)
--sample-rate INT       # Synthesis rate (default: 44100Hz)
```

### Auto-Tune

```bash
--autotune              # Enable pitch correction
--autotune-strength FLOAT  # Correction strength 0.0-1.0 (default: 1.0)
```

### Instrument Names (examples)

```bash
# Wind (recommended for vocalization)
--instrument oboe           # 68 - nasal timbre
--instrument trumpet        # 56 - bright brass
--instrument clarinet       # 71 - warm woody
--instrument flute          # 73 - airy pure

# Strings
--instrument violin         # 40
--instrument cello          # 42

# Piano
--instrument acoustic_grand_piano  # 0
--instrument electric_piano_1      # 4

# Synth
--instrument lead_1_square  # 80
--instrument pad_2_warm     # 89
```

Full list: See `GM_INSTRUMENTS` in [swift_f0/music_theory.py](swift_f0/music_theory.py)

---

## SoundFont Management

### Auto-Discovery

The system automatically searches for `.sf2`/`.sf3` files in:
1. `./soundfonts/` (project directory)
2. `~/Audio/SoundFonts/` (user directory)
3. `/usr/share/soundfonts/` (system, Linux)
4. `/usr/local/share/soundfonts/` (Homebrew, macOS)

### List Available SoundFonts

```python
from swift_f0.streaming import list_available_soundfonts

list_available_soundfonts()
# Output:
#   Found 2 SoundFont(s):
#     1. GeneralUser-GS.sf2 (30.8 MB) - soundfonts/GeneralUser-GS.sf2
#     2. FluidR3_GM.sf2 (142.0 MB) - ~/Audio/SoundFonts/FluidR3_GM.sf2
```

### Download Options

See [soundfonts/README.md](soundfonts/README.md) for download links and quality comparison.

---

## Testing

```bash
# All tests
pytest tests/

# By category
pytest tests/unit/           # Fast unit tests (< 1s)
pytest tests/integration/    # Integration tests (~5s)
pytest tests/examples/       # Example demonstrations

# Specific tests
pytest tests/unit/test_soundfont_discovery.py -v
pytest tests/integration/test_realtime_pipeline.py -v

# With coverage
pytest tests/ --cov=swift_f0 --cov-report=html
```

See [tests/README.md](tests/README.md) for detailed test documentation.

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Detection Latency | ~16ms | 1024 samples @ 16kHz |
| Synthesis Latency | ~5.8ms | 256 samples @ 44.1kHz |
| Total Latency | ~22ms | Perceptually instant |
| CPU Usage | ~15% | M1/M2 Mac (single core) |
| Memory | ~350MB | Model + buffers |
| Pitch Accuracy | ±10 cents | Sub-semitone precision |

---

## Recent Changes (v1.1.0)

### SOLID Refactoring (2025-10-15)

**Problem**: Violation of Dependency Inversion Principle
- Streaming modules depended on `music_enhanced.py` (offline module) for constants
- Caused circular dependency risk and poor separation of concerns

**Solution**: Extracted `swift_f0/music_theory.py`
- Single source of truth for `GM_INSTRUMENTS`, `KEY_NAMES`, K-S profiles
- Both offline and streaming modules now depend on this abstraction
- Public API: `extract_pitch_and_confidence()` (was private `_extract_...`)

**Benefits**:
- ✅ DIP compliant (high-level modules depend on abstractions)
- ✅ DRY (no duplicate music theory data)
- ✅ ISP compliant (streaming uses public API, not private methods)

### SoundFont Auto-Discovery

- New `soundfont_utils.py` module for automatic `.sf2`/`.sf3` detection
- Supports multiple SoundFonts with quality comparison
- Auto-detection via `--sf2 auto` or omitting `--sf2` flag

### Test Suite Reorganization

- Structured into `unit/`, `integration/`, `examples/`
- New tests: SoundFont discovery, full pipeline integration
- Coverage tracking ready

See [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for detailed changes.

---

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[streaming/SwiftF0_Streaming_Architecture.md](docs/streaming/SwiftF0_Streaming_Architecture.md)** - Streaming pipeline design
- **[tests/README.md](tests/README.md)** - Test suite documentation
- **[soundfonts/README.md](soundfonts/README.md)** - SoundFont management

---

## API Usage (Python)

### Real-Time Pipeline

```python
from swift_f0.core import SwiftF0
from swift_f0.streaming import (
    MicSource,
    SwiftF0Streamer,
    RealtimeNoteSegmenter,
    AudioSynthConfig,
    RealtimeAudioSink,
    get_default_soundfont,
)

# Setup
detector = SwiftF0()
streamer = SwiftF0Streamer(detector)
segmenter = RealtimeNoteSegmenter()

# Auto-detect SoundFont
soundfont_path = get_default_soundfont()

config = AudioSynthConfig(
    sample_rate=44100.0,
    soundfont_path=str(soundfont_path),
    initial_program=68,  # oboe
)
sink = RealtimeAudioSink(config)

# Process loop
source = MicSource(sample_rate=16000, block_size=256)
for chunk in source.frames():
    pitch_frame = streamer.process_chunk(chunk)
    note_events = list(segmenter.process(pitch_frame))
    if note_events:
        sink.send(note_events)

sink.finalize()
```

---

## Troubleshooting

**Issue**: `ImportError: fluidsynth not found`
```bash
brew install fluid-synth
pip install --force-reinstall pyfluidsynth
```

**Issue**: No SoundFonts found
```bash
# Download to soundfonts/ directory
cd soundfonts/
# See soundfonts/README.md for download links
```

**Issue**: No audio output
- Check system volume and audio device
- Verify SoundFont path: `python -c "from swift_f0.streaming import list_available_soundfonts; list_available_soundfonts()"`
- Try different `--instrument` values

**Issue**: High latency / crackling
- Increase buffer size: `--block-size 512`
- Close background audio apps
- Use `--sample-rate 44100`

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Contact

**Adrian** - Technical Lead  
For questions or issues, open a GitHub issue or contact via team Slack.

---

**Version**: 1.1.0 (SOLID refactoring + SoundFont auto-discovery)  
**Last Updated**: 2025-10-15  
**Status**: Production-ready for Mac desktop
