# SwiftF0 Test Suite

This directory contains all tests for the SwiftF0 library.

## Test Organization

### 📁 unit/
Unit tests for individual components and functions:
- Testing isolated functionality
- Mock dependencies
- Fast execution
- High code coverage

### 📁 integration/
Integration tests for complete workflows:
- `test_timbre_transform.py` - Full pipeline testing with timbre transformation
- End-to-end scenarios
- Real file I/O
- Performance benchmarks

### 📁 fixtures/
Test data and fixtures:
- Sample audio files
- Expected output files
- Mock data for unit tests

## Running Tests

### Run all tests
```bash
# From project root
python -m pytest tests/

# With coverage report
python -m pytest tests/ --cov=swift_f0 --cov-report=html
```

### Run specific test categories
```bash
# Unit tests only
python -m pytest tests/unit/

# Integration tests only
python -m pytest tests/integration/

# Specific test file
python -m pytest tests/integration/test_timbre_transform.py
```

### Run with verbose output
```bash
python -m pytest tests/ -v

# Show print statements
python -m pytest tests/ -s
```

## Test Data Management

Test data is organized in `/test_data/`:
- `inputs/` - Source files for testing (version controlled)
- `outputs/` - Generated test outputs (git-ignored)
- `batch_outputs/` - Batch processing results (git-ignored)

The test suite automatically creates necessary directories and synthetic test audio when needed.

## Writing New Tests

### Unit Test Template
```python
import pytest
from swift_f0.core import SwiftF0

class TestSwiftF0:
    def test_initialization(self):
        detector = SwiftF0()
        assert detector.confidence_threshold == 0.9

    def test_invalid_threshold(self):
        with pytest.raises(ValueError):
            SwiftF0(confidence_threshold=1.5)
```

### Integration Test Template
```python
import pytest
from pathlib import Path
from swift_f0 import SwiftF0, segment_notes

class TestPipeline:
    def test_audio_to_midi_pipeline(self, tmp_path):
        # Create test audio
        audio_path = create_test_audio(tmp_path / "test.wav")

        # Run pipeline
        detector = SwiftF0()
        result = detector.detect_from_file(audio_path)
        notes = segment_notes(result)

        # Assertions
        assert len(notes) > 0
```

## Continuous Integration

Tests are automatically run on:
- Every push to main branch
- All pull requests
- Nightly builds

Coverage requirements:
- Minimum 80% overall coverage
- 100% coverage for critical paths