"""
Online key detection using sliding window and Krumhansl-Schmuckler algorithm.

This module provides real-time key detection by maintaining a sliding window
of note events and computing pitch class histograms for K-S template matching.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

from ..music_enhanced import KEY_NAMES, MAJOR_PROFILE, MINOR_PROFILE
from .types import NoteEvent


@dataclass
class NoteSegment:
    """Internal representation of a completed note segment for histogram tracking."""

    pitch_class: int  # 0-11
    start_time: float
    end_time: float
    duration: float


class OnlineKeyTracker:
    """
    Real-time key detection using sliding window K-S algorithm.

    This tracker maintains a sliding window of note events and computes
    the current key signature by correlating pitch class histograms with
    Krumhansl-Schmuckler major/minor profiles.

    Algorithm:
        1. Collect note_on/off events and pair them to compute durations
        2. Maintain sliding window of completed note segments
        3. Build pitch class histogram weighted by duration
        4. Correlate with 24 key templates (12 major + 12 minor)
        5. Return best matching key with correlation score

    Attributes:
        window_seconds: Duration of sliding window (default 10.0)
        step_seconds: Update interval for key detection (default 2.0)
        include_active: Include partially played notes in histogram (default True)
    """

    def __init__(
        self,
        window_seconds: float = 10.0,
        step_seconds: float = 2.0,
        include_active: bool = True,
    ) -> None:
        """
        Initialize OnlineKeyTracker.

        Args:
            window_seconds: Duration of sliding window for statistics (seconds)
            step_seconds: Interval for key updates (seconds, not enforced, just for reference)
            include_active: Whether to include currently playing notes in histogram
        """
        self.window_seconds = window_seconds
        self.step_seconds = step_seconds
        self.include_active = include_active

        # Active notes: dict[midi_note] -> list[start_times]
        # Use list to support same pitch overlapping (though unlikely in single voice)
        self.active_notes: Dict[int, List[float]] = {}

        # Completed segments within the window
        self.segments: deque[NoteSegment] = deque()

        # Current time (updated by latest event)
        self.current_time: float = 0.0

        # Last computed key (cached)
        self._last_key: Tuple[str, str, float] = ("C", "major", 0.0)
        self._last_histogram: np.ndarray = np.zeros(12)

    def update(self, events: List[NoteEvent]) -> None:
        """
        Process incoming note events and update internal state.

        This method:
        1. Pairs note_on/off events to compute durations
        2. Adds completed segments to the window
        3. Removes expired segments outside the window
        4. Updates current time

        Args:
            events: List of NoteEvent objects (note_on or note_off)
        """
        for event in events:
            self.current_time = event.time

            if event.type == "note_on":
                # Add to active notes
                if event.note not in self.active_notes:
                    self.active_notes[event.note] = []
                self.active_notes[event.note].append(event.time)

            elif event.type == "note_off":
                # Pair with earliest note_on for this pitch
                if event.note in self.active_notes and self.active_notes[event.note]:
                    start_time = self.active_notes[event.note].pop(0)
                    duration = event.time - start_time

                    # Create completed segment
                    segment = NoteSegment(
                        pitch_class=event.note % 12,
                        start_time=start_time,
                        end_time=event.time,
                        duration=duration,
                    )
                    self.segments.append(segment)

                    # Clean up empty list
                    if not self.active_notes[event.note]:
                        del self.active_notes[event.note]

        # Prune expired segments outside the window
        self._prune_old_segments()

    def _prune_old_segments(self) -> None:
        """Remove segments that ended before the current window."""
        window_start = self.current_time - self.window_seconds

        # Remove from left (oldest)
        while self.segments and self.segments[0].end_time < window_start:
            self.segments.popleft()

    def _build_histogram(self) -> np.ndarray:
        """
        Build pitch class histogram weighted by duration.

        Returns:
            12-element array with durations for each pitch class (C, C#, ..., B)
        """
        histogram = np.zeros(12)
        window_start = self.current_time - self.window_seconds

        # Add completed segments
        for segment in self.segments:
            # Clip segment to current window
            effective_start = max(segment.start_time, window_start)
            effective_end = min(segment.end_time, self.current_time)
            effective_duration = effective_end - effective_start

            if effective_duration > 0:
                histogram[segment.pitch_class] += effective_duration

        # Optionally add active notes (partial durations)
        if self.include_active:
            for midi_note, start_times in self.active_notes.items():
                pitch_class = midi_note % 12
                for start_time in start_times:
                    # Only count if started within window
                    if start_time >= window_start:
                        partial_duration = self.current_time - start_time
                        histogram[pitch_class] += partial_duration

        return histogram

    def current_key(self) -> Tuple[str, str, float]:
        """
        Compute current key signature using K-S algorithm.

        Returns:
            Tuple of (key_name, mode, correlation) where:
            - key_name: 'C', 'C#', 'D', etc.
            - mode: 'major' or 'minor'
            - correlation: Pearson correlation coefficient [-1.0, 1.0]

        Note:
            Returns ('C', 'major', 0.0) if no data available yet.
        """
        histogram = self._build_histogram()
        self._last_histogram = histogram

        # Check if we have any data
        total_duration = histogram.sum()
        if total_duration == 0:
            return ("C", "major", 0.0)

        # Normalize histogram
        normalized_histogram = histogram / total_duration

        # Test all 24 keys (12 major + 12 minor)
        correlations = []

        for tonic in range(12):
            # Rotate profiles to match tonic
            major_profile_rotated = np.roll(MAJOR_PROFILE, tonic)
            minor_profile_rotated = np.roll(MINOR_PROFILE, tonic)

            # Compute correlations
            # Handle edge case where variance is zero
            try:
                major_corr = np.corrcoef(normalized_histogram, major_profile_rotated)[0, 1]
                if np.isnan(major_corr):
                    major_corr = 0.0
            except:
                major_corr = 0.0

            try:
                minor_corr = np.corrcoef(normalized_histogram, minor_profile_rotated)[0, 1]
                if np.isnan(minor_corr):
                    minor_corr = 0.0
            except:
                minor_corr = 0.0

            correlations.append((KEY_NAMES[tonic], "major", major_corr))
            correlations.append((KEY_NAMES[tonic], "minor", minor_corr))

        # Find best match
        best = max(correlations, key=lambda x: x[2])
        self._last_key = best

        return best

    def get_histogram(self) -> np.ndarray:
        """
        Get current pitch class histogram (for debugging/visualization).

        Returns:
            12-element array with durations for each pitch class
        """
        return self._last_histogram.copy()

    def reset(self) -> None:
        """Reset tracker state (clear all data)."""
        self.active_notes.clear()
        self.segments.clear()
        self.current_time = 0.0
        self._last_key = ("C", "major", 0.0)
        self._last_histogram = np.zeros(12)
