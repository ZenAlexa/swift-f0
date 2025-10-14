from __future__ import annotations

from .audio import BaseAudioSource
from .inference import SwiftF0Streamer
from .notes import RealtimeNoteSegmenter
from .midi import BaseMIDISink


class StreamingPipeline:
    """
    Orchestrates audio -> pitch -> note events -> MIDI sink.
    """

    def __init__(
        self,
        source: BaseAudioSource,
        streamer: SwiftF0Streamer,
        segmenter: RealtimeNoteSegmenter,
        sink: BaseMIDISink,
    ) -> None:
        self.source = source
        self.streamer = streamer
        self.segmenter = segmenter
        self.sink = sink

    def run(self) -> None:
        for chunk in self.source.frames():
            frame = self.streamer.process_chunk(chunk)
            events = list(self.segmenter.process(frame))
            if events:
                self.sink.send(events)
        self.sink.finalize()

