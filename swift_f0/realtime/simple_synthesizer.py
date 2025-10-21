"""
Simple synthesizer using soundfont or basic waveform generation.

This module provides a simple, low-latency synthesis solution
for real-time timbre transformation.
"""

import numpy as np
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
import os

# Optional: Use pyfluidsynth if available
try:
    import fluidsynth
    HAS_FLUIDSYNTH = True
except ImportError:
    fluidsynth = None  # Define as None to avoid unbound variable issues
    HAS_FLUIDSYNTH = False
    print("Note: pyfluidsynth not available. Using simple waveform synthesis.")


class SimpleSynthesizer:
    """
    Simple synthesizer for real-time audio generation.

    Uses either soundfont (if available) or basic waveform synthesis.
    """

    def __init__(self, config):
        """
        Initialize synthesizer.

        Args:
            config: RealtimeConfig object with synthesis settings
        """
        self.config = config
        self.sample_rate = config.audio.sample_rate

        # Synthesis state
        self.current_phase = 0.0
        self.current_frequency = 0.0
        self.current_amplitude = 0.0

        # Initialize soundfont if available
        self.synth = None
        self.sf_id = None

        if HAS_FLUIDSYNTH and config.synthesis.method == "soundfont":
            self._init_soundfont()

    def _init_soundfont(self):
        """Initialize FluidSynth with soundfont."""
        try:
            # Check if soundfont exists
            sf_path = self.config.soundfont_absolute_path
            if not os.path.exists(sf_path):
                print(f"Soundfont not found: {sf_path}")
                print("Falling back to simple synthesis")
                return

            # Create synthesizer
            if fluidsynth is not None:
                self.synth = fluidsynth.Synth()
                self.synth.start()
            else:
                print("FluidSynth module not available")
                self.synth = None
                return

            # Load soundfont
            self.sf_id = self.synth.sfload(sf_path)
            if self.sf_id < 0:
                print("Failed to load soundfont")
                self.synth = None
                return

            # Set initial instrument
            self.synth.program_select(
                0,  # Channel
                self.sf_id,
                0,  # Bank
                self.config.synthesis.default_instrument
            )

            print(f"Soundfont loaded: {os.path.basename(sf_path)}")

        except Exception as e:
            print(f"Error initializing soundfont: {e}")
            self.synth = None

    def synthesize(
        self,
        frequency: float,
        amplitude: float,
        n_samples: int
    ) -> np.ndarray:
        """
        Synthesize audio samples for given frequency and amplitude.

        Args:
            frequency: Fundamental frequency in Hz
            amplitude: Amplitude (0.0 to 1.0)
            n_samples: Number of samples to generate

        Returns:
            Synthesized audio samples
        """
        if self.synth is not None:
            # Use FluidSynth
            return self._synthesize_soundfont(frequency, amplitude, n_samples)
        else:
            # Use simple waveform synthesis
            return self._synthesize_simple(frequency, amplitude, n_samples)

    def _synthesize_simple(
        self,
        frequency: float,
        amplitude: float,
        n_samples: int
    ) -> np.ndarray:
        """
        Simple waveform synthesis.

        Args:
            frequency: Fundamental frequency in Hz
            amplitude: Amplitude (0.0 to 1.0)
            n_samples: Number of samples to generate

        Returns:
            Synthesized audio samples
        """
        # Generate time array
        t = np.arange(n_samples) / self.sample_rate

        # Phase increment per sample
        phase_increment = 2 * np.pi * frequency / self.sample_rate

        # Generate waveform based on type
        waveform_type = self.config.synthesis.simple_waveform
        harmonics = self.config.synthesis.simple_harmonics

        if waveform_type == "sine":
            # Pure sine wave with harmonics
            signal = np.zeros(n_samples)
            for h in range(1, harmonics + 1):
                # Add harmonics with decreasing amplitude
                harmonic_amp = amplitude / h
                harmonic_freq = frequency * h

                # Generate phase array with continuity
                phases = self.current_phase + \
                         np.cumsum(np.full(n_samples, 2 * np.pi * harmonic_freq / self.sample_rate))
                signal += harmonic_amp * np.sin(phases)

        elif waveform_type == "square":
            # Square wave
            phases = self.current_phase + np.cumsum(np.full(n_samples, phase_increment))
            signal = amplitude * np.sign(np.sin(phases))

        elif waveform_type == "sawtooth":
            # Sawtooth wave
            phases = self.current_phase + np.cumsum(np.full(n_samples, phase_increment))
            signal = amplitude * (2 * (phases / (2 * np.pi) % 1) - 1)

        else:
            # Default to sine
            phases = self.current_phase + np.cumsum(np.full(n_samples, phase_increment))
            signal = amplitude * np.sin(phases)

        # Update phase for continuity
        self.current_phase = (self.current_phase + n_samples * phase_increment) % (2 * np.pi)

        # Apply volume
        signal *= self.config.synthesis.volume

        # Smooth amplitude transitions
        if abs(amplitude - self.current_amplitude) > 0.1:
            # Create smooth envelope
            envelope = np.linspace(self.current_amplitude, amplitude, n_samples)
            signal *= envelope / amplitude if amplitude > 0 else 1

        self.current_amplitude = amplitude
        self.current_frequency = frequency

        return signal.astype(np.float32)

    def _synthesize_soundfont(
        self,
        frequency: float,
        amplitude: float,
        n_samples: int
    ) -> np.ndarray:
        """
        Synthesize using FluidSynth soundfont.

        Args:
            frequency: Fundamental frequency in Hz
            amplitude: Amplitude (0.0 to 1.0)
            n_samples: Number of samples to generate

        Returns:
            Synthesized audio samples
        """
        # Convert frequency to MIDI note
        midi_note = int(round(69 + 12 * np.log2(frequency / 440.0)))
        midi_note = max(0, min(127, midi_note))

        # Convert amplitude to velocity
        velocity = int(amplitude * 127)

        # Note on/off management
        if self.synth is not None:  # Check synth exists
            if frequency > 0 and amplitude > 0.1:
                # Turn on note
                if self.current_frequency == 0 or \
                   abs(self.current_frequency - frequency) > 1.0:
                    # New note
                    if self.current_frequency > 0:  # Avoid log of zero
                        old_midi = int(round(69 + 12 * np.log2(self.current_frequency / 440.0)))
                        self.synth.noteoff(0, old_midi)
                    self.synth.noteon(0, midi_note, velocity)
            else:
                # Turn off note
                if self.current_frequency > 0:
                    old_note = int(round(69 + 12 * np.log2(self.current_frequency / 440.0)))
                    self.synth.noteoff(0, old_note)

        # Generate samples
        # Note: This is a simplified approach
        # Real implementation would need proper FluidSynth sample generation
        samples = np.zeros(n_samples, dtype=np.float32)

        # For now, fall back to simple synthesis
        # TODO: Implement proper FluidSynth sample generation
        samples = self._synthesize_simple(frequency, amplitude, n_samples)

        self.current_frequency = frequency
        self.current_amplitude = amplitude

        return samples

    def process_pitch(
        self,
        pitch_hz: Optional[float],
        confidence: float,
        n_samples: int
    ) -> np.ndarray:
        """
        Process detected pitch and generate audio.

        Args:
            pitch_hz: Detected pitch in Hz (None if unvoiced)
            confidence: Detection confidence (0.0 to 1.0)
            n_samples: Number of samples to generate

        Returns:
            Synthesized audio samples
        """
        if pitch_hz is None or pitch_hz <= 0 or confidence < 0.5:
            # No valid pitch - generate silence or fade out
            if self.current_amplitude > 0:
                # Fade out
                self.current_amplitude *= 0.9
                return self.synthesize(
                    self.current_frequency,
                    self.current_amplitude,
                    n_samples
                )
            else:
                return np.zeros(n_samples, dtype=np.float32)

        # Valid pitch - synthesize
        amplitude = min(1.0, confidence)
        return self.synthesize(pitch_hz, amplitude, n_samples)

    def set_instrument(self, instrument: int):
        """
        Change instrument (for soundfont).

        Args:
            instrument: GM instrument number (0-127)
        """
        if self.synth is not None:
            self.synth.program_change(0, instrument)
            print(f"Changed to instrument {instrument}")

    def reset(self):
        """Reset synthesis state."""
        self.current_phase = 0.0
        self.current_frequency = 0.0
        self.current_amplitude = 0.0

        if self.synth is not None:
            # Turn off all notes
            for note in range(128):
                self.synth.noteoff(0, note)

    def cleanup(self):
        """Clean up resources."""
        if self.synth is not None:
            self.synth.delete()
            self.synth = None