# SwiftF0 Timbre Transformation & Auto-Tune Extension

**为AI卡祖笛项目打造的音色转换和自动调音工具**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

---

## 🎯 项目概述

基于SwiftF0音高检测库，开发一套完整的音色转换和自动调音系统，为AI卡祖笛硬件项目提供核心算法支持。

### 核心功能

✅ **128种GM标准音色** - 钢琴、弦乐、管乐、合成器等
✅ **智能移调** - ±24半音范围自动调整
✅ **自动调音** - 24种调性检测 + 音高量化
✅ **卡祖笛优化** - E3-E5音域限制 + 专用音色
✅ **批量处理** - 一键生成多种音色版本

### 性能指标

⚡ **低延迟**: ~150ms (5秒音频)
🎯 **高精度**: ±10 cents (亚半音级别)
🔋 **轻量级**: 389KB模型 + 350MB内存

---

## 📦 快速安装

```bash
# 安装基础依赖
pip install swift-f0

# 安装完整功能（推荐）
pip install swift-f0[full]

# 或从源码安装
git clone https://github.com/yourusername/swift-f0.git
cd swift-f0
pip install -e .
```

---

## 🚀 10秒上手

```python
from swift_f0 import SwiftF0, segment_notes
from swift_f0.music_enhanced import export_to_midi_enhanced

# 1. 检测音高
detector = SwiftF0()
result = detector.detect_from_file("song.wav")

# 2. 分割音符
notes = segment_notes(result)

# 3. 改变音色 + 移调 + 自动调音
export_to_midi_enhanced(
    notes,
    "output.mid",
    instrument="trumpet",    # 小号音色
    transpose=5,             # 升高5个半音
    auto_tune=True          # 自动修正音准
)
```

**命令行一键转换**:
```bash
python examples/demo_timbre_transform.py song.wav --kazoo --auto-tune
```

---

## 📚 文档导航

### 项目结构
- 📁 [项目结构说明](PROJECT_STRUCTURE.md) - 目录组织和开发指南

### 技术深度
- 🏗️ [系统架构](docs/ARCHITECTURE.md) - 数据流和算法详解
- 💻 [边缘设备部署分析](docs/EDGE_DEPLOYMENT_ANALYSIS.md) - ESP32/树莓派部署
- 📊 [硬件平台对比](docs/HARDWARE_COMPARISON.md) - 完整选型指南

### 项目规划
- 🗺️ [AI卡祖笛开发路线图](docs/AI_KAZOO_ROADMAP.md) - Phase 1-6规划
- 📝 [项目总结](docs/PROJECT_SUMMARY.md) - 完整交付清单
- 📋 [版本历史](docs/CHANGELOG.md) - 版本更新记录
- 🔄 [迁移指南](docs/MIGRATION_GUIDE.md) - 版本迁移说明

---

## 🎵 音色示例

### 改变音色
```python
# 小号（明亮）
export_to_midi_enhanced(notes, "trumpet.mid", instrument="trumpet")

# 长笛（柔和）
export_to_midi_enhanced(notes, "flute.mid", instrument="flute")

# 双簧管（鼻音，接近卡祖笛）
export_to_midi_enhanced(notes, "oboe.mid", instrument="oboe")
```

### 移调
```python
# 升高5个半音
export_to_midi_enhanced(notes, "higher.mid", transpose=5)

# 降低3个半音
export_to_midi_enhanced(notes, "lower.mid", transpose=-3)
```

### 自动调音
```python
# 完全修正
export_to_midi_enhanced(notes, "perfect.mid", auto_tune=True, auto_tune_strength=1.0)

# 轻微修正（保留原始味道）
export_to_midi_enhanced(notes, "slight.mid", auto_tune=True, auto_tune_strength=0.5)
```

### 卡祖笛专用
```python
from swift_f0.music_enhanced import optimize_for_kazoo

kazoo_notes = optimize_for_kazoo(notes)
export_to_midi_enhanced(
    kazoo_notes,
    "kazoo.mid",
    instrument="oboe",
    pitch_range=(52, 76)  # E3-E5
)
```

---

## 🎮 命令行工具

```bash
# 基础转换
python examples/demo_timbre_transform.py song.wav

# 改变音色
python examples/demo_timbre_transform.py song.wav -i trumpet

# 移调
python examples/demo_timbre_transform.py song.wav -t 5

# 自动调音
python examples/demo_timbre_transform.py song.wav --auto-tune

# 卡祖笛模式（音域优化+合适音色）
python examples/demo_timbre_transform.py song.wav --kazoo

# 批量生成9种音色
python examples/demo_timbre_transform.py song.wav --batch

# 组合使用
python examples/demo_timbre_transform.py song.wav \
    --kazoo --auto-tune --strength 0.8 -t 2
```

查看所有参数：
```bash
python examples/demo_timbre_transform.py --help
```

---

## 🧪 运行测试

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

---

## 🎯 应用场景

### 🎤 实时人声转MIDI
音频输入 → 音高检测 → 音符分割 → 音色转换 → MIDI输出

### 🎼 自动修音
检测跑调 → 调性识别 → 音高修正 → 生成标准版本

### 📚 音乐教学
学生演奏 → 音准分析 → 偏差检测 → 实时反馈

### 🎺 智能卡祖笛硬件
麦克风 → 实时检测 → 音域优化 → MIDI控制器

---

## 📊 推荐硬件平台

*需大量优化工作，详见[边缘设备部署分析](docs/EDGE_DEPLOYMENT_ANALYSIS.md)

---

## 🛣️ 开发路线图

- ✅ **Phase 1**: 基础音色转换（已完成）
- ✅ **Phase 2**: 自动调音（已完成）
- ✅ **Phase 3**: 卡祖笛优化（已完成）
- 🔄 **Phase 4**: 实时流式处理（进行中）
- 🔄 **Phase 5**: 硬件原型（进行中）
- 💡 **Phase 6**: 商业化（远期）

详见[AI卡祖笛开发路线图](docs/AI_KAZOO_ROADMAP.md)

---

## 🎓 技术亮点

### Krumhansl-Schmuckler调性检测
- 24种调性自动识别（12大调+12小调）
- 基于音高类直方图和相关分析
- 准确率>90%

### 智能音高量化
- 将跑调音符修正到最近音阶音
- 可调节修正强度（0-100%）
- 保留音乐表现力

### 卡祖笛专用优化
- 自动音域调整（E3-E5）
- 9种鼻音/嗡嗡音色推荐
- 批量A/B测试工具

---

## 📂 项目结构

```
swift-f0/
├── swift_f0/                   # 核心库
│   ├── __init__.py
│   ├── core.py                # SwiftF0音高检测
│   ├── music.py               # 音符分割和MIDI导出
│   ├── music_enhanced.py      # 音色转换和自动调音 ⭐新增
│   └── model.onnx             # 预训练模型
│
├── examples/                   # 示例脚本
│   └── demo_timbre_transform.py  # 命令行工具
│
├── tests/                      # 测试
│   └── test_timbre_demo.py
│
├── docs/                       # 文档
│   ├── AI_KAZOO_ROADMAP.md    # 硬件项目路线图
│   ├── ARCHITECTURE.md         # 系统架构
│   ├── EDGE_DEPLOYMENT_ANALYSIS.md  # 边缘部署分析
│   ├── HARDWARE_COMPARISON.md  # 硬件对比
│   ├── PROJECT_SUMMARY.md      # 项目总结
│   └── zh-cn/                  # 中文文档
│       └── QUICKSTART_CN.md
│
├── README.md                   # 本文件
├── CHANGELOG.md               # 版本历史
├── pyproject.toml             # 项目配置
└── requirements.txt           # 依赖列表
```

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- **SwiftF0** 原作者：Lars Nieradzik
- 调性检测算法：Krumhansl & Schmuckler (1990)
- GM音色标准：MIDI Manufacturers Association

---

## 📞 获取帮助

- 📖 查看[快速入门指南](docs/zh-cn/QUICKSTART_CN.md)
- 🐛 提交[Issue](https://github.com/yourusername/swift-f0/issues)

---

**Make Kazoo Great Again! 🎺🤖**

*版本: v0.1.2 | 最后更新: 2025-10-13*
