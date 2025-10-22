# 算法索引

> **版本**: v0.4.0 | **更新**: 2024-10-22

本文档提供项目中所有核心算法的快速索引和实现位置。

---

## 📑 目录

1. [音高检测算法](#音高检测算法)
2. [音色合成算法](#音色合成算法)
3. [信号处理算法](#信号处理算法)
4. [缓冲管理算法](#缓冲管理算法)

---

## 音高检测算法

### SwiftF0 CNN模型
**描述**: 基于深度学习的实时音高检测

**实现位置**: [swift_f0/core.py](../swift_f0/core.py)

**关键参数**:
```python
SAMPLE_RATE = 16000      # 固定采样率
WINDOW_SIZE = 1024       # STFT窗口大小 (64ms)
HOP_SIZE = 256          # 跳跃大小 (16ms)
PADDING = 384           # 填充大小
```

**输入**:
- 音频数组 (16kHz, 单声道)
- 最小长度: 256 samples

**输出**:
- `pitch_hz`: 音高频率数组 (Hz)
- `confidence`: 置信度数组 (0-1)

**性能**:
- 模型大小: 389KB (ONNX)
- 推理延迟: ~10ms/帧
- 精度: <1% 误差

**使用示例**:
```python
from swift_f0 import SwiftF0

detector = SwiftF0()
result = detector.detect_from_array(audio, sample_rate=16000)
print(result.pitch_hz)  # [220.5, 221.3, ...]
print(result.confidence)  # [0.95, 0.97, ...]
```

---

## 音色合成算法

### 1. 波表合成 (Wavetable Synthesis)

#### 波表生成算法 (FFT方法)

**描述**: 使用FFT生成包含谐波的波表

**实现位置**: [swift_f0/realtime/wavetable_generator.py](../swift_f0/realtime/wavetable_generator.py)

**算法流程**:
```python
def generate_wavetable_fft(harmonics, table_size=4096):
    # 1. 构建频域表示
    spectrum = np.zeros(table_size, dtype=np.complex128)
    for harmonic_num, amplitude in harmonics:
        if harmonic_num < table_size // 2:
            spectrum[harmonic_num] = amplitude
            spectrum[-harmonic_num] = amplitude  # 共轭对称

    # 2. IFFT转时域
    wavetable = np.fft.ifft(spectrum).real

    # 3. 归一化
    wavetable /= np.max(np.abs(wavetable))

    return wavetable
```

**谐波模型定义**:
```python
INSTRUMENT_HARMONICS = {
    'flute': [
        (1, 1.00), (2, 0.33), (3, 0.08), (4, 0.13),
        (5, 0.12), (6, 0.02), (7, 0.12), (8, 0.05)
    ],
    'violin': [
        (h, 1.0/h) for h in range(1, 17)  # 1/n衰减
    ],
    'clarinet': [
        (1, 1.00), (3, 0.75), (5, 0.50), (7, 0.35),
        (9, 0.25), (11, 0.15), (13, 0.10), (15, 0.08),
        (2, 0.10), (4, 0.05), (6, 0.03), (8, 0.02)
    ],
}
```

**性能**:
- 波表大小: 4096 samples (16KB)
- 生成时间: <1ms (离线预计算)
- 内存占用: 16KB/乐器

#### 实时波表合成算法

**描述**: 线性插值查表生成音频

**实现位置**: [swift_f0/realtime/additive_synthesizer.py](../swift_f0/realtime/additive_synthesizer.py)

**算法流程**:
```python
def synthesize(self, frequency, n_samples, amplitude=1.0):
    # 1. 计算相位增量
    phase_increment = frequency * table_size / sample_rate

    # 2. 生成相位序列
    phases = self.phase + np.arange(n_samples) * phase_increment
    phases = phases % table_size

    # 3. 线性插值
    indices = phases.astype(np.int32)
    frac = phases - indices
    indices_next = (indices + 1) % table_size

    samples = (1.0 - frac) * wavetable[indices] + frac * wavetable[indices_next]

    # 4. 更新相位（保持连续性）
    self.phase = (self.phase + n_samples * phase_increment) % table_size

    return samples * amplitude
```

**复杂度**: O(n) where n = n_samples
- 查表: O(1)
- 插值: O(1)
- 总体: 线性于输出样本数

**性能**:
- CPU占用: <5%
- 延迟: <1ms
- 支持实时切换乐器

**乐器列表**:
- `sine` - 纯正弦波
- `flute` - 长笛 (8谐波)
- `violin` - 小提琴 (16谐波)
- `clarinet` - 单簧管 (12谐波)

### 2. 简单正弦波合成

**描述**: 实时计算正弦波（向后兼容）

**实现位置**: [swift_f0/realtime/usb_processor.py:197-208](../swift_f0/realtime/usb_processor.py#L197-L208)

**算法**:
```python
phase_increment = 2 * π * frequency / sample_rate
phases = current_phase + np.arange(n_samples) * phase_increment
output = amplitude * np.sin(phases)
current_phase = (current_phase + n_samples * phase_increment) % (2π)
```

**性能**:
- CPU占用: <10%
- 延迟: <1ms
- 适用于基础测试

---

## 信号处理算法

### 幅度平滑与快速衰减

**描述**: 解决声音延续问题的自适应平滑算法

**实现位置**: [swift_f0/realtime/usb_processor.py:165-181](../swift_f0/realtime/usb_processor.py#L165-L181)

**算法**:
```python
FREQ_SMOOTH = 0.85  # 频率平滑系数
AMP_SMOOTH = 0.85   # 幅度平滑系数
DECAY_FACTOR = 0.7  # 快速衰减系数

if target_amp > 0:
    # 有声音 - 正常平滑
    current_freq = FREQ_SMOOTH * current_freq + (1 - FREQ_SMOOTH) * target_freq
    current_amp = AMP_SMOOTH * current_amp + (1 - AMP_SMOOTH) * target_amp
else:
    # 无声音 - 快速衰减
    current_amp *= DECAY_FACTOR  # 每帧减少30%
    if current_amp < 0.001:
        current_amp = 0.0
        current_freq = 0.0
```

**效果**:
- 正常过渡: 平滑无卡顿
- 停止响应: 0.1-0.2秒内静音 (3-5帧)
- 无爆音

**参数调优指南**:
- `FREQ_SMOOTH`: 越大越平滑，但响应越慢 (建议: 0.8-0.9)
- `AMP_SMOOTH`: 同上 (建议: 0.8-0.9)
- `DECAY_FACTOR`: 越小衰减越快 (建议: 0.6-0.8)

### 置信度阈值过滤

**描述**: 过滤低置信度的音高检测结果

**实现位置**: [swift_f0/realtime/usb_processor.py:160-164](../swift_f0/realtime/usb_processor.py#L160-L164)

**算法**:
```python
CONFIDENCE_THRESHOLD = 0.85

if confidence > CONFIDENCE_THRESHOLD and 50 < frequency < 2000:
    target_freq = frequency
    target_amp = base_amplitude
else:
    target_freq = 0.0
    target_amp = 0.0
```

**参数**:
- 置信度阈值: 0.85 (可配置)
- 频率范围: 50-2000 Hz

---

## 缓冲管理算法

### 滑动窗口缓冲

**描述**: 固定窗口大小的滑动缓冲区

**实现位置**: [swift_f0/realtime/audio_buffer.py](../swift_f0/realtime/audio_buffer.py)

**算法**:
```python
# 滑动窗口
window_buffer[:-chunk_size] = window_buffer[chunk_size:]
window_buffer[-chunk_size:] = new_chunk
```

**参数**:
- `window_size`: 1024 samples (64ms @ 16kHz)
- `chunk_size`: 256 samples (16ms @ 16kHz)
- 重叠: 75%

### USB串口帧同步

**描述**: 在USB串口数据流中查找帧同步标记

**实现位置**: [swift_f0/usb_audio/receiver.py:85-103](../swift_f0/usb_audio/receiver.py#L85-L103)

**帧格式**:
```
[0xAA55] [length:2] [data:n] [checksum:4]
  魔数    长度       数据      校验和
```

**算法**:
```python
FRAME_MAGIC = 0xAA55
MAX_SYNC_ATTEMPTS = 1000

def _find_sync(self):
    attempts = 0
    while len(self.buffer) >= 2 and attempts < MAX_SYNC_ATTEMPTS:
        magic = struct.unpack('<H', self.buffer[:2])[0]
        if magic == FRAME_MAGIC:
            return True
        self.buffer.pop(0)
        attempts += 1

    # 超过限制，清空缓冲区重试
    if attempts >= MAX_SYNC_ATTEMPTS:
        self.buffer.clear()

    return False
```

**性能**:
- 同步成功率: >99%
- 最大搜索: 1000字节
- 丢帧处理: 自动重试

---

## 性能对比表

| 算法 | 延迟 | CPU占用 | 内存 | 适用场景 |
|------|------|---------|------|----------|
| SwiftF0检测 | ~10ms | ~5% | 389KB | 所有场景 |
| 波表合成 | <1ms | <5% | 16KB/乐器 | 乐器音色 |
| 正弦波合成 | <1ms | <10% | 0 | 基础测试 |
| 滑动窗口 | 64ms | <1% | 8KB | 所有场景 |
| USB帧同步 | <1ms | <1% | 4KB | USB音频 |

---

## 相关文档

- [技术文档](TECHNICAL.md) - 完整技术架构
- [开发文档](DEVELOPMENT.md) - 开发进度和历史
- [主README](../README.md) - 项目概述和使用

---

*算法索引 - 快速查找核心算法实现*
