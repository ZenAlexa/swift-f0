#!/usr/bin/env python3
"""
Simple test using basic sine wave synthesis.

This bypasses soundfont complexity for initial testing.
"""

import sys
import os
import time
import numpy as np

# Add project to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import sounddevice as sd
from swift_f0.core import SwiftF0


class SimplePitchToSine:
    """Simple pitch detection to sine wave conversion."""

    def __init__(self, sample_rate=16000, chunk_size=256):
        """Initialize with basic settings."""
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

        # Pitch detector
        self.detector = SwiftF0(confidence_threshold=0.8)

        # Buffer for pitch detection
        self.window_size = 1024
        self.window_buffer = np.zeros(self.window_size, dtype=np.float32)

        # Synthesis state
        self.phase = 0.0
        self.current_freq = 0.0
        self.current_amp = 0.0

        # Stats
        self.pitch_detected = False

    def audio_callback(self, indata, outdata, frames, time_info, status):
        """Process audio in real-time."""
        if status:
            print(f"Status: {status}")

        # Get mono input
        if indata.shape[1] > 1:
            audio_in = np.mean(indata, axis=1)
        else:
            audio_in = indata[:, 0]

        # Update buffer
        self.window_buffer = np.roll(self.window_buffer, -frames)
        self.window_buffer[-frames:] = audio_in

        # Detect pitch
        try:
            result = self.detector.detect_from_array(
                self.window_buffer,
                self.sample_rate
            )

            # Get last voiced frame
            if len(result.pitch_hz) > 0 and np.any(result.voicing):
                voiced_indices = np.where(result.voicing)[0]
                if len(voiced_indices) > 0:
                    idx = voiced_indices[-1]
                    pitch_hz = result.pitch_hz[idx]
                    confidence = result.confidence[idx]

                    if confidence > 0.7:
                        self.current_freq = pitch_hz
                        self.current_amp = confidence * 0.3  # Reduce volume
                        self.pitch_detected = True

                        # Print pitch info
                        midi = int(round(69 + 12 * np.log2(pitch_hz / 440)))
                        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                        note = note_names[midi % 12]
                        octave = (midi // 12) - 1
                        print(f"\rPitch: {pitch_hz:6.1f} Hz | Note: {note}{octave} | Conf: {confidence:.2f}    ",
                              end='', flush=True)
                    else:
                        # Fade out
                        self.current_amp *= 0.95
                else:
                    # No voiced frames - fade out
                    self.current_amp *= 0.95
            else:
                # No pitch detected - fade out
                self.current_amp *= 0.95

        except Exception as e:
            print(f"\nError in pitch detection: {e}")
            self.current_amp = 0

        # Generate output sine wave
        if self.current_freq > 0 and self.current_amp > 0.01:
            # Generate sine wave
            phase_increment = 2 * np.pi * self.current_freq / self.sample_rate
            phases = self.phase + np.arange(frames) * phase_increment
            audio_out = self.current_amp * np.sin(phases)

            # Update phase for continuity
            self.phase = (self.phase + frames * phase_increment) % (2 * np.pi)
        else:
            # Silence
            audio_out = np.zeros(frames)

        # Write to output
        if outdata.shape[1] == 1:
            outdata[:, 0] = audio_out
        else:
            # Stereo - duplicate to both channels
            outdata[:, 0] = audio_out
            outdata[:, 1] = audio_out

    def run(self):
        """Run the real-time processor."""
        print("Simple Pitch-to-Sine Test")
        print("=" * 50)
        print(f"Sample rate: {self.sample_rate} Hz")
        print(f"Chunk size: {self.chunk_size} samples")
        print("=" * 50)
        print("\nSpeak or sing into the microphone.")
        print("You should hear a sine wave at the detected pitch.")
        print("Press Ctrl+C to stop.\n")

        # Open stream
        with sd.Stream(
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            channels=(1, 2),  # Mono in, stereo out
            dtype='float32',
            callback=self.audio_callback
        ):
            # Keep running
            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n\nStopping...")

        print("Done!")


def main():
    """Main entry point."""
    # Check for sounddevice
    try:
        import sounddevice as sd
        print(f"Using sounddevice version: {sd.__version__}")

        # List devices
        print("\nAvailable audio devices:")
        print("-" * 50)
        devices = sd.query_devices()
        default_in = sd.default.device[0]
        default_out = sd.default.device[1]

        for i, dev in enumerate(devices):
            marker = ""
            if i == default_in:
                marker += "[DEFAULT IN]"
            if i == default_out:
                marker += "[DEFAULT OUT]"
            print(f"{i:2d}: {dev['name'][:30]:30s} (in:{dev['max_input_channels']}, out:{dev['max_output_channels']}) {marker}")
        print("-" * 50)
        print()

    except ImportError:
        print("Error: sounddevice not installed")
        print("Install with: pip install sounddevice")
        return 1

    # Run the processor
    processor = SimplePitchToSine()
    processor.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())