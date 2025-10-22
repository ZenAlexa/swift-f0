# Smart Kazoo 项目结构总览

> **版本**: v0.4.0 Alpha Demo | **更新**: 2024-10-22

---

## 📁 目录结构

```
swift-f0/
├── swift_f0/                          # 核心代码包
│   ├── __init__.py                    # 包初始化
│   ├── core.py                        # 音高检测核心 (435行)
│   ├── model.onnx                     # SwiftF0 CNN模型 (389KB)
│   ├── music.py                       # 音符分段工具
│   ├── music_enhanced.py              # 音色转换（MIDI方向，暂不使用）
│   │
│   ├── realtime/                      # 实时处理模块 ⭐
│   │   ├── __init__.py
│   │   ├── config.py                  # 配置管理
│   │   ├── audio_buffer.py            # 音频缓冲区
│   │   ├── audio_stream.py            # 麦克风音频流
│   │   ├── additive_synthesizer.py    # 波表合成器 ⭐ 新增
│   │   ├── wavetable_generator.py     # 波表生成器 ⭐ 新增
│   │   ├── simple_synthesizer.py      # 简单合成器（向后兼容）
│   │   └── usb_processor.py           # USB音频处理器 ⭐
│   │
│   └── usb_audio/                     # USB音频接收
│       ├── __init__.py
│       └── receiver.py                # ESP32数据接收 ⭐
│
├── wavetables/                        # 预生成波表 ⭐ 新增
│   ├── flute.npy                      # 长笛音色 (16KB)
│   ├── violin.npy                     # 小提琴音色 (16KB)
│   ├── clarinet.npy                   # 单簧管音色 (16KB)
│   └── sine.npy                       # 纯正弦波 (16KB)
│
├── demos/                             # 演示程序
│   ├── README.md
│   ├── basic/                         # 基础示例
│   │   ├── simple_pitch_detection.py  # 简单音高检测
│   │   ├── note_segmentation_example.py
│   │   └── simple_midi_export.py
│   │
│   ├── realtime/                      # 实时处理示例 ⭐
│   │   ├── run_usb_audio.py           # USB音频主程序 ⭐
│   │   ├── test_additive_synth.py     # 波表合成测试 ⭐ 新增
│   │   └── test_simple_sine.py        # 麦克风测试
│   │
│   ├── advanced/                      # 高级示例
│   │   └── timbre_transform_cli.py    # 音色转换CLI（暂不使用）
│   │
│   └── tutorials/                     # 教程
│       └── 01_getting_started.py
│
├── tests/                             # 测试目录
│   ├── README.md
│   └── integration/
│       └── test_timbre_transform.py
│
├── test_data/                         # 测试数据
│   ├── README.md
│   ├── inputs/
│   │   └── test_audio.wav            # 测试输入音频
│   └── audio_output/                  # 测试输出 ⭐ 整理
│       ├── README.md
│       └── wavetable_synthesis/       # 波表合成测试输出
│           ├── test_flute_*.wav       # 长笛测试音频 (4个)
│           ├── test_violin_*.wav      # 小提琴测试音频 (4个)
│           ├── test_clarinet_*.wav    # 单簧管测试音频 (4个)
│           └── test_sine_*.wav        # 正弦波测试音频 (4个)
│
├── config/                            # 配置文件
│   └── realtime_config.yaml           # 实时处理配置
│
├── soundfonts/                        # 音色字体（MIDI方向）
│   └── README.md
│
├── docs/                              # 文档 ⭐ 整理
│   ├── README.md                      # 文档导航中心 ⭐ 更新
│   ├── TECHNICAL.md                   # 技术文档 ⭐ 活跃维护
│   ├── DEVELOPMENT.md                 # 开发进度 ⭐ 活跃维护
│   ├── ALGORITHMS.md                  # 算法索引 ⭐ 新增
│   ├── changelog.md                   # 变更日志
│   │
│   ├── guides/                        # 使用指南（参考）
│   │   ├── realtime_setup.md
│   │   └── migration_guide.md
│   │
│   ├── research/                      # 研究文档（参考）
│   │   ├── ai_kazoo_roadmap.md
│   │   ├── embedded_interface_report.md
│   │   ├── project_summary.md
│   │   └── streaming_research_brief.md
│   │
│   ├── technical/                     # 技术细节（参考）
│   │   ├── architecture.md
│   │   ├── realtime_architecture.md
│   │   ├── edge_deployment_analysis.md
│   │   └── hardware_comparison.md
│   │
│   └── archive/                       # 历史归档（只读）
│       ├── PROJECT_STATUS_20241021.md
│       ├── REORGANIZATION_REPORT.md
│       ├── index.md
│       ├── project_overview.md
│       └── project_structure.md
│
├── CLAUDE.md                          # Claude协作框架 ⭐
├── README.md                          # 项目主页 ⭐ 更新
├── PROJECT_STRUCTURE.md               # 本文件 ⭐ 新增
├── requirements.txt                   # Python依赖
└── setup.py                           # 安装脚本
```

**图例**:
- ⭐ 核心文件/最近更新
- 无标记 = 稳定/参考文件

---

## 🔧 核心模块依赖关系

### 实时处理链路

```
┌─────────────────────────────────────────────────────────────────┐
│                     demos/realtime/run_usb_audio.py             │
│                          (主程序入口)                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              swift_f0/realtime/usb_processor.py                 │
│                    (USB处理器核心)                                │
│  • USBProcessorConfig - 配置类                                   │
│  • USBProcessor - 处理逻辑                                       │
│  • RealtimeUSBPlayer - 播放器                                    │
└──────┬────────────────────┬──────────────────┬───────────────────┘
       │                    │                  │
       ▼                    ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌────────────────────────┐
│ usb_audio/   │  │   core.py       │  │ additive_synthesizer.py│
│ receiver.py  │  │   (SwiftF0)     │  │   (波表合成)            │
│              │  │                 │  │                        │
│ • 串口通信   │  │ • 音高检测      │  │ • synthesize()         │
│ • 帧解析     │  │ • CNN推理       │  │ • set_instrument()     │
│ • 校验       │  │                 │  │                        │
└──────────────┘  └─────────────────┘  └───────┬────────────────┘
                                                │
                                                ▼
                                       ┌────────────────────────┐
                                       │ wavetable_generator.py │
                                       │   (波表生成)            │
                                       │                        │
                                       │ • generate_wavetable() │
                                       │ • INSTRUMENT_HARMONICS │
                                       └────────┬───────────────┘
                                                │
                                                ▼
                                       ┌────────────────────────┐
                                       │    wavetables/*.npy    │
                                       │   (预生成波表文件)      │
                                       └────────────────────────┘
```

### 数据流

```
ESP32麦克风 (24kHz)
    │
    ├─ USB Serial (2Mbps)
    │
    ▼
receiver.py
    │  解析帧 + 校验
    ├─ int16[] audio_frame (256 samples)
    │
    ▼
usb_processor.py
    │  降采样 24kHz → 16kHz
    ├─ float32[] audio_16k
    │
    ▼
core.py (SwiftF0)
    │  CNN音高检测
    ├─ pitch_hz (float)
    ├─ confidence (float)
    │
    ▼
usb_processor.py
    │  平滑 + 阈值过滤
    ├─ current_freq (smoothed)
    ├─ current_amp (smoothed)
    │
    ▼
additive_synthesizer.py
    │  波表查表 + 线性插值
    ├─ output (float32[])
    │
    ▼
sounddevice
    │  音频输出
    └─ 扬声器 🔊
```

---

## 📊 代码统计

### 核心模块行数

| 模块 | 文件 | 行数 | 说明 |
|------|------|------|------|
| 音高检测 | `core.py` | 435 | SwiftF0核心 |
| USB处理 | `usb_processor.py` | 354 | 实时处理管道 |
| USB接收 | `receiver.py` | 148 | 串口通信 |
| 波表合成 | `additive_synthesizer.py` | 126 | 合成引擎 |
| 波表生成 | `wavetable_generator.py` | 158 | 离线生成 |
| 音频流 | `audio_stream.py` | 183 | 麦克风输入 |
| 配置 | `config.py` | 120 | 参数管理 |
| **总计** | | **1524** | 核心代码 |

### 文件类型统计

| 类型 | 数量 | 说明 |
|------|------|------|
| Python源码 | 23 | 包括核心+演示+测试 |
| 文档 (Markdown) | 19 | 包括归档 |
| 配置文件 | 1 | YAML配置 |
| 波表文件 | 4 | NPY格式 |
| 模型文件 | 1 | ONNX模型 (389KB) |
| 测试音频 | 16 | WAV格式 (31KB each) |

---

## 🎯 关键文件说明

### 1. 主程序入口
**[demos/realtime/run_usb_audio.py](demos/realtime/run_usb_audio.py)**
- 命令行参数解析
- 串口自动检测
- 处理器初始化和启动
- 用法: `python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000 --instrument violin`

### 2. USB处理器核心
**[swift_f0/realtime/usb_processor.py](swift_f0/realtime/usb_processor.py)**
- `USBProcessorConfig`: 配置类 (L18-47)
- `USBProcessor`: 处理逻辑 (L50-354)
  - `process_frame()`: 主处理函数 (L137-230)
  - 幅度平滑算法 (L165-181)
  - 波表合成集成 (L186-208)
- `RealtimeUSBPlayer`: 播放器封装 (L257-354)

### 3. 波表合成器
**[swift_f0/realtime/additive_synthesizer.py](swift_f0/realtime/additive_synthesizer.py)**
- `AdditiveSynthesizer`: 合成器类
  - `__init__()`: 加载波表
  - `synthesize()`: 实时合成 (L66-101)
  - `set_instrument()`: 切换乐器 (L103-117)

### 4. 波表生成器
**[swift_f0/realtime/wavetable_generator.py](swift_f0/realtime/wavetable_generator.py)**
- `INSTRUMENT_HARMONICS`: 谐波定义 (L12-42)
- `generate_wavetable_fft()`: FFT生成法 (L45-69)
- `generate_wavetable_time()`: 时域生成法 (L72-90)
- `save_wavetables()`: 批量保存 (L93-112)

### 5. USB音频接收器
**[swift_f0/usb_audio/receiver.py](swift_f0/usb_audio/receiver.py)**
- `USBAudioReceiver`: 接收器类
  - `open()`: 打开串口 (L41-54)
  - `read_frame()`: 读取一帧 (L56-83)
  - `_find_sync()`: 帧同步 (L85-103)
  - `_verify_checksum()`: 校验 (L105-113)

### 6. 音高检测核心
**[swift_f0/core.py](swift_f0/core.py)**
- `SwiftF0`: 检测器类
  - `detect_from_array()`: 从数组检测 (L175-225)
  - `detect_from_file()`: 从文件检测 (L131-173)
  - `_forward()`: ONNX推理 (L271-318)

---

## 📝 文档索引

### 必读文档（活跃维护）

1. **[README.md](README.md)** - 项目主页
   - 快速开始
   - 功能特性
   - 使用示例

2. **[docs/TECHNICAL.md](docs/TECHNICAL.md)** - 技术文档
   - 核心算法原理
   - 系统架构
   - 性能优化

3. **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - 开发进度
   - 版本历史
   - 已知问题
   - 下一步计划

4. **[docs/ALGORITHMS.md](docs/ALGORITHMS.md)** - 算法索引
   - 算法快速查找
   - 实现位置
   - 性能对比

### 参考文档

5. **[docs/README.md](docs/README.md)** - 文档导航
6. **[CLAUDE.md](CLAUDE.md)** - Claude协作框架
7. **[docs/guides/](docs/guides/)** - 使用指南
8. **[docs/research/](docs/research/)** - 研究文档
9. **[docs/technical/](docs/technical/)** - 技术细节

---

## 🔗 依赖关系

### Python包依赖
```
numpy          # 数值计算
onnxruntime    # ONNX推理
sounddevice    # 音频I/O
pyserial       # 串口通信
scipy          # 信号处理
PyYAML         # 配置解析
```

### 文件依赖

#### 运行时依赖
- `swift_f0/model.onnx` - 必须（音高检测）
- `wavetables/*.npy` - 可选（使用波表合成时需要）
- `config/realtime_config.yaml` - 可选（使用默认配置）

#### 测试依赖
- `test_data/inputs/test_audio.wav` - 基础测试
- `test_data/audio_output/` - 测试输出目录

---

## 🚀 快速导航

### 我想...

**理解系统架构** → [docs/TECHNICAL.md](docs/TECHNICAL.md)

**查找某个算法** → [docs/ALGORITHMS.md](docs/ALGORITHMS.md)

**查看开发进度** → [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

**运行USB音频处理** → [demos/realtime/run_usb_audio.py](demos/realtime/run_usb_audio.py)

**测试波表合成** → [demos/realtime/test_additive_synth.py](demos/realtime/test_additive_synth.py)

**修改合成算法** → [swift_f0/realtime/additive_synthesizer.py](swift_f0/realtime/additive_synthesizer.py)

**修改谐波模型** → [swift_f0/realtime/wavetable_generator.py](swift_f0/realtime/wavetable_generator.py)

**调整平滑参数** → [swift_f0/realtime/usb_processor.py:165-181](swift_f0/realtime/usb_processor.py#L165-L181)

**修改USB通信** → [swift_f0/usb_audio/receiver.py](swift_f0/usb_audio/receiver.py)

---

## 📌 版本信息

- **当前版本**: v0.4.0 Alpha Demo
- **最后更新**: 2024-10-22
- **Python版本**: 3.8+
- **核心依赖**: numpy, onnxruntime, sounddevice, pyserial

---

*Smart Kazoo 项目结构总览 - 完整的项目导航和依赖关系*
