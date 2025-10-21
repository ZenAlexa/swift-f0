#!/usr/bin/env python3
"""
Advanced CLI Tool: Timbre Transformation and Auto-Tuning
=========================================================

A comprehensive command-line interface for audio transformation using SwiftF0.

Features:
1. Timbre transformation - Change to any of 128 GM instruments
2. Transposition - Shift pitch up or down by semitones
3. Auto-tuning - Automatic pitch correction to detected musical key
4. Kazoo optimization - Optimize for kazoo-like instruments with range limiting
5. Batch processing - Generate multiple timbre versions simultaneously

Usage Examples:
    python timbre_transform_cli.py input_audio.wav
    python timbre_transform_cli.py input_audio.wav --instrument trumpet --transpose 5
    python timbre_transform_cli.py input_audio.wav --auto-tune --strength 0.8
    python timbre_transform_cli.py input_audio.wav --kazoo
    python timbre_transform_cli.py input_audio.wav --batch
"""

import argparse
import os
from swift_f0 import SwiftF0, segment_notes
from swift_f0.music_enhanced import (
    export_to_midi_enhanced,
    optimize_for_kazoo,
    create_multi_timbre_versions,
    GM_INSTRUMENTS,
    KAZOO_LIKE_INSTRUMENTS,
)


def main():
    parser = argparse.ArgumentParser(
        description="Transform audio to MIDI with timbre and pitch control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion (default piano)
  python demo_timbre_transform.py song.wav

  # Change instrument to trumpet
  python demo_timbre_transform.py song.wav -i trumpet

  # Transpose up 5 semitones (change key)
  python demo_timbre_transform.py song.wav -t 5

  # Auto-tune to detected key
  python demo_timbre_transform.py song.wav --auto-tune

  # Optimize for kazoo (limited range)
  python demo_timbre_transform.py song.wav --kazoo

  # Create multiple versions with different timbres
  python demo_timbre_transform.py song.wav --batch

Available instruments:
  Piano: acoustic_grand_piano, electric_piano_1, honky_tonk_piano
  Strings: violin, cello, pizzicato_strings
  Brass: trumpet, trombone, french_horn
  Woodwinds: flute, clarinet, oboe, saxophone (alto/tenor/soprano)
  Synth: synth_bass_1, lead_1_square, pad_2_warm
  Kazoo-like: oboe, trumpet, harmonica, accordion
  ... and 100+ more! See GM_INSTRUMENTS in music_enhanced.py
        """
    )

    # Required arguments
    parser.add_argument('input_audio', help='Input audio file (WAV, MP3, FLAC, etc.)')

    # Output options
    parser.add_argument('-o', '--output', help='Output MIDI file path (default: input_name.mid)')

    # Timbre options
    parser.add_argument(
        '-i', '--instrument',
        default='acoustic_grand_piano',
        help='GM instrument name (default: acoustic_grand_piano)'
    )

    # Pitch options
    parser.add_argument(
        '-t', '--transpose',
        type=int,
        default=0,
        help='Transpose by N semitones (default: 0, range: -12 to +12)'
    )

    # Auto-tune options
    parser.add_argument(
        '--auto-tune',
        action='store_true',
        help='Enable auto-tune (quantize to detected key)'
    )
    parser.add_argument(
        '--strength',
        type=float,
        default=1.0,
        help='Auto-tune strength (0.0-1.0, default: 1.0)'
    )

    # Kazoo options
    parser.add_argument(
        '--kazoo',
        action='store_true',
        help='Optimize for kazoo (limit range to E3-E5, use kazoo-like timbre)'
    )

    # Batch processing
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Create multiple versions with different kazoo-like timbres'
    )

    # Detection parameters
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.8,
        help='Note split threshold in semitones (default: 0.8)'
    )
    parser.add_argument(
        '--min-duration',
        type=float,
        default=0.05,
        help='Minimum note duration in seconds (default: 0.05)'
    )

    # Tempo
    parser.add_argument(
        '--tempo',
        type=int,
        default=120,
        help='MIDI tempo in BPM (default: 120)'
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_audio):
        print(f"Error: Input file not found: {args.input_audio}")
        return 1

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        base_name = os.path.splitext(os.path.basename(args.input_audio))[0]
        output_path = f"{base_name}_output.mid"

    print("=" * 70)
    print("SwiftF0 Timbre Transformation Demo")
    print("=" * 70)
    print(f"\nInput: {args.input_audio}")

    # Step 1: Pitch detection
    print("\n[1/3] Detecting pitch...")
    detector = SwiftF0(confidence_threshold=0.9)
    result = detector.detect_from_file(args.input_audio)
    print(f"  ✓ Detected {len(result.timestamps)} frames")
    print(f"  ✓ Duration: {result.timestamps[-1]:.2f} seconds")

    # Step 2: Note segmentation
    print("\n[2/3] Segmenting notes...")
    notes = segment_notes(
        result,
        split_semitone_threshold=args.threshold,
        min_note_duration=args.min_duration,
    )
    print(f"  ✓ Found {len(notes)} note segments")

    if not notes:
        print("\nError: No notes detected. Try adjusting --threshold or --min-duration.")
        return 1

    # Show note statistics
    durations = [note.end - note.start for note in notes]
    pitches = [note.pitch_midi for note in notes]
    print(f"  ✓ Pitch range: MIDI {min(pitches)} - {max(pitches)} "
          f"({min([note.pitch_median for note in notes]):.1f} - "
          f"{max([note.pitch_median for note in notes]):.1f} Hz)")
    print(f"  ✓ Note duration: {min(durations):.3f} - {max(durations):.3f} seconds")

    # Step 3: MIDI export with transformations
    print("\n[3/3] Exporting MIDI...")

    if args.batch:
        # Batch mode: create multiple timbres
        output_dir = os.path.splitext(output_path)[0] + "_batch"
        print(f"  Mode: Batch processing")
        print(f"  Output directory: {output_dir}")

        created_files = create_multi_timbre_versions(
            notes,
            output_dir,
            base_name=os.path.splitext(os.path.basename(output_path))[0],
        )
        print(f"  ✓ Created {len(created_files)} MIDI files:")
        for file in created_files:
            print(f"    - {os.path.basename(file)}")

    else:
        # Single file mode
        instrument = args.instrument
        transpose = args.transpose
        pitch_range = None

        # Kazoo mode overrides
        if args.kazoo:
            print(f"  Mode: Kazoo optimization")
            notes = optimize_for_kazoo(notes)
            if instrument == 'acoustic_grand_piano':  # If user didn't specify
                instrument = 'oboe'  # Default kazoo-like timbre
            pitch_range = (52, 76)  # E3-E5
            print(f"  ✓ Optimized for kazoo range (E3-E5)")

        # Validate instrument
        if instrument not in GM_INSTRUMENTS:
            print(f"\nError: Unknown instrument '{instrument}'")
            print(f"Available instruments: {', '.join(sorted(GM_INSTRUMENTS.keys())[:10])}...")
            return 1

        print(f"  Instrument: {instrument} (GM #{GM_INSTRUMENTS[instrument]})")
        print(f"  Transpose: {transpose:+d} semitones")
        print(f"  Tempo: {args.tempo} BPM")
        if args.auto_tune:
            print(f"  Auto-tune: {args.strength*100:.0f}% strength")

        # Export
        export_to_midi_enhanced(
            notes,
            output_path,
            instrument=instrument,
            transpose=transpose,
            tempo=args.tempo,
            auto_tune=args.auto_tune,
            auto_tune_strength=args.strength,
            pitch_range=pitch_range,
        )

        print(f"\n✓ Success! Saved to: {output_path}")

    print("\n" + "=" * 70)
    print("Done! You can play the MIDI file with:")
    print("  - macOS: GarageBand, Logic Pro, or QuickTime")
    print("  - Windows: Windows Media Player, FL Studio")
    print("  - Linux: TiMidity++, MuseScore")
    print("  - Online: https://onlinesequencer.net (drag & drop)")
    print("=" * 70)

    return 0


if __name__ == '__main__':
    exit(main())
