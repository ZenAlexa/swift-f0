from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StreamConfig:
    sample_rate: int = 16000
    block_size: int = 256
    window_size: int = 1024
    hop_size: int = 256  # must match block_size for 1:1 frame output


@dataclass
class SegmenterConfig:
    split_threshold: float = 0.7  # in semitone
    grace_period_frames: int = 2  # 2*16ms = 32ms
    min_note_frames: int = 3      # 3*16ms = 48ms


@dataclass
class MidiConfig:
    instrument: str | int = "acoustic_grand_piano"
    velocity: int = 80
    tempo: int = 120
    virtual_port_name: str = "SwiftF0 Streaming"
    output_path: str | None = None  # if set, write to MIDI file

