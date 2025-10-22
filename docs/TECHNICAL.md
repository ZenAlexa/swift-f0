# 技术文档

> 最后更新：2024-10-22
> 版本：v0.4.0

## 核心技术原理

### 为什么能实时？
1. **固定采样率** - 16kHz，SwiftF0模型训练优化
2. **滑动窗口** - 不等待完整音频，增量处理
3. **简单合成** - 查表式波形生成，避免复杂计算
4. **流式架构** - 输入输出并行，无阻塞

### 为什么准确？
1. **CNN模型** - 深度学习提取音高特征
2. **STFT预处理** - 时频域联合分析
3. **置信度筛选** - 只处理高置信度帧
4. **平滑处理** - 相位连续，避免跳变

### 为什么轻量？
1. **ONNX优化** - 模型压缩到389KB
2. **定点计算** - 减少浮点运算
3. **预分配缓冲** - 避免动态内存分配
4. **单线程设计** - 简化同步开销

## 系统架构

### 整体架构图
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Audio Input  │────▶│   SwiftF0    │────▶│  Synthesizer │
│  (16kHz)     │     │   (ONNX)     │     │   (Sine)     │
└──────────────┘     └──────────────┘     └──────────────┘
        ↓                    ↓                    ↓
   [Sounddevice]        [CNN Model]         [Simple Synth]
```

## 核心算法

### 1. 音高检测（SwiftF0）

**STFT参数**:
```python
SAMPLE_RATE = 16000      # Hz
WINDOW_SIZE = 1024       # samples (64ms)
HOP_SIZE = 256          # samples (16ms)
PADDING = 384           # samples
```

**CNN模型**:
- 输入：STFT频谱
- 输出：音高(Hz) + 置信度
- 模型大小：389KB
- 推理时间：~10ms

### 2. 音色合成

#### 2.1 波表合成（Additive Synthesis）

**核心思想**：预计算包含谐波的波表，实时查表+插值生成音频。

**实现文件**：
- [wavetable_generator.py](../swift_f0/realtime/wavetable_generator.py) - 波表生成
- [additive_synthesizer.py](../swift_f0/realtime/additive_synthesizer.py) - 合成引擎

**乐器谐波模型**：
```python
INSTRUMENT_HARMONICS = {
    'flute': [
        (1, 1.00), (2, 0.33), (3, 0.08), (4, 0.13),
        (5, 0.12), (6, 0.02), (7, 0.12), (8, 0.05)
    ],
    'violin': [
        (h, 1.0/h) for h in range(1, 17)  # 1/n衰减规律
    ],
    'clarinet': [
        (1, 1.00), (3, 0.75), (5, 0.50), (7, 0.35),
        (9, 0.25), (11, 0.15), (13, 0.10), (15, 0.08),
        (2, 0.10), (4, 0.05), (6, 0.03), (8, 0.02)
    ],
}
```

**波表生成算法（FFT方法）**：
```python
def generate_wavetable_fft(harmonics, table_size=4096):
    # 1. 构建频域表示
    spectrum = np.zeros(table_size, dtype=np.complex128)
    for harmonic_num, amplitude in harmonics:
        if harmonic_num < table_size // 2:
            spectrum[harmonic_num] = amplitude
            spectrum[-harmonic_num] = amplitude  # 共轭对称

    # 2. IFFT转换到时域
    wavetable = np.fft.ifft(spectrum).real

    # 3. 归一化
    max_val = np.max(np.abs(wavetable))
    if max_val > 0:
        wavetable /= max_val

    return wavetable.astype(np.float32)
```

**实时合成算法（线性插值）**：
```python
def synthesize(self, frequency, n_samples, amplitude=1.0):
    # 1. 计算相位增量
    phase_increment = frequency * table_size / sample_rate

    # 2. 生成相位序列
    phases = self.phase + np.arange(n_samples) * phase_increment
    phases = phases % table_size

    # 3. 线性插值读取波表
    indices = phases.astype(np.int32)
    frac = phases - indices
    indices_next = (indices + 1) % table_size

    samples = (1.0 - frac) * wavetable[indices] + frac * wavetable[indices_next]

    # 4. 更新相位（保持连续）
    self.phase = (self.phase + n_samples * phase_increment) % table_size

    return (samples * amplitude).astype(np.float32)
```

**性能优势**：
- ⚡ **O(1)复杂度** - 预计算消除实时谐波累加
- 🎯 **高保真** - FFT保证精确谐波关系
- 🔊 **零爆音** - 相位连续避免不连续点
- 💾 **低内存** - 4096样本 × 4字节 = 16KB/波表

#### 2.2 简单正弦波合成（Simple Synthesis）

**向后兼容模式**，用于基础测试：
```python
def synthesize_sine(frequency, amplitude, n_samples):
    phase_increment = 2 * π * frequency / sample_rate
    phases = current_phase + np.arange(n_samples) * phase_increment
    signal = amplitude * np.sin(phases)
    return signal
```

**相位连续性**：
- 保持相位状态避免咔嗒声
- 平滑幅度过渡

### 3. 幅度平滑与快速衰减

**问题**：用户停止哼唱后，声音持续数秒（平滑系数过高导致）

**解决方案**（实现于 [usb_processor.py:165-181](../swift_f0/realtime/usb_processor.py#L165-L181)）：
```python
# 平滑过渡
if self.target_amp > 0:
    # 有声音 - 正常平滑
    self.current_freq = 0.85 * self.current_freq + 0.15 * self.target_freq
    self.current_amp = 0.85 * self.current_amp + 0.15 * self.target_amp
else:
    # 静音状态 - 快速衰减
    self.current_amp *= 0.7  # 每帧减少30%
    if self.current_amp < 0.001:
        self.current_amp = 0.0
        self.current_freq = 0.0
```

**效果**：
- ✅ 停止哼唱后 0.1-0.2 秒内静音（3-5帧）
- ✅ 保持正常声音的平滑过渡
- ✅ 避免爆音和卡顿

### 4. 缓冲管理

**滑动窗口**:
```python
window_buffer[:-chunk_size] = window_buffer[chunk_size:]
window_buffer[-chunk_size:] = new_audio
```

## 实时处理流程

### 音频回调函数
```python
def audio_callback(indata, outdata, frames, time_info, status):
    # 1. 更新缓冲区
    update_buffer(indata)

    # 2. 检测音高
    pitch, confidence = detect_pitch(buffer)

    # 3. 合成音频
    output = synthesize(pitch, confidence, frames)

    # 4. 输出
    outdata[:] = output
```

### 延迟分析

| 组件 | 延迟 | 说明 |
|------|------|------|
| 输入缓冲 | 16ms | chunk_size=256 |
| 窗口填充 | 64ms | window_size=1024 |
| 处理 | ~10ms | 音高检测+合成 |
| 输出缓冲 | 0ms | 直接输出 |
| **总计** | **~90ms** | 实测~80ms |

## 配置系统

### 配置文件结构
```yaml
audio:
  sample_rate: 16000
  chunk_size: 256

pitch_detection:
  window_size: 1024
  confidence_threshold: 0.85

synthesis:
  method: "additive"        # additive 或 simple
  instrument: "flute"       # sine, flute, violin, clarinet
  volume: 0.8
```

### 配置加载
```python
config = ConfigManager().load("config/realtime_config.yaml")
```

## 性能优化

### CPU优化
1. **向量化运算** - 使用NumPy
2. **避免内存分配** - 预分配缓冲区
3. **简化计算** - 查表替代三角函数

### 延迟优化
1. **减小窗口** - 512样本（32ms）
2. **增量STFT** - 只计算新数据
3. **并行处理** - 分离I/O和处理线程

## USB音频集成

### 数据帧格式
```
[Magic:2] [SeqNum:2] [Length:2] [Data:N] [Checksum:2]
```
- Magic: 0xAA55 (同步标志)
- SeqNum: 帧序号 (0-65535循环)
- Length: 音频数据长度
- Data: PCM音频 (int16)
- Checksum: 校验和

### 串口参数
- 波特率: 2000000 bps
- 数据位: 8
- 停止位: 1
- 无校验

### 重采样
ESP32 (24kHz) → SwiftF0 (16kHz)
- 线性插值重采样
- 比率: 2/3

## API接口

### USBProcessor
```python
config = USBProcessorConfig(
    serial_port='/dev/tty.usbmodem1101',
    baudrate=2000000,
    input_sample_rate=24000
)
processor = USBProcessor(config)
processor.open()
frame = processor.receiver.receive_frame()
output = processor.process_frame(frame)
```

### StreamProcessor
```python
stream = AudioStreamWithOutput(config)
stream.set_pitch_callback(on_pitch)
stream.start()
```

### SimpleSynthesizer
```python
synth = SimpleSynthesizer(config)
output = synth.process_pitch(pitch_hz, confidence, n_samples)
```

## 开发板集成接口

### USB音频模式
```python
# 配置指定设备
config.audio.device_in = "USB Audio Device"
```

### 自定义协议
```python
class BoardInterface:
    def read_audio(self) -> np.ndarray:
        # 从串口/SPI读取
        pass

    def write_audio(self, data: np.ndarray):
        # 写入到开发板
        pass
```

## 依赖关系

### 核心依赖
- `onnxruntime` - 模型推理
- `numpy` - 数值计算
- `sounddevice` - 音频I/O

### 可选依赖
- `pyfluidsynth` - 高级音色合成
- `scipy` - 信号处理
- `matplotlib` - 可视化

## 测试方法

### 延迟测试
```bash
# 使用音频环回测试
python test_latency.py
```

### 性能测试
```python
import cProfile
cProfile.run('stream.process_chunk(audio)')
```

## 故障排查

### 常见问题

1. **音频断续**
   - 增大buffer_size
   - 检查CPU占用

2. **延迟过高**
   - 减小chunk_size
   - 优化处理算法

3. **音高不准**
   - 调整confidence_threshold
   - 检查输入音频质量

---
*此文档记录技术实现细节，持续更新*