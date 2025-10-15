"""
紧急诊断脚本 - 捕获 MIDI 事件和音高数据

用法:
    python DEBUG_CAPTURE.py --audio --sf2 <path> --duration 10

会生成:
    - debug_midi_events.txt (所有 MIDI 事件)
    - debug_pitch_frames.txt (所有音高帧)
    - debug_active_notes.txt (活跃音符状态)
"""

import sys
import time
import queue
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from swift_f0.core import SwiftF0
from swift_f0.streaming import RealtimeNoteSegmenter, NoteEvent

import sounddevice as sd
import numpy as np

# 诊断日志文件
midi_log = open("debug_midi_events.txt", "w")
pitch_log = open("debug_pitch_frames.txt", "w")
active_log = open("debug_active_notes.txt", "w")

midi_log.write("timestamp,event_type,note,velocity\n")
pitch_log.write("timestamp,pitch_hz,confidence,voiced,gate_open\n")
active_log.write("timestamp,active_notes_count,notes_list\n")

active_notes = set()


def log_midi_event(evt: NoteEvent):
    """记录 MIDI 事件"""
    global active_notes

    if evt.type == "note_on":
        active_notes.add(evt.note)
    elif evt.type == "note_off":
        active_notes.discard(evt.note)

    midi_log.write(f"{evt.time:.4f},{evt.type},{evt.note},{evt.velocity}\n")
    midi_log.flush()

    active_log.write(f"{evt.time:.4f},{len(active_notes)},{sorted(active_notes)}\n")
    active_log.flush()

    # 实时打印到控制台
    print(f"[{evt.time:6.3f}s] {evt.type:8s} note={evt.note:3d} vel={evt.velocity:3d} | active={len(active_notes)}")


def log_pitch_frame(timestamp, pitch_hz, confidence, voiced, gate_open):
    """记录音高帧"""
    pitch_log.write(f"{timestamp:.4f},{pitch_hz:.2f},{confidence:.4f},{voiced},{gate_open}\n")
    pitch_log.flush()


# 简化的推理逻辑（加日志）
class DiagnosticInferenceWorker:
    def __init__(self, detector, segmenter, pitch_queue):
        self.detector = detector
        self.segmenter = segmenter
        self.pitch_queue = pitch_queue
        self.frame_index = 0
        self.buffer = np.zeros(1024, dtype=np.float32)

    def process_chunk(self, chunk):
        # 滑动窗口
        self.buffer[:-256] = self.buffer[256:]
        self.buffer[-256:] = chunk

        # 推理
        pitch_hz, conf = self.detector.extract_pitch_and_confidence(self.buffer)
        p = float(pitch_hz[-1]) if len(pitch_hz) else 0.0
        c = float(conf[-1]) if len(conf) else 0.0

        # 简化的 voiced 判定（无能量门控，便于诊断）
        voiced = bool(c > 0.9 and 46.875 <= p <= 2093.75)

        timestamp = self.frame_index * (256 / 16000)
        self.frame_index += 1

        # 记录音高帧
        log_pitch_frame(timestamp, p, c, voiced, True)  # gate_open 暂时固定 True

        # 构造帧
        from swift_f0.streaming.types import PitchFrame
        frame = PitchFrame(timestamp=timestamp, pitch_hz=p, confidence=c, voiced=voiced)

        # 分段处理
        events = self.segmenter.process(frame)
        for evt in events:
            log_midi_event(evt)

        return frame, events


def audio_callback(indata, frames, time_info, status, audio_queue):
    if status and status.input_overflow:
        print("[WARN] Audio overflow")
    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=10, help="录制时长（秒）")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("🔍 诊断模式启动")
    print("=" * 70)
    print("将捕获以下数据:")
    print("  - debug_midi_events.txt (MIDI 事件时间序列)")
    print("  - debug_pitch_frames.txt (音高检测结果)")
    print("  - debug_active_notes.txt (活跃音符状态)")
    print()
    print(f"录制时长: {args.duration} 秒")
    print("请在此期间:")
    print("  1. 保持安静 3 秒（观察是否有误触发）")
    print("  2. 哼唱单音 2 秒（观察音高稳定性）")
    print("  3. 哼唱快速变化音阶（观察事件密度）")
    print("=" * 70)
    print()

    input("按 Enter 开始录制...")

    # 初始化
    detector = SwiftF0(confidence_threshold=0.9)
    segmenter = RealtimeNoteSegmenter(
        split_threshold=0.7,
        grace_period_frames=10,
        min_note_frames=5,
    )

    audio_queue = queue.Queue(maxsize=8)
    worker = DiagnosticInferenceWorker(detector, segmenter, None)

    # 启动音频流
    print("🎤 开始录制...\n")
    start_time = time.time()

    with sd.InputStream(
        samplerate=16000,
        blocksize=256,
        dtype="float32",
        channels=1,
        device=None,  # 默认麦克风
        callback=lambda *args: audio_callback(*args, audio_queue),
    ):
        while time.time() - start_time < args.duration:
            try:
                chunk = audio_queue.get(timeout=0.1)
                chunk = chunk.reshape(-1).astype(np.float32)
                worker.process_chunk(chunk)
            except queue.Empty:
                continue

    print("\n✅ 录制完成！")
    print("\n生成的诊断文件:")
    print("  - debug_midi_events.txt")
    print("  - debug_pitch_frames.txt")
    print("  - debug_active_notes.txt")
    print("\n请检查这些文件，特别关注:")
    print("  1. MIDI 事件密度（每秒事件数）")
    print("  2. active_notes_count 是否持续增长")
    print("  3. 音高是否稳定（pitch_hz 列）")

    # 关闭日志
    midi_log.close()
    pitch_log.close()
    active_log.close()


if __name__ == "__main__":
    main()
