# SwiftF0 Project Overview

## Executive Summary

SwiftF0 is a production-ready Python library for real-time pitch detection and music transformation. Built on a lightweight CNN model (389KB), it provides accurate fundamental frequency detection with advanced features including timbre transformation, auto-tuning, and MIDI export capabilities.

## Project Architecture

### Core Components

```
SwiftF0 Architecture
├── Pitch Detection Layer
│   ├── ONNX CNN Model (389KB)
│   ├── STFT Processing (1024 samples, 256 hop)
│   └── Confidence Scoring
├── Music Processing Layer
│   ├── Note Segmentation
│   ├── Key Detection (Krumhansl-Schmuckler)
│   └── Auto-Tuning Engine
├── Output Layer
│   ├── MIDI Export (128 GM Instruments)
│   ├── Visualization (Piano Roll)
│   └── CSV Data Export
└── Enhancement Features
    ├── Timbre Transformation
    ├── Transposition
    └── Kazoo Optimization
```

### Technical Specifications

| Component | Specification |
|-----------|--------------|
| **Frequency Range** | 46.875 - 2093.75 Hz |
| **Sample Rate** | 16 kHz (internal) |
| **Frame Length** | 1024 samples |
| **Hop Size** | 256 samples |
| **Latency** | ~150ms (5s audio) |
| **Accuracy** | ±10 cents |
| **Model Size** | 389 KB |
| **Memory Usage** | ~350 MB |

## Software Design Principles

The project follows Object-Oriented Programming (OOP) principles and SOLID design patterns:

### Current Implementation

1. **Single Responsibility** - Each module handles specific concerns:
   - `core.py` - Pitch detection only
   - `music.py` - Note segmentation
   - `music_enhanced.py` - Advanced features

2. **Data Classes** - Clean data structures:
   - `PitchResult` - Encapsulates detection results
   - `NoteSegment` - Represents musical notes

3. **Dependency Management** - Optional features:
   - Core: onnxruntime, numpy (required)
   - Audio: librosa (optional)
   - MIDI: mido (optional)
   - Visualization: matplotlib (optional)

### Planned Improvements

Following the seven principles of software engineering:

1. **Single Responsibility Principle (SRP)**
   - Split `music_enhanced.py` into focused modules
   - Separate concerns for each feature

2. **Open/Closed Principle (OCP)**
   - Plugin architecture for instruments
   - Extensible without modification

3. **Liskov Substitution Principle (LSP)**
   - Proper inheritance hierarchies
   - Consistent interfaces

4. **Interface Segregation Principle (ISP)**
   - Fine-grained interfaces
   - Users only depend on what they need

5. **Dependency Inversion Principle (DIP)**
   - Abstract interfaces over concrete implementations
   - Dependency injection

6. **Law of Demeter (LoD)**
   - Minimize coupling between modules
   - Clear module boundaries

7. **Don't Repeat Yourself (DRY)**
   - Eliminate code duplication
   - Reusable components

## Project Organization

### Directory Structure

```
swift-f0/
├── swift_f0/              # Core library (1,637 lines)
│   ├── core.py           # Pitch detection (435 lines)
│   ├── music.py          # Note segmentation (581 lines)
│   ├── music_enhanced.py # Advanced features (589 lines)
│   └── model.onnx        # CNN model (389 KB)
├── demos/                 # Example scripts
│   ├── basic/            # Simple examples
│   ├── advanced/         # Complex demonstrations
│   └── tutorials/        # Learning materials
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # End-to-end tests
│   └── fixtures/        # Test data
├── docs/                 # Documentation
│   ├── api/             # API reference
│   ├── guides/          # User guides
│   ├── technical/       # Architecture docs
│   └── research/        # Research papers
└── resources/           # Assets
    └── soundfonts/      # GM soundfont (30.8 MB)
```

### Development Workflow

1. **Version Control**: Git with semantic versioning
2. **Testing**: pytest with >80% coverage target
3. **Documentation**: Comprehensive markdown docs
4. **CI/CD**: Automated testing and deployment
5. **Package Management**: pip/pyproject.toml

## Use Cases

### 1. Music Production
- Convert melodies to MIDI
- Change instrument timbres
- Auto-tune vocals
- Transpose songs

### 2. Music Education
- Pitch accuracy feedback
- Note transcription
- Ear training tools
- Performance analysis

### 3. Research Applications
- Music information retrieval
- Computational musicology
- Audio analysis
- Signal processing

### 4. Hardware Integration
- AI Kazoo device
- Embedded systems (ESP32/Raspberry Pi)
- Real-time processing
- Edge deployment

## Performance Benchmarks

### Processing Speed
- **5-second audio**: ~150ms
- **1-minute audio**: ~1.8 seconds
- **Real-time factor**: ~0.03x

### Accuracy Metrics
- **Pitch accuracy**: ±10 cents
- **Note detection**: >95% for clean audio
- **Key detection**: 85% accuracy (24 keys)

### Resource Usage
- **RAM**: 350 MB typical
- **CPU**: Single-threaded
- **Model**: 389 KB ONNX

## Roadmap

### Phase 1-3 ✅ (Completed)
- Core pitch detection
- Note segmentation
- MIDI export
- 128 GM instruments
- Auto-tuning
- Batch processing

### Phase 4 🔄 (In Progress)
- Real-time streaming
- Buffer management
- Latency optimization

### Phase 5-6 📋 (Planned)
- Hardware prototype
- Commercial product
- Cloud API
- Mobile SDK

## Getting Started

### Installation
```bash
pip install swift-f0[full]
```

### Basic Usage
```python
from swift_f0 import SwiftF0, segment_notes, export_to_midi

# Detect pitch
detector = SwiftF0()
result = detector.detect_from_file("audio.wav")

# Convert to notes
notes = segment_notes(result)

# Export MIDI
export_to_midi(notes, "output.mid")
```

### Advanced Features
```python
from swift_f0.music_enhanced import export_to_midi_enhanced

# With timbre and auto-tune
export_to_midi_enhanced(
    notes,
    "output.mid",
    instrument="trumpet",
    auto_tune=True,
    transpose=5
)
```

## License

MIT License - Free for personal and commercial use

## Contributors

- Core Development Team
- Open Source Contributors
- Research Partners

---

*For detailed technical information, see the [Architecture Document](technical/architecture.md)*