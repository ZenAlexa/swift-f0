from __future__ import annotations

from dataclasses import dataclass
import logging

import numpy as np

from ..core import SwiftF0
from .types import PitchFrame

logger = logging.getLogger(__name__)


class EnergyGate:
    """
    Professional-grade RMS energy gate with hysteresis.

    Based on industry-standard implementations (EasyEffects Gate, Reaper ReaGate):
    - RMS detection (not peak) for perceptual accuracy matching human hearing
    - Dual-threshold hysteresis to prevent chattering when signal hovers near threshold
    - Hold time to ignore brief pauses in natural speech

    Industry-standard default parameters:
    - Open threshold: -40 dB (typical for voice/instrument gating)
    - Close threshold: -45 dB (5 dB hysteresis, prevents rapid on/off switching)
    - Hold time: 100-200 ms (maintains gate during natural speech pauses)
    - RMS window: 20 ms (smooths transients while preserving responsiveness)

    PHASE 1 Design Decision:
    - Gate always processes audio (even when closed) to maintain time-series consistency
    - Returns boolean state; caller decides whether to skip inference
    - Phase 2 may add adaptive skip for CPU savings after sustained silence

    Reference:
    - https://wwmm.github.io/easyeffects/gate.html
    - https://www.soundonsound.com/techniques/reagate-noise-reduction
    """

    def __init__(
        self,
        open_threshold_db: float = -40.0,  # ReaGate/EasyEffects default: -40dB
        hysteresis_db: float = 5.0,        # Industry standard: 3-6dB
        hold_time_ms: float = 150.0,       # Typical DAW: 100-200ms for voice
        sample_rate: int = 16000,
        hop_length: int = 256,
    ):
        """
        Initialize energy gate with industry-standard parameters.

        Args:
            open_threshold_db: RMS level (dB) required to open gate
                              Range: -60 to -20 dB
                              Typical: -40 dB for voice, -50 dB for quiet instruments
            hysteresis_db: Gap between open and close thresholds (dB)
                          Range: 2-10 dB
                          Larger values = more stable, but may cut off natural decay
            hold_time_ms: Minimum time gate stays open after signal drops (ms)
                         Range: 50-500 ms
                         Speech: 100-200 ms, Music: 200-500 ms
            sample_rate: Audio sample rate (Hz)
            hop_length: Number of samples per processing frame

        Microadjustment (per evaluation):
        - If too sensitive (triggers on noise): increase open_threshold_db (e.g., -35)
        - If unresponsive (misses speech): decrease open_threshold_db (e.g., -45)
        - If chattering (rapid on/off): increase hysteresis_db (e.g., 7-10)
        - If cutting off syllables: increase hold_time_ms (e.g., 200-250)
        """
        # Convert dB to linear amplitude
        self.open_threshold = 10 ** (open_threshold_db / 20.0)
        self.close_threshold = 10 ** ((open_threshold_db - hysteresis_db) / 20.0)

        # Hold time in frames
        self.hold_frames = int((hold_time_ms / 1000.0) / (hop_length / sample_rate))

        # State machine
        self.is_open = False
        self.hold_counter = 0

        # RMS smoothing window (industry: 10-30ms for voice)
        # Per evaluation: balance responsiveness vs stability
        self.rms_window_size = max(1, int(0.02 * sample_rate / hop_length))  # 20ms
        self.rms_history = []

        logger.debug(
            f"EnergyGate initialized: open={open_threshold_db:.1f}dB, "
            f"hysteresis={hysteresis_db:.1f}dB, hold={hold_time_ms:.0f}ms, "
            f"hold_frames={self.hold_frames}"
        )

    def process(self, audio_chunk: np.ndarray) -> bool:
        """
        Process audio chunk and return gate state.

        Args:
            audio_chunk: Audio samples (1D array, typically hop_length samples)

        Returns:
            True if gate is open (signal passes), False if closed (silence)

        Industry practice:
        - Use RMS (not peak) for vocal/sustained sounds (matches human perception)
        - Apply smoothing to avoid rapid switching on transients
        - Hysteresis prevents chattering when signal hovers near threshold

        PHASE 1 Note:
        - Gate processes audio even when closed (maintains time consistency)
        - Caller may skip inference when gate is closed (Phase 2 optimization)
        """
        # Calculate RMS energy (root mean square)
        rms = np.sqrt(np.mean(audio_chunk ** 2))

        # Smooth RMS over window (reduce sensitivity to single-frame spikes)
        # Industry practice: temporal averaging for stability
        self.rms_history.append(rms)
        if len(self.rms_history) > self.rms_window_size:
            self.rms_history.pop(0)
        smoothed_rms = np.mean(self.rms_history)

        # Hysteresis state machine (EasyEffects pattern)
        if not self.is_open:
            # Gate is closed: need to exceed OPEN threshold to open
            if smoothed_rms > self.open_threshold:
                self.is_open = True
                self.hold_counter = self.hold_frames
                logger.debug(f"Gate OPENED (RMS={smoothed_rms:.6f} > {self.open_threshold:.6f})")
        else:
            # Gate is open: apply hold time before closing
            if smoothed_rms < self.close_threshold:
                self.hold_counter -= 1
                if self.hold_counter <= 0:
                    self.is_open = False
                    logger.debug(f"Gate CLOSED (RMS={smoothed_rms:.6f} < {self.close_threshold:.6f})")
            else:
                # Signal above close threshold: reset hold counter
                self.hold_counter = self.hold_frames

        return self.is_open


class SwiftF0Streamer:
    """
    Sliding-window streaming wrapper around SwiftF0 with integrated energy gating.

    PHASE 1 Enhancement:
    - Integrated EnergyGate for multi-layer voice activity detection
    - Combines RMS energy gating AND model confidence (AND logic)
    - Prevents acoustic feedback by blocking low-energy signals at source

    Assumes block_size == hop_length for 1:1 frame advance. For each audio chunk,
    it outputs exactly one PitchFrame corresponding to the newest center.

    Design Decision (per evaluation):
    - Gate closed: still runs inference to maintain time consistency
    - voiced flag = gate_open AND confidence_check (multi-layer AND)
    - Phase 2 may skip inference after sustained silence for CPU savings
    """

    def __init__(
        self,
        detector: SwiftF0,
        enable_energy_gate: bool = True,
        gate_open_threshold_db: float = -40.0,
        gate_hysteresis_db: float = 5.0,
        gate_hold_time_ms: float = 150.0,
    ) -> None:
        """
        Initialize streaming wrapper with optional energy gating.

        Args:
            detector: SwiftF0 instance for pitch detection
            enable_energy_gate: Enable RMS energy gate (CRITICAL for feedback prevention)
            gate_open_threshold_db: RMS threshold to open gate (dB)
                                   Adjust based on microphone noise floor
            gate_hysteresis_db: Hysteresis gap (dB) to prevent chattering
            gate_hold_time_ms: Hold time (ms) to ignore brief pauses

        Microadjustment (per evaluation):
        - Noisy environment: increase gate_open_threshold_db to -35 or -30
        - Quiet environment: decrease to -45 or -50
        - Rapid on/off switching: increase gate_hysteresis_db to 7-10
        - Syllables cut off: increase gate_hold_time_ms to 200-250
        """
        self.detector = detector
        self.window_size = detector.FRAME_LENGTH
        self.hop = detector.HOP_LENGTH
        self.sr = detector.TARGET_SAMPLE_RATE
        self.center_offset = detector.CENTER_OFFSET
        self.buffer = np.zeros(self.window_size, dtype=np.float32)
        self.frame_index = 0

        # PHASE 1: Integrated energy gate (industry-standard noise gate)
        self.enable_energy_gate = enable_energy_gate
        self.energy_gate: EnergyGate | None = None  # Type annotation for Pylance
        if enable_energy_gate:
            self.energy_gate = EnergyGate(
                open_threshold_db=gate_open_threshold_db,
                hysteresis_db=gate_hysteresis_db,
                hold_time_ms=gate_hold_time_ms,
                sample_rate=self.sr,
                hop_length=self.hop,
            )
            logger.info(
                f"SwiftF0Streamer initialized with EnergyGate: "
                f"threshold={gate_open_threshold_db:.1f}dB, "
                f"hysteresis={gate_hysteresis_db:.1f}dB, "
                f"hold={gate_hold_time_ms:.0f}ms"
            )
        else:
            logger.warning(
                "SwiftF0Streamer initialized WITHOUT energy gate. "
                "This may cause acoustic feedback. Enable for production use."
            )

    def process_chunk(self, chunk: np.ndarray) -> PitchFrame:
        """
        Process audio chunk with multi-layer voice activity detection.

        PHASE 1 Enhancement:
        - Layer 1: RMS energy gate (blocks background noise and feedback)
        - Layer 2: SwiftF0 model confidence check
        - Layer 3: Frequency range validation
        - Final voiced decision: ALL layers must agree (AND logic)

        Industry practice (per evaluation):
        - Always run inference (even when gate closed) to maintain time consistency
        - Gate state and model output combined for robust VAD
        - Phase 2 may add adaptive inference skip for CPU savings

        Args:
            chunk: Audio samples (must be exactly hop_length samples)

        Returns:
            PitchFrame with timestamp, pitch, confidence, and voiced flag
        """
        if chunk.ndim != 1:
            chunk = chunk.reshape(-1)
        if len(chunk) != self.hop:
            raise ValueError(f"Expected chunk length {self.hop}, got {len(chunk)}")

        # PHASE 1: Layer 1 - Energy gate (CRITICAL for feedback prevention)
        gate_open = True  # Default: pass-through if gate disabled
        if self.enable_energy_gate:
            gate_open = self.energy_gate.process(chunk)

        # Slide window
        self.buffer[:-self.hop] = self.buffer[self.hop :]
        self.buffer[-self.hop :] = chunk

        # PHASE 1: Always run inference (maintain time consistency)
        # Per evaluation: gate closed doesn't skip inference (Phase 1 design)
        # Phase 2 may add adaptive skip after sustained silence
        pitch_hz, conf = self.detector.extract_pitch_and_confidence(self.buffer)

        # Extract last frame (newest prediction)
        p = float(pitch_hz[-1]) if len(pitch_hz) else 0.0
        c = float(conf[-1]) if len(conf) else 0.0

        # PHASE 1: Multi-layer voiced decision (AND logic)
        # Industry practice: combine energy gate AND model confidence
        # All conditions must be True for voiced=True:
        #   1. Energy gate open (Layer 1: RMS threshold)
        #   2. Model confidence high (Layer 2: SwiftF0 confidence)
        #   3. Frequency in valid range (Layer 3: fmin/fmax)
        voiced = bool(
            gate_open  # Layer 1: Energy gate (prevents noise/feedback)
            and (c > self.detector.confidence_threshold)  # Layer 2: Model confidence
            and (p >= self.detector.fmin)  # Layer 3: Frequency range lower bound
            and (p <= self.detector.fmax)  # Layer 3: Frequency range upper bound
        )

        # Timestamp for newest frame center
        t = (self.frame_index * self.hop + self.center_offset) / self.sr
        self.frame_index += 1

        return PitchFrame(timestamp=t, pitch_hz=p, confidence=c, voiced=voiced)

