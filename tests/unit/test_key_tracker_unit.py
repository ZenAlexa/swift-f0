"""
Unit tests for OnlineKeyTracker (online key detection with sliding window).

This module tests the real-time key detection functionality without requiring
audio devices or MIDI hardware.
"""

import pytest
from swift_f0.streaming.key_detection import OnlineKeyTracker
from swift_f0.streaming.types import NoteEvent


def test_empty_tracker_returns_default():
    """Test that empty tracker returns default C major with zero correlation."""
    tracker = OnlineKeyTracker(window_seconds=10.0, include_active=False)
    key_name, mode, correlation = tracker.current_key()

    assert key_name == "C"
    assert mode == "major"
    assert correlation == 0.0


def test_c_major_scale_detection():
    """Test detection of C major scale from note events."""
    tracker = OnlineKeyTracker(window_seconds=10.0, include_active=False)

    # Create C major scale events (C, D, E, F, G, A, B, C)
    # MIDI numbers: 60, 62, 64, 65, 67, 69, 71, 72
    c_major_notes = [60, 62, 64, 65, 67, 69, 71, 72]

    events = []
    current_time = 0.0

    # Generate note_on/off pairs with 0.5s duration each
    for note in c_major_notes:
        events.append(NoteEvent(type="note_on", note=note, time=current_time, velocity=80))
        current_time += 0.5
        events.append(NoteEvent(type="note_off", note=note, time=current_time, velocity=80))
        current_time += 0.1  # Small gap between notes

    # Feed events to tracker
    tracker.update(events)

    # Query key
    key_name, mode, correlation = tracker.current_key()

    # Should detect C major with reasonable correlation
    assert key_name == "C"
    assert mode == "major"
    assert correlation > 0.3, f"Expected correlation > 0.3, got {correlation}"


def test_a_minor_scale_detection():
    """Test detection of A minor scale (natural minor)."""
    tracker = OnlineKeyTracker(window_seconds=10.0, include_active=False)

    # A natural minor scale: A, B, C, D, E, F, G, A
    # MIDI numbers: 69, 71, 60, 62, 64, 65, 67, 69
    a_minor_notes = [69, 71, 60, 62, 64, 65, 67, 69]

    events = []
    current_time = 0.0

    # Generate note_on/off pairs
    for note in a_minor_notes:
        events.append(NoteEvent(type="note_on", note=note, time=current_time, velocity=80))
        current_time += 0.5
        events.append(NoteEvent(type="note_off", note=note, time=current_time, velocity=80))
        current_time += 0.1

    tracker.update(events)
    key_name, mode, correlation = tracker.current_key()

    # Should detect A minor
    assert key_name == "A"
    assert mode == "minor"
    assert correlation > 0.3


def test_sliding_window_pruning():
    """Test that old segments are pruned outside the sliding window."""
    tracker = OnlineKeyTracker(window_seconds=2.0, include_active=False)

    # Add a C note at time 0.0-0.5
    events_early = [
        NoteEvent(type="note_on", note=60, time=0.0, velocity=80),
        NoteEvent(type="note_off", note=60, time=0.5, velocity=80),
    ]
    tracker.update(events_early)

    # Verify C is detected
    key1, mode1, corr1 = tracker.current_key()
    assert corr1 > 0.0  # Should have some data

    # Add a D# note at time 3.0-3.5 (outside 2s window from time 0.5)
    events_late = [
        NoteEvent(type="note_on", note=63, time=3.0, velocity=80),  # D#
        NoteEvent(type="note_off", note=63, time=3.5, velocity=80),
    ]
    tracker.update(events_late)

    # The early C note should have been pruned (ended at 0.5, now at 3.5, window=2.0)
    # Only D# should remain
    key2, mode2, corr2 = tracker.current_key()

    # Histogram should only contain D# now (pitch class 3)
    histogram = tracker.get_histogram()

    # Check that pitch class 0 (C) has zero duration (pruned)
    assert histogram[0] == 0.0, "Early C note should be pruned"

    # Check that pitch class 3 (D#) has non-zero duration
    assert histogram[3] > 0.0, "Recent D# note should be present"


def test_include_active_notes():
    """Test that active (not yet ended) notes are included in histogram."""
    tracker = OnlineKeyTracker(window_seconds=10.0, include_active=True)

    # Start a long C note but don't end it yet
    events = [
        NoteEvent(type="note_on", note=60, time=0.0, velocity=80),
    ]
    tracker.update(events)

    # Advance time without sending note_off
    events2 = [
        NoteEvent(type="note_on", note=64, time=1.0, velocity=80),  # E note
    ]
    tracker.update(events2)

    # Query key to trigger histogram build
    key_name, mode, correlation = tracker.current_key()

    # Get histogram (cached from current_key call)
    histogram = tracker.get_histogram()

    # C (pitch class 0) should have ~1.0s duration
    assert histogram[0] > 0.5, "Active C note should contribute to histogram"

    # E (pitch class 4) should have ~0.0s duration (just started)
    # (might be small due to rounding, but should be >= 0)
    assert histogram[4] >= 0.0


def test_exclude_active_notes():
    """Test that active notes can be excluded from histogram."""
    tracker = OnlineKeyTracker(window_seconds=10.0, include_active=False)

    # Start a C note but don't end it
    events = [
        NoteEvent(type="note_on", note=60, time=0.0, velocity=80),
    ]
    tracker.update(events)

    # Query key to trigger histogram build
    tracker.current_key()

    # Check histogram should be empty (no completed segments)
    histogram = tracker.get_histogram()
    total_duration = histogram.sum()

    assert total_duration == 0.0, "No completed notes, histogram should be empty"


def test_overlapping_same_pitch():
    """Test handling of same pitch overlapping (unlikely but should not crash)."""
    tracker = OnlineKeyTracker(window_seconds=10.0, include_active=False)

    # Start two C notes at different times without ending the first
    events = [
        NoteEvent(type="note_on", note=60, time=0.0, velocity=80),
        NoteEvent(type="note_on", note=60, time=0.5, velocity=80),
        NoteEvent(type="note_off", note=60, time=1.0, velocity=80),  # Pairs with first
        NoteEvent(type="note_off", note=60, time=1.5, velocity=80),  # Pairs with second
    ]
    tracker.update(events)

    # Query key to trigger histogram build
    tracker.current_key()

    # Should handle gracefully and create two segments
    histogram = tracker.get_histogram()

    # Total duration should be 1.0s (first note) + 1.0s (second note) = 2.0s for C
    # Allow some tolerance due to window clipping
    assert histogram[0] >= 1.5, f"Expected ~2.0s for C, got {histogram[0]}"


def test_reset():
    """Test that reset clears all state."""
    tracker = OnlineKeyTracker(window_seconds=10.0, include_active=False)

    # Add some events
    events = [
        NoteEvent(type="note_on", note=60, time=0.0, velocity=80),
        NoteEvent(type="note_off", note=60, time=1.0, velocity=80),
    ]
    tracker.update(events)

    # Verify data exists
    key1, mode1, corr1 = tracker.current_key()
    assert corr1 > 0.0

    # Reset
    tracker.reset()

    # Verify empty state
    key2, mode2, corr2 = tracker.current_key()
    assert key2 == "C"
    assert mode2 == "major"
    assert corr2 == 0.0

    histogram = tracker.get_histogram()
    assert histogram.sum() == 0.0


def test_long_duration_notes():
    """Test that long duration notes contribute appropriately to histogram."""
    tracker = OnlineKeyTracker(window_seconds=10.0, include_active=False)

    # Create one long C note (5 seconds) and one short E note (0.5 seconds)
    events = [
        NoteEvent(type="note_on", note=60, time=0.0, velocity=80),   # C
        NoteEvent(type="note_off", note=60, time=5.0, velocity=80),
        NoteEvent(type="note_on", note=64, time=5.0, velocity=80),   # E
        NoteEvent(type="note_off", note=64, time=5.5, velocity=80),
    ]
    tracker.update(events)

    # Query key to trigger histogram build
    tracker.current_key()

    histogram = tracker.get_histogram()

    # C should have ~5.0s, E should have ~0.5s
    # C should dominate (10x longer)
    assert histogram[0] > 4.0, f"C should have ~5.0s, got {histogram[0]}"
    assert histogram[4] > 0.3, f"E should have ~0.5s, got {histogram[4]}"
    assert histogram[0] / histogram[4] > 5.0, "C should be much longer than E"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
