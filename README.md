# SwiftF0 实时流式处理与音色转换

**为 AI 卡祖笛项目打造的实时音高检测、调性分析和自动调音工具**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

---

## 🎯 项目概述

基于 SwiftF0 音高检测库，开发一套完整的**实时流式处理框架**，支持音色转换、调性检测和自动调音，为 AI 卡祖笛硬件项目提供核心算法支持。

### 核心功能

✅ **实时流式处理** - 低延迟音频流 → MIDI 事件转换
✅ **在线调性检测** - 10秒滑窗 K-S 算法，24种调性实时跟踪
✅ **自动调音** - 音高量化到音阶，可调节修正强度（0-100%）
✅ **128种 GM 标准音色** - 钢琴、弦乐、管乐、合成器等
✅ **智能移调** - ±24半音范围自动调整
✅ **卡祖笛优化** - E3-E5 音域限制 + 专用音色

### 性能指标

⚡ **低延迟**: 帧级推理 ~16ms（1024样本/16kHz）
🎯 **高精度**: ±10 cents（亚半音级别）
🔋 **轻量级**: 389KB 模型 + 350MB 内存
🎵 **实时性**: 滑窗处理，无需等待完整音频

---

## 📦 安装

### 基础安装（必需）

```bash
# 克隆仓库
git clone https://github.com/yourusername/swift-f0.git
cd swift-f0

# 安装核心依赖
pip install -r requirements.txt

# 开发模式安装（推荐）
pip install -e .
```

### 可选依赖

```bash
# 实时 MIDI 端口输出（可选）
pip install mido python-rtmidi

# 麦克风音频采集（可选）
pip install sounddevice librosa
```

**注意**：流式 Demo 不需要实时端口，仅需要 `mido` 用于 MIDI 文件写入。

---

## 🚀 快速开始：流式处理 Demo

### 基础命令

```bash
# 1. 基线导出（默认钢琴音色）
python examples/streaming/run_pipeline.py test_data/inputs/test_audio.wav output.mid

# 2. 指定乐器（双簧管，适合卡祖笛）
python examples/streaming/run_pipeline.py test_data/inputs/test_audio.wav output.mid \
    --instrument oboe

# 3. 打印实时调性检测
python examples/streaming/run_pipeline.py test_data/inputs/test_audio.wav output.mid \
    --print-key

# 4. 启用自动调音（完全量化到音阶）
python examples/streaming/run_pipeline.py test_data/inputs/test_audio.wav output.mid \
    --autotune --autotune-strength 1.0

# 5. 部分修正（保留原始风格）
python examples/streaming/run_pipeline.py test_data/inputs/test_audio.wav output.mid \
    --autotune --autotune-strength 0.5

# 6. 组合使用（调性打印 + 自动调音 + 音色）
python examples/streaming/run_pipeline.py test_data/inputs/test_audio.wav output.mid \
    --instrument trumpet --print-key --autotune --autotune-strength 0.8
```

### 输出示例

```
Key detection enabled (10s window, 2s update interval)
Auto-tune enabled (strength=1.00)
[2.0s] Key: C major (corr=0.670)
[4.0s] Key: C major (corr=0.712)
Saved streaming MIDI to: /path/to/output.mid
```

---

## 📖 参数说明

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `input` | 输入音频文件路径（WAV 格式） | `song.wav` |
| `output` | 输出 MIDI 文件路径 | `output.mid` |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--instrument` | str | `acoustic_grand_piano` | GM 乐器名称或程序号（0-127），见[音色列表](#可用音色) |
| `--tempo` | int | `120` | MIDI 文件速度（BPM） |
| `--simulate` | flag | 关闭 | 模拟实时处理（16ms 节拍） |
| `--print-key` | flag | 关闭 | 打印实时调性检测结果 |
| `--autotune` | flag | 关闭 | 启用自动调音（音高量化） |
| `--autotune-strength` | float | `1.0` | 自动调音强度（0.0=关闭，1.0=完全量化） |

---

## 🎵 可用音色

### 常用推荐

```bash
# 管乐（适合卡祖笛）
--instrument oboe          # 双簧管（鼻音）
--instrument trumpet       # 小号（明亮）
--instrument clarinet      # 单簧管（木质）

# 弦乐
--instrument violin        # 小提琴
--instrument cello         # 大提琴

# 键盘
--instrument acoustic_grand_piano  # 原声钢琴
--instrument electric_piano_1      # 电钢琴
```

### 完整列表

查看 `swift_f0/music_enhanced.py` 中的 `GM_INSTRUMENTS` 字典，包含 128 种 GM 标准音色。

也可以直接使用程序号：
```bash
--instrument 68   # 等同于 oboe
--instrument 0    # 等同于 acoustic_grand_piano
```

---

## 🏗️ 组件结构

### 流式处理框架

| 模块 | 文件 | 职责 |
|------|------|------|
| **音频源** | `swift_f0/streaming/audio.py` | WAV 文件流式读取、麦克风采集（可选） |
| **推理引擎** | `swift_f0/streaming/inference.py` | 滑窗推理（1024窗/256跳步） |
| **音符分段** | `swift_f0/streaming/notes.py` | 状态机实时分割（note_on/off） |
| **调性跟踪** | `swift_f0/streaming/key_detection.py` | 在线 K-S 算法（滑窗直方图） |
| **自动调音** | `swift_f0/streaming/autotune.py` | 音高量化到音阶 |
| **MIDI 输出** | `swift_f0/streaming/midi.py` | 文件写入、实时端口（可选） |
| **音色解析** | `swift_f0/streaming/timbre.py` | GM 名称/数字映射 |

### 核心库

| 模块 | 文件 | 职责 |
|------|------|------|
| **音高检测** | `swift_f0/core.py` | SwiftF0 ONNX 推理 |
| **音符分割** | `swift_f0/music.py` | 离线批处理分割 |
| **增强导出** | `swift_f0/music_enhanced.py` | 音色转换、调性检测、自动调音（离线版） |

---

## 📚 工作流程

### 流式处理管道

```
WAV 文件
  ↓
[WavFileSource] 按块输出音频帧（float32 mono）
  ↓
[SwiftF0Streamer] 滑窗推理 → PitchFrame (Hz, confidence, timestamp)
  ↓
[RealtimeNoteSegmenter] 状态机 → NoteEvent (note_on/off)
  ↓
[OnlineKeyTracker] 滑窗直方图 → 调性 (key_name, mode, correlation)
  ↓
[AutoTuneQuantizer] 量化 note_on 音高到音阶（可选）
  ↓
[FileMIDISink] 写入 MIDI 文件
```

### 调性检测算法

**Krumhansl-Schmuckler (K-S) 算法**：

1. 配对 `note_on`/`note_off` 事件，计算音符时长
2. 维护 10 秒滑窗，构建 12 维音高类直方图（按时长加权）
3. 与 24 种调性模板（12 大调 + 12 小调）计算 Pearson 相关性
4. 返回相关性最高的调性及置信度

### 自动调音逻辑

1. 获取当前调性 `(key, mode, correlation)`
2. 若置信度 < 0.3，回退到 C major
3. 对每个 `note_on` 事件：
   - 生成调性音阶（如 C major: [0,2,4,5,7,9,11]）
   - 找到最近的音阶音（最小化半音距离）
   - 按强度混合：`new = round(orig * (1-s) + quantized * s)`
   - Clamp 到 [0, 127]
4. `note_off` 事件直接透传

---

## ❓ 常见问题（FAQ）

### 1. 找不到模块 `swift_f0`

**原因**：未安装包或未在仓库根目录运行。

**解决**：
```bash
# 方案 1：开发模式安装
cd /path/to/swift-f0
pip install -e .

# 方案 2：从仓库根目录运行
cd /path/to/swift-f0
python examples/streaming/run_pipeline.py ...
```

### 2. MIDI 音色未切换

**原因**：乐器名称拼写错误或不存在。

**解决**：
- 检查 `swift_f0/music_enhanced.py` 第 23 行的 `GM_INSTRUMENTS` 字典
- 使用下划线（`acoustic_grand_piano`）而非空格
- 或直接使用数字：`--instrument 68`

### 3. 自动调音效果不明显

**原因**：
- 前 2-4 秒数据不足，低置信度回退到 C major
- 音频本身已在正确音阶上

**解决**：
- 增大 `--autotune-strength`（尝试 1.0 完全量化）
- 查看 `--print-key` 输出，确认调性检测置信度（corr）
- 使用更长的音频片段（>10 秒）

### 4. 依赖安装失败（`rtmidi` 或 `sounddevice`）

**原因**：缺少系统库。

**解决**：
```bash
# macOS
brew install portaudio rtmidi

# Ubuntu/Debian
sudo apt-get install portaudio19-dev librtmidi-dev

# Windows
# 下载预编译轮子：https://www.lfd.uci.edu/~gohlke/pythonlibs/
```

**注意**：流式 Demo（`run_pipeline.py`）**不需要**这些依赖，仅需 `mido`。

### 5. 输出 MIDI 文件无声

**可能原因**：
- DAW 未加载音色库
- MIDI 文件为空（输入音频无音高信息）

**解决**：
- 用支持 GM 音色的播放器（如 GarageBand、MuseScore）
- 检查终端输出是否有 "Saved streaming MIDI to: ..." 消息
- 用 `mido` 检查文件：
  ```python
  import mido
  mid = mido.MidiFile('output.mid')
  for msg in mid.tracks[0]:
      print(msg)
  ```

---

## 🧪 运行测试

### 离线音色转换测试

```bash
python tests/test_timbre_demo.py
```

测试内容：
1. ✅ 生成测试音频
2. ✅ 音高检测和音符分割
3. ✅ 多种音色导出
4. ✅ 移调功能
5. ✅ 自动调音
6. ✅ 卡祖笛优化
7. ✅ 批量处理

### 流式框架单元测试（即将添加）

```bash
# 调性跟踪器测试
python tests/test_key_tracker_unit.py

# 自动调音器测试
python tests/test_autotune_unit.py
```

---

## 🎯 应用场景

### 🎤 实时人声转 MIDI
音频输入 → 音高检测 → 音符分割 → 调性分析 → MIDI 输出

### 🎼 自动修音
检测跑调 → 调性识别 → 音高修正 → 生成标准版本

### 📚 音乐教学
学生演奏 → 音准分析 → 偏差检测 → 实时反馈

### 🎺 智能卡祖笛硬件
麦克风 → 实时检测 → 音域优化 → MIDI 控制器

---

## 📂 项目结构

```
swift-f0/
├── swift_f0/                      # 核心库
│   ├── __init__.py
│   ├── core.py                    # SwiftF0 音高检测
│   ├── music.py                   # 音符分割和 MIDI 导出（离线）
│   ├── music_enhanced.py          # 音色转换和自动调音（离线）⭐
│   ├── model.onnx                 # 预训练模型
│   └── streaming/                 # 流式处理框架 ⭐新增
│       ├── __init__.py
│       ├── audio.py               # 音频源（WAV/麦克风）
│       ├── inference.py           # 滑窗推理
│       ├── notes.py               # 实时音符分段
│       ├── key_detection.py       # 在线调性跟踪
│       ├── autotune.py            # 自动调音量化器
│       ├── midi.py                # MIDI 输出
│       ├── timbre.py              # 音色解析
│       ├── types.py               # 数据类型
│       ├── config.py              # 配置类
│       └── pipeline.py            # 管道编排
│
├── examples/                      # 示例脚本
│   ├── demo_timbre_transform.py   # 离线命令行工具
│   └── streaming/                 # 流式 Demo ⭐新增
│       ├── run_pipeline.py        # WAV → MIDI 流式处理
│       └── realtime_demo.py       # 实时麦克风 Demo（实验性）
│
├── tests/                         # 测试
│   ├── test_timbre_demo.py        # 离线功能测试
│   ├── test_key_tracker_unit.py   # 调性跟踪单元测试（待添加）
│   └── test_autotune_unit.py      # 自动调音单元测试（待添加）
│
├── docs/                          # 文档
│   ├── streaming/                 # 流式框架文档 ⭐
│   │   ├── SwiftF0_Streaming_Research_v1.0.md
│   │   ├── SwiftF0_Streaming_Architecture.md
│   │   ├── SwiftF0_Streaming_Optimization.md
│   │   └── Platforms_Scouting.md
│   ├── AI_KAZOO_ROADMAP.md        # 硬件项目路线图
│   ├── ARCHITECTURE.md            # 系统架构
│   ├── EDGE_DEPLOYMENT_ANALYSIS.md
│   └── zh-cn/
│       └── QUICKSTART_CN.md
│
├── README.md                      # 本文件
├── requirements.txt               # 依赖列表
└── pyproject.toml                 # 项目配置
```

---

## 🛣️ 开发路线图

- ✅ **Phase 1**: 基础音色转换（已完成）
- ✅ **Phase 2**: 自动调音（已完成）
- ✅ **Phase 3**: 卡祖笛优化（已完成）
- ✅ **Phase 4**: 实时流式处理（**已完成** ⭐）
  - ✅ 滑窗推理框架
  - ✅ 实时音符分段
  - ✅ 在线调性检测
  - ✅ 自动调音量化器
- 🔄 **Phase 5**: 硬件原型（进行中）
- 💡 **Phase 6**: 商业化（远期）

详见 [AI 卡祖笛开发路线图](docs/AI_KAZOO_ROADMAP.md)

---

## 🎓 技术亮点

### 实时流式架构

- **滑窗推理**：1024 样本窗口，256 样本跳步，低延迟推理
- **状态机分段**：IDLE → TENTATIVE_START → ACTIVE，支持 grace period
- **事件驱动**：NoteEvent (note_on/off) 流式输出，无需等待完整音频

### Krumhansl-Schmuckler 调性检测

- 24 种调性自动识别（12 大调 + 12 小调）
- 基于音高类直方图和相关分析
- 滑窗实时更新（10 秒窗口，2 秒步进）

### 智能音高量化

- 将跑调音符修正到最近音阶音
- 可调节修正强度（0-100%）
- 保留音乐表现力

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- **SwiftF0** 原作者：Lars Nieradzik
- 调性检测算法：Krumhansl & Schmuckler (1990)
- GM 音色标准：MIDI Manufacturers Association

---

## 📞 获取帮助

- 📖 查看[流式架构文档](docs/streaming/SwiftF0_Streaming_Architecture.md)
- 📖 查看[快速入门指南](docs/zh-cn/QUICKSTART_CN.md)
- 🐛 提交 [Issue](https://github.com/yourusername/swift-f0/issues)

---

**Make Kazoo Great Again! 🎺🤖**

*版本: v1.0.0 | 最后更新: 2025-10-14*
