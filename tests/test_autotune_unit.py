"""
Unit tests for AutoTuneQuantizer (real-time pitch quantization to scale).

This module tests the auto-tune quantization functionality without requiring
audio devices or MIDI hardware.
"""

import pytest
from swift_f0.streaming.autotune import AutoTuneQuantizer
from swift_f0.streaming.types import NoteEvent


def mock_get_key_c_major():
    """Mock key tracker that always returns C major with high confidence."""
    return ("C", "major", 0.8)


def mock_get_key_g_major():
    """Mock key tracker that always returns G major with high confidence."""
    return ("G", "major", 0.9)


def mock_get_key_low_confidence():
    """Mock key tracker with low confidence (should trigger fallback)."""
    return ("D", "major", 0.1)


def test_disabled_mode_bypasses():
    """Test that disabled mode returns events unchanged."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=1.0,
        enabled=False,
    )

    events = [
        NoteEvent(type="note_on", note=61, time=0.0, velocity=80),  # C#
        NoteEvent(type="note_off", note=61, time=1.0, velocity=80),
    ]

    transformed = quantizer.transform(events)

    # Should return identical events
    assert len(transformed) == 2
    assert transformed[0].note == 61  # Unchanged
    assert transformed[1].note == 61


def test_zero_strength_bypasses():
    """Test that strength=0.0 returns events unchanged."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=0.0,
        enabled=True,
    )

    events = [
        NoteEvent(type="note_on", note=61, time=0.0, velocity=80),  # C#
    ]

    transformed = quantizer.transform(events)

    assert transformed[0].note == 61  # Unchanged


def test_quantize_to_c_major_full_strength():
    """Test full quantization (strength=1.0) to C major scale."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=1.0,
        enabled=True,
    )

    # C major scale: C(60), D(62), E(64), F(65), G(67), A(69), B(71)
    # Non-scale notes: C#(61), D#(63), F#(66), G#(68), A#(70)

    # Test C# (61) should quantize to C(60) or D(62)
    events1 = [NoteEvent(type="note_on", note=61, time=0.0, velocity=80)]
    result1 = quantizer.transform(events1)
    assert result1[0].note in [60, 62], f"C# should quantize to C or D, got {result1[0].note}"

    # Test D# (63) should quantize to D(62) or E(64)
    events2 = [NoteEvent(type="note_on", note=63, time=0.0, velocity=80)]
    result2 = quantizer.transform(events2)
    assert result2[0].note in [62, 64], f"D# should quantize to D or E, got {result2[0].note}"

    # Test F# (66) should quantize to F(65) or G(67)
    events3 = [NoteEvent(type="note_on", note=66, time=0.0, velocity=80)]
    result3 = quantizer.transform(events3)
    assert result3[0].note in [65, 67], f"F# should quantize to F or G, got {result3[0].note}"


def test_notes_on_scale_unchanged():
    """Test that notes already on the scale remain unchanged."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=1.0,
        enabled=True,
    )

    # C major scale notes should not be changed
    c_major_notes = [60, 62, 64, 65, 67, 69, 71, 72]

    for note in c_major_notes:
        events = [NoteEvent(type="note_on", note=note, time=0.0, velocity=80)]
        result = quantizer.transform(events)
        assert result[0].note == note, f"Scale note {note} should remain unchanged"


def test_note_off_passthrough():
    """Test that note_off events pass through unchanged."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=1.0,
        enabled=True,
    )

    events = [
        NoteEvent(type="note_on", note=61, time=0.0, velocity=80),  # C# (quantized)
        NoteEvent(type="note_off", note=61, time=1.0, velocity=80),  # Should pass through
    ]

    transformed = quantizer.transform(events)

    # note_on should be quantized
    assert transformed[0].type == "note_on"
    assert transformed[0].note in [60, 62]  # Quantized

    # note_off should pass through unchanged
    assert transformed[1].type == "note_off"
    assert transformed[1].note == 61  # Original value


def test_partial_strength():
    """Test strength parameter creates interpolation between original and quantized."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=0.5,
        enabled=True,
    )

    # C# (61) should quantize to C(60) in C major
    # With strength=0.5: result = round(61 * 0.5 + 60 * 0.5) = round(60.5) = 60 or 61
    events = [NoteEvent(type="note_on", note=61, time=0.0, velocity=80)]
    result = quantizer.transform(events)

    # Result should be between 60 and 61 (inclusive)
    assert 60 <= result[0].note <= 61, f"Partial strength should give intermediate value"


def test_clamping_to_midi_range():
    """Test that output is clamped to valid MIDI range [0, 127]."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=1.0,
        enabled=True,
    )

    # Test near boundaries (though unlikely to occur in practice)
    events = [
        NoteEvent(type="note_on", note=0, time=0.0, velocity=80),    # Lowest MIDI
        NoteEvent(type="note_on", note=127, time=0.0, velocity=80),  # Highest MIDI
    ]

    result = quantizer.transform(events)

    # Should remain in valid range
    assert 0 <= result[0].note <= 127
    assert 0 <= result[1].note <= 127


def test_low_confidence_fallback():
    """Test that low confidence triggers fallback to C major."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_low_confidence,  # Returns D major with corr=0.1
        strength=1.0,
        enabled=True,
        fallback_key=("C", "major"),
        confidence_threshold=0.3,
    )

    # Should use C major scale (fallback) instead of D major
    # C# (61) should quantize to C(60) or D(62) in C major
    events = [NoteEvent(type="note_on", note=61, time=0.0, velocity=80)]
    result = quantizer.transform(events)

    # If using D major, C# would quantize to C#(61) or D(62)
    # If using C major (fallback), C# quantizes to C(60) or D(62)
    # We expect C(60) as closest in C major
    assert result[0].note in [60, 62]


def test_different_key_g_major():
    """Test quantization to G major scale."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_g_major,
        strength=1.0,
        enabled=True,
    )

    # G major scale: G(67), A(69), B(71), C(72), D(74), E(76), F#(78)
    # At MIDI 60-72 range: C(60), D(62), E(64), F#(66), G(67), A(69), B(71), C(72)

    # Test F natural (65) - not in G major, should quantize to E(64) or F#(66)
    events = [NoteEvent(type="note_on", note=65, time=0.0, velocity=80)]
    result = quantizer.transform(events)
    assert result[0].note in [64, 66], f"F should quantize to E or F# in G major"


def test_set_strength_dynamically():
    """Test dynamic strength adjustment."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=1.0,
        enabled=True,
    )

    # Initial strength=1.0
    events = [NoteEvent(type="note_on", note=61, time=0.0, velocity=80)]
    result1 = quantizer.transform(events)
    assert result1[0].note in [60, 62]  # Fully quantized

    # Change to strength=0.0
    quantizer.set_strength(0.0)
    result2 = quantizer.transform(events)
    assert result2[0].note == 61  # No quantization


def test_set_enabled_dynamically():
    """Test dynamic enable/disable."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=1.0,
        enabled=True,
    )

    events = [NoteEvent(type="note_on", note=61, time=0.0, velocity=80)]

    # Enabled
    result1 = quantizer.transform(events)
    assert result1[0].note in [60, 62]  # Quantized

    # Disable
    quantizer.set_enabled(False)
    result2 = quantizer.transform(events)
    assert result2[0].note == 61  # Unchanged


def test_invalid_strength_raises_error():
    """Test that invalid strength values raise ValueError."""
    with pytest.raises(ValueError, match="strength must be in"):
        AutoTuneQuantizer(
            get_key=mock_get_key_c_major,
            strength=1.5,  # Invalid
        )

    with pytest.raises(ValueError, match="strength must be in"):
        AutoTuneQuantizer(
            get_key=mock_get_key_c_major,
            strength=-0.1,  # Invalid
        )


def test_invalid_fallback_key_raises_error():
    """Test that invalid fallback key raises ValueError."""
    with pytest.raises(ValueError, match="Invalid fallback key name"):
        AutoTuneQuantizer(
            get_key=mock_get_key_c_major,
            fallback_key=("H", "major"),  # Invalid key name
        )

    with pytest.raises(ValueError, match="Invalid fallback mode"):
        AutoTuneQuantizer(
            get_key=mock_get_key_c_major,
            fallback_key=("C", "blues"),  # Invalid mode
        )


def test_multiple_events_batch():
    """Test processing multiple events in a batch."""
    quantizer = AutoTuneQuantizer(
        get_key=mock_get_key_c_major,
        strength=1.0,
        enabled=True,
    )

    events = [
        NoteEvent(type="note_on", note=60, time=0.0, velocity=80),   # C (on scale)
        NoteEvent(type="note_on", note=61, time=0.1, velocity=80),   # C# (not on scale)
        NoteEvent(type="note_off", note=60, time=0.5, velocity=80),  # Pass through
        NoteEvent(type="note_on", note=64, time=0.6, velocity=80),   # E (on scale)
        NoteEvent(type="note_off", note=61, time=0.7, velocity=80),  # Pass through
    ]

    result = quantizer.transform(events)

    assert len(result) == 5

    # C should remain
    assert result[0].type == "note_on"
    assert result[0].note == 60

    # C# should be quantized
    assert result[1].type == "note_on"
    assert result[1].note in [60, 62]

    # Note offs should pass through
    assert result[2].type == "note_off"
    assert result[2].note == 60

    assert result[3].type == "note_on"
    assert result[3].note == 64

    assert result[4].type == "note_off"
    assert result[4].note == 61


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
