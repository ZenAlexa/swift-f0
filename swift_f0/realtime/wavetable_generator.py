#!/usr/bin/env python3
"""
波表生成工具 - 为加法合成器创建乐器波表

基于谐波分析数据生成高质量的波表库
"""

import numpy as np
import os
from typing import List, Tuple


# 乐器谐波数据（基于调研）
INSTRUMENT_HARMONICS = {
    'flute': [
        # 长笛 - 纯净音色，基频主导
        (1, 1.00),   # H1: 基频
        (2, 0.33),   # H2
        (3, 0.08),   # H3
        (4, 0.13),   # H4
        (5, 0.12),   # H5
        (6, 0.02),   # H6
        (7, 0.12),   # H7
        (8, 0.05),   # H8
    ],

    'violin': [
        # 小提琴 - 锯齿波近似，1/n规律
        (1, 1.00),    # H1
        (2, 0.50),    # H2: 1/2
        (3, 0.33),    # H3: 1/3
        (4, 0.25),    # H4: 1/4
        (5, 0.20),    # H5: 1/5
        (6, 0.17),    # H6: 1/6
        (7, 0.14),    # H7: 1/7
        (8, 0.13),    # H8: 1/8
        (9, 0.11),    # H9
        (10, 0.10),   # H10
        (11, 0.09),   # H11
        (12, 0.08),   # H12
        (13, 0.08),   # H13
        (14, 0.07),   # H14
        (15, 0.07),   # H15
        (16, 0.06),   # H16
    ],

    'clarinet': [
        # 单簧管 - 奇次谐波主导
        (1, 1.00),    # H1: 基频（奇）
        (2, 0.10),    # H2: 偶次弱
        (3, 0.75),    # H3: 强（奇）
        (4, 0.05),    # H4: 偶次弱
        (5, 0.50),    # H5: 强（奇）
        (6, 0.03),    # H6
        (7, 0.35),    # H7: （奇）
        (8, 0.02),    # H8
        (9, 0.25),    # H9: （奇）
        (10, 0.02),   # H10
        (11, 0.15),   # H11: （奇）
        (12, 0.01),   # H12
    ],

    'sine': [
        # 纯正弦波（后备/对比）
        (1, 1.00),
    ],
}


def generate_wavetable_additive(
    harmonics: List[Tuple[int, float]],
    table_size: int = 4096
) -> np.ndarray:
    """
    使用加法合成生成波表（时域法）

    Args:
        harmonics: 谐波列表 [(谐波次数, 振幅), ...]
        table_size: 波表大小（建议2的幂次）

    Returns:
        归一化的波表数组
    """
    wavetable = np.zeros(table_size, dtype=np.float64)
    phase = np.linspace(0, 2*np.pi, table_size, endpoint=False)

    # 叠加所有谐波
    for harmonic_num, amplitude in harmonics:
        wavetable += amplitude * np.sin(harmonic_num * phase)

    # 归一化防止削波
    max_val = np.max(np.abs(wavetable))
    if max_val > 0:
        wavetable /= max_val

    return wavetable.astype(np.float32)


def generate_wavetable_fft(
    harmonics: List[Tuple[int, float]],
    table_size: int = 4096
) -> np.ndarray:
    """
    使用IFFT生成波表（频域法，更快）

    Args:
        harmonics: 谐波列表 [(谐波次数, 振幅), ...]
        table_size: 波表大小

    Returns:
        归一化的波表数组
    """
    # 创建频谱
    spectrum = np.zeros(table_size, dtype=np.complex128)

    # 填充谐波（正负频率对称）
    for harmonic_num, amplitude in harmonics:
        if harmonic_num < table_size // 2:
            # 正频率
            spectrum[harmonic_num] = amplitude
            # 负频率（共轭对称，保证实数输出）
            spectrum[-harmonic_num] = amplitude

    # IFFT得到时域波形
    wavetable = np.fft.ifft(spectrum).real

    # 归一化
    max_val = np.max(np.abs(wavetable))
    if max_val > 0:
        wavetable /= max_val

    return wavetable.astype(np.float32)


def analyze_wavetable(wavetable: np.ndarray, name: str = ""):
    """
    分析并打印波表统计信息
    """
    print(f"\n{'='*60}")
    print(f"波表分析: {name}")
    print(f"{'='*60}")
    print(f"大小: {len(wavetable)} 样本")
    print(f"最大值: {np.max(wavetable):.4f}")
    print(f"最小值: {np.min(wavetable):.4f}")
    print(f"RMS: {np.sqrt(np.mean(wavetable**2)):.4f}")
    print(f"峰值因子: {np.max(np.abs(wavetable)) / (np.sqrt(np.mean(wavetable**2)) + 1e-10):.2f}")

    # FFT分析前16个谐波
    spectrum = np.fft.rfft(wavetable)
    magnitudes = np.abs(spectrum)

    print(f"\n前16个谐波振幅:")
    for i in range(1, min(17, len(magnitudes))):
        db = 20 * np.log10(magnitudes[i] / magnitudes[1] + 1e-10)
        print(f"  H{i:2d}: {magnitudes[i]/magnitudes[1]:6.3f} ({db:+6.1f} dB)")


def generate_all_wavetables(
    output_dir: str = "wavetables",
    table_size: int = 4096,
    method: str = "fft"  # 'fft' or 'additive'
):
    """
    生成所有乐器波表并保存

    Args:
        output_dir: 输出目录
        table_size: 波表大小
        method: 生成方法（'fft'快，'additive'清晰）
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 选择生成函数
    if method == "fft":
        generate_func = generate_wavetable_fft
        print(f"使用FFT方法生成波表（快速）")
    else:
        generate_func = generate_wavetable_additive
        print(f"使用加法方法生成波表（精确）")

    print(f"波表大小: {table_size} 样本")
    print(f"输出目录: {output_dir}/")

    # 生成每种乐器
    for instrument_name, harmonics in INSTRUMENT_HARMONICS.items():
        print(f"\n生成 {instrument_name} 波表...")

        # 生成波表
        wavetable = generate_func(harmonics, table_size)

        # 保存
        output_path = os.path.join(output_dir, f"{instrument_name}.npy")
        np.save(output_path, wavetable)
        print(f"✓ 已保存: {output_path}")

        # 分析
        analyze_wavetable(wavetable, instrument_name.upper())

    print(f"\n{'='*60}")
    print(f"✓ 所有波表生成完成！")
    print(f"{'='*60}\n")


def plot_wavetables(wavetable_dir: str = "wavetables"):
    """
    可视化波表（需要matplotlib）
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("需要安装 matplotlib: pip install matplotlib")
        return

    instruments = ['sine', 'flute', 'clarinet', 'violin']
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    for idx, inst in enumerate(instruments):
        path = os.path.join(wavetable_dir, f"{inst}.npy")
        if not os.path.exists(path):
            continue

        wavetable = np.load(path)

        # 只显示一个周期
        axes[idx].plot(wavetable, linewidth=0.8)
        axes[idx].set_title(f"{inst.upper()} Wavetable", fontsize=12, fontweight='bold')
        axes[idx].set_xlabel("Sample")
        axes[idx].set_ylabel("Amplitude")
        axes[idx].grid(True, alpha=0.3)
        axes[idx].set_ylim(-1.1, 1.1)

    plt.tight_layout()
    plt.savefig(os.path.join(wavetable_dir, "wavetables_plot.png"), dpi=150)
    print(f"✓ 波形图已保存: {wavetable_dir}/wavetables_plot.png")
    plt.show()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='波表生成工具')
    parser.add_argument('--output', '-o', default='wavetables',
                        help='输出目录')
    parser.add_argument('--size', '-s', type=int, default=4096,
                        help='波表大小（建议2的幂次）')
    parser.add_argument('--method', '-m', choices=['fft', 'additive'], default='fft',
                        help='生成方法')
    parser.add_argument('--plot', '-p', action='store_true',
                        help='生成波形图')

    args = parser.parse_args()

    # 生成波表
    generate_all_wavetables(
        output_dir=args.output,
        table_size=args.size,
        method=args.method
    )

    # 可视化
    if args.plot:
        plot_wavetables(args.output)


if __name__ == "__main__":
    main()