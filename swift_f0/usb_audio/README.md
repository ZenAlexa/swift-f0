# USB 音频模块

## 概述

这个模块用于接收 ESP32 开发板通过 USB Serial 传输的音频数据，并与 SwiftF0 音高检测集成。

⚠️ **重要**: ESP32 设备必须正在运行音频采集程序并通过 USB 发送数据。如果没有接收到数据，请检查：
1. ESP32 是否正在运行音频采集程序
2. USB 连接是否正常
3. 串口设备路径是否正确（使用 `--list-ports` 查看）

## 模块结构

```
swift_f0/usb_audio/
├── __init__.py       # 模块入口
└── receiver.py       # USB 音频接收器（来自 xiaozhi-esp32）

swift_f0/realtime/
└── usb_processor.py  # USB 音频处理器（集成音高检测和合成）
```

## 数据流

```
ESP32 麦克风
    ↓
USB Serial (2Mbps)
    ↓
AudioFrameReceiver (接收音频帧)
    ↓
USBProcessor (音高检测 + 音色合成)
    ↓
音频输出（扬声器）
```

## 使用方法

### 1. 测试串口连接

先测试是否能接收到数据：

```bash
python demos/realtime/test_usb_connection.py --port /dev/tty.usbmodem1101 --rate 24000
```

如果成功，会显示：
```
帧 1: 收到 60 个采样
  范围: [-32768, 32767]
  前10个值: [...]
```

### 2. 列出可用串口

```bash
python demos/realtime/run_usb_audio.py --list-ports
```

### 3. 运行实时处理

```bash
# 自动检测串口
python demos/realtime/run_usb_audio.py

# 指定串口
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000

# 使用调试模式
python demos/realtime/run_usb_audio.py --debug
```

### 3. 在代码中使用

```python
from swift_f0.realtime.usb_processor import USBProcessorConfig, RealtimeUSBPlayer

# 配置
config = USBProcessorConfig(
    serial_port='/dev/tty.usbmodem1101',
    baudrate=2000000,
    input_sample_rate=24000,
    debug=True
)

# 创建播放器
player = RealtimeUSBPlayer(config)
player.start()
player.run()
```

## 参数说明

- **serial_port**: 串口设备路径
- **baudrate**: 波特率（默认 2000000）
- **input_sample_rate**: ESP32 音频采样率（默认 24000 Hz）
- **process_sample_rate**: 音高检测采样率（默认 16000 Hz）
- **window_size**: 音高检测窗口大小（默认 1024）
- **confidence_threshold**: 音高检测置信度阈值（默认 0.8）

## 依赖

- pyserial: 串口通信
- sounddevice 或 pyaudio: 音频输出
- numpy: 数组处理
- swift_f0: 音高检测

## 注意事项

1. ESP32 输出 24kHz 采样率，系统会自动重采样到 16kHz 用于音高检测
2. macOS 上串口设备使用 `/dev/tty.usbmodem*` （不是 `/dev/cu.`）
3. Windows 上串口设备为 `COM` 端口
4. Linux 上串口设备通常为 `/dev/ttyUSB` 或 `/dev/ttyACM`

## 故障排查

### 没有收到音频数据

如果运行测试脚本显示 "无数据..."：

1. **确认 ESP32 正在发送数据**
   - ESP32 必须运行音频采集程序
   - 检查 ESP32 串口监视器是否显示正在发送

2. **检查串口设备**
   ```bash
   # macOS
   ls /dev/tty.usb*

   # Linux
   ls /dev/ttyUSB* /dev/ttyACM*
   ```

3. **测试原始接收**
   使用 xiaozhi-esp32 项目的原始脚本测试：
   ```bash
   cd /Users/zimingwang/Documents/GitHub/xiaozhi-esp32/scripts/usb_audio
   python play.py --port /dev/tty.usbmodem1101 --rate 24000
   ```

4. **调试模式**
   ```bash
   python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000 --debug
   ```