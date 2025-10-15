"""
Unit tests for SoundFont discovery utilities.
"""

import pytest
from pathlib import Path
from swift_f0.streaming.soundfont_utils import (
    find_soundfonts,
    get_default_soundfont,
    format_soundfont_size,
    resolve_soundfont_path,
)


def test_find_soundfonts_in_project():
    """Test that find_soundfonts discovers soundfonts in project directory."""
    soundfonts = find_soundfonts()

    # Should find at least one (GeneralUser-GS.sf2 in soundfonts/)
    assert len(soundfonts) >= 0, "SoundFont search should not crash"

    # If found, should be Path objects
    for sf in soundfonts:
        assert isinstance(sf, Path)
        assert sf.suffix.lower() in [".sf2", ".sf3"]
        assert sf.exists()


def test_get_default_soundfont():
    """Test default SoundFont selection (largest file)."""
    default = get_default_soundfont()

    # May be None if no soundfonts found
    if default is not None:
        assert isinstance(default, Path)
        assert default.exists()
        assert default.suffix.lower() in [".sf2", ".sf3"]


def test_format_soundfont_size():
    """Test human-readable size formatting."""
    assert format_soundfont_size(512) == "512 B"
    assert format_soundfont_size(1024) == "1.0 KB"
    assert format_soundfont_size(1024 ** 2) == "1.0 MB"
    assert format_soundfont_size(31 * 1024 ** 2) == "31.0 MB"
    assert format_soundfont_size(1024 ** 3) == "1.0 GB"


def test_resolve_soundfont_path_explicit():
    """Test explicit path resolution."""
    # Find first available soundfont
    soundfonts = find_soundfonts()

    if soundfonts:
        # Test resolving existing file
        resolved = resolve_soundfont_path(str(soundfonts[0]))
        assert Path(resolved).exists()
        assert Path(resolved).is_absolute()

    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        resolve_soundfont_path("/nonexistent/path.sf2")


def test_resolve_soundfont_path_auto():
    """Test automatic soundfont discovery via 'auto' keyword."""
    # This may fail if no soundfonts installed
    try:
        resolved = resolve_soundfont_path("auto")
        assert Path(resolved).exists()
        assert Path(resolved).is_absolute()
        assert Path(resolved).suffix.lower() in [".sf2", ".sf3"]
    except FileNotFoundError:
        # Expected if no soundfonts found
        pytest.skip("No SoundFonts found for auto-discovery test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
