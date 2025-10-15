"""
Music theory constants and utilities (DRY principle - single source of truth).

This module provides shared music theory data used by both offline (music_enhanced.py)
and streaming (streaming/key_detection.py, streaming/autotune.py) modules.

Extracted to eliminate circular dependencies and follow Dependency Inversion Principle:
- High-level modules (offline/streaming) depend on this abstraction
- Not the other way around
"""

from __future__ import annotations

import numpy as np
from typing import List

# ============================================================================
# Key Detection - Krumhansl-Schmuckler Profiles
# ============================================================================

# Major key profile (Krumhansl & Kessler 1982)
# Higher values = more characteristic of the scale degree
MAJOR_PROFILE = np.array([
    6.35,  # Tonic (most important)
    2.23,  # Minor 2nd
    3.48,  # Major 2nd
    2.33,  # Minor 3rd
    4.38,  # Major 3rd
    4.09,  # Perfect 4th
    2.52,  # Tritone
    5.19,  # Perfect 5th (dominant)
    2.39,  # Minor 6th
    3.66,  # Major 6th
    2.29,  # Minor 7th
    2.88   # Major 7th
])

# Minor key profile (Krumhansl & Kessler 1982)
MINOR_PROFILE = np.array([
    6.33,  # Tonic
    2.68,  # Minor 2nd
    3.52,  # Major 2nd
    5.38,  # Minor 3rd (characteristic)
    2.60,  # Major 3rd
    3.53,  # Perfect 4th
    2.54,  # Tritone
    4.75,  # Perfect 5th
    3.98,  # Minor 6th (characteristic)
    2.69,  # Major 6th
    3.34,  # Minor 7th (characteristic)
    3.17   # Major 7th
])

# Pitch class names (0=C, 1=C#, ..., 11=B)
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


# ============================================================================
# General MIDI (GM) Instrument Map
# ============================================================================

GM_INSTRUMENTS = {
    # Piano (0-7)
    "acoustic_grand_piano": 0,
    "bright_acoustic_piano": 1,
    "electric_grand_piano": 2,
    "honky_tonk_piano": 3,
    "electric_piano_1": 4,
    "electric_piano_2": 5,
    "harpsichord": 6,
    "clavinet": 7,
    # Chromatic Percussion (8-15)
    "celesta": 8,
    "glockenspiel": 9,
    "music_box": 10,
    "vibraphone": 11,
    "marimba": 12,
    "xylophone": 13,
    "tubular_bells": 14,
    "dulcimer": 15,
    # Organ (16-23)
    "drawbar_organ": 16,
    "percussive_organ": 17,
    "rock_organ": 18,
    "church_organ": 19,
    "reed_organ": 20,
    "accordion": 21,
    "harmonica": 22,
    "tango_accordion": 23,
    # Guitar (24-31)
    "acoustic_guitar_nylon": 24,
    "acoustic_guitar_steel": 25,
    "electric_guitar_jazz": 26,
    "electric_guitar_clean": 27,
    "electric_guitar_muted": 28,
    "overdriven_guitar": 29,
    "distortion_guitar": 30,
    "guitar_harmonics": 31,
    # Bass (32-39)
    "acoustic_bass": 32,
    "electric_bass_finger": 33,
    "electric_bass_pick": 34,
    "fretless_bass": 35,
    "slap_bass_1": 36,
    "slap_bass_2": 37,
    "synth_bass_1": 38,
    "synth_bass_2": 39,
    # Strings (40-47)
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contrabass": 43,
    "tremolo_strings": 44,
    "pizzicato_strings": 45,
    "orchestral_harp": 46,
    "timpani": 47,
    # Ensemble (48-55)
    "string_ensemble_1": 48,
    "string_ensemble_2": 49,
    "synth_strings_1": 50,
    "synth_strings_2": 51,
    "choir_aahs": 52,
    "voice_oohs": 53,
    "synth_voice": 54,
    "orchestra_hit": 55,
    # Brass (56-63)
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "muted_trumpet": 59,
    "french_horn": 60,
    "brass_section": 61,
    "synth_brass_1": 62,
    "synth_brass_2": 63,
    # Reed (64-71)
    "soprano_sax": 64,
    "alto_sax": 65,
    "tenor_sax": 66,
    "baritone_sax": 67,
    "oboe": 68,
    "english_horn": 69,
    "bassoon": 70,
    "clarinet": 71,
    # Pipe (72-79)
    "piccolo": 72,
    "flute": 73,
    "recorder": 74,
    "pan_flute": 75,
    "blown_bottle": 76,
    "shakuhachi": 77,
    "whistle": 78,
    "ocarina": 79,
    # Synth Lead (80-87)
    "lead_1_square": 80,
    "lead_2_sawtooth": 81,
    "lead_3_calliope": 82,
    "lead_4_chiff": 83,
    "lead_5_charang": 84,
    "lead_6_voice": 85,
    "lead_7_fifths": 86,
    "lead_8_bass_lead": 87,
    # Synth Pad (88-95)
    "pad_1_new_age": 88,
    "pad_2_warm": 89,
    "pad_3_polysynth": 90,
    "pad_4_choir": 91,
    "pad_5_bowed": 92,
    "pad_6_metallic": 93,
    "pad_7_halo": 94,
    "pad_8_sweep": 95,
    # Synth Effects (96-103)
    "fx_1_rain": 96,
    "fx_2_soundtrack": 97,
    "fx_3_crystal": 98,
    "fx_4_atmosphere": 99,
    "fx_5_brightness": 100,
    "fx_6_goblins": 101,
    "fx_7_echoes": 102,
    "fx_8_sci_fi": 103,
    # Ethnic (104-111)
    "sitar": 104,
    "banjo": 105,
    "shamisen": 106,
    "koto": 107,
    "kalimba": 108,
    "bagpipe": 109,
    "fiddle": 110,
    "shanai": 111,
    # Percussive (112-119)
    "tinkle_bell": 112,
    "agogo": 113,
    "steel_drums": 114,
    "woodblock": 115,
    "taiko_drum": 116,
    "melodic_tom": 117,
    "synth_drum": 118,
    "reverse_cymbal": 119,
    # Sound Effects (120-127)
    "guitar_fret_noise": 120,
    "breath_noise": 121,
    "seashore": 122,
    "bird_tweet": 123,
    "telephone_ring": 124,
    "helicopter": 125,
    "applause": 126,
    "gunshot": 127,
}


# ============================================================================
# Scale Utilities
# ============================================================================

def get_scale_notes(key: str, mode: str) -> List[int]:
    """
    Get pitch classes for a given key and mode.

    Args:
        key: Key name (e.g., 'C', 'G', 'F#')
        mode: 'major' or 'minor'

    Returns:
        List of pitch classes (0-11) in the scale

    Example:
        >>> get_scale_notes('C', 'major')
        [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B
        >>> get_scale_notes('A', 'minor')
        [9, 11, 0, 2, 4, 5, 7]  # A B C D E F G
    """
    tonic = KEY_NAMES.index(key)

    if mode == 'major':
        intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale intervals (W-W-H-W-W-W-H)
    else:  # minor
        intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale intervals (W-H-W-W-H-W-W)

    return [(tonic + interval) % 12 for interval in intervals]


def quantize_to_scale(midi_note: int, scale_notes: List[int]) -> int:
    """
    Quantize a MIDI note to the nearest note in a given scale.

    Args:
        midi_note: Original MIDI note number [0-127]
        scale_notes: List of pitch classes in the scale [0-11]

    Returns:
        Quantized MIDI note number [0-127]

    Algorithm:
        1. Extract pitch class (midi_note % 12) and octave (midi_note // 12)
        2. Find nearest scale note (minimum chromatic distance, wraparound-aware)
        3. Reconstruct MIDI note preserving octave
        4. Handle octave boundary crossing (e.g., B to C)

    Example:
        >>> scale = get_scale_notes('C', 'major')  # [0,2,4,5,7,9,11]
        >>> quantize_to_scale(61, scale)  # C# → C or D?
        60  # C (closer by 1 semitone)
        >>> quantize_to_scale(66, scale)  # F# → F or G?
        67  # G (closer by 1 semitone)
    """
    pitch_class = midi_note % 12
    octave = midi_note // 12

    # Find nearest scale note (with wraparound handling)
    distances = [abs(pitch_class - scale_note) for scale_note in scale_notes]
    distances_wrapped = [min(d, 12 - d) for d in distances]  # Handle wraparound (e.g., B to C)

    nearest_idx = np.argmin(distances_wrapped)
    nearest_scale_note = scale_notes[nearest_idx]

    # Reconstruct MIDI note
    quantized = octave * 12 + nearest_scale_note

    # Handle octave boundary crossing
    # If distance is large (>6 semitones), we crossed an octave boundary
    if abs(quantized - midi_note) > 6:
        if quantized > midi_note:
            quantized -= 12
        else:
            quantized += 12

    return quantized
