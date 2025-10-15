#!/usr/bin/env python3
"""
Quick test script to verify timbre transformation functionality.

This creates a synthetic audio test case and demonstrates all features.
All test files are organized in the test_data/ directory structure.
"""

import os
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Define test data paths
TEST_DATA_ROOT = Path(__file__).parent.parent / "test_data"
TEST_INPUTS_DIR = TEST_DATA_ROOT / "inputs"
TEST_OUTPUTS_DIR = TEST_DATA_ROOT / "outputs"
TEST_MIDI_DIR = TEST_OUTPUTS_DIR / "midi"
TEST_AUDIO_DIR = TEST_OUTPUTS_DIR / "audio"
TEST_PLOTS_DIR = TEST_OUTPUTS_DIR / "plots"
TEST_BATCH_DIR = TEST_DATA_ROOT / "batch_outputs"

# Ensure directories exist
for directory in [TEST_INPUTS_DIR, TEST_MIDI_DIR, TEST_AUDIO_DIR, TEST_PLOTS_DIR, TEST_BATCH_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def create_test_audio(output_path=None, duration=3.0, sample_rate=16000):
    """Create a simple test audio with a melody."""
    if output_path is None:
        output_path = TEST_INPUTS_DIR / "test_audio.wav"
    else:
        output_path = Path(output_path)

    print("Creating test audio...")

    # Simple melody: C4, E4, G4, C5 (major chord arpeggio)
    notes_hz = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
    note_duration = duration / len(notes_hz)

    audio = []
    for freq in notes_hz:
        t = np.linspace(0, note_duration, int(sample_rate * note_duration))
        # Add harmonics for richer tone
        note = (
            0.5 * np.sin(2 * np.pi * freq * t) +
            0.3 * np.sin(2 * np.pi * 2 * freq * t) +
            0.2 * np.sin(2 * np.pi * 3 * freq * t)
        )
        # Simple envelope (fade in/out)
        envelope = np.ones_like(note)
        fade_samples = int(0.01 * sample_rate)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        note *= envelope

        audio.extend(note)

    audio = np.array(audio, dtype=np.float32)

    # Normalize
    audio = audio / np.max(np.abs(audio))

    # Save as WAV
    try:
        import scipy.io.wavfile as wav
        wav.write(str(output_path), sample_rate, audio)
        print(f"✓ Created test audio: {output_path}")
        return output_path
    except ImportError:
        print("scipy not available, trying soundfile...")
        try:
            import soundfile as sf
            sf.write(str(output_path), audio, sample_rate)
            print(f"✓ Created test audio: {output_path}")
            return output_path
        except ImportError:
            print("Could not save audio (need scipy or soundfile)")
            return None


def test_basic_functionality():
    """Test basic timbre transformation."""
    print("\n" + "=" * 70)
    print("Testing SwiftF0 Timbre Transformation")
    print("=" * 70)
    print(f"Test data root: {TEST_DATA_ROOT}")
    print(f"  - Inputs: {TEST_INPUTS_DIR}")
    print(f"  - Outputs: {TEST_OUTPUTS_DIR}")
    print("=" * 70)

    # Create test audio
    test_audio_path = create_test_audio()
    if test_audio_path is None:
        print("\nSkipping tests - could not create test audio")
        return

    print("\n[Test 1] Basic pitch detection and MIDI export")
    print("-" * 70)

    try:
        from swift_f0 import SwiftF0, segment_notes
        from swift_f0.music_enhanced import export_to_midi_enhanced

        # Detect pitch
        detector = SwiftF0()
        result = detector.detect_from_file(str(test_audio_path))
        print(f"✓ Detected {len(result.timestamps)} frames")

        # Segment notes
        notes = segment_notes(result)
        print(f"✓ Segmented into {len(notes)} notes")

        # Export with different timbres
        print("\n[Test 2] Exporting with different timbres...")
        print("-" * 70)

        test_instruments = ["acoustic_grand_piano", "trumpet", "flute", "oboe"]

        for instrument in test_instruments:
            output_file = TEST_MIDI_DIR / f"test_output_{instrument}.mid"
            export_to_midi_enhanced(
                notes,
                str(output_file),
                instrument=instrument,
                track_name=f"Test - {instrument}"
            )
            print(f"✓ Exported: {output_file.name}")

        print("\n[Test 3] Testing transposition...")
        print("-" * 70)

        for transpose in [-5, 0, 5]:
            output_file = TEST_MIDI_DIR / f"test_transpose_{transpose:+d}.mid"
            export_to_midi_enhanced(
                notes,
                str(output_file),
                instrument="acoustic_grand_piano",
                transpose=transpose,
                track_name=f"Transpose {transpose:+d}"
            )
            print(f"✓ Exported with transpose {transpose:+d}: {output_file.name}")

        print("\n[Test 4] Testing auto-tune...")
        print("-" * 70)

        from swift_f0.music_enhanced import detect_key

        key, mode = detect_key(notes)
        print(f"✓ Detected key: {key} {mode}")

        output_file = TEST_MIDI_DIR / "test_autotuned.mid"
        export_to_midi_enhanced(
            notes,
            str(output_file),
            instrument="acoustic_grand_piano",
            auto_tune=True,
            auto_tune_strength=1.0,
            track_name="Auto-tuned"
        )
        print(f"✓ Exported auto-tuned: {output_file.name}")

        print("\n[Test 5] Testing kazoo optimization...")
        print("-" * 70)

        from swift_f0.music_enhanced import optimize_for_kazoo

        kazoo_notes = optimize_for_kazoo(notes)
        print(f"✓ Optimized {len(kazoo_notes)} notes for kazoo range")

        output_file = TEST_MIDI_DIR / "test_kazoo.mid"
        export_to_midi_enhanced(
            kazoo_notes,
            str(output_file),
            instrument="oboe",
            pitch_range=(52, 76),
            track_name="Kazoo Optimized"
        )
        print(f"✓ Exported kazoo version: {output_file.name}")

        print("\n[Test 6] Testing batch processing...")
        print("-" * 70)

        from swift_f0.music_enhanced import create_multi_timbre_versions

        created = create_multi_timbre_versions(
            notes,
            output_dir=str(TEST_BATCH_DIR),
            base_name="test_melody"
        )
        print(f"✓ Created {len(created)} MIDI files in {TEST_BATCH_DIR.name}/")

        print("\n" + "=" * 70)
        print("All tests passed!")
        print("=" * 70)

        print("\nGenerated files in test_data/:")
        print(f"  - inputs/test_audio.wav (test input)")
        print(f"  - outputs/midi/test_output_*.mid (various timbres)")
        print(f"  - outputs/midi/test_transpose_*.mid (transposition)")
        print(f"  - outputs/midi/test_autotuned.mid (auto-tune)")
        print(f"  - outputs/midi/test_kazoo.mid (kazoo-optimized)")
        print(f"  - batch_outputs/ (batch processing)")

        print("\nYou can play these MIDI files with any MIDI player!")
        print(f"\nAll test data is organized in: {TEST_DATA_ROOT.relative_to(Path.cwd())}")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_basic_functionality()
