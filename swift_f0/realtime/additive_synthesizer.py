#!/usr/bin/env python3
"""
加法波表合成器 - 高性能实时乐器音色合成

基于预计算波表的加法合成实现，支持多种乐器音色
"""

import numpy as np
import os
from typing import Dict, Optional


class AdditiveSynthesizer:
    """
    加法波表合成器

    使用预计算的波表实现高效的实时音色合成
    """

    def __init__(self, sample_rate: int = 16000, wavetable_dir: str = "wavetables"):
        """
        初始化合成器

        Args:
            sample_rate: 采样率（Hz）
            wavetable_dir: 波表目录路径
        """
        self.sample_rate = sample_rate
        self.wavetable_dir = wavetable_dir

        # 相位累积器（保证连续性）
        self.phase = 0.0  # [0, table_size)

        # 波表库
        self.wavetables: Dict[str, np.ndarray] = {}
        self.current_instrument = 'sine'  # 默认乐器

        # 音色状态
        self.current_freq = 0.0
        self.current_amp = 0.0

        # 加载波表
        self._load_wavetables()

    def _load_wavetables(self):
        """加载所有波表"""
        instruments = ['sine', 'flute', 'violin', 'clarinet']

        for inst in instruments:
            path = os.path.join(self.wavetable_dir, f"{inst}.npy")
            if os.path.exists(path):
                self.wavetables[inst] = np.load(path)
                print(f"✓ 加载波表: {inst} ({len(self.wavetables[inst])} 样本)")
            else:
                # 回退到纯正弦波
                if inst == 'sine' or len(self.wavetables) == 0:
                    print(f"⚠ 未找到 {path}，生成纯正弦波")
                    table_size = 4096
                    phase = np.linspace(0, 2*np.pi, table_size, endpoint=False)
                    self.wavetables[inst] = np.sin(phase).astype(np.float32)

        if not self.wavetables:
            raise RuntimeError(f"无法加载任何波表，检查目录: {self.wavetable_dir}")

        print(f"✓ 波表加载完成，可用乐器: {list(self.wavetables.keys())}")

    def set_instrument(self, instrument: str):
        """
        切换乐器

        Args:
            instrument: 乐器名称 ('flute', 'violin', 'clarinet', 'sine')
        """
        if instrument in self.wavetables:
            self.current_instrument = instrument
            # 重置相位避免爆音
            self.phase = 0.0
            print(f"切换乐器: {instrument}")
        else:
            print(f"⚠ 未知乐器: {instrument}，可用: {list(self.wavetables.keys())}")

    def synthesize(
        self,
        frequency: float,
        n_samples: int,
        amplitude: float = 1.0
    ) -> np.ndarray:
        """
        合成音频块（高性能波表插值）

        Args:
            frequency: 基频（Hz）
            n_samples: 样本数量
            amplitude: 振幅 [0.0, 1.0]

        Returns:
            音频样本数组 (float32)
        """
        # 获取当前乐器波表
        wavetable = self.wavetables[self.current_instrument]
        table_size = len(wavetable)

        # 计算相位增量（每样本前进多少个波表索引）
        # phase_increment = frequency * table_size / sample_rate
        phase_increment = frequency * table_size / self.sample_rate

        # 生成相位数组
        phases = self.phase + np.arange(n_samples) * phase_increment

        # 模运算保持在 [0, table_size)
        phases = phases % table_size

        # 线性插值读取波表
        indices = phases.astype(np.int32)  # 整数部分
        frac = phases - indices             # 小数部分

        # 下一个索引（循环）
        indices_next = (indices + 1) % table_size

        # 插值: sample = (1-frac) * table[i] + frac * table[i+1]
        samples = (
            (1.0 - frac) * wavetable[indices] +
            frac * wavetable[indices_next]
        )

        # 更新相位（保持连续性）
        self.phase = (self.phase + n_samples * phase_increment) % table_size

        # 应用振幅
        samples *= amplitude

        return samples.astype(np.float32)

    def process_pitch(
        self,
        pitch_hz: Optional[float],
        confidence: float,
        n_samples: int,
        volume: float = 0.8
    ) -> np.ndarray:
        """
        处理检测到的音高并生成音频（兼容现有API）

        Args:
            pitch_hz: 检测到的音高（Hz），None表示无音
            confidence: 置信度 [0.0, 1.0]
            n_samples: 样本数量
            volume: 整体音量

        Returns:
            音频样本数组
        """
        if pitch_hz is None or pitch_hz <= 0 or confidence < 0.5:
            # 无有效音高 - 静音
            return np.zeros(n_samples, dtype=np.float32)

        # 计算振幅（基于置信度）
        amplitude = min(1.0, confidence) * volume

        # 合成
        return self.synthesize(pitch_hz, n_samples, amplitude)

    def reset(self):
        """重置合成器状态"""
        self.phase = 0.0
        self.current_freq = 0.0
        self.current_amp = 0.0

    def cleanup(self):
        """清理资源"""
        pass  # 波表合成器无需清理

    def get_info(self) -> dict:
        """获取合成器信息"""
        return {
            'type': 'additive_wavetable',
            'sample_rate': self.sample_rate,
            'current_instrument': self.current_instrument,
            'available_instruments': list(self.wavetables.keys()),
            'wavetable_size': len(self.wavetables.get(self.current_instrument, [])),
        }


# 向后兼容：别名
AdditiveWavetableSynthesizer = AdditiveSynthesizer