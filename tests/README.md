# Test Suite

Organized test suite for SwiftF0 real-time system.

---

## Directory Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_key_tracker_unit.py
│   ├── test_autotune_unit.py
│   └── test_soundfont_discovery.py
├── integration/             # Integration tests (multi-component)
│   ├── test_streaming_strategy.py
│   └── test_realtime_pipeline.py
└── examples/                # Example-based tests (demonstrations)
    └── test_timbre_demo.py
```

---

## Running Tests

### All Tests
```bash
pytest tests/
```

### By Category
```bash
# Unit tests (fast, < 1s total)
pytest tests/unit/

# Integration tests (moderate, ~5s total)
pytest tests/integration/

# Examples (slow, may generate files)
pytest tests/examples/
```

### Specific Test
```bash
# Test SoundFont discovery
pytest tests/unit/test_soundfont_discovery.py -v

# Test full pipeline
pytest tests/integration/test_realtime_pipeline.py -v

# Test key tracker
pytest tests/unit/test_key_tracker_unit.py -v
```

### With Coverage
```bash
pytest tests/ --cov=swift_f0 --cov-report=html
open htmlcov/index.html  # View coverage report
```

---

## Test Categories

### Unit Tests (`unit/`)

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast (< 100ms each)
- No external dependencies (except test data)
- No file I/O (except temp files)
- Deterministic results

**Tests**:
- `test_key_tracker_unit.py` - Online key detection algorithm
- `test_autotune_unit.py` - Pitch quantization logic
- `test_soundfont_discovery.py` - SoundFont file discovery

---

### Integration Tests (`integration/`)

**Purpose**: Test component interactions and data flow

**Characteristics**:
- Moderate speed (~1-5s each)
- Tests multiple components together
- May use temporary files
- Tests end-to-end scenarios

**Tests**:
- `test_streaming_strategy.py` - Streaming pipeline orchestration
- `test_realtime_pipeline.py` - Full audio → MIDI pipeline

---

### Example Tests (`examples/`)

**Purpose**: Demonstrate usage and validate examples

**Characteristics**:
- Slow (may take 10s+)
- Generate output files
- Test complete workflows
- Serve as documentation

**Tests**:
- `test_timbre_demo.py` - Offline timbre transformation demo

---

## Writing New Tests

### Unit Test Template

```python
"""Test description."""

import pytest
from swift_f0.streaming import ComponentToTest


def test_component_basic_behavior():
    """Test basic functionality."""
    component = ComponentToTest()
    result = component.process(input_data)
    assert result is not None


def test_component_edge_case():
    """Test edge case handling."""
    component = ComponentToTest()
    with pytest.raises(ValueError):
        component.process(invalid_input)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### Integration Test Template

```python
"""Test multi-component interaction."""

import pytest
import tempfile
import os
from swift_f0.streaming import Component1, Component2


def test_components_integration():
    """Test Component1 → Component2 data flow."""
    c1 = Component1()
    c2 = Component2()

    # Setup
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.mid")

        # Process
        intermediate = c1.process(input_data)
        result = c2.process(intermediate, output_path)

        # Assert
        assert os.path.exists(output_path)
        assert result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[test]
      - run: pytest tests/unit tests/integration -v --cov=swift_f0
```

---

## Test Data

Test data should be:
- Small (<1MB)
- Committed to repo (in `test_data/inputs/`)
- Documented purpose

Generated outputs go to:
- `test_data/outputs/` (gitignored)
- Or temporary directories (auto-cleaned)

---

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Core (core.py) | 90% | TBD |
| Streaming (streaming/*) | 85% | TBD |
| Music Theory (music_theory.py) | 95% | TBD |
| Overall | 85% | TBD |

Run: `pytest --cov=swift_f0 --cov-report=term-missing`

---

**Last Updated**: 2025-10-15
**Maintainer**: Adrian
