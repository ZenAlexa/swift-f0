# SwiftF0 Demos and Examples

This directory contains demonstration scripts and tutorials for the SwiftF0 library.

## Directory Structure

### 📁 basic/
Simple, focused examples demonstrating core functionality:
- `simple_pitch_detection.py` - Basic pitch detection from audio files
- `note_segmentation_example.py` - Converting pitch to musical notes
- `simple_midi_export.py` - Basic audio to MIDI conversion

### 📁 advanced/
Complex examples showcasing advanced features:
- `timbre_transform_cli.py` - Full-featured CLI for timbre transformation, auto-tuning, and batch processing

### 📁 tutorials/
Step-by-step learning materials:
- `01_getting_started.py` - Introduction to SwiftF0 concepts and basic usage

## Quick Start

### Basic Usage
```bash
# Detect pitch from an audio file
python basic/simple_pitch_detection.py your_audio.wav

# Convert audio to MIDI
python basic/simple_midi_export.py your_audio.wav output.mid

# See detected notes
python basic/note_segmentation_example.py your_audio.wav
```

### Advanced Features
```bash
# Change instrument timbre
python advanced/timbre_transform_cli.py audio.wav -i trumpet

# Auto-tune to detected key
python advanced/timbre_transform_cli.py audio.wav --auto-tune

# Create multiple timbre versions
python advanced/timbre_transform_cli.py audio.wav --batch
```

### Learning Path
1. Start with `tutorials/01_getting_started.py` to understand core concepts
2. Try the basic examples to see practical applications
3. Explore advanced features with the CLI tool

## Requirements

- Python 3.8+
- swift-f0 library installed
- Optional: librosa (for audio I/O), mido (for MIDI export)

## Audio Format Support

- WAV (recommended)
- MP3, FLAC, M4A (requires librosa)
- Any format supported by librosa

## Tips

- For best results, use clean, monophonic audio (single melody line)
- Adjust confidence threshold (0.8-0.95) based on audio quality
- Use `--min-duration` to filter out very short notes
- The `--kazoo` option optimizes for kazoo-like instruments