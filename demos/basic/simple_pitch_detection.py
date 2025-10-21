#!/usr/bin/env python3
"""
Basic Pitch Detection Example
==============================

This example demonstrates the fundamental pitch detection capability of SwiftF0.
It loads an audio file and outputs the detected pitch frequencies and confidence scores.

Usage:
    python simple_pitch_detection.py <audio_file>
"""

import sys
import numpy as np
from swift_f0 import SwiftF0


def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_pitch_detection.py <audio_file>")
        print("Example: python simple_pitch_detection.py song.wav")
        sys.exit(1)

    audio_file = sys.argv[1]

    # Initialize the pitch detector with default settings
    detector = SwiftF0(confidence_threshold=0.9)

    print(f"Detecting pitch from: {audio_file}")
    print("-" * 50)

    try:
        # Detect pitch from audio file
        result = detector.detect_from_file(audio_file)

        # Display summary statistics
        voiced_frames = np.sum(result.voicing)
        total_frames = len(result.voicing)
        voicing_rate = voiced_frames / total_frames * 100 if total_frames > 0 else 0

        print(f"Total frames: {total_frames}")
        print(f"Voiced frames: {voiced_frames} ({voicing_rate:.1f}%)")

        if voiced_frames > 0:
            voiced_pitches = result.pitch_hz[result.voicing]
            print(f"Pitch range: {voiced_pitches.min():.1f} Hz - {voiced_pitches.max():.1f} Hz")
            print(f"Average pitch: {voiced_pitches.mean():.1f} Hz")
            print(f"Median pitch: {np.median(voiced_pitches):.1f} Hz")

            # Show first few detected pitches
            print("\nFirst 10 voiced pitches:")
            for i, (pitch, conf, time) in enumerate(zip(
                voiced_pitches[:10],
                result.confidence[result.voicing][:10],
                result.timestamps[result.voicing][:10]
            )):
                print(f"  {time:.3f}s: {pitch:.1f} Hz (confidence: {conf:.2f})")
        else:
            print("No voiced segments detected in the audio.")

    except Exception as e:
        print(f"Error processing audio: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()