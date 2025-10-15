"""
Streaming framework for SwiftF0.

Modules:
- config: Typed configuration for audio/inference/segmenter/MIDI.
- types: Shared dataclasses (PitchFrame, NoteEvent).
- audio: Audio sources (WAV streaming, mic source stub).
- inference: Sliding-window streaming wrapper over SwiftF0.
- notes: Realtime note segmentation state machine.
- midi: MIDI sinks (realtime port, file writer).
- pipeline: Orchestration glue.
"""

from .config import StreamConfig, SegmenterConfig, MidiConfig
from .types import PitchFrame, NoteEvent
from .audio import WavFileSource
from .inference import SwiftF0Streamer
from .notes import RealtimeNoteSegmenter
from .midi import FileMIDISink, RealtimeMIDISink
from .pipeline import StreamingPipeline
from .timbre import resolve_instrument
from .key_detection import OnlineKeyTracker
from .autotune import AutoTuneQuantizer
from .synthesis import (
    AudioSynthesizerProtocol,
    AudioSynthConfig,
    BaseAudioSink,
    FluidSynthBackend,
    RealtimeAudioSink,
)
from .soundfont_utils import (
    find_soundfonts,
    get_default_soundfont,
    list_available_soundfonts,
    resolve_soundfont_path,
)

__all__ = [
    "StreamConfig",
    "SegmenterConfig",
    "MidiConfig",
    "PitchFrame",
    "NoteEvent",
    "WavFileSource",
    "SwiftF0Streamer",
    "RealtimeNoteSegmenter",
    "FileMIDISink",
    "RealtimeMIDISink",
    "StreamingPipeline",
    "resolve_instrument",
    "OnlineKeyTracker",
    "AutoTuneQuantizer",
    "AudioSynthesizerProtocol",
    "AudioSynthConfig",
    "BaseAudioSink",
    "FluidSynthBackend",
    "RealtimeAudioSink",
    "find_soundfonts",
    "get_default_soundfont",
    "list_available_soundfonts",
    "resolve_soundfont_path",
]

