from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .types import NoteEvent


class BaseMIDISink:
    def send(self, events: Iterable[NoteEvent]) -> None:
        raise NotImplementedError

    def finalize(self) -> None:
        pass


class RealtimeMIDISink(BaseMIDISink):  # pragma: no cover (depends on MIDI device)
    def __init__(self, port_name: str = "SwiftF0 Streaming", instrument: int | None = None) -> None:
        import mido

        self.mido = mido
        self.port = mido.open_output(port_name, virtual=True)
        if instrument is not None:
            self.port.send(mido.Message("program_change", program=int(instrument)))

    def send(self, events: Iterable[NoteEvent]) -> None:
        for e in events:
            if e.type == "note_on":
                self.port.send(self.mido.Message("note_on", note=int(e.note), velocity=int(e.velocity), time=0))
            elif e.type == "note_off":
                self.port.send(self.mido.Message("note_off", note=int(e.note), velocity=0, time=0))

    def finalize(self) -> None:
        try:
            self.port.close()
        except Exception:
            pass


class FileMIDISink(BaseMIDISink):
    """
    Collects note_on/off events with timestamp in seconds and writes a MIDI file.
    """

    def __init__(self, output_path: str, tempo_bpm: int = 120, instrument: int | None = None) -> None:
        import mido

        self.mido = mido
        self.output_path = output_path
        self.tempo_bpm = tempo_bpm
        self.instrument = instrument
        self.events: List[NoteEvent] = []

    def send(self, events: Iterable[NoteEvent]) -> None:
        self.events.extend(list(events))

    def finalize(self) -> None:
        mido = self.mido
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("track_name", name="SwiftF0 Streaming", time=0))
        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.tempo_bpm), time=0))
        if self.instrument is not None:
            track.append(mido.Message("program_change", program=int(self.instrument), time=0))

        ticks_per_beat = 480

        def seconds_to_ticks(seconds: float) -> int:
            return int(seconds * (ticks_per_beat * self.tempo_bpm / 60))

        # Build delta times by sorting by absolute time
        events = sorted(self.events, key=lambda e: e.time)
        current_ticks = 0
        for e in events:
            t = seconds_to_ticks(e.time)
            delta = max(0, t - current_ticks)
            if e.type == "note_on":
                track.append(mido.Message("note_on", note=int(e.note), velocity=int(e.velocity), time=delta))
            elif e.type == "note_off":
                track.append(mido.Message("note_off", note=int(e.note), velocity=0, time=delta))
            current_ticks = t

        mid.save(self.output_path)

