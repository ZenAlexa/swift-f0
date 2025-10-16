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

    PHASE 1 Enhancement:
    - Increased grace_period_frames: 2 → 10 (32ms → 160ms)
    - Increased min_note_frames: 3 → 5 (48ms → 80ms)
    - Added pitch stability check (CV < 10%)

    Industry-standard timing (per evaluation):
    - Grace period: 100-300ms for natural speech pauses (we use 160ms)
    - Min note duration: 50-100ms for reliable pitch detection (we use 80ms)
    - WebRTC VAD typically uses 100-300ms hold time

    Reference:
    - WebRTC VAD timing parameters
    - Professional DAW note segmentation algorithms
    """

    def __init__(
        self,
        split_threshold: float = 2.0,  # FIX B: 0.7→2.0 (减少音符抖动)
        grace_period_frames: int = 10,  # PHASE 1: 2→10 (160ms @ 16kHz/256hop)
        min_note_frames: int = 5,       # PHASE 1: 3→5 (80ms @ 16kHz/256hop)
    ):
        self.split_threshold = split_threshold
        self.grace = grace_period_frames
        self.min_frames = min_note_frames
        self.reset()

    def reset(self) -> None:
        self.state = "IDLE"
        self.note_start_time = 0.0
        self.grace_counter = 0
        self.pitch_history: List[float] = []
        self.current_note: int | None = None  # FIX A: 追踪实际发送的音符号

    @staticmethod
    def hz_to_midi(p: float) -> float:
        if p <= 0:
            return 0.0
        return 69.0 + 12.0 * math.log2(p / 440.0)

    def median_midi(self) -> float:
        if not self.pitch_history:
            return 0.0
        return float(np.median(self.pitch_history))

    def is_pitch_stable(self) -> bool:
        """
        Check pitch stability using coefficient of variation (CV).

        Industry practice (WebRTC VAD stability heuristics):
        - CV = std / mean (coefficient of variation)
        - Stable pitch: CV < 10% (0.10)
        - Prevents triggering on:
          * Random noise with high confidence
          * Acoustic feedback (unstable pitch oscillation)
          * Microphone handling noise

        Per evaluation microadjustment:
        - Initial threshold: CV < 0.10 (10%)
        - If rejecting valid humming: relax to 0.12-0.15 (12-15%)
        - If accepting noisy feedback: tighten to 0.08 (8%)

        Returns:
            True if pitch is stable, False otherwise

        Reference:
        - WebRTC VAD stability checks
        - Professional DAW pitch detection algorithms
        """
        if len(self.pitch_history) < 3:
            return False  # Need at least 3 samples for meaningful statistics

        # Calculate coefficient of variation (CV = std / mean)
        pitch_array = np.array(self.pitch_history)
        mean_pitch = np.mean(pitch_array)
        std_pitch = np.std(pitch_array)

        if mean_pitch < 1e-6:
            return False  # Near-zero mean, likely silence or invalid

        cv = std_pitch / mean_pitch

        # Industry threshold: CV < 10% for stable vocal pitch
        # Per evaluation: may adjust to 0.12-0.15 if too strict
        return cv < 0.10

    def process(self, frame: PitchFrame) -> Iterable[NoteEvent]:
        evts: List[NoteEvent] = []

        if not frame.voiced:
            if self.state in {"ACTIVE", "TENTATIVE_END"}:
                self.grace_counter += 1
                if self.grace_counter >= self.grace:
                    # FIX A: 使用追踪的音符号，确保 note_off 与之前的 note_on 匹配
                    if self.current_note is not None:
                        evts.append(NoteEvent(type="note_off", note=self.current_note, time=frame.timestamp))
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
                # PHASE 1: Add stability check (WebRTC VAD pattern)
                # Industry practice: require stable pitch before triggering note_on
                # Prevents false triggers from noise, feedback, or transients
                if self.is_pitch_stable():
                    pitch_midi = int(round(self.median_midi()))
                    self.current_note = pitch_midi  # FIX A: 记录发送的音符号
                    evts.append(NoteEvent(type="note_on", note=pitch_midi, velocity=80, time=self.note_start_time))
                    self.state = "ACTIVE"
                else:
                    # Unstable pitch: require more frames or timeout
                    # Per evaluation: balance responsiveness vs false rejection
                    if len(self.pitch_history) > self.min_frames * 2:
                        # Timeout: pitch never stabilized, reset
                        # Prevents infinite accumulation on sustained noise
                        self.reset()
            return evts

        if self.state == "ACTIVE":
            median_midi = self.median_midi()
            if abs(midi_pitch - median_midi) >= self.split_threshold:
                # FIX A: 关键修复 - 使用追踪的音符号，而不是重新计算 median
                # 旧代码: old_pitch = int(round(median_midi)) ← 错误！median 会动态变化
                # 新代码: 使用 self.current_note（之前 note_on 发送的实际音符）
                if self.current_note is not None:
                    evts.append(NoteEvent(type="note_off", note=self.current_note, time=frame.timestamp))

                # 发送新音符的 note_on
                new_pitch = int(round(midi_pitch))
                self.current_note = new_pitch  # FIX A: 更新追踪的音符号
                self.pitch_history = [midi_pitch]
                self.note_start_time = frame.timestamp
                evts.append(NoteEvent(type="note_on", note=new_pitch, velocity=80, time=frame.timestamp))
            else:
                self.pitch_history.append(midi_pitch)
                if len(self.pitch_history) > 32:
                    self.pitch_history.pop(0)
            self.grace_counter = 0
            return evts

        return evts

