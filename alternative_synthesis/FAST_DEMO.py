#!/usr/bin/env python3
"""
超快响应版本 - 牺牲稳定性换取速度
适合快速旋律识别
"""

from __future__ import annotations

import sys
from pathlib import Path
import time
import signal
from collections import deque
import numpy as np
import sounddevice as sd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from swift_f0.core import SwiftF0
from swift_f0.streaming import SwiftF0Streamer
from swift_f0.streaming.types import NoteEvent, PitchFrame
from realtime_synth import RealtimeAdditiveSynth

# ============================================================================
# 激进配置 - 追求极致响应速度
# ============================================================================

SAMPLE_RATE = 16000
BLOCK_SIZE = 256
AUDIO_OUT_SR = 44100

# 音高检测 - 降低阈值提升响应
CONFIDENCE_THRESHOLD = 0.80  # 从 0.9 降到 0.75
FMIN = 80.0
FMAX = 600.0

# 能量门控 - 更快响应
GATE_OPEN_DB = -35.0  # 更敏感
GATE_HYSTERESIS_DB = 5.0  # 更小迟滞
GATE_HOLD_MS = 50.0  # 更快释放

# 合成器
NUM_HARMONICS = 5

print("="*80)
print("🚀 智慧卡祖笛 - 超快响应版本")
print("="*80)
print()
print("⚡ 极致优化:")
print("  • 无音符分段器 - 直接音高转音符")
print("  • confidence=0.75 (更敏感)")
print("  • 自适应平滑 + 跳音快速跟随")
print("  • 响度映射力度，降低电流感")
print()
print("⚠️  权衡:")
print("  • 极短音（<30ms）可能被忽略")
print("  • 响应速度维持在 ≈40-50ms")
print("="*80)
print()

# ============================================================================
# 简化的实时处理器
# ============================================================================

class FastPitchToNote:
    """
    超快音高转音符
    无复杂状态机，直接转换
    """

    def __init__(
        self,
        smoothing_frames: int = 4,
        confirm_frames: int = 1,
        min_note_frames: int = 2,
    ):
        self.pitch_buffer: deque[float] = deque(maxlen=max(1, smoothing_frames))
        self.current_note: int | None = None
        self.note_age = 0
        self.pending_note: int | None = None
        self.pending_age = 0
        self.smoothed_pitch: float | None = None
        self.confirm_frames = max(1, confirm_frames)
        self.min_note_frames = max(1, min_note_frames)  # 2帧 = 32ms 最短音符
        self.current_velocity = 80

    def _estimate_velocity(self, loudness: float | None, confidence: float) -> int:
        """
        根据响度+置信度估算力度，减少突兀的音量变化
        """
        base_conf = float(np.clip(confidence, 0.0, 1.0))
        if loudness is None:
            level = base_conf
        else:
            # 假设人声 RMS 大约在 0.01 - 0.12 之间
            norm = float(np.clip(loudness / 0.08, 0.0, 1.2))
            level = 0.65 * min(norm, 1.0) + 0.35 * base_conf

        velocity = int(np.clip(35.0 + level * 70.0, 30.0, 115.0))
        return velocity

    def _switch_note(self, new_note: int, timestamp: float, velocity: int):
        events = []
        if self.current_note is not None:
            events.append(NoteEvent(
                type="note_off",
                note=self.current_note,
                time=timestamp,
                velocity=self.current_velocity,
            ))
        self.current_note = new_note
        self.note_age = 0
        self.pending_note = None
        self.pending_age = 0
        self.current_velocity = velocity
        events.append(NoteEvent(
            type="note_on",
            note=new_note,
            time=timestamp,
            velocity=velocity,
        ))
        return events

    def process(self, frame: PitchFrame, loudness: float | None = None):
        events = []

        if not frame.voiced:
            # 立即停止当前音符
            if self.current_note is not None:
                events.append(NoteEvent(
                    type="note_off",
                    note=self.current_note,
                    time=frame.timestamp,
                    velocity=self.current_velocity,
                ))
                self.current_note = None
                self.note_age = 0
            self.pending_note = None
            self.pending_age = 0
            self.pitch_buffer.clear()
            self.smoothed_pitch = None
            return events

        # 有声 - 转换为 MIDI
        midi_pitch = 69.0 + 12.0 * np.log2(frame.pitch_hz / 440.0)
        self.pitch_buffer.append(midi_pitch)

        # 使用中位数 + IIR 平滑，兼顾响应速度与稳定性
        window_pitch = float(np.median(self.pitch_buffer))

        if self.smoothed_pitch is None:
            self.smoothed_pitch = window_pitch
        else:
            delta = window_pitch - self.smoothed_pitch
            # 大幅度跳跃时加速跟随，平稳段保持柔和
            abs_delta = abs(delta)
            confidence = float(np.clip(frame.confidence, 0.0, 1.0))
            base_alpha = 0.25 + 0.55 * confidence
            if abs_delta >= 2.0:
                alpha = max(base_alpha, 0.7)
            elif abs_delta >= 1.0:
                alpha = max(base_alpha, 0.5)
            else:
                alpha = max(0.3, base_alpha * 0.8)
            alpha = float(np.clip(alpha, 0.25, 0.9))
            self.smoothed_pitch += alpha * delta

        target_note = int(round(self.smoothed_pitch))
        velocity = self._estimate_velocity(loudness, frame.confidence)

        if self.current_note is None:
            return self._switch_note(target_note, frame.timestamp, velocity)

        # 检查是否需要切换音符
        if target_note == self.current_note:
            self.note_age += 1
            self.pending_note = None
            self.pending_age = 0
            return events

        # 极短音或跳音处理
        semitone_jump = abs(target_note - self.current_note)
        allow_instant_switch = (
            self.note_age >= self.min_note_frames
            or semitone_jump >= 2
        )

        if allow_instant_switch:
            return self._switch_note(target_note, frame.timestamp, velocity)

        # 等待确认，避免 1 帧抖动
        if self.pending_note != target_note:
            self.pending_note = target_note
            self.pending_age = 1
        else:
            self.pending_age += 1

        if self.pending_age >= self.confirm_frames:
            return self._switch_note(target_note, frame.timestamp, velocity)

        return events


# ============================================================================
# 初始化
# ============================================================================

print("初始化组件...")

detector = SwiftF0(
    confidence_threshold=CONFIDENCE_THRESHOLD,
    fmin=FMIN,
    fmax=FMAX,
)

streamer = SwiftF0Streamer(
    detector=detector,
    enable_energy_gate=True,
    gate_open_threshold_db=GATE_OPEN_DB,
    gate_hysteresis_db=GATE_HYSTERESIS_DB,
    gate_hold_time_ms=GATE_HOLD_MS,
)

processor = FastPitchToNote(
    smoothing_frames=4,
    confirm_frames=1,
    min_note_frames=2,
)

synth = RealtimeAdditiveSynth(
    sample_rate=AUDIO_OUT_SR,
    block_size=256,
    num_harmonics=NUM_HARMONICS,
)

synth.start()

print("✅ 所有组件初始化完成")
print()
print("🎤 开始实时处理... 按 Ctrl+C 停止")
print("   试试快速哼唱旋律，看响应速度！")
print()

# ============================================================================
# 音频处理
# ============================================================================

stop_event = False
note_count = 0

def audio_callback(indata, frames, time_info, status):
    global note_count

    if status:
        print(f"⚠️  {status}")

    try:
        chunk = indata[:, 0] if indata.ndim > 1 else indata.flatten()
        chunk = chunk.astype(np.float32)
        loudness = float(np.sqrt(np.mean(chunk ** 2))) if len(chunk) else 0.0

        pitch_frame = streamer.process_chunk(chunk)
        note_events = processor.process(pitch_frame, loudness=loudness)

        if note_events:
            synth.send(note_events)
            for e in note_events:
                if e.type == "note_on":
                    note_count += 1
                    print(
                        f"🎵 #{note_count:3d} | Note {e.note:3d} ON  "
                        f"| {pitch_frame.pitch_hz:6.1f} Hz | vel={e.velocity:3d} "
                        f"| age={processor.note_age}"
                    )
                else:
                    print(f"🔇      | Note {e.note:3d} OFF | vel={e.velocity:3d}")

    except Exception as ex:
        print(f"❌ Error: {ex}")
        import traceback
        traceback.print_exc()

def handle_sigint(signum, frame):
    global stop_event
    stop_event = True
    print("\n\n⏹️  停止中...")

signal.signal(signal.SIGINT, handle_sigint)
signal.signal(signal.SIGTERM, handle_sigint)

# ============================================================================
# 主循环
# ============================================================================

try:
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="float32",
        channels=1,
        callback=audio_callback,
    ):
        while not stop_event:
            time.sleep(0.1)

finally:
    print("\n🔧 清理资源...")
    synth.finalize()
    print("✅ 完成！")
    print()
    print(f"总共识别 {note_count} 个音符")
    print()
    print("响应速度如何？应该快很多了！")
