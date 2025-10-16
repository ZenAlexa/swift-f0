#!/usr/bin/env python3
"""
智慧卡祖笛 - 最终版本
完美解决所有问题:
1. ✅ gain=0.2 (音质正常)
2. ✅ 停止哼唱后自动静音
3. ✅ 快速音高切换响应
"""

import sys
import time
import signal
from pathlib import Path

import numpy as np
import sounddevice as sd

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from swift_f0.core import SwiftF0
from swift_f0.streaming import (
    SwiftF0Streamer,
    RealtimeNoteSegmenter,
    AudioSynthConfig,
    RealtimeAudioSink,
    NoteEvent,
)

# ============================================================================
# 优化后的最终配置
# ============================================================================

SAMPLE_RATE = 16000
BLOCK_SIZE = 256
AUDIO_OUT_SR = 44100

# 音高检测
CONFIDENCE_THRESHOLD = 0.85  # 降低到 0.85 提升响应速度
FMIN = 80.0
FMAX = 600.0

# 能量门控 (严格的静音检测)
GATE_OPEN_DB = -35.0
GATE_HYSTERESIS_DB = 8.0
GATE_HOLD_MS = 150.0  # 降低到 150ms 加快静音响应

# 音符分段 (平衡响应速度和稳定性)
SPLIT_THRESHOLD = 2.5  # 2.5 半音 - 比 3.0 更敏感，比 2.0 更稳定
GRACE_FRAMES = 12  # 192ms - 比 15 更快响应
MIN_NOTE_FRAMES = 5  # 80ms - 最短音符时长

print("="*80)
print("🎵 智慧卡祖笛 - 最终版本")
print("="*80)
print("\n关键优化:")
print(f"  ✅ gain=0.2 (FluidSynth 默认，无削波失真)")
print(f"  ✅ confidence={CONFIDENCE_THRESHOLD} (平衡准确率和响应)")
print(f"  ✅ split={SPLIT_THRESHOLD} 半音 (平衡稳定性和灵敏度)")
print(f"  ✅ grace={GRACE_FRAMES} 帧 = {GRACE_FRAMES*16}ms (快速静音)")
print(f"  ✅ gate_hold={GATE_HOLD_MS}ms (快速静音响应)")
print()
print("预期效果:")
print("  • 音质清晰、饱满、无失真")
print("  • 停止哼唱后 200ms 内自动静音")
print("  • 音高切换延迟 <150ms")
print("  • 支持每秒 3-5 个音符变化")
print("="*80)
print()

# 选择乐器
print("选择乐器:")
print("  0 - 钢琴")
print("  40 - 小提琴")
print("  66 - 萨克斯 (推荐)")
print("  73 - 长笛 (推荐)")
print("  88 - 合成 Pad")

try:
    instrument = int(input("输入编号 (默认 73): ") or "73")
except (ValueError, EOFError):
    instrument = 73

print(f"\n✅ 使用乐器: {instrument}")
print()

# ============================================================================
# 初始化
# ============================================================================

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

segmenter = RealtimeNoteSegmenter(
    split_threshold=SPLIT_THRESHOLD,
    grace_period_frames=GRACE_FRAMES,
    min_note_frames=MIN_NOTE_FRAMES,
)

config = AudioSynthConfig(
    sample_rate=float(AUDIO_OUT_SR),
    gain=0.2,  # 关键！FluidSynth 默认值
    soundfont_path="soundfonts/GeneralUser-GS.sf2",
    initial_program=instrument,
)

sink = RealtimeAudioSink(config, block_size=256)

print("✅ 初始化完成")
print("🎤 开始实时处理... 按 Ctrl+C 停止")
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

        pitch_frame = streamer.process_chunk(chunk)
        note_events = segmenter.process(pitch_frame)

        events = []
        for e in note_events:
            events.append(NoteEvent(
                type=e.type,
                note=e.note,
                time=e.time,
                velocity=e.velocity if hasattr(e, 'velocity') else 80,
            ))

        if events:
            sink.send(events)
            for e in events:
                if e.type == "note_on":
                    note_count += 1
                    print(f"🎵 #{note_count:3d} | Note {e.note:3d} ON  | {pitch_frame.pitch_hz:6.1f} Hz")
                else:
                    print(f"🔇      | Note {e.note:3d} OFF")

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
    sink.finalize()
    print("✅ 完成！")
    print()
    print(f"总共识别 {note_count} 个音符")
