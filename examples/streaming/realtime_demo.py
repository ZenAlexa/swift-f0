"""
SwiftF0 streaming prototype combining audio capture, ONNX inference,
incremental note segmentation, and realtime MIDI output.

This script is intended for desktop prototyping; it uses queues to decouple
audio capture from inference and post-processing threads. Replace the placeholder
model path if `model_int8.onnx` is available.
"""

from __future__ import annotations

import math
import queue
import signal
import threading
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

import numpy as np
import sounddevice as sd

from swift_f0.core import PitchResult, SwiftF0

try:
    import mido
    import rtmidi  # noqa: F401  # Ensures python-rtmidi backend is available
except ImportError:  # pragma: no cover - optional dependency
    mido = None


SAMPLE_RATE = 16000
BLOCK_SIZE = 256
WINDOW_SIZE = 1024
CONFIDENCE_THRESHOLD = 0.9
SPLIT_THRESHOLD = 0.7
GRACE_PERIOD_FRAMES = 2  # 2 * 16ms = 32ms


class SlidingWindow:
    """Maintains a fixed-length sliding window over incoming audio samples."""

    def __init__(self, window_size: int, hop_size: int) -> None:
        self.window_size = window_size
        self.hop_size = hop_size
        self.buffer = np.zeros(window_size, dtype=np.float32)

    def update(self, chunk: np.ndarray) -> np.ndarray:
        if len(chunk) != self.hop_size:
            raise ValueError(f"Expected chunk of {self.hop_size} samples, got {len(chunk)}")
        self.buffer[:-self.hop_size] = self.buffer[self.hop_size:]
        self.buffer[-self.hop_size :] = chunk
        return self.buffer


@dataclass
class PitchFrame:
    timestamp: float
    pitch_hz: float
    confidence: float
    is_voiced: bool


class RealtimeNoteSegmenter:
    """Simple state machine for streaming note segmentation."""

    def __init__(
        self,
        split_threshold: float,
        grace_frames: int,
        min_frames: int = 3,
    ) -> None:
        self.split_threshold = split_threshold
        self.grace_frames = grace_frames
        self.min_frames = min_frames
        self.reset()

    def reset(self) -> None:
        self.state = "IDLE"
        self.note_start_time = 0.0
        self.grace_counter = 0
        self.pitch_history: List[float] = []

    @staticmethod
    def hz_to_midi(pitch_hz: float) -> float:
        if pitch_hz <= 0:
            return 0.0
        return 69.0 + 12.0 * math.log2(pitch_hz / 440.0)

    def median_midi(self) -> float:
        if not self.pitch_history:
            return 0.0
        return float(np.median(self.pitch_history))

    def process(self, frame: PitchFrame) -> Iterable[dict]:
        events = []

        if not frame.is_voiced:
            if self.state in {"ACTIVE", "TENTATIVE_END"}:
                self.grace_counter += 1
                if self.grace_counter >= self.grace_frames:
                    if self.pitch_history and len(self.pitch_history) >= self.min_frames:
                        pitch_midi = int(round(self.median_midi()))
                        events.append({"type": "note_off", "note": pitch_midi, "time": frame.timestamp})
                    self.reset()
            return events

        midi_pitch = self.hz_to_midi(frame.pitch_hz)

        if self.state == "IDLE":
            self.state = "TENTATIVE_START"
            self.note_start_time = frame.timestamp
            self.pitch_history = [midi_pitch]
            return events

        if self.state == "TENTATIVE_START":
            self.pitch_history.append(midi_pitch)
            if len(self.pitch_history) >= self.min_frames:
                pitch_midi = int(round(self.median_midi()))
                events.append({"type": "note_on", "note": pitch_midi, "velocity": 80, "time": self.note_start_time})
                self.state = "ACTIVE"
            return events

        if self.state == "ACTIVE":
            median_pitch = self.median_midi()
            if abs(midi_pitch - median_pitch) >= self.split_threshold:
                old_pitch = int(round(median_pitch))
                events.append({"type": "note_off", "note": old_pitch, "time": frame.timestamp})
                self.pitch_history = [midi_pitch]
                self.note_start_time = frame.timestamp
                events.append({"type": "note_on", "note": int(round(midi_pitch)), "velocity": 80, "time": frame.timestamp})
            else:
                self.pitch_history.append(midi_pitch)
                if len(self.pitch_history) > 32:
                    self.pitch_history.pop(0)
            self.grace_counter = 0
            return events

        if self.state == "TENTATIVE_END":
            # Not currently used; kept for completeness if more states are added
            return events

        return events


class RealtimeMIDISender:
    """Wrapper around mido for realtime MIDI output."""

    def __init__(self, port_name: Optional[str] = None, instrument: int = 56) -> None:
        if mido is None:
            raise RuntimeError("mido and python-rtmidi are required for realtime MIDI output")

        if port_name:
            self.port = mido.open_output(port_name)
        else:
            self.port = mido.open_output("SwiftF0 Streaming", virtual=True)

        self.program_change(instrument)
        self.active_notes: set[int] = set()

    def program_change(self, program: int) -> None:
        self.port.send(mido.Message("program_change", program=program))

    def note_on(self, note: int, velocity: int, timestamp: float) -> None:
        self.active_notes.add(note)
        self.port.send(mido.Message("note_on", note=note, velocity=velocity, time=0))

    def note_off(self, note: int, timestamp: float) -> None:
        if note in self.active_notes:
            self.port.send(mido.Message("note_off", note=note, velocity=0, time=0))
            self.active_notes.discard(note)

    def close(self) -> None:
        for note in list(self.active_notes):
            self.note_off(note, time.time())
        self.port.close()


def audio_callback(indata, frames, time_info, status, audio_queue: queue.Queue) -> None:
    if status and status.input_overflow:
        print("[WARN] Audio overflow detected")
    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        # Drop the frame to keep latency bounded
        pass


def inference_worker(
    audio_queue: queue.Queue,
    pitch_queue: queue.Queue,
    detector: SwiftF0,
    stop_event: threading.Event,
) -> None:
    window = SlidingWindow(WINDOW_SIZE, BLOCK_SIZE)
    frame_index = 0
    while not stop_event.is_set():
        try:
            chunk = audio_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        chunk = chunk.reshape(-1).astype(np.float32)
        history = window.update(chunk)

        pitch_hz, confidence = detector._extract_pitch_and_confidence(history)
        if len(pitch_hz) == 0:
            continue

        # Only keep the newest frame to limit downstream load
        latest_pitch = float(pitch_hz[-1])
        latest_conf = float(confidence[-1])
        timestamp = frame_index * (BLOCK_SIZE / SAMPLE_RATE)
        frame_index += 1

        pitch_queue.put(
            PitchFrame(
                timestamp=timestamp,
                pitch_hz=latest_pitch,
                confidence=latest_conf,
                is_voiced=latest_conf > CONFIDENCE_THRESHOLD and latest_pitch > 0.0,
            )
        )


def postprocessing_worker(
    pitch_queue: queue.Queue,
    midi_sender: RealtimeMIDISender,
    segmenter: RealtimeNoteSegmenter,
    stop_event: threading.Event,
) -> None:
    while not stop_event.is_set():
        try:
            frame: PitchFrame = pitch_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        for event in segmenter.process(frame):
            if event["type"] == "note_on":
                midi_sender.note_on(event["note"], event["velocity"], event["time"])
            elif event["type"] == "note_off":
                midi_sender.note_off(event["note"], event["time"])


def main() -> None:
    audio_queue: queue.Queue = queue.Queue(maxsize=8)
    pitch_queue: queue.Queue = queue.Queue(maxsize=32)
    stop_event = threading.Event()

    detector = SwiftF0(confidence_threshold=CONFIDENCE_THRESHOLD)
    segmenter = RealtimeNoteSegmenter(SPLIT_THRESHOLD, GRACE_PERIOD_FRAMES)
    midi_sender = RealtimeMIDISender(instrument=56)

    infer_thread = threading.Thread(
        target=inference_worker,
        args=(audio_queue, pitch_queue, detector, stop_event),
        daemon=True,
    )
    post_thread = threading.Thread(
        target=postprocessing_worker,
        args=(pitch_queue, midi_sender, segmenter, stop_event),
        daemon=True,
    )

    infer_thread.start()
    post_thread.start()

    def handle_sigint(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="float32",
        channels=1,
        callback=lambda indata, frames, time_info, status: audio_callback(
            indata, frames, time_info, status, audio_queue
        ),
    ):
        print("Streaming... Press Ctrl+C to stop.")
        while not stop_event.is_set():
            time.sleep(0.1)

    midi_sender.close()
    print("Stopped.")


if __name__ == "__main__":
    main()
