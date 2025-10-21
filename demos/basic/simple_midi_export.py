#!/usr/bin/env python3
"""
Simple MIDI Export Example
==========================

This example demonstrates converting an audio file to MIDI format.
It performs pitch detection, note segmentation, and exports the result as a MIDI file.

Usage:
    python simple_midi_export.py <input_audio> [output_midi]
"""

import sys
import os
from swift_f0 import SwiftF0, segment_notes, export_to_midi


def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_midi_export.py <input_audio> [output_midi]")
        print("Example: python simple_midi_export.py song.wav song.mid")
        sys.exit(1)

    input_audio = sys.argv[1]

    # Determine output filename
    if len(sys.argv) >= 3:
        output_midi = sys.argv[2]
    else:
        base_name = os.path.splitext(os.path.basename(input_audio))[0]
        output_midi = f"{base_name}.mid"

    print(f"Converting audio to MIDI...")
    print(f"Input:  {input_audio}")
    print(f"Output: {output_midi}")
    print("-" * 50)

    try:
        # Step 1: Detect pitch from audio
        print("1. Detecting pitch...")
        detector = SwiftF0(confidence_threshold=0.9)
        pitch_result = detector.detect_from_file(input_audio)
        print(f"   ✓ Detected {len(pitch_result.timestamps)} frames")

        # Step 2: Segment into musical notes
        print("2. Segmenting notes...")
        notes = segment_notes(
            pitch_result,
            split_semitone_threshold=0.8,
            min_note_duration=0.05
        )
        print(f"   ✓ Found {len(notes)} notes")

        if not notes:
            print("   ⚠ No notes detected. The audio may be too quiet or non-musical.")
            sys.exit(1)

        # Step 3: Export to MIDI
        print("3. Exporting MIDI...")
        export_to_midi(
            notes,
            output_midi,
            tempo=120,  # 120 BPM
            velocity=80  # Medium velocity
        )
        print(f"   ✓ MIDI file saved: {output_midi}")

        # Display summary
        print("\nConversion Summary:")
        print("-" * 50)

        # Calculate statistics
        total_duration = notes[-1].end if notes else 0
        note_count = len(notes)

        print(f"Duration: {total_duration:.2f} seconds")
        print(f"Notes: {note_count}")
        print(f"Tempo: 120 BPM")

        # Show pitch range
        if notes:
            min_pitch = min(note.pitch_midi for note in notes)
            max_pitch = max(note.pitch_midi for note in notes)
            print(f"Pitch range: MIDI {min_pitch}-{max_pitch}")

        print("\n✓ Conversion complete!")
        print(f"You can now open '{output_midi}' in any MIDI player or DAW.")

    except FileNotFoundError:
        print(f"Error: File not found: {input_audio}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()