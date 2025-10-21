#!/usr/bin/env python3
"""
Note Segmentation Example
=========================

This example shows how to convert continuous pitch contours into discrete musical notes.
It detects pitch from an audio file and segments it into individual notes with timing information.

Usage:
    python note_segmentation_example.py <audio_file>
"""

import sys
from swift_f0 import SwiftF0, segment_notes


def note_name_from_midi(midi_number):
    """Convert MIDI note number to note name (e.g., 60 -> C4)."""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_number // 12) - 1
    note = note_names[midi_number % 12]
    return f"{note}{octave}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python note_segmentation_example.py <audio_file>")
        print("Example: python note_segmentation_example.py melody.wav")
        sys.exit(1)

    audio_file = sys.argv[1]

    print(f"Processing: {audio_file}")
    print("=" * 60)

    try:
        # Step 1: Detect pitch
        detector = SwiftF0(confidence_threshold=0.9)
        pitch_result = detector.detect_from_file(audio_file)
        print("✓ Pitch detection complete")

        # Step 2: Segment into notes
        notes = segment_notes(
            pitch_result,
            split_semitone_threshold=0.8,  # Split when pitch changes by 0.8 semitones
            min_note_duration=0.05,         # Minimum note duration of 50ms
            unvoiced_grace_period=0.02      # Allow 20ms gaps within notes
        )
        print(f"✓ Found {len(notes)} note segments")

        # Step 3: Display detected notes
        if notes:
            print("\nDetected Notes:")
            print("-" * 60)
            print(f"{'#':<3} {'Note':<6} {'MIDI':<5} {'Pitch (Hz)':<10} {'Start (s)':<10} {'Duration (s)':<12}")
            print("-" * 60)

            for i, note in enumerate(notes, 1):
                note_name = note_name_from_midi(note.pitch_midi)
                duration = note.end - note.start
                print(f"{i:<3} {note_name:<6} {note.pitch_midi:<5} "
                      f"{note.pitch_median:<10.1f} {note.start:<10.3f} {duration:<12.3f}")

            # Summary statistics
            print("\nSummary:")
            print("-" * 60)
            total_duration = sum(note.end - note.start for note in notes)
            avg_duration = total_duration / len(notes)
            pitch_range_midi = max(note.pitch_midi for note in notes) - min(note.pitch_midi for note in notes)

            print(f"Total notes: {len(notes)}")
            print(f"Total duration: {total_duration:.2f} seconds")
            print(f"Average note duration: {avg_duration:.3f} seconds")
            print(f"Pitch range: {pitch_range_midi} semitones")

            # Find most common note
            from collections import Counter
            note_counts = Counter(note.pitch_midi for note in notes)
            most_common_midi, count = note_counts.most_common(1)[0]
            print(f"Most frequent note: {note_name_from_midi(most_common_midi)} (appears {count} times)")
        else:
            print("No notes detected in the audio.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()