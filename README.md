# SwiftF0 - 实时音高检测与音色变换系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

---

## 🎯 项目概述

SwiftF0 是一个轻量级、高精度的实时音高检测和音色变换系统，专为嵌入式设备和实时应用设计。

### 核心特性

✅ **实时音高检测** - CNN模型仅389KB，CPU即可运行
✅ **USB音频集成** - 支持ESP32/开发板音频输入
✅ **音色合成** - 实时正弦波合成，可扩展至MIDI
✅ **低延迟处理** - <100ms端到端延迟
✅ **跨平台支持** - Windows/macOS/Linux

### 性能指标

⚡ **延迟**: ~80ms (标准模式)
🎯 **精度**: <1% 音高误差
🔋 **轻量**: 389KB模型 + 低内存占用
📊 **采样率**: 16kHz (处理) / 24kHz (输入)

---

## 📦 快速安装

```bash
# 克隆项目
git clone https://github.com/yourusername/swift-f0.git
cd swift-f0

# 安装依赖
pip install -e .

# 安装实时处理依赖
pip install sounddevice pyserial numpy
```

---

## 🚀 快速开始

### 1. 简单音高检测

```python
from swift_f0 import SwiftF0

# 初始化检测器
detector = SwiftF0()

# 从文件检测
result = detector.detect_from_file("audio.wav")
print(f"检测到 {len(result.pitch_hz)} 帧")

# 从数组检测
import numpy as np
audio = np.random.randn(16000)  # 1秒音频
result = detector.detect_from_array(audio, sample_rate=16000)
```

### 2. 实时USB音频处理

```bash
# 列出可用串口
python demos/realtime/run_usb_audio.py --list-ports

# 运行实时处理（ESP32音频输入）
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000
```

### 3. 实时麦克风处理

```python
python demos/realtime/test_simple_sine.py
```

---

## 🎵 系统架构

```
输入源 → 音高检测 → 音色变换 → 音频输出
  ↓         ↓          ↓          ↓
ESP32    SwiftF0    正弦合成   扬声器
USB音频   CNN模型    MIDI合成   文件输出
麦克风    16kHz      实时处理
```

---

## 📚 项目结构

```
swift-f0/
├── swift_f0/
│   ├── core.py                # 核心音高检测
│   ├── model.onnx             # CNN模型 (389KB)
│   ├── realtime/              # 实时处理模块
│   │   ├── config.py          # 配置管理
│   │   ├── audio_stream.py    # 音频流处理
│   │   ├── simple_synthesizer.py # 音色合成
│   │   └── usb_processor.py   # USB音频处理器
│   └── usb_audio/             # USB音频接收
│       └── receiver.py        # ESP32数据接收
│
├── demos/realtime/            # 演示程序
│   ├── run_usb_audio.py      # USB音频主程序
│   └── test_simple_sine.py   # 简单测试
│
├── config/                    # 配置文件
│   └── realtime_config.yaml
│
└── docs/                      # 文档
    ├── README.md              # 文档中心
    ├── DEVELOPMENT.md         # 开发进度
    ├── TECHNICAL.md           # 技术细节
    └── PROJECT_SUMMARY.md     # 项目总结
```

---

## 🔧 USB音频集成

本项目支持从ESP32或其他开发板接收音频数据：

### 硬件连接

1. ESP32通过USB连接到电脑
2. ESP32运行音频采集固件
3. 通过USB Serial传输音频数据（2Mbps）

### 使用方法

```python
from swift_f0.realtime.usb_processor import USBProcessorConfig, RealtimeUSBPlayer

# 配置
config = USBProcessorConfig(
    serial_port='/dev/tty.usbmodem1101',
    baudrate=2000000,
    input_sample_rate=24000  # ESP32采样率
)

# 运行
player = RealtimeUSBPlayer(config)
player.start()
player.run()
```

---

## 📊 性能优化

### 延迟优化选项

| 模式 | 延迟 | 窗口大小 | 块大小 | 适用场景 |
|------|------|---------|---------|----------|
| 标准 | ~80ms | 1024 | 256 | 一般处理 |
| 优化 | ~47ms | 512 | 128 | 实时交互 |
| 超低 | ~20ms | 256 | 64 | 实时演奏 |

### 内存占用

- 模型：389KB (ONNX)
- 运行时：~50MB RAM
- 缓冲区：可配置

---

## 🎮 命令行工具

```bash
# USB音频处理
python demos/realtime/run_usb_audio.py [选项]

选项：
  --port PORT        串口设备 (如: /dev/tty.usbmodem1101)
  --rate RATE        采样率 (默认: 24000)
  --list-ports       列出可用串口
  --debug            显示调试信息

# 麦克风测试
python demos/realtime/test_simple_sine.py
```

---

## 🧪 测试

```bash
# 测试音高检测精度
python demos/realtime/test_pipeline.py

# 测试实时处理
python demos/realtime/test_simple_sine.py
```

---

## 📈 应用场景

### 🎤 实时音高检测
- 人声/乐器音高追踪
- 音准训练和反馈
- 卡拉OK评分系统

### 🎼 音色变换
- 实时变声效果
- MIDI控制器
- 电子乐器

### 🎺 嵌入式应用
- ESP32音频处理
- 智能乐器
- IoT音频设备

---

## 🛠️ 开发状态

- ✅ **核心音高检测** - 完成
- ✅ **实时处理框架** - 完成
- ✅ **USB音频集成** - 完成
- ✅ **简单音色合成** - 完成
- 🔄 **MIDI集成** - 进行中
- 💡 **高级音色** - 计划中

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- **SwiftF0** 原作者提供的优秀音高检测算法
- ESP32社区的USB音频传输方案

---

**版本**: v0.3.0 | **更新**: 2024-10-21