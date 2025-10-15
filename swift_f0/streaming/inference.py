from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core import SwiftF0
from .types import PitchFrame


class SwiftF0Streamer:
    """
    Sliding-window streaming wrapper around SwiftF0.

    Assumes block_size == hop_length for 1:1 frame advance. For each audio chunk,
    it outputs exactly one PitchFrame corresponding to the newest center.
    """

    def __init__(self, detector: SwiftF0) -> None:
        self.detector = detector
        self.window_size = detector.FRAME_LENGTH
        self.hop = detector.HOP_LENGTH
        self.sr = detector.TARGET_SAMPLE_RATE
        self.center_offset = detector.CENTER_OFFSET
        self.buffer = np.zeros(self.window_size, dtype=np.float32)
        self.frame_index = 0

    def process_chunk(self, chunk: np.ndarray) -> PitchFrame:
        if chunk.ndim != 1:
            chunk = chunk.reshape(-1)
        if len(chunk) != self.hop:
            raise ValueError(f"Expected chunk length {self.hop}, got {len(chunk)}")

        # Slide window
        self.buffer[:-self.hop] = self.buffer[self.hop :]
        self.buffer[-self.hop :] = chunk

        # Run model on full window, take newest frame
        pitch_hz, conf = self.detector.extract_pitch_and_confidence(self.buffer)
        # last frame
        p = float(pitch_hz[-1]) if len(pitch_hz) else 0.0
        c = float(conf[-1]) if len(conf) else 0.0
        voiced = bool(
            (c > self.detector.confidence_threshold)
            and (p >= self.detector.fmin)
            and (p <= self.detector.fmax)
        )

        # Timestamp for newest frame center
        t = (self.frame_index * self.hop + self.center_offset) / self.sr
        self.frame_index += 1

        return PitchFrame(timestamp=t, pitch_hz=p, confidence=c, voiced=voiced)

