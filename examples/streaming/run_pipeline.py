"""
Run the modular streaming pipeline on a WAV file and write a MIDI file.

This demo focuses on architecture and reusability on macOS without realtime constraints.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from swift_f0.core import SwiftF0
from swift_f0.streaming import (
    StreamConfig,
    SegmenterConfig,
    MidiConfig,
    WavFileSource,
    SwiftF0Streamer,
    RealtimeNoteSegmenter,
    FileMIDISink,
    StreamingPipeline,
    resolve_instrument,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="SwiftF0 streaming pipeline (WAV -> MIDI)")
    parser.add_argument("input", type=str, help="Path to input audio file")
    parser.add_argument("output", type=str, help="Path to output MIDI file")
    parser.add_argument("--instrument", type=str, default="acoustic_grand_piano", help="GM name or program number")
    parser.add_argument("--tempo", type=int, default=120, help="MIDI tempo BPM")
    parser.add_argument("--simulate", action="store_true", help="Simulate realtime timing while streaming WAV")
    args = parser.parse_args()

    cfg = StreamConfig()
    seg = SegmenterConfig()
    midi_cfg = MidiConfig(instrument=args.instrument, tempo=args.tempo, output_path=args.output)

    # Build components
    source = WavFileSource(path=args.input, sample_rate=cfg.sample_rate, block_size=cfg.block_size, simulate_timing=args.simulate)
    detector = SwiftF0()
    streamer = SwiftF0Streamer(detector)
    segmenter = RealtimeNoteSegmenter(split_threshold=seg.split_threshold, grace_period_frames=seg.grace_period_frames, min_note_frames=seg.min_note_frames)

    # Resolve instrument name or number to GM program number
    try:
        instrument_program = resolve_instrument(args.instrument)
    except ValueError as e:
        raise SystemExit(str(e))

    sink = FileMIDISink(output_path=args.output, tempo_bpm=midi_cfg.tempo, instrument=instrument_program)

    pipeline = StreamingPipeline(source, streamer, segmenter, sink)
    pipeline.run()
    print(f"Saved streaming MIDI to: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()

