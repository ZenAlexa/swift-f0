"""
Timbre resolution utilities for MIDI instrument mapping.

This module provides a unified interface to resolve instrument names/numbers
to GM (General MIDI) program numbers (0-127).
"""

from __future__ import annotations


def resolve_instrument(name_or_num: str | int) -> int:
    """
    Resolve instrument name or number to GM program number (0-127).

    Args:
        name_or_num: Either a GM instrument name (e.g., "oboe", "trumpet")
                     or a program number as int/str (e.g., 56, "56")

    Returns:
        int: GM program number (0-127)

    Raises:
        ValueError: If instrument name is unknown or number is out of range

    Examples:
        >>> resolve_instrument("oboe")
        68
        >>> resolve_instrument(56)
        56
        >>> resolve_instrument("56")
        56
        >>> resolve_instrument("unknown")
        ValueError: Unknown instrument name: unknown
        >>> resolve_instrument(128)
        ValueError: Instrument program number must be 0-127, got: 128
    """
    # Case 1: Already an integer
    if isinstance(name_or_num, int):
        if not 0 <= name_or_num <= 127:
            raise ValueError(f"Instrument program number must be 0-127, got: {name_or_num}")
        return name_or_num

    # Case 2: String that might be a number
    if isinstance(name_or_num, str):
        # Try to parse as integer first
        try:
            program = int(name_or_num)
            if not 0 <= program <= 127:
                raise ValueError(f"Instrument program number must be 0-127, got: {program}")
            return program
        except ValueError:
            # Not a number, treat as instrument name
            pass

        # Look up in GM_INSTRUMENTS map
        from ..music_enhanced import GM_INSTRUMENTS

        if name_or_num not in GM_INSTRUMENTS:
            raise ValueError(
                f"Unknown instrument name: {name_or_num}. "
                f"Use a GM instrument name (e.g., 'oboe', 'trumpet') or a number (0-127)."
            )
        return GM_INSTRUMENTS[name_or_num]

    # Case 3: Unexpected type
    raise TypeError(f"Expected str or int, got {type(name_or_num).__name__}")
