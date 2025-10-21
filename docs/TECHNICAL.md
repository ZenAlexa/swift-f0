# 技术文档

> 最后更新：2024-10-21
> 版本：v0.2.0-realtime

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

**简单波形合成**:
```python
def synthesize_sine(frequency, amplitude, n_samples):
    phase_increment = 2 * π * frequency / sample_rate
    phases = current_phase + np.arange(n_samples) * phase_increment
    signal = amplitude * np.sin(phases)
    return signal
```

**相位连续性**:
- 保持相位状态避免咔嗒声
- 平滑幅度过渡

### 3. 缓冲管理

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
  method: "simple"
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

## API接口

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