# Changelog

All notable changes to this project will be documented in this file.

---

## [1.1.0] - 2025-10-15

### Added
- **SoundFont Auto-Discovery** (`swift_f0/streaming/soundfont_utils.py`)
  - Automatic `.sf2`/`.sf3` file detection in common locations
  - `find_soundfonts()` - Search for available SoundFonts
  - `get_default_soundfont()` - Get largest (highest quality) SoundFont
  - `list_available_soundfonts()` - Print available files with sizes
  - `resolve_soundfont_path()` - Support `"auto"` keyword for discovery

- **Organized Documentation Structure**
  - Created `docs/archive/` for outdated documents
  - New `docs/README.md` with clear navigation
  - Moved 6 superseded documents to archive

- **SoundFonts Directory** (`soundfonts/`)
  - Dedicated directory for `.sf2`/`.sf3` files
  - `soundfonts/README.md` with download instructions
  - Quality comparison table
  - Auto-excluded from git (`.gitignore`)

- **Test Suite Reorganization**
  - `tests/unit/` - Fast unit tests
  - `tests/integration/` - Multi-component tests
  - `tests/examples/` - Example demonstrations
  - `tests/README.md` - Test documentation
  - New tests:
    - `test_soundfont_discovery.py` - SoundFont utilities
    - `test_realtime_pipeline.py` - Full pipeline integration

### Changed
- **SOLID Refactoring** (Dependency Inversion Principle)
  - Extracted `swift_f0/music_theory.py` from `music_enhanced.py`
  - Eliminated circular dependency between offline and streaming modules
  - Both modules now depend on shared abstraction
  - Reduced code duplication by ~180 lines

- **Public API Improvement** (Interface Segregation Principle)
  - Renamed `SwiftF0._extract_pitch_and_confidence()` → `extract_pitch_and_confidence()`
  - Streaming modules now use public API instead of private methods
  - Updated all references in core and examples

- **Updated Imports** (Dependency Inversion)
  - `streaming/key_detection.py` - Now imports from `music_theory`
  - `streaming/autotune.py` - Now imports from `music_theory`
  - `streaming/timbre.py` - Now imports from `music_theory`
  - `music_enhanced.py` - Re-exports for backward compatibility

### Fixed
- Thread safety documentation in `RealtimeAudioSink`
- Test assertions for integration tests
- Import paths for better modularity

### Documentation
- Completely rewrote `README.md` for technical team
- Added `REFACTORING_SUMMARY.md` - Detailed SOLID refactoring report
- Updated `docs/README.md` - Clear document organization
- Created `tests/README.md` - Test suite guide
- Created `soundfonts/README.md` - SoundFont management

---

## [1.0.0] - 2025-10-14

### Added
- Real-time audio synthesis with FluidSynth backend
- `swift_f0/streaming/synthesis.py` module
- Real-time auto-tune quantization
- Online key detection
- Unit tests for key tracker and auto-tune

### Changed
- Updated realtime demo to support audio synthesis mode

---

## [0.2.0] - 2025-10-13

### Added
- Streaming framework (`swift_f0/streaming/`)
- Real-time note segmentation
- MIDI file and virtual port output
- Streaming examples and tests

### Changed
- Modularized music utilities
- Added GM instrument mapping

---

## [0.1.0] - 2025-10-06

### Added
- Initial release with core pitch detection
- Offline batch processing
- Basic test suite

---

**Maintainer**: Adrian
