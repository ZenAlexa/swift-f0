#!/usr/bin/env python3
"""
Tutorial 01: Getting Started with SwiftF0
==========================================

This tutorial introduces the basic concepts of SwiftF0:
1. Loading the library
2. Creating a pitch detector
3. Processing audio
4. Understanding the results

Run this tutorial to learn the basics step by step.
"""

import numpy as np


def create_sample_audio():
    """Create a simple sine wave for demonstration."""
    sample_rate = 16000
    duration = 1.0  # 1 second
    frequency = 440.0  # A4 note

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * frequency * t)

    return audio, sample_rate


def tutorial():
    print("=" * 70)
    print("Tutorial 01: Getting Started with SwiftF0")
    print("=" * 70)

    # Step 1: Import the library
    print("\n📚 Step 1: Importing SwiftF0")
    print("-" * 40)
    print("from swift_f0 import SwiftF0")

    try:
        from swift_f0 import SwiftF0
        print("✓ SwiftF0 imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        print("Make sure swift-f0 is installed: pip install swift-f0")
        return

    # Step 2: Create a pitch detector
    print("\n🎯 Step 2: Creating a Pitch Detector")
    print("-" * 40)
    print("detector = SwiftF0(confidence_threshold=0.9)")

    detector = SwiftF0(confidence_threshold=0.9)
    print("✓ Detector created")
    print(f"  - Confidence threshold: {detector.confidence_threshold}")
    print(f"  - Frequency range: {detector.fmin:.1f} - {detector.fmax:.1f} Hz")
    print(f"  - Target sample rate: {detector.TARGET_SAMPLE_RATE} Hz")

    # Step 3: Process audio
    print("\n🎵 Step 3: Processing Audio")
    print("-" * 40)

    # Create sample audio
    audio, sample_rate = create_sample_audio()
    print(f"Created sample audio: 440 Hz sine wave, 1 second")

    # Detect pitch
    print("Detecting pitch...")
    result = detector.detect_from_array(audio, sample_rate)
    print("✓ Pitch detection complete")

    # Step 4: Understanding results
    print("\n📊 Step 4: Understanding the Results")
    print("-" * 40)
    print("The PitchResult object contains four arrays:")
    print()

    # 1. Timestamps
    print("1. timestamps: Time position of each frame")
    print(f"   - Shape: {result.timestamps.shape}")
    print(f"   - Range: {result.timestamps[0]:.3f} - {result.timestamps[-1]:.3f} seconds")
    print(f"   - Frame period: {result.timestamps[1] - result.timestamps[0]:.3f} seconds")

    # 2. Pitch Hz
    print("\n2. pitch_hz: Detected pitch frequency for each frame")
    print(f"   - Shape: {result.pitch_hz.shape}")
    voiced_pitches = result.pitch_hz[result.voicing]
    if len(voiced_pitches) > 0:
        print(f"   - Average: {voiced_pitches.mean():.1f} Hz (expected ~440 Hz)")
        print(f"   - Std dev: {voiced_pitches.std():.2f} Hz")

    # 3. Confidence
    print("\n3. confidence: Model confidence (0-1) for each frame")
    print(f"   - Shape: {result.confidence.shape}")
    print(f"   - Mean confidence: {result.confidence.mean():.2f}")
    print(f"   - Max confidence: {result.confidence.max():.2f}")

    # 4. Voicing
    print("\n4. voicing: Boolean array indicating voiced frames")
    print(f"   - Shape: {result.voicing.shape}")
    print(f"   - Voiced frames: {result.voicing.sum()} / {len(result.voicing)}")
    voicing_rate = result.voicing.sum() / len(result.voicing) * 100
    print(f"   - Voicing rate: {voicing_rate:.1f}%")

    # Example: Access specific frame
    print("\n📍 Example: Accessing Frame Data")
    print("-" * 40)
    frame_idx = len(result.timestamps) // 2  # Middle frame
    print(f"Frame {frame_idx} (middle of audio):")
    print(f"  - Time: {result.timestamps[frame_idx]:.3f} seconds")
    print(f"  - Pitch: {result.pitch_hz[frame_idx]:.1f} Hz")
    print(f"  - Confidence: {result.confidence[frame_idx]:.2f}")
    print(f"  - Is voiced: {result.voicing[frame_idx]}")

    # Key concepts
    print("\n💡 Key Concepts")
    print("-" * 40)
    print("• Frames: Audio is processed in small time windows (frames)")
    print("• Voicing: Determines if a frame contains pitched sound")
    print("• Confidence: How certain the model is about the pitch")
    print("• Pitch: The fundamental frequency in Hz")

    print("\n✅ Tutorial Complete!")
    print("Next: Run 02_note_segmentation.py to learn about converting pitch to notes")


if __name__ == "__main__":
    tutorial()