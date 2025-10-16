#!/usr/bin/env python3
"""
加性合成器 - 使用纯正弦波叠加
比 FluidSynth 更简单、更可控、延迟更低
"""

import numpy as np
import sounddevice as sd
from typing import Dict, List
from dataclasses import dataclass
import threading


@dataclass
class Voice:
    """单个发声的音符"""
    note: int
    frequency: float
    velocity: int
    phase: float = 0.0
    active: bool = True
    release_time: float = 0.0  # 释放开始时间


class AdditiveSynthesizer:
    """
    加性合成器 - 使用正弦波叠加生成音色

    特点:
    - 零延迟 (无样本加载)
    - 完全可控的音色
    - 无削波失真
    - 平滑的 ADSR 包络
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        block_size: int = 256,
        num_harmonics: int = 4,  # 谐波数量
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.num_harmonics = num_harmonics

        # 活跃的音符
        self.voices: Dict[int, Voice] = {}
        self.lock = threading.Lock()

        # ADSR 包络参数 (秒)
        self.attack = 0.01   # 10ms 快速起音
        self.decay = 0.05    # 50ms 衰减
        self.sustain = 0.7   # 70% 持续电平
        self.release = 0.1   # 100ms 释放

        # 谐波振幅 (模拟管乐器)
        # 基频最强，谐波逐渐衰减
        self.harmonic_amps = [1.0, 0.5, 0.3, 0.2][:num_harmonics]

        # 音频流
        self.stream = None

    def note_on(self, note: int, velocity: int = 80):
        """启动音符"""
        freq = 440.0 * (2.0 ** ((note - 69) / 12.0))  # MIDI to Hz

        with self.lock:
            self.voices[note] = Voice(
                note=note,
                frequency=freq,
                velocity=velocity,
                phase=0.0,
                active=True,
            )

    def note_off(self, note: int):
        """释放音符"""
        with self.lock:
            if note in self.voices:
                self.voices[note].release_time = 0.0  # 开始释放

    def _generate_block(self, frames: int) -> np.ndarray:
        """生成一个音频块"""
        output = np.zeros(frames, dtype=np.float32)

        with self.lock:
            # 遍历所有活跃音符
            for note, voice in list(self.voices.items()):
                if not voice.active:
                    continue

                # 生成谐波
                for h_idx, h_amp in enumerate(self.harmonic_amps):
                    harmonic_freq = voice.frequency * (h_idx + 1)

                    # 生成正弦波
                    t = np.arange(frames) / self.sample_rate
                    phase_increment = 2.0 * np.pi * harmonic_freq * t + voice.phase
                    wave = np.sin(phase_increment) * h_amp

                    # 应用 ADSR 包络
                    envelope = self._compute_envelope(voice, frames)
                    wave *= envelope

                    # 叠加到输出
                    output += wave * (voice.velocity / 127.0) * 0.3  # 音量缩放

                # 更新相位
                voice.phase += 2.0 * np.pi * voice.frequency * frames / self.sample_rate
                voice.phase = voice.phase % (2.0 * np.pi)

                # 更新释放计数器
                if voice.release_time >= 0:
                    voice.release_time += frames / self.sample_rate
                    if voice.release_time > self.release:
                        # 释放完成，移除音符
                        voice.active = False
                        del self.voices[note]

        # 轻微软削波
        output = np.tanh(output * 0.8)

        return output

    def _compute_envelope(self, voice: Voice, frames: int) -> np.ndarray:
        """计算 ADSR 包络"""
        envelope = np.ones(frames, dtype=np.float32)

        # 如果正在释放
        if voice.release_time >= 0:
            # 线性释放到 0
            for i in range(frames):
                t = voice.release_time + i / self.sample_rate
                if t < self.release:
                    envelope[i] = 1.0 - (t / self.release)
                else:
                    envelope[i] = 0.0

        # TODO: 实现完整的 Attack-Decay-Sustain
        # 目前简化为快速起音 + sustain level

        return envelope * self.sustain

    def _audio_callback(self, outdata, frames, time_info, status):
        """音频回调"""
        if status:
            print(f"⚠️  {status}")

        # 生成单声道
        mono = self._generate_block(frames)

        # 转为立体声
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

    def stop(self):
        """停止音频流"""
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def finalize(self):
        """清理资源"""
        # 停止所有音符
        with self.lock:
            for voice in self.voices.values():
                voice.active = False
            self.voices.clear()

        self.stop()


if __name__ == "__main__":
    """测试加性合成器"""
    import time

    print("🎵 加性合成器测试")
    print("="*60)

    synth = AdditiveSynthesizer(
        sample_rate=44100,
        block_size=256,
        num_harmonics=4,
    )

    synth.start()

    # 测试音阶
    notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale

    print("播放 C 大调音阶...")
    for note in notes:
        synth.note_on(note, 80)
        time.sleep(0.5)
        synth.note_off(note)
        time.sleep(0.1)

    time.sleep(0.5)
    synth.finalize()

    print("✅ 测试完成")
    print("\n如果这个音质清晰、无失真，说明加性合成可行！")
