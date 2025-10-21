"""
Sounddevice-based audio streaming for real-time processing.

This module provides a simple, reliable audio I/O interface using sounddevice.
"""

import numpy as np
import sounddevice as sd
from typing import Optional, Callable
import time
import threading
from .config import get_config
from .simple_synthesizer import SimpleSynthesizer
from ..core import SwiftF0


class AudioStream:
    """
    Simple audio stream handler using sounddevice.

    This class manages audio I/O and coordinates pitch detection with synthesis.
    """

    def __init__(self, config=None):
        """
        Initialize audio stream.

        Args:
            config: RealtimeConfig object (uses default if None)
        """
        self.config = config or get_config()

        # Validate configuration
        if self.config.audio.backend != "sounddevice":
            print(f"Warning: Config specifies {self.config.audio.backend}, but using sounddevice")

        # Initialize components
        self.pitch_detector = SwiftF0(
            confidence_threshold=self.config.pitch_detection.confidence_threshold,
            fmin=self.config.pitch_detection.min_frequency,
            fmax=self.config.pitch_detection.max_frequency
        )
        self.synthesizer = SimpleSynthesizer(self.config)

        # Audio stream
        self.stream = None
        self.is_running = False

        # Processing buffer for pitch detection
        self.window_buffer = np.zeros(
            self.config.pitch_detection.window_size,
            dtype=np.float32
        )
        self.buffer_pos = 0

        # Statistics
        self.stats = {
            'frames_processed': 0,
            'current_pitch': 0.0,
            'confidence': 0.0,
            'dropouts': 0
        }

        # Callbacks
        self.pitch_callback: Optional[Callable] = None

    def start(self):
        """Start audio streaming."""
        if self.is_running:
            return

        print("Starting audio stream...")
        print(f"  Sample rate: {self.config.audio.sample_rate} Hz")
        print(f"  Chunk size: {self.config.audio.chunk_size} samples")
        print(f"  Latency: ~{self.config.latency_ms:.1f} ms")

        # Open stream
        self.stream = sd.InputStream(
            samplerate=self.config.audio.sample_rate,
            blocksize=self.config.audio.chunk_size,
            device=self.config.audio.device_in,
            channels=self.config.audio.channels,
            dtype='float32',
            callback=self._audio_callback
        )

        self.stream.start()
        self.is_running = True
        print("Audio stream started")

    def stop(self):
        """Stop audio streaming."""
        if not self.is_running:
            return

        self.is_running = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.synthesizer.cleanup()
        print("Audio stream stopped")

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Audio callback for processing.

        Args:
            indata: Input audio data
            frames: Number of frames
            time_info: Timing information
            status: Stream status
        """
        if status:
            self.stats['dropouts'] += 1

        # Get mono audio
        if indata.shape[1] > 1:
            audio = np.mean(indata, axis=1)
        else:
            audio = indata[:, 0]

        # Update sliding window buffer
        self._update_buffer(audio)

        # Check if we have enough data for pitch detection
        if self.buffer_pos >= self.config.pitch_detection.hop_size:
            # Detect pitch
            pitch_hz, confidence = self._detect_pitch()

            # Update stats
            self.stats['frames_processed'] += 1
            self.stats['current_pitch'] = pitch_hz if pitch_hz else 0.0
            self.stats['confidence'] = confidence

            # Call pitch callback if set
            if self.pitch_callback:
                self.pitch_callback(pitch_hz, confidence)

    def _update_buffer(self, audio_chunk):
        """Update sliding window buffer."""
        chunk_size = len(audio_chunk)

        # Shift buffer and add new data
        self.window_buffer = np.roll(self.window_buffer, -chunk_size)
        self.window_buffer[-chunk_size:] = audio_chunk

        self.buffer_pos += chunk_size

    def _detect_pitch(self) -> tuple:
        """
        Detect pitch from current buffer.

        Returns:
            Tuple of (pitch_hz, confidence)
        """
        try:
            # Run pitch detection
            result = self.pitch_detector.detect_from_array(
                self.window_buffer,
                self.config.audio.sample_rate
            )

            # Get most recent pitch
            if len(result.pitch_hz) > 0:
                # Get last valid frame
                idx = -1
                while idx >= -len(result.pitch_hz):
                    if result.voicing[idx]:
                        return result.pitch_hz[idx], result.confidence[idx]
                    idx -= 1

        except Exception as e:
            print(f"Pitch detection error: {e}")

        return None, 0.0

    def get_stats(self) -> dict:
        """Get current statistics."""
        return self.stats.copy()

    def set_pitch_callback(self, callback: Callable):
        """
        Set callback for pitch detection results.

        Args:
            callback: Function(pitch_hz, confidence) called on each detection
        """
        self.pitch_callback = callback


class AudioStreamWithOutput(AudioStream):
    """
    Audio stream with both input and output (for synthesis playback).

    This extends AudioStream to include real-time synthesis output.
    """

    def start(self):
        """Start audio streaming with output."""
        if self.is_running:
            return

        print("Starting audio stream with synthesis output...")
        print(f"  Sample rate: {self.config.audio.sample_rate} Hz")
        print(f"  Chunk size: {self.config.audio.chunk_size} samples")
        print(f"  Synthesis: {self.config.synthesis.method}")
        print(f"  Latency: ~{self.config.latency_ms:.1f} ms")

        # Open duplex stream (input and output)
        self.stream = sd.Stream(
            samplerate=self.config.audio.sample_rate,
            blocksize=self.config.audio.chunk_size,
            device=(self.config.audio.device_in, self.config.audio.device_out),
            channels=self.config.audio.channels,
            dtype='float32',
            callback=self._audio_callback_with_output
        )

        self.stream.start()
        self.is_running = True
        print("Audio stream started")

    def _audio_callback_with_output(self, indata, outdata, frames, time_info, status):
        """
        Audio callback with synthesis output.

        Args:
            indata: Input audio data
            outdata: Output audio buffer to fill
            frames: Number of frames
            time_info: Timing information
            status: Stream status
        """
        if status:
            self.stats['dropouts'] += 1

        # Get mono audio
        if indata.shape[1] > 1:
            audio = np.mean(indata, axis=1)
        else:
            audio = indata[:, 0]

        # Update sliding window buffer
        self._update_buffer(audio)

        # Detect pitch if enough data
        pitch_hz = None
        confidence = 0.0

        if self.buffer_pos >= self.config.pitch_detection.hop_size:
            pitch_hz, confidence = self._detect_pitch()

            # Update stats
            self.stats['frames_processed'] += 1
            self.stats['current_pitch'] = pitch_hz if pitch_hz else 0.0
            self.stats['confidence'] = confidence

            # Reset buffer position
            self.buffer_pos = 0

        # Synthesize output based on detected pitch
        if self.config.debug.bypass_synthesis:
            # Bypass mode - pass through input
            if self.config.audio.channels == 1:
                outdata[:, 0] = audio
            else:
                outdata[:] = indata
        else:
            # Generate synthesis
            synth_audio = self.synthesizer.process_pitch(
                pitch_hz,
                confidence,
                frames
            )

            # Write to output
            if self.config.audio.channels == 1:
                outdata[:, 0] = synth_audio
            else:
                # Duplicate to all channels
                for ch in range(self.config.audio.channels):
                    outdata[:, ch] = synth_audio

        # Call pitch callback if set
        if self.pitch_callback and pitch_hz is not None:
            self.pitch_callback(pitch_hz, confidence)