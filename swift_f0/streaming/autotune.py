"""
Online auto-tune (pitch quantization to scale) for streaming note events.

This module provides real-time pitch correction by quantizing MIDI note values
to the nearest note in a detected key/scale. It integrates with OnlineKeyTracker
to get the current key signature and applies quantization with configurable strength.

Key features:
- Quantizes only note_on events (preserves note_off timing)
- Supports variable strength (0.0 = bypass, 1.0 = full quantization)
- Falls back to a default key when confidence is low
- Clamps output to valid MIDI range [0, 127]
"""

from __future__ import annotations

import logging
from typing import Callable, List, Tuple

from ..music_enhanced import KEY_NAMES, get_scale_notes, quantize_to_scale
from .types import NoteEvent


logger = logging.getLogger(__name__)


class AutoTuneQuantizer:
    """
    Real-time pitch quantization to scale for streaming note events.

    This class quantizes MIDI note values to the nearest note in a given scale,
    using a key detection callback (typically from OnlineKeyTracker.current_key).

    Attributes:
        get_key: Callable returning (key_name, mode) tuple
        strength: Quantization strength [0.0, 1.0] (0=bypass, 1=full)
        enabled: Whether auto-tune is active
        fallback_key: Default key when confidence is insufficient
    """

    def __init__(
        self,
        get_key: Callable[[], Tuple[str, str, float]],
        strength: float = 1.0,
        enabled: bool = True,
        fallback_key: Tuple[str, str] = ("C", "major"),
        confidence_threshold: float = 0.3,
    ) -> None:
        """
        Initialize AutoTuneQuantizer.

        Args:
            get_key: Callback returning (key_name, mode, correlation) tuple
            strength: Quantization strength [0.0, 1.0] (default 1.0)
            enabled: Whether to apply quantization (default True)
            fallback_key: Key to use when confidence is low (default C major)
            confidence_threshold: Minimum correlation to trust key detection (default 0.3)
        """
        if not 0.0 <= strength <= 1.0:
            raise ValueError(f"strength must be in [0.0, 1.0], got {strength}")

        self.get_key = get_key
        self.strength = strength
        self.enabled = enabled
        self.fallback_key = fallback_key
        self.confidence_threshold = confidence_threshold

        # Validate fallback key
        if fallback_key[0] not in KEY_NAMES:
            raise ValueError(f"Invalid fallback key name: {fallback_key[0]}")
        if fallback_key[1] not in ("major", "minor"):
            raise ValueError(f"Invalid fallback mode: {fallback_key[1]}")

        # Cache for current scale notes (avoid recomputation)
        self._current_key: Tuple[str, str] | None = None
        self._current_scale_notes: List[int] | None = None

        # Track first fallback usage
        self._first_fallback_logged = False

    def transform(self, events: List[NoteEvent]) -> List[NoteEvent]:
        """
        Apply auto-tune to note events.

        This method quantizes MIDI note values in note_on events to the nearest
        note in the current scale. Note_off events pass through unchanged.

        Args:
            events: List of NoteEvent objects (note_on or note_off)

        Returns:
            List of transformed NoteEvent objects (new instances, originals unchanged)
        """
        # Fast path: disabled or zero strength
        if not self.enabled or self.strength == 0.0:
            return events

        # Get current key and scale
        key_name, mode, scale_notes = self._get_current_scale()

        # Transform events
        transformed = []
        for event in events:
            if event.type == "note_on":
                # Quantize note
                original_note = event.note
                quantized_note = quantize_to_scale(original_note, scale_notes)

                # Blend based on strength
                new_note = round(
                    original_note * (1.0 - self.strength) + quantized_note * self.strength
                )

                # Clamp to valid MIDI range
                new_note = max(0, min(127, new_note))

                # Create new event with quantized note
                transformed.append(
                    NoteEvent(
                        type=event.type,
                        note=new_note,
                        time=event.time,
                        velocity=event.velocity,
                    )
                )

                # Debug logging for significant changes
                if abs(new_note - original_note) > 0:
                    logger.debug(
                        f"Auto-tune: {original_note} -> {new_note} "
                        f"(key={key_name} {mode}, strength={self.strength:.2f})"
                    )

            else:
                # Pass through note_off unchanged
                transformed.append(event)

        return transformed

    def _get_current_scale(self) -> Tuple[str, str, List[int]]:
        """
        Get current scale notes, using cache or fallback.

        Returns:
            Tuple of (key_name, mode, scale_notes)
        """
        # Query key tracker
        key_name, mode, correlation = self.get_key()

        # Check confidence threshold
        use_fallback = correlation < self.confidence_threshold

        if use_fallback:
            key_name, mode = self.fallback_key

            # Log first fallback usage (info level)
            if not self._first_fallback_logged:
                logger.info(
                    f"Auto-tune: Using fallback key {key_name} {mode} "
                    f"(confidence {correlation:.3f} < {self.confidence_threshold:.3f})"
                )
                self._first_fallback_logged = True
            else:
                # Subsequent fallbacks at debug level
                logger.debug(
                    f"Auto-tune: Using fallback key {key_name} {mode} "
                    f"(low confidence: {correlation:.3f})"
                )

        # Update cache if key changed
        if (key_name, mode) != self._current_key:
            self._current_key = (key_name, mode)
            self._current_scale_notes = get_scale_notes(key_name, mode)
            logger.debug(f"Auto-tune: Scale updated to {key_name} {mode}")

        # Ensure non-None scale notes for return (satisfy type checker and runtime)
        if self._current_scale_notes is None:
            self._current_scale_notes = get_scale_notes(key_name, mode)

        scale_notes: List[int] = self._current_scale_notes
        return key_name, mode, scale_notes

    def set_strength(self, strength: float) -> None:
        """
        Update quantization strength dynamically.

        Args:
            strength: New strength value [0.0, 1.0]
        """
        if not 0.0 <= strength <= 1.0:
            raise ValueError(f"strength must be in [0.0, 1.0], got {strength}")
        self.strength = strength
        logger.debug(f"Auto-tune strength updated to {strength:.2f}")

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable auto-tune dynamically.

        Args:
            enabled: Whether to apply quantization
        """
        self.enabled = enabled
        logger.debug(f"Auto-tune {'enabled' if enabled else 'disabled'}")
