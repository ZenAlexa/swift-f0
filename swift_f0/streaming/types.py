from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PitchFrame:
    timestamp: float
    pitch_hz: float
    confidence: float
    voiced: bool


@dataclass
class NoteEvent:
    type: str  # "note_on" | "note_off"
    note: int
    time: float
    velocity: int = 80

