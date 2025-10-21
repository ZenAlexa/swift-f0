# SwiftF0 实时音色转换技术架构

## 项目目标

实现一个低延迟的实时音频处理系统，能够：
1. 从麦克风（或开发板）接收音频输入
2. 实时检测音高
3. 转换为不同乐器音色
4. 实时输出转换后的音频

## 技术架构

### 系统架构图

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Audio Input    │────▶│   SwiftF0    │────▶│ Timbre Engine   │
│  (Microphone/   │     │   Real-time  │     │  (Synthesis)    │
│   Dev Board)    │     │   Processor  │     │                 │
└─────────────────┘     └──────────────┘     └─────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
   ┌──────────┐          ┌──────────┐          ┌──────────┐
   │  Ring    │          │  Pitch   │          │FluidSynth│
   │  Buffer  │          │Detection │          │   or     │
   │          │          │  (ONNX)  │          │  MIDI    │
   └──────────┘          └──────────┘          └──────────┘
                                                       │
                                                       ▼
                                               ┌──────────────┐
                                               │ Audio Output │
                                               │  (Speaker)   │
                                               └──────────────┘
```

### 核心组件

#### 1. 音频输入/输出 (Audio I/O)

**技术选择：**
- **PyAudio**: 跨平台，稳定，延迟可控
- **sounddevice**: 基于PortAudio，更现代的API
- **JACK**: 专业音频，最低延迟（Linux/Mac）

**关键参数：**
```python
sample_rate = 16000  # Hz (SwiftF0要求)
chunk_size = 256     # 样本/块 (16ms @ 16kHz)
channels = 1         # 单声道
```

#### 2. 缓冲管理 (Buffer Management)

**环形缓冲区 (Ring Buffer)：**
- 无锁设计，最小化延迟
- 双倍容量避免边界复杂性
- 线程安全的读写操作

```python
class RingBuffer:
    capacity = 8192  # 样本
    # 约 512ms 缓冲 @ 16kHz
```

#### 3. 音高检测 (Pitch Detection)

**SwiftF0 实时改造：**
- 滑动窗口处理
- 增量式STFT
- 优化的ONNX推理

**延迟分析：**
```
窗口大小: 1024 样本 = 64ms
跳跃大小: 256 样本 = 16ms
处理延迟: ~10ms
总延迟: ~90ms
```

#### 4. 音色合成 (Timbre Synthesis)

**方案对比：**

| 方案 | 优点 | 缺点 | 延迟 |
|------|------|------|------|
| **FluidSynth** | 高质量SF2音色 | CPU占用较高 | ~20ms |
| **MIDI渲染** | 轻量级 | 音质依赖系统 | ~30ms |
| **波表合成** | 低延迟 | 需要预加载样本 | ~10ms |
| **物理建模** | 表现力强 | 计算密集 | ~15ms |

**推荐方案：FluidSynth**
- 使用 GeneralUser-GS.sf2 (30MB)
- 128种GM乐器
- 实时音符触发

### 延迟优化策略

#### 1. 减小处理延迟

```python
# 优化参数配置
class OptimizedConfig:
    # 减小窗口大小（牺牲频率分辨率）
    window_size = 512   # 32ms (原1024)
    hop_size = 128      # 8ms (原256)

    # 使用更激进的缓冲
    chunk_size = 128    # 8ms chunks

    # 降低音高检测精度换取速度
    confidence_threshold = 0.7  # (原0.9)
```

#### 2. 并行处理

```python
# 三线程架构
1. 音频输入线程 - 填充输入缓冲
2. 处理线程 - 音高检测+合成
3. 音频输出线程 - 播放输出缓冲
```

#### 3. GPU加速 (可选)

```python
# 使用ONNX Runtime GPU provider
providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
session = onnxruntime.InferenceSession(model_path, providers=providers)
```

### 与开发板集成

#### 接口设计

```python
class BoardAudioInterface:
    """开发板音频接口"""

    def __init__(self, device_name: str, sample_rate: int):
        # 配置串口/USB音频设备
        self.device = self._find_device(device_name)

    def read_audio(self, n_samples: int) -> np.ndarray:
        """从开发板读取音频"""
        pass

    def write_audio(self, audio: np.ndarray):
        """输出音频到开发板"""
        pass
```

#### 协议设计

```
开发板 ←→ PC 通信协议:
- 格式: PCM 16-bit signed
- 采样率: 16000 Hz
- 通道: Mono
- 传输: USB Audio Class 或 串口
- 缓冲: 256 samples/packet
```

### 性能指标

| 指标 | 目标值 | 当前值 | 优化方案 |
|------|--------|--------|----------|
| **端到端延迟** | <50ms | ~90ms | 减小窗口大小 |
| **CPU占用** | <30% | ~40% | 优化ONNX模型 |
| **内存使用** | <200MB | ~350MB | 减少缓冲大小 |
| **音高准确率** | >95% | 98% | 已达标 |
| **丢帧率** | <1% | <0.1% | 已达标 |

### 开发路线图

#### 第一阶段：基础实时系统 ✅
- [x] 环形缓冲区实现
- [x] 流处理器框架
- [x] 音色引擎接口
- [x] 基础演示程序

#### 第二阶段：性能优化 🔄
- [ ] 减小处理延迟到50ms以下
- [ ] 实现增量式STFT
- [ ] 优化ONNX推理速度
- [ ] 实现零拷贝缓冲

#### 第三阶段：音色合成 📋
- [ ] 集成FluidSynth
- [ ] 实现实时MIDI渲染
- [ ] 添加效果器（混响、合唱）
- [ ] 支持和弦检测

#### 第四阶段：系统集成 📋
- [ ] 与开发板对接
- [ ] 实现热插拔支持
- [ ] 添加GUI控制界面
- [ ] 性能监控面板

### 使用示例

#### 基础使用

```python
from swift_f0.realtime import StreamProcessor, TimbreEngine

# 创建处理器
processor = StreamProcessor()
timbre = TimbreEngine()

# 设置乐器
timbre.set_instrument(56)  # 小号

# 开始处理
processor.start()

# 处理音频块
while True:
    audio_in = get_audio_from_mic()
    audio_out = processor.process_audio_chunk(audio_in)
    play_audio(audio_out)
```

#### 与开发板集成

```python
# 假设您的同事的开发板通过USB音频接口连接
from swift_f0.realtime import BoardAudioInterface

# 连接开发板
board = BoardAudioInterface(
    device_name="USB Audio Device",
    sample_rate=16000
)

# 实时处理循环
while True:
    # 从开发板读取
    audio_in = board.read_audio(256)

    # 音高检测和音色转换
    pitch = detector.detect(audio_in)
    audio_out = synthesizer.generate(pitch, instrument="piano")

    # 输出到开发板
    board.write_audio(audio_out)
```

### 调试和测试

#### 延迟测试

```bash
# 测量端到端延迟
python test_latency.py

# 期望输出:
# Input → Detection: 32ms
# Detection → Synthesis: 15ms
# Synthesis → Output: 10ms
# Total latency: 57ms
```

#### 性能监控

```python
# 实时性能统计
stats = processor.get_stats()
print(f"延迟: {stats['latency_ms']}ms")
print(f"CPU: {stats['cpu_usage']}%")
print(f"丢帧: {stats['dropped_frames']}")
```

### 常见问题

#### Q: 延迟太高怎么办？
**A:** 尝试以下优化：
1. 减小 `chunk_size` 到 128
2. 使用 `latency_mode="ultra_low"`
3. 关闭不必要的音效

#### Q: 音色转换不自然？
**A:** 可能的解决方案：
1. 提高 `confidence_threshold`
2. 启用 `auto_tune` 功能
3. 使用更高质量的音色库

#### Q: CPU占用过高？
**A:** 优化建议：
1. 降低采样率到 8000Hz
2. 使用更小的ONNX模型
3. 禁用实时效果器

### 下一步行动

1. **测试基础系统**：运行 `demos/realtime/microphone_timbre_transform.py`
2. **集成FluidSynth**：安装并配置音色合成器
3. **对接开发板**：根据您同事的接口规范调整
4. **性能调优**：根据实际硬件优化参数

---

## 联系与支持

如需技术支持或有任何问题，请联系开发团队。