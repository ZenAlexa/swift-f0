# SwiftF0 嵌入式接口技术报告
## 麦克风与气压计数据输入方案

**文档版本**: 1.0
**创建日期**: 2025-10-21
**目标读者**: 嵌入式软件和硬件开发工程师

---

## 一、执行摘要

本报告为嵌入式开发团队提供SwiftF0项目的音频输入接口技术规范。当前SwiftF0系统**尚未实现麦克风实时输入**，仅支持文件输入。本文档基于项目的研究设计文档，为嵌入式系统集成麦克风和气压计输入提供技术指导。

### 关键发现
- **当前状态**: SwiftF0仅支持文件输入，无实时音频流处理
- **目标架构**: 已设计三线程实时处理架构，延迟目标<50ms
- **推荐方案**: 嵌入式端采集+预处理，通过USB/UART传输至主处理器

---

## 二、SwiftF0音频输入现状分析

### 2.1 当前实现状态

| 功能 | 状态 | 说明 |
|-----|------|------|
| 文件输入 | ✅ 已实现 | 支持WAV、MP3等格式 |
| 麦克风实时输入 | ❌ 未实现 | 仅有设计文档 |
| 流式处理 | ❌ 未实现 | 批处理模式，延迟~150ms |
| 嵌入式接口 | ❌ 未实现 | 需要定制开发 |

### 2.2 现有音频处理流程

```
[音频文件] → [librosa加载] → [重采样至16kHz] → [STFT变换] → [ONNX推理] → [音高输出]
```

**关键参数**:
- 采样率: 16000 Hz (固定)
- 单声道，32位浮点
- STFT帧长: 1024样本 (64ms)
- STFT跳跃: 256样本 (16ms)
- 频率范围: 46.875 Hz ~ 2093.75 Hz

---

## 三、麦克风数据接收架构设计

### 3.1 推荐的实时音频架构

基于项目研究文档，推荐采用**三线程架构**：

```
┌─────────────┐     队列1      ┌──────────────┐     队列2      ┌─────────────┐
│  音频采集   │ ───────────→ │  音高检测    │ ───────────→ │  音符分割   │
│  线程       │  音频块        │  线程        │  音高数据      │  线程       │
│ (16kHz采样) │                │ (ONNX推理)  │                │ (MIDI输出)  │
└─────────────┘                └──────────────┘                └─────────────┘
```

### 3.2 嵌入式系统接口方案

#### 方案A: 直接USB音频设备 (推荐)

```
┌──────────────────────────────────────┐
│        嵌入式采集模块                   │
├──────────────────────────────────────┤
│  麦克风 → ADC → MCU → USB Audio Class │
│  气压计 → I2C → MCU → HID/Serial      │
└──────────────────────────────────────┘
                    ↓ USB
┌──────────────────────────────────────┐
│           主处理器 (树莓派等)           │
├──────────────────────────────────────┤
│  USB Audio → sounddevice → SwiftF0   │
│  HID/Serial → 气压数据处理            │
└──────────────────────────────────────┘
```

**优点**:
- 标准USB Audio Class，无需驱动
- 低延迟 (<10ms)
- 支持同步时间戳

**硬件要求**:
- MCU: STM32F4系列或类似 (支持USB FS/HS)
- ADC: 16位，≥16kHz采样率
- 内存: ≥8KB缓冲

#### 方案B: UART/SPI串行传输

```
┌─────────────────────────────────────┐
│        嵌入式采集模块                  │
├─────────────────────────────────────┤
│  麦克风 → ADC → 缓冲 → UART/SPI     │
│  气压计 → I2C → 混合 → 打包发送      │
└─────────────────────────────────────┘
                    ↓ UART (921600 bps)
┌─────────────────────────────────────┐
│           主处理器                    │
├─────────────────────────────────────┤
│  Serial → 解包 → numpy array        │
│  → SwiftF0.detect_from_array()      │
└─────────────────────────────────────┘
```

**数据包格式建议**:
```c
typedef struct {
    uint16_t magic;        // 0xF0F0 同步头
    uint16_t seq;          // 序列号
    uint32_t timestamp;    // 微秒时间戳
    int16_t audio[256];    // 16ms音频数据
    uint16_t pressure;     // 气压值
    uint16_t crc16;        // 校验和
} DataPacket;  // 总大小: 528字节
```

---

## 四、嵌入式端实现要求

### 4.1 音频采集规格

| 参数 | 要求 | 说明 |
|-----|------|------|
| 采样率 | 16000 Hz ±0.1% | SwiftF0固定要求 |
| 位深度 | ≥12位 | 建议16位 |
| 通道数 | 1 (单声道) | 可从立体声混合 |
| 缓冲大小 | 256样本/块 | 16ms延迟 |
| 时钟精度 | <100ppm | 避免音高漂移 |

### 4.2 实时性要求

```
总延迟预算 (目标<50ms):
├─ ADC采集:        2ms
├─ MCU缓冲/打包:   3ms
├─ USB/UART传输:   5ms
├─ 主机接收缓冲:   5ms
├─ ONNX推理:      25ms
└─ 音符分割:      10ms
```

### 4.3 气压计集成

**建议配置**:
- 采样率: 100 Hz (与音频异步)
- 分辨率: 0.1 Pa
- 时间同步: 使用共同时间戳

**数据融合方案**:
```python
class AudioPressureStream:
    def __init__(self):
        self.audio_buffer = RingBuffer(16000)
        self.pressure_buffer = RingBuffer(100)

    def add_audio_chunk(self, audio, timestamp):
        self.audio_buffer.append(audio, timestamp)

    def add_pressure(self, pressure, timestamp):
        self.pressure_buffer.append(pressure, timestamp)

    def get_synchronized_frame(self, t):
        """获取时间t的同步音频和气压数据"""
        audio = self.audio_buffer.get_at(t)
        pressure = self.pressure_buffer.interpolate_at(t)
        return audio, pressure
```

---

## 五、Python端接收实现

### 5.1 基于sounddevice的实时接收 (USB Audio)

```python
import sounddevice as sd
import numpy as np
import queue
from swift_f0 import SwiftF0

class MicrophoneReceiver:
    def __init__(self, device_index=None):
        self.audio_queue = queue.Queue(maxsize=10)
        self.detector = SwiftF0()
        self.stream = None

    def audio_callback(self, indata, frames, time, status):
        """sounddevice回调函数"""
        if status:
            print(f"Audio error: {status}")
        # 复制数据到队列（避免覆盖）
        self.audio_queue.put(indata.copy())

    def start(self):
        """启动音频流"""
        self.stream = sd.InputStream(
            device=device_index,  # None使用默认设备
            channels=1,
            samplerate=16000,
            blocksize=256,  # 16ms块
            dtype='float32',
            callback=self.audio_callback
        )
        self.stream.start()

    def process_audio(self):
        """处理音频队列"""
        buffer = np.array([])

        while True:
            try:
                # 获取音频块（超时1秒）
                chunk = self.audio_queue.get(timeout=1.0)
                buffer = np.append(buffer, chunk.flatten())

                # 当缓冲足够时进行推理
                if len(buffer) >= 1024:
                    # 提取1024样本进行处理
                    input_chunk = buffer[:1024]
                    buffer = buffer[256:]  # 滑动窗口

                    # 音高检测
                    result = self.detector.detect_from_array(
                        input_chunk,
                        sample_rate=16000
                    )

                    # 输出结果
                    if result.voicing[0]:
                        print(f"Pitch: {result.pitch_hz[0]:.2f} Hz, "
                              f"Confidence: {result.confidence[0]:.2f}")

            except queue.Empty:
                continue
```

### 5.2 串口数据接收 (UART方案)

```python
import serial
import struct
import numpy as np
from dataclasses import dataclass

@dataclass
class DataPacket:
    timestamp: int
    audio: np.ndarray
    pressure: int

class SerialReceiver:
    def __init__(self, port='/dev/ttyUSB0', baudrate=921600):
        self.serial = serial.Serial(port, baudrate)
        self.packet_size = 528

    def read_packet(self):
        """读取并解析数据包"""
        # 寻找同步头
        while True:
            if self.serial.read(1)[0] == 0xF0:
                if self.serial.read(1)[0] == 0xF0:
                    break

        # 读取剩余数据
        data = self.serial.read(self.packet_size - 2)

        # 解包
        seq, timestamp = struct.unpack('<HI', data[0:6])
        audio_bytes = data[6:518]
        audio = np.frombuffer(audio_bytes, dtype=np.int16)
        pressure = struct.unpack('<H', data[518:520])[0]
        crc = struct.unpack('<H', data[520:522])[0]

        # 验证CRC
        if self.verify_crc(data[:520], crc):
            # 转换音频为float32 [-1, 1]
            audio_float = audio.astype(np.float32) / 32768.0

            return DataPacket(
                timestamp=timestamp,
                audio=audio_float,
                pressure=pressure
            )
        else:
            print("CRC错误，丢弃数据包")
            return None

    def verify_crc(self, data, crc):
        """CRC16-CCITT验证"""
        # 实现CRC校验...
        return True  # 简化示例
```

---

## 六、同步与时延优化

### 6.1 时间戳同步

**推荐方案**: 使用统一的硬件时钟源

```c
// 嵌入式端
uint32_t get_timestamp_us() {
    return DWT->CYCCNT / (SystemCoreClock / 1000000);
}

typedef struct {
    uint32_t audio_timestamp;
    uint32_t pressure_timestamp;
    int16_t audio_data[256];
    uint16_t pressure_data;
} SyncedPacket;
```

### 6.2 延迟优化策略

1. **降低缓冲大小**: 128样本/块 (8ms) vs 256样本 (16ms)
2. **使用DMA传输**: 减少CPU开销
3. **优先级调度**: 音频线程设为实时优先级
4. **零拷贝传输**: 使用共享内存或mmap

### 6.3 抖动补偿

```python
class JitterBuffer:
    def __init__(self, target_delay_ms=20):
        self.buffer = collections.deque()
        self.target_delay = target_delay_ms

    def add_packet(self, packet):
        # 按时间戳排序插入
        bisect.insort(self.buffer, packet, key=lambda x: x.timestamp)

    def get_packet(self):
        # 等待足够延迟后输出
        if len(self.buffer) > 0:
            oldest = self.buffer[0]
            current_time = time.time() * 1000
            if current_time - oldest.timestamp > self.target_delay:
                return self.buffer.popleft()
        return None
```

---

## 七、测试与验证

### 7.1 功能测试清单

- [ ] 音频采集精度: THD < 1%
- [ ] 采样率准确性: ±0.1%
- [ ] 延迟测试: <50ms端到端
- [ ] 丢包率: <0.1%
- [ ] 长时间稳定性: >24小时

### 7.2 性能基准

```python
# 延迟测试代码
def measure_latency():
    # 生成1kHz测试音
    test_tone = generate_sine(1000, duration=0.1)

    start_time = time.perf_counter()

    # 播放并录制
    recorded = sd.playrec(test_tone, 16000)
    sd.wait()

    # 检测第一个峰值
    first_peak = detect_first_peak(recorded)

    latency_ms = (first_peak / 16000) * 1000
    print(f"往返延迟: {latency_ms:.1f} ms")
```

### 7.3 调试工具

```bash
# 监控音频流
python -c "import sounddevice as sd; sd.query_devices()"

# 测试串口
screen /dev/ttyUSB0 921600

# 性能分析
python -m cProfile -s cumtime mic_receiver.py
```

---

## 八、硬件选型建议

### 8.1 麦克风选择

| 类型 | 型号示例 | 特点 | 适用场景 |
|-----|---------|------|---------|
| MEMS数字 | INMP441 | I2S接口，低功耗 | 便携设备 |
| MEMS模拟 | SPH0645 | 高SNR，宽频响 | 高质量录音 |
| 驻极体 | CMA-4544 | 低成本，易集成 | 原型开发 |

### 8.2 MCU选择

**最低要求**:
- 主频: ≥48 MHz
- RAM: ≥8 KB
- Flash: ≥32 KB
- ADC: 12位，≥20 ksps
- 通信: USB FS 或 UART ≥921600 bps

**推荐型号**:
- STM32F401 (USB Audio Class)
- ESP32 (WiFi传输选项)
- nRF52840 (BLE选项)

### 8.3 气压计选择

- **BMP280**: I2C/SPI, 0.12 Pa分辨率
- **MS5611**: 高精度，0.012 mbar
- **LPS22HB**: 低功耗，内置FIFO

---

## 九、集成示例代码

### 9.1 完整的嵌入式端代码框架 (STM32)

```c
// main.c
#include "stm32f4xx.h"
#include "usbd_audio.h"

#define AUDIO_BUFFER_SIZE 256
#define SAMPLE_RATE 16000

// 音频缓冲
int16_t audio_buffer[AUDIO_BUFFER_SIZE];
volatile uint8_t buffer_ready = 0;

// ADC DMA完成回调
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc) {
    buffer_ready = 1;

    // 读取气压计
    uint16_t pressure = read_pressure_sensor();

    // 打包数据
    DataPacket packet = {
        .magic = 0xF0F0,
        .seq = packet_counter++,
        .timestamp = HAL_GetTick() * 1000,
        .pressure = pressure
    };
    memcpy(packet.audio, audio_buffer, sizeof(audio_buffer));
    packet.crc16 = calculate_crc16(&packet, sizeof(packet) - 2);

    // 发送via USB或UART
    send_packet(&packet);
}

// 初始化音频采集
void init_audio_capture() {
    // 配置ADC为16kHz采样
    // 配置DMA循环模式
    // 配置定时器触发ADC
    HAL_ADC_Start_DMA(&hadc1, (uint32_t*)audio_buffer,
                      AUDIO_BUFFER_SIZE);
    HAL_TIM_Base_Start(&htim2);
}
```

### 9.2 Python端完整集成示例

```python
# realtime_swift_f0.py
import threading
import queue
import sounddevice as sd
import numpy as np
from swift_f0 import SwiftF0
from swift_f0.music import segment_notes
import mido

class RealtimeF0System:
    def __init__(self):
        self.audio_queue = queue.Queue(maxsize=10)
        self.pitch_queue = queue.Queue(maxsize=10)
        self.detector = SwiftF0()
        self.midi_out = mido.open_output('SwiftF0 Output')

    def start(self):
        # 启动三个线程
        threading.Thread(target=self.audio_thread, daemon=True).start()
        threading.Thread(target=self.pitch_thread, daemon=True).start()
        threading.Thread(target=self.midi_thread, daemon=True).start()

        # 启动音频流
        with sd.InputStream(
            channels=1,
            samplerate=16000,
            blocksize=256,
            callback=self.audio_callback
        ):
            print("系统运行中... 按Ctrl+C停止")
            while True:
                time.sleep(0.1)

    def audio_callback(self, indata, frames, time, status):
        """音频输入回调"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())

    def audio_thread(self):
        """音频采集线程 - 由sounddevice管理"""
        pass

    def pitch_thread(self):
        """音高检测线程"""
        buffer = np.array([])

        while True:
            chunk = self.audio_queue.get()
            buffer = np.append(buffer, chunk.flatten())

            if len(buffer) >= 1024:
                input_chunk = buffer[:1024]
                buffer = buffer[256:]  # 滑动窗口

                # 检测音高
                result = self.detector.detect_from_array(
                    input_chunk,
                    sample_rate=16000
                )

                self.pitch_queue.put({
                    'pitch': result.pitch_hz[0],
                    'confidence': result.confidence[0],
                    'timestamp': time.time()
                })

    def midi_thread(self):
        """MIDI输出线程"""
        current_note = None

        while True:
            frame = self.pitch_queue.get()

            if frame['confidence'] > 0.9:
                midi_note = int(69 + 12 * np.log2(frame['pitch'] / 440))

                if current_note != midi_note:
                    # 结束旧音符
                    if current_note:
                        msg = mido.Message('note_off', note=current_note)
                        self.midi_out.send(msg)

                    # 开始新音符
                    msg = mido.Message('note_on', note=midi_note, velocity=80)
                    self.midi_out.send(msg)
                    current_note = midi_note
            else:
                # 静音时结束音符
                if current_note:
                    msg = mido.Message('note_off', note=current_note)
                    self.midi_out.send(msg)
                    current_note = None

if __name__ == "__main__":
    system = RealtimeF0System()
    system.start()
```

---

## 十、故障排查指南

### 常见问题及解决方案

| 问题 | 可能原因 | 解决方案 |
|-----|---------|----------|
| 音高检测不准 | 采样率偏差 | 校准晶振，使用PLL |
| 延迟过高 | 缓冲过大 | 减小blocksize |
| 音频断续 | 丢包/缓冲不足 | 增加缓冲，检查USB带宽 |
| 无音频输入 | 设备未识别 | 检查USB描述符 |
| 气压数据不同步 | 时钟漂移 | 使用NTP或GPS同步 |

---

## 十一、总结与建议

### 11.1 实施路线图

1. **第一阶段**: USB Audio Class实现 (2周)
   - 实现基础音频采集
   - 验证端到端延迟

2. **第二阶段**: 气压计集成 (1周)
   - 添加I2C读取
   - 实现数据同步

3. **第三阶段**: 优化与测试 (2周)
   - 延迟优化
   - 长时间稳定性测试

### 11.2 关键成功因素

- ✅ 严格的16kHz采样率
- ✅ <50ms总延迟
- ✅ 可靠的数据传输
- ✅ 精确的时间同步

### 11.3 下一步行动

1. 确定硬件平台（MCU型号）
2. 选择传输方案（USB Audio vs UART）
3. 搭建原型验证系统
4. 集成测试与优化

---

## 附录A: 参考资源

- [SwiftF0 GitHub仓库](https://github.com/your-repo/swift-f0)
- [USB Audio Class规范](https://www.usb.org/audio)
- [sounddevice文档](https://python-sounddevice.readthedocs.io/)
- [STM32 USB Audio示例](https://github.com/STMicroelectronics/STM32CubeF4)

## 附录B: 术语表

- **STFT**: Short-Time Fourier Transform, 短时傅里叶变换
- **ONNX**: Open Neural Network Exchange, 开放神经网络交换格式
- **MIDI**: Musical Instrument Digital Interface, 乐器数字接口
- **ADC**: Analog-to-Digital Converter, 模数转换器
- **DMA**: Direct Memory Access, 直接内存访问
- **MEMS**: Micro-Electro-Mechanical Systems, 微机电系统

---

**文档结束**

如有技术问题，请联系SwiftF0开发团队。