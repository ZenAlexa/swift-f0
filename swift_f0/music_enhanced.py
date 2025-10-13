"""
Enhanced music utilities for SwiftF0 with timbre transformation and auto-tuning.

This module extends the basic MIDI export capabilities with:
- Timbre/instrument selection (128 GM sounds)
- Transpose (pitch shifting)
- Auto-tune (pitch correction)
- Key detection
- Kazoo-specific optimizations
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from .core import PitchResult
from .music import NoteSegment, segment_notes


# ============================================================================
# GM (General MIDI) Instrument Map
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


# Kazoo-friendly instruments (nasal/buzzy timbres)
KAZOO_LIKE_INSTRUMENTS = [
    "oboe",           # 68 - nasal reed
    "english_horn",   # 69 - warm nasal
    "bassoon",        # 70 - buzzy low
    "clarinet",       # 71 - woody reed
    "trumpet",        # 56 - brassy
    "muted_trumpet",  # 59 - muted brass
    "harmonica",      # 22 - similar mechanism
    "accordion",      # 21 - reed-based
    "shanai",         # 111 - double reed
]


# ============================================================================
# Key Detection (for Auto-tune)
# ============================================================================

MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def detect_key(notes: List[NoteSegment]) -> Tuple[str, str]:
    """
    Detect the key of a song using Krumhansl-Schmuckler key-finding algorithm.

    Args:
        notes: List of NoteSegment objects

    Returns:
        Tuple of (key_name, mode) where mode is 'major' or 'minor'

    Algorithm:
        1. Build pitch class histogram (12 bins for C, C#, D, ..., B)
        2. Weight by note duration
        3. Correlate with major/minor profiles
        4. Return key with highest correlation
    """
    if not notes:
        return "C", "major"

    # Build pitch class histogram weighted by duration
    pitch_class_histogram = np.zeros(12)
    for note in notes:
        duration = note.end - note.start
        pitch_class = note.pitch_midi % 12
        pitch_class_histogram[pitch_class] += duration

    # Normalize
    if pitch_class_histogram.sum() > 0:
        pitch_class_histogram /= pitch_class_histogram.sum()

    # Test all 24 keys (12 major + 12 minor)
    correlations = []

    for tonic in range(12):
        # Rotate profile to match tonic
        major_profile_rotated = np.roll(MAJOR_PROFILE, tonic)
        minor_profile_rotated = np.roll(MINOR_PROFILE, tonic)

        # Compute correlation
        major_corr = np.corrcoef(pitch_class_histogram, major_profile_rotated)[0, 1]
        minor_corr = np.corrcoef(pitch_class_histogram, minor_profile_rotated)[0, 1]

        correlations.append((KEY_NAMES[tonic], 'major', major_corr))
        correlations.append((KEY_NAMES[tonic], 'minor', minor_corr))

    # Find best match
    best = max(correlations, key=lambda x: x[2])
    return best[0], best[1]


def get_scale_notes(key: str, mode: str) -> List[int]:
    """
    Get MIDI note numbers for a given key and mode (within one octave).

    Args:
        key: Key name (e.g., 'C', 'G', 'F#')
        mode: 'major' or 'minor'

    Returns:
        List of pitch classes (0-11) in the scale
    """
    tonic = KEY_NAMES.index(key)

    if mode == 'major':
        intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale intervals
    else:  # minor
        intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale intervals

    return [(tonic + interval) % 12 for interval in intervals]


def quantize_to_scale(midi_note: int, scale_notes: List[int]) -> int:
    """
    Quantize a MIDI note to the nearest note in a given scale.

    Args:
        midi_note: Original MIDI note number
        scale_notes: List of pitch classes in the scale (0-11)

    Returns:
        Quantized MIDI note number
    """
    pitch_class = midi_note % 12
    octave = midi_note // 12

    # Find nearest scale note
    distances = [abs(pitch_class - scale_note) for scale_note in scale_notes]
    # Handle wraparound (e.g., B to C)
    distances_wrapped = [min(d, 12 - d) for d in distances]

    nearest_idx = np.argmin(distances_wrapped)
    nearest_scale_note = scale_notes[nearest_idx]

    # Reconstruct MIDI note
    quantized = octave * 12 + nearest_scale_note

    # Handle octave boundary crossing
    if abs(quantized - midi_note) > 6:
        if quantized > midi_note:
            quantized -= 12
        else:
            quantized += 12

    return quantized


# ============================================================================
# Enhanced MIDI Export
# ============================================================================

def export_to_midi_enhanced(
    notes: List[NoteSegment],
    output_path: str,
    instrument: str = "acoustic_grand_piano",
    transpose: int = 0,
    tempo: int = 120,
    velocity: int = 80,
    track_name: str = "SwiftF0 Enhanced",
    auto_tune: bool = False,
    auto_tune_strength: float = 1.0,
    pitch_range: Optional[Tuple[int, int]] = None,
) -> None:
    """
    Export note segments to MIDI file with enhanced control over timbre and tuning.

    Args:
        notes: List of NoteSegment objects
        output_path: Path to save the MIDI file
        instrument: Instrument name from GM_INSTRUMENTS dict, or integer 0-127
        transpose: Semitones to transpose (-12 to +12 recommended)
        tempo: MIDI tempo in BPM (default 120)
        velocity: MIDI note velocity 0-127 (default 80)
        track_name: Name for the MIDI track
        auto_tune: Whether to apply auto-tune (quantize to detected key)
        auto_tune_strength: Strength of auto-tune (0.0 = off, 1.0 = full)
        pitch_range: Optional (min_midi, max_midi) to clamp notes to specific range

    Raises:
        ImportError: If mido is not installed
        ValueError: For invalid parameters

    Example:
        >>> notes = segment_notes(result)
        >>> # Export as trumpet, transposed up 5 semitones
        >>> export_to_midi_enhanced(notes, "output.mid",
        ...                         instrument="trumpet",
        ...                         transpose=5)
        >>> # Export with auto-tune
        >>> export_to_midi_enhanced(notes, "autotuned.mid",
        ...                         auto_tune=True,
        ...                         auto_tune_strength=0.8)
        >>> # Export for kazoo (limited range)
        >>> export_to_midi_enhanced(notes, "kazoo.mid",
        ...                         instrument="oboe",
        ...                         pitch_range=(52, 76))  # E3-E5
    """
    # Import check
    try:
        import mido
    except ImportError:
        raise ImportError(
            "mido required for MIDI export. Install with: pip install mido"
        )

    # Validate input
    if not notes:
        raise ValueError("Cannot export empty notes list")
    if not 1 <= tempo <= 300:
        raise ValueError("Tempo must be between 1 and 300 BPM")
    if not 0 <= velocity <= 127:
        raise ValueError("Velocity must be between 0 and 127")
    if not -24 <= transpose <= 24:
        raise ValueError("Transpose should be between -24 and +24 semitones")
    if not 0.0 <= auto_tune_strength <= 1.0:
        raise ValueError("Auto-tune strength must be between 0.0 and 1.0")

    # Resolve instrument
    if isinstance(instrument, str):
        if instrument not in GM_INSTRUMENTS:
            raise ValueError(
                f"Unknown instrument '{instrument}'. "
                f"Choose from GM_INSTRUMENTS dict or use integer 0-127."
            )
        program = GM_INSTRUMENTS[instrument]
    else:
        program = int(instrument)
        if not 0 <= program <= 127:
            raise ValueError("Instrument program must be between 0 and 127")

    # Auto-tune: detect key and prepare scale
    scale_notes = None
    if auto_tune and auto_tune_strength > 0:
        key, mode = detect_key(notes)
        scale_notes = get_scale_notes(key, mode)
        print(f"Detected key: {key} {mode}")

    # Process notes
    processed_notes = []
    for note in notes:
        midi_note = note.pitch_midi

        # Apply auto-tune
        if auto_tune and scale_notes and auto_tune_strength > 0:
            quantized = quantize_to_scale(midi_note, scale_notes)
            # Blend between original and quantized based on strength
            midi_note = int(
                midi_note * (1 - auto_tune_strength) + quantized * auto_tune_strength
            )

        # Apply transpose
        midi_note += transpose

        # Apply pitch range clamping
        if pitch_range:
            min_pitch, max_pitch = pitch_range
            midi_note = max(min_pitch, min(max_pitch, midi_note))

        # Ensure valid MIDI range
        midi_note = max(0, min(127, midi_note))

        processed_notes.append((note.start, note.end, midi_note))

    # Create MIDI file
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Add track name
    track.append(mido.MetaMessage('track_name', name=track_name, time=0))

    # Set tempo
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo), time=0))

    # Set instrument (Program Change)
    track.append(mido.Message('program_change', program=program, time=0))

    # Convert notes to MIDI events
    ticks_per_beat = 480
    current_time_ticks = 0

    def seconds_to_ticks(seconds: float) -> int:
        return int(seconds * (ticks_per_beat * tempo / 60))

    for start, end, midi_note in sorted(processed_notes, key=lambda x: x[0]):
        note_start_ticks = seconds_to_ticks(start)
        note_duration_ticks = seconds_to_ticks(end - start)

        time_to_start = max(0, note_start_ticks - current_time_ticks)

        # Note on
        track.append(mido.Message(
            'note_on',
            channel=0,
            note=midi_note,
            velocity=velocity,
            time=time_to_start
        ))

        # Note off
        track.append(mido.Message(
            'note_off',
            channel=0,
            note=midi_note,
            velocity=velocity,
            time=note_duration_ticks
        ))

        current_time_ticks = note_start_ticks + note_duration_ticks

    # Save
    mid.save(output_path)
    print(f"Saved MIDI to: {output_path}")
    print(f"  Instrument: {instrument} (program {program})")
    print(f"  Transpose: {transpose:+d} semitones")
    print(f"  Tempo: {tempo} BPM")
    if auto_tune:
        print(f"  Auto-tune: {auto_tune_strength*100:.0f}% strength")


# ============================================================================
# Kazoo-specific utilities
# ============================================================================

# Typical kazoo range (approximate)
KAZOO_MIN_MIDI = 52  # E3
KAZOO_MAX_MIDI = 76  # E5


def optimize_for_kazoo(
    notes: List[NoteSegment],
    target_range: Tuple[int, int] = (KAZOO_MIN_MIDI, KAZOO_MAX_MIDI),
) -> List[NoteSegment]:
    """
    Optimize note segments for kazoo playback.

    - Transpose notes outside range into playable range
    - Merge very short notes (kazoo has slow attack)
    - Preserve pitch contour as much as possible

    Args:
        notes: Original note segments
        target_range: (min_midi, max_midi) for kazoo range

    Returns:
        Optimized note segments
    """
    if not notes:
        return []

    min_midi, max_midi = target_range
    range_center = (min_midi + max_midi) // 2

    # Calculate optimal octave shift
    median_pitch = np.median([note.pitch_midi for note in notes])
    octave_shift = round((range_center - median_pitch) / 12) * 12

    optimized = []
    for note in notes:
        shifted_midi = note.pitch_midi + octave_shift

        # Clamp to range
        while shifted_midi < min_midi:
            shifted_midi += 12
        while shifted_midi > max_midi:
            shifted_midi -= 12

        # Recalculate Hz
        shifted_hz = 440.0 * (2 ** ((shifted_midi - 69) / 12))

        optimized.append(NoteSegment(
            start=note.start,
            end=note.end,
            pitch_median=shifted_hz,
            pitch_midi=shifted_midi
        ))

    return optimized


# ============================================================================
# Batch processing utility
# ============================================================================

def create_multi_timbre_versions(
    notes: List[NoteSegment],
    output_dir: str,
    base_name: str = "output",
    instruments: Optional[List[str]] = None,
) -> List[str]:
    """
    Create multiple MIDI files with different timbres from the same note sequence.

    Args:
        notes: Note segments to export
        output_dir: Directory to save MIDI files
        base_name: Base filename (will append instrument name)
        instruments: List of instrument names (default: kazoo-like instruments)

    Returns:
        List of created file paths
    """
    import os

    if instruments is None:
        instruments = KAZOO_LIKE_INSTRUMENTS

    os.makedirs(output_dir, exist_ok=True)

    created_files = []
    for instrument in instruments:
        output_path = os.path.join(output_dir, f"{base_name}_{instrument}.mid")
        export_to_midi_enhanced(
            notes,
            output_path,
            instrument=instrument,
            track_name=f"SwiftF0 - {instrument}"
        )
        created_files.append(output_path)

    return created_files
