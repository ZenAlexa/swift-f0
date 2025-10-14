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
    OnlineKeyTracker,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="SwiftF0 streaming pipeline (WAV -> MIDI)")
    parser.add_argument("input", type=str, help="Path to input audio file")
    parser.add_argument("output", type=str, help="Path to output MIDI file")
    parser.add_argument("--instrument", type=str, default="acoustic_grand_piano", help="GM name or program number")
    parser.add_argument("--tempo", type=int, default=120, help="MIDI tempo BPM")
    parser.add_argument("--simulate", action="store_true", help="Simulate realtime timing while streaming WAV")
    parser.add_argument("--print-key", action="store_true", help="Print detected key signature during streaming")
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

    # Optional: Initialize key tracker
    key_tracker = None
    if args.print_key:
        key_tracker = OnlineKeyTracker(window_seconds=10.0, step_seconds=2.0)
        print("Key detection enabled (10s window, 2s update interval)")

    # Run pipeline with optional key tracking
    last_key_print_time = 0.0
    for chunk in source.frames():
        frame = streamer.process_chunk(chunk)
        events = list(segmenter.process(frame))

        # Update key tracker if enabled
        if key_tracker:
            if events:
                key_tracker.update(events)

            # Print key periodically (throttle by step_seconds)
            if frame.timestamp - last_key_print_time >= key_tracker.step_seconds:
                key_name, mode, correlation = key_tracker.current_key()
                print(f"[{frame.timestamp:.1f}s] Key: {key_name} {mode} (corr={correlation:.3f})")
                last_key_print_time = frame.timestamp

        # Send to MIDI sink
        if events:
            sink.send(events)

    sink.finalize()
    print(f"Saved streaming MIDI to: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()

