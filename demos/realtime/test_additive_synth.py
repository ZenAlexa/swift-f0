#!/usr/bin/env python3
"""
测试加法波表合成器

生成测试音频验证音色质量
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import numpy as np
from swift_f0.realtime.additive_synthesizer import AdditiveSynthesizer


def generate_test_tone(synth, frequency, duration, instrument):
    """生成测试音"""
    synth.set_instrument(instrument)

    sample_rate = synth.sample_rate
    n_samples = int(duration * sample_rate)

    # 生成音频
    audio = synth.synthesize(frequency, n_samples, amplitude=0.8)

    return audio


def main():
    print("=" * 60)
    print("加法波表合成器测试")
    print("=" * 60)

    # 创建合成器
    synth = AdditiveSynthesizer(sample_rate=16000, wavetable_dir="wavetables")

    # 打印信息
    info = synth.get_info()
    print(f"\n合成器信息:")
    print(f"  采样率: {info['sample_rate']} Hz")
    print(f"  当前乐器: {info['current_instrument']}")
    print(f"  可用乐器: {info['available_instruments']}")
    print(f"  波表大小: {info['wavetable_size']} 样本")

    # 测试每种乐器
    instruments = ['sine', 'flute', 'clarinet', 'violin']
    frequencies = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
    duration = 1.0  # 1秒

    print(f"\n生成测试音频...")

    for inst in instruments:
        if inst not in synth.wavetables:
            continue

        print(f"\n{inst.upper()}:")
        for i, freq in enumerate(frequencies):
            note_names = ['C4', 'E4', 'G4', 'C5']
            audio = generate_test_tone(synth, freq, duration, inst)

            # 保存
            filename = f"test_{inst}_{note_names[i]}.wav"

            # 简单的WAV写入
            try:
                import scipy.io.wavfile as wavfile
                # 转换为int16
                audio_int16 = (audio * 32767).astype(np.int16)
                wavfile.write(filename, synth.sample_rate, audio_int16)
                print(f"  ✓ {note_names[i]} ({freq:.2f} Hz) -> {filename}")
            except ImportError:
                print(f"  ⚠ 需要scipy来保存WAV文件")
                print(f"  生成了 {len(audio)} 样本，RMS={np.sqrt(np.mean(audio**2)):.3f}")

    print(f"\n{'='*60}")
    print("✓ 测试完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()