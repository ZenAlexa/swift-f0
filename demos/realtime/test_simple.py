#!/usr/bin/env python3
"""
Simple test for real-time pitch detection and synthesis.

This is a minimal example to test the basic functionality.
"""

import sys
import time
import signal
from swift_f0.realtime import AudioStreamWithOutput, get_config


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\nStopping...")
    sys.exit(0)


def main():
    """Main test function."""
    print("SwiftF0 Real-time Test")
    print("=" * 50)

    # Load configuration
    config = get_config()
    print(f"Configuration loaded")
    print(f"  Soundfont: {config.synthesis.soundfont_path}")
    print(f"  Method: {config.synthesis.method}")
    print(f"  Sample rate: {config.audio.sample_rate} Hz")
    print(f"  Expected latency: {config.latency_ms:.1f} ms")
    print("=" * 50)

    # Validate configuration
    from swift_f0.realtime.config import ConfigManager
    manager = ConfigManager()
    if not manager.validate():
        print("Configuration validation failed!")
        return 1

    # Create audio stream
    stream = AudioStreamWithOutput(config)

    # Define pitch callback for monitoring
    def on_pitch(pitch_hz, confidence):
        if pitch_hz and confidence > 0.5:
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F',
                         'F#', 'G', 'G#', 'A', 'A#', 'B']
            midi = int(round(69 + 12 * (pitch_hz / 440)))
            note = note_names[midi % 12]
            octave = (midi // 12) - 1
            print(f"\rPitch: {pitch_hz:6.1f} Hz | Note: {note}{octave} | "
                  f"Confidence: {confidence:.2f}    ", end='', flush=True)

    # Set callback
    stream.set_pitch_callback(on_pitch)

    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Start streaming
    print("\nStarting audio stream...")
    print("Speak or sing into the microphone.")
    print("Press Ctrl+C to stop.")
    print("-" * 50)

    stream.start()

    # Keep running
    try:
        while True:
            time.sleep(1)
            stats = stream.get_stats()
            if stats['dropouts'] > 0:
                print(f"\nWarning: {stats['dropouts']} audio dropouts")

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        stream.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())