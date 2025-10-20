# SwiftF0 Project Structure

This document describes the clean, organized structure of the SwiftF0 project.

## Directory Layout

```
swift-f0/
├── swift_f0/              # Core library (source code)
│   ├── __init__.py        # Public API exports
│   ├── core.py            # SwiftF0 pitch detection engine
│   ├── music.py           # Note segmentation and basic MIDI export
│   ├── music_enhanced.py  # Timbre transformation, auto-tune, kazoo optimization
│   └── model.onnx         # Pre-trained CNN model (389KB)
│
├── examples/              # Example scripts and demos
│   ├── demo_timbre_transform.py  # CLI tool for timbre transformation
│   └── streaming/         # Streaming processing examples (planned)
│
├── tests/                 # Test suite
│   ├── test_timbre_demo.py       # Integration tests
│   ├── unit/              # Unit tests (planned)
│   └── integration/       # Integration tests (planned)
│
├── test_data/             # Test data directory
│   ├── inputs/            # Input test audio files
│   └── outputs/           # Generated test outputs (git-ignored)
│
├── soundfonts/            # MIDI soundfont files
│   ├── GeneralUser-GS.sf2  # GM soundfont (30.8MB)
│   └── README.md          # Soundfont documentation
│
├── docs/                  # Documentation
│   ├── README.md                      # Documentation index
│   ├── ARCHITECTURE.md                # System architecture
│   ├── CHANGELOG.md                   # Version history
│   ├── MIGRATION_GUIDE.md             # Migration guide
│   ├── AI_KAZOO_ROADMAP.md            # Roadmap for AI Kazoo project
│   ├── PROJECT_SUMMARY.md             # Project summary
│   ├── HARDWARE_COMPARISON.md         # Hardware platform comparison
│   ├── EDGE_DEPLOYMENT_ANALYSIS.md    # Edge deployment analysis
│   └── v1.0STREAMING_RESEARCH_BRIEF.md # Streaming research
│
├── README.md              # Main project README
├── pyproject.toml         # Project metadata and dependencies
├── requirements.txt       # Core dependencies
├── MANIFEST.in            # Package manifest
├── LICENSE                # MIT License
└── .gitignore             # Git ignore rules

```

## Key Principles

### Clean Architecture
- **Separation of Concerns**: Core detection, music processing, and enhanced features are in separate modules
- **Single Responsibility**: Each module has a clear, focused purpose
- **Low Coupling**: Modules communicate through well-defined interfaces (dataclasses)

### File Organization
- **Source code**: All in `swift_f0/`
- **Documentation**: All in `docs/`
- **Examples**: All in `examples/`
- **Tests**: All in `tests/`
- **Test data**: Structured in `test_data/` with separate input/output directories

### Git Hygiene
- **Ignored**: Build artifacts, caches, test outputs, egg-info
- **Tracked**: Source code, documentation, test inputs, configuration files
- **Large files**: Soundfonts documented but can be git-ignored if needed

## Development Workflow

### Adding New Features
1. **Core algorithms** → `swift_f0/core.py` or new module in `swift_f0/`
2. **Documentation** → Create `.md` file in `docs/`
3. **Examples** → Add demo script in `examples/`
4. **Tests** → Add unit tests in `tests/unit/` and integration tests in `tests/integration/`

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_timbre_demo.py

# Test with coverage
python -m pytest --cov=swift_f0 tests/
```

### Documentation
- **Architecture changes** → Update `docs/ARCHITECTURE.md`
- **API changes** → Update docstrings and `docs/README.md`
- **Version changes** → Update `docs/CHANGELOG.md`

## Module Dependencies

```
examples/
    ↓ imports
swift_f0/
    ├── music_enhanced.py (imports music, core)
    ├── music.py (imports core)
    └── core.py (no internal dependencies)
```

**Dependency Direction**: Always from high-level (examples) to low-level (core)

## Next Steps for Development

### Phase 1: Testing Infrastructure
- [ ] Set up pytest configuration
- [ ] Add unit tests for core functions
- [ ] Add integration tests for full pipeline
- [ ] Set up CI/CD (GitHub Actions)

### Phase 2: Code Quality
- [ ] Implement dependency injection in core classes
- [ ] Add abstract interfaces for extensibility
- [ ] Refactor configuration management
- [ ] Add type hints throughout

### Phase 3: Feature Development
- [ ] Implement streaming processing (Phase 4 of roadmap)
- [ ] Add GPU acceleration support
- [ ] Develop real-time processing capabilities
- [ ] Hardware prototype development

### Phase 4: Documentation
- [ ] API reference documentation
- [ ] Tutorial notebooks
- [ ] Performance benchmarking results
- [ ] Deployment guides

---

**Last Updated**: 2025-10-20
**Project Version**: v0.1.2
