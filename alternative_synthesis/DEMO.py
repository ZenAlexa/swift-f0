#!/usr/bin/env python3
"""
智慧卡祖笛 - 加性合成版本
使用纯正弦波合成，音质完美！
"""

import sys
from pathlib import Path
import time
import signal
import numpy as np
import sounddevice as sd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from swift_f0.core import SwiftF0
from swift_f0.streaming import SwiftF0Streamer, RealtimeNoteSegmenter
from swift_f0.streaming.types import NoteEvent
from realtime_synth import RealtimeAdditiveSynth

# ============================================================================
# 配置参数
# ============================================================================

SAMPLE_RATE = 16000
BLOCK_SIZE = 256
AUDIO_OUT_SR = 44100

# 音高检测
CONFIDENCE_THRESHOLD = 0.85
FMIN = 80.0
FMAX = 600.0

# 能量门控
GATE_OPEN_DB = -35.0
GATE_HYSTERESIS_DB = 8.0
GATE_HOLD_MS = 150.0

# 音符分段
SPLIT_THRESHOLD = 2.5
GRACE_FRAMES = 12
MIN_NOTE_FRAMES = 5

# 合成器
NUM_HARMONICS = 5  # 谐波数量

print("="*80)
print("🎵 智慧卡祖笛 - 加性合成版本")
print("="*80)
print()
print("✨ 技术亮点:")
print("  • 纯正弦波加性合成 (无 FluidSynth)")
print("  • 音质清晰、无失真")
print("  • 零延迟启动")
print("  • 完全可控的音色")
print()
print("配置:")
print(f"  • 音高检测: confidence={CONFIDENCE_THRESHOLD}, range={FMIN}-{FMAX}Hz")
print(f"  • 音符分段: split={SPLIT_THRESHOLD}半音, grace={GRACE_FRAMES}帧")
print(f"  • 合成器: {NUM_HARMONICS}谐波加性合成")
print("="*80)
print()

# ============================================================================
# 初始化组件
# ============================================================================

print("初始化组件...")

# 1. SwiftF0 音高检测
detector = SwiftF0(
    confidence_threshold=CONFIDENCE_THRESHOLD,
    fmin=FMIN,
    fmax=FMAX,
)

# 2. Streamer (带 energy gate)
streamer = SwiftF0Streamer(
    detector=detector,
    enable_energy_gate=True,
    gate_open_threshold_db=GATE_OPEN_DB,
    gate_hysteresis_db=GATE_HYSTERESIS_DB,
    gate_hold_time_ms=GATE_HOLD_MS,
)

# 3. 音符分段
segmenter = RealtimeNoteSegmenter(
    split_threshold=SPLIT_THRESHOLD,
    grace_period_frames=GRACE_FRAMES,
    min_note_frames=MIN_NOTE_FRAMES,
)

# 4. 加性合成器
synth = RealtimeAdditiveSynth(
    sample_rate=AUDIO_OUT_SR,
    block_size=256,
    num_harmonics=NUM_HARMONICS,
)

synth.start()

print("✅ 所有组件初始化完成")
print()
print("🎤 开始实时处理... 按 Ctrl+C 停止")
print("   对着麦克风哼唱，听听这清晰的音质！")
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
        # 提取单声道
        chunk = indata[:, 0] if indata.ndim > 1 else indata.flatten()
        chunk = chunk.astype(np.float32)

        # 音高检测 (带 energy gate)
        pitch_frame = streamer.process_chunk(chunk)

        # 音符分段
        note_events = segmenter.process(pitch_frame)

        # 转换为 NoteEvent
        events = []
        for e in note_events:
            events.append(NoteEvent(
                type=e.type,
                note=e.note,
                time=e.time,
                velocity=e.velocity if hasattr(e, 'velocity') else 80,
            ))

        # 发送到合成器
        if events:
            synth.send(events)
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
    synth.finalize()
    print("✅ 完成！")
    print()
    print(f"总共识别 {note_count} 个音符")
    print()
    print("音质如何？应该比之前清晰太多了！")
