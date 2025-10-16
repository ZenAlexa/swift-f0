#!/usr/bin/env python3
"""
实时加性合成系统
使用纯正弦波合成，音质清晰、延迟低、完全可控
"""

import sys
from pathlib import Path
import numpy as np
import sounddevice as sd
import threading
from typing import Dict
from dataclasses import dataclass

# 添加项目路径
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from swift_f0.streaming.types import NoteEvent


@dataclass
class ActiveVoice:
    """活跃的音符"""
    note: int
    frequency: float
    velocity: float
    phase: float
    age: float  # 音符年龄（秒）
    releasing: bool = False  # 是否正在释放
    release_age: float = 0.0  # 释放开始时的年龄


class RealtimeAdditiveSynth:
    """
    实时加性合成器

    特点：
    - 使用谐波叠加生成音色
    - 平滑的包络控制
    - 零延迟启动
    - 无削波失真
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        block_size: int = 256,
        num_harmonics: int = 5,
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.num_harmonics = num_harmonics

        # 活跃音符
        self.voices: Dict[int, ActiveVoice] = {}
        self.lock = threading.Lock()

        # ADSR 包络参数
        self.attack_time = 0.005   # 5ms 快速起音
        self.release_time = 0.05   # 50ms 快速释放
        self.sustain_level = 0.8   # 80% 持续电平

        # 谐波设置 (模拟管乐器音色)
        # 基频最强，高次谐波逐渐衰减
        self.harmonic_amplitudes = self._compute_harmonic_profile(num_harmonics)

        # 主音量
        self.master_volume = 0.25

        # 音频流
        self.stream = None

    def _compute_harmonic_profile(self, n: int) -> np.ndarray:
        """计算谐波振幅分布"""
        # 模拟萨克斯/长笛音色：奇次谐波较强
        profile = []
        for i in range(1, n + 1):
            if i % 2 == 1:  # 奇次谐波
                amp = 1.0 / i ** 0.7
            else:  # 偶次谐波
                amp = 0.5 / i ** 0.9
            profile.append(amp)

        # 归一化
        profile = np.array(profile)
        profile /= np.sum(profile)
        return profile

    def note_on(self, note: int, velocity: int = 80):
        """启动音符"""
        freq = 440.0 * (2.0 ** ((note - 69) / 12.0))

        with self.lock:
            self.voices[note] = ActiveVoice(
                note=note,
                frequency=freq,
                velocity=velocity / 127.0,
                phase=0.0,
                age=0.0,
                releasing=False,
            )

    def note_off(self, note: int):
        """释放音符"""
        with self.lock:
            if note in self.voices:
                voice = self.voices[note]
                voice.releasing = True
                voice.release_age = voice.age

    def send(self, events):
        """接收 NoteEvent 列表"""
        for event in events:
            if event.type == "note_on":
                self.note_on(event.note, event.velocity)
            elif event.type == "note_off":
                self.note_off(event.note)

    def _generate_samples(self, num_frames: int) -> np.ndarray:
        """生成音频样本"""
        output = np.zeros(num_frames, dtype=np.float32)

        dt = 1.0 / self.sample_rate

        with self.lock:
            voices_to_remove = []

            for note, voice in self.voices.items():
                # 计算包络
                envelope = self._compute_envelope(voice, num_frames, dt)

                # 生成谐波
                signal = np.zeros(num_frames, dtype=np.float32)

                for h_idx in range(self.num_harmonics):
                    h_freq = voice.frequency * (h_idx + 1)
                    h_amp = self.harmonic_amplitudes[h_idx]

                    # 生成正弦波
                    t = np.arange(num_frames) * dt
                    phases = 2.0 * np.pi * h_freq * t + voice.phase
                    harmonic = np.sin(phases) * h_amp

                    signal += harmonic

                # 应用包络和音量
                signal *= envelope * voice.velocity * self.master_volume

                # 叠加到输出
                output += signal

                # 更新相位
                voice.phase += 2.0 * np.pi * voice.frequency * num_frames * dt
                voice.phase = voice.phase % (2.0 * np.pi)

                # 更新年龄
                voice.age += num_frames * dt

                # 检查是否完成释放
                if voice.releasing:
                    release_duration = voice.age - voice.release_age
                    if release_duration > self.release_time:
                        voices_to_remove.append(note)

            # 移除完成释放的音符
            for note in voices_to_remove:
                del self.voices[note]

        # 轻微软削波防止过载
        output = np.tanh(output * 1.2)

        return output

    def _compute_envelope(
        self,
        voice: ActiveVoice,
        num_frames: int,
        dt: float
    ) -> np.ndarray:
        """计算 ADSR 包络"""
        envelope = np.ones(num_frames, dtype=np.float32)

        for i in range(num_frames):
            t = voice.age + i * dt

            if voice.releasing:
                # Release 阶段
                release_t = t - voice.release_age
                if release_t < self.release_time:
                    # 线性衰减
                    envelope[i] = self.sustain_level * (1.0 - release_t / self.release_time)
                else:
                    envelope[i] = 0.0
            else:
                # Attack + Sustain
                if t < self.attack_time:
                    # Attack: 线性上升到 sustain level
                    envelope[i] = self.sustain_level * (t / self.attack_time)
                else:
                    # Sustain
                    envelope[i] = self.sustain_level

        return envelope

    def _audio_callback(self, outdata, frames, time_info, status):
        """音频回调"""
        if status:
            print(f"⚠️  {status}")

        # 生成单声道
        mono = self._generate_samples(frames)

        # 转立体声
        outdata[:, 0] = mono
        outdata[:, 1] = mono

    def start(self):
        """启动音频流"""
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=2,
            callback=self._audio_callback,
            dtype='float32',
        )
        self.stream.start()
        print(f"✅ 音频流已启动: {self.sample_rate}Hz, block={self.block_size}")

    def stop(self):
        """停止音频流"""
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def finalize(self):
        """清理资源"""
        with self.lock:
            self.voices.clear()
        self.stop()


if __name__ == "__main__":
    """测试加性合成器"""
    import time

    print("="*70)
    print("🎵 实时加性合成器测试")
    print("="*70)
    print()

    synth = RealtimeAdditiveSynth(
        sample_rate=44100,
        block_size=256,
        num_harmonics=5,
    )

    synth.start()

    # 测试 1: 音阶
    print("测试 1: 播放 C 大调音阶")
    notes = [60, 62, 64, 65, 67, 69, 71, 72]
    for note in notes:
        synth.note_on(note, 80)
        time.sleep(0.4)
        synth.note_off(note)
        time.sleep(0.1)

    time.sleep(0.5)

    # 测试 2: 和弦
    print("测试 2: 播放 C 大三和弦")
    chord = [60, 64, 67]
    for note in chord:
        synth.note_on(note, 80)
    time.sleep(2.0)
    for note in chord:
        synth.note_off(note)

    time.sleep(0.5)

    # 测试 3: 快速音符
    print("测试 3: 快速音符切换")
    melody = [60, 62, 64, 62, 60, 64, 62, 60]
    for note in melody:
        synth.note_on(note, 80)
        time.sleep(0.15)
        synth.note_off(note)
        time.sleep(0.05)

    time.sleep(0.5)
    synth.finalize()

    print()
    print("✅ 测试完成")
    print()
    print("如果音质清晰、流畅、无失真，说明系统可行！")
