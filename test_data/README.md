# Test Data Directory Structure

This directory contains all test-related audio files and outputs, organized following software engineering best practices.

## Directory Layout

```
test_data/
├── inputs/                 # Test input audio files
│   └── test_audio.wav     # Synthetic test melody (version controlled)
├── outputs/               # Generated outputs (git ignored)
│   ├── midi/             # MIDI files from various transformations
│   ├── audio/            # Audio outputs (if any)
│   └── plots/            # Visualization outputs (if any)
└── batch_outputs/         # Batch processing results (git ignored)
```

## Usage

Run the test script to generate all outputs:

```bash
python tests/test_timbre_demo.py
```

This will:
1. Create a synthetic test audio in `inputs/`
2. Run pitch detection and note segmentation
3. Export MIDI files with different timbres to `outputs/midi/`
4. Generate batch processing results in `batch_outputs/`

## Version Control

- `inputs/` - Input test files are committed to git
- `outputs/` and `batch_outputs/` - Generated files are git-ignored
- `.gitkeep` files preserve directory structure

## Maintenance

- Keep input test files minimal and representative
- Clean output directories periodically with: `rm -rf outputs/*/*.mid batch_outputs/*.mid`
- Add new test inputs with descriptive names (e.g., `inputs/melody_major_scale.wav`)
