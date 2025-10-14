from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np

from .types import PitchFrame, NoteEvent


class RealtimeNoteSegmenter:
    """
    Streaming note segmentation via a simple state machine.
    States: IDLE -> TENTATIVE_START -> ACTIVE, with grace period handling for ends.
    """

    def __init__(self, split_threshold: float = 0.7, grace_period_frames: int = 2, min_note_frames: int = 3):
        self.split_threshold = split_threshold
        self.grace = grace_period_frames
        self.min_frames = min_note_frames
        self.reset()

    def reset(self) -> None:
        self.state = "IDLE"
        self.note_start_time = 0.0
        self.grace_counter = 0
        self.pitch_history: List[float] = []

    @staticmethod
    def hz_to_midi(p: float) -> float:
        if p <= 0:
            return 0.0
        return 69.0 + 12.0 * math.log2(p / 440.0)

    def median_midi(self) -> float:
        if not self.pitch_history:
            return 0.0
        return float(np.median(self.pitch_history))

    def process(self, frame: PitchFrame) -> Iterable[NoteEvent]:
        evts: List[NoteEvent] = []

        if not frame.voiced:
            if self.state in {"ACTIVE", "TENTATIVE_END"}:
                self.grace_counter += 1
                if self.grace_counter >= self.grace:
                    if self.pitch_history and len(self.pitch_history) >= self.min_frames:
                        pitch_midi = int(round(self.median_midi()))
                        evts.append(NoteEvent(type="note_off", note=pitch_midi, time=frame.timestamp))
                    self.reset()
            return evts

        midi_pitch = self.hz_to_midi(frame.pitch_hz)

        if self.state == "IDLE":
            self.state = "TENTATIVE_START"
            self.note_start_time = frame.timestamp
            self.pitch_history = [midi_pitch]
            return evts

        if self.state == "TENTATIVE_START":
            self.pitch_history.append(midi_pitch)
            if len(self.pitch_history) >= self.min_frames:
                pitch_midi = int(round(self.median_midi()))
                evts.append(NoteEvent(type="note_on", note=pitch_midi, velocity=80, time=self.note_start_time))
                self.state = "ACTIVE"
            return evts

        if self.state == "ACTIVE":
            median_midi = self.median_midi()
            if abs(midi_pitch - median_midi) >= self.split_threshold:
                old_pitch = int(round(median_midi))
                evts.append(NoteEvent(type="note_off", note=old_pitch, time=frame.timestamp))
                self.pitch_history = [midi_pitch]
                self.note_start_time = frame.timestamp
                evts.append(NoteEvent(type="note_on", note=int(round(midi_pitch)), velocity=80, time=frame.timestamp))
            else:
                self.pitch_history.append(midi_pitch)
                if len(self.pitch_history) > 32:
                    self.pitch_history.pop(0)
            self.grace_counter = 0
            return evts

        return evts

