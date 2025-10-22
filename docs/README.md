# SwiftF0 文档中心

> **版本**: v0.4.0 | **更新**: 2024-10-22

---

## 📚 核心文档

### 活跃文档

| 文档 | 说明 | 受众 |
|------|------|------|
| [TECHNICAL.md](TECHNICAL.md) | 技术架构与算法详解 | 开发者 |
| [ALGORITHMS.md](ALGORITHMS.md) | 算法快速索引 | 开发者 |
| [DEVELOPMENT.md](DEVELOPMENT.md) | 开发进度和日志 | 团队 |
| [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) | 项目结构总览 | 开发者 |
| [../README.md](../README.md) | 项目主页 | 所有人 |

---

## 🎯 项目现状（Alpha Demo v1）

### 已完成功能
- ✅ **实时音高检测** - CNN模型389KB，<1%误差
- ✅ **USB音频集成** - ESP32/开发板输入
- ✅ **波表合成** - 长笛/小提琴/单簧管音色
- ✅ **声音衰减优化** - 快速响应停止信号
- ✅ **低延迟处理** - 标准80ms，可优化至20ms

### 性能指标
- 📊 模型: 389KB ONNX
- ⚡ 延迟: ~80ms
- 🎯 精度: <1% 误差
- 💾 内存: ~50MB
- 🔊 音色: 3种乐器 + 纯正弦波

---

## 🚀 快速导航

### 开发者
1. **项目结构** → [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)
2. **了解技术** → [TECHNICAL.md](TECHNICAL.md)
3. **查找算法** → [ALGORITHMS.md](ALGORITHMS.md)
4. **查看进度** → [DEVELOPMENT.md](DEVELOPMENT.md)
5. **安装使用** → [../README.md](../README.md)

### 用户
1. **项目简介** → [../README.md](../README.md#项目概述)
2. **快速开始** → [../README.md](../README.md#快速开始)
3. **命令行工具** → [../README.md](../README.md#命令行工具)

---

## 📂 文档结构

```
docs/
├── README.md                 # 本文件 - 文档导航中心
├── TECHNICAL.md             # 技术文档（活跃维护）
├── ALGORITHMS.md            # 算法索引（活跃维护）
├── DEVELOPMENT.md           # 开发日志（活跃维护）
│
├── guides/                  # 指南（参考）
│   ├── realtime_setup.md   # 实时处理配置
│   └── migration_guide.md  # 迁移指南
│
├── research/                # 研究文档（参考）
│   ├── ai_kazoo_roadmap.md
│   ├── embedded_interface_report.md
│   └── streaming_research_brief.md
│
├── technical/               # 技术细节（参考）
│   ├── architecture.md      # 系统架构
│   ├── realtime_architecture.md
│   ├── edge_deployment_analysis.md
│   └── hardware_comparison.md
│
└── archive/                 # 归档（历史记录）
    ├── PROJECT_STATUS_20241021.md
    ├── REORGANIZATION_REPORT.md
    └── ...
```

---

## 🔧 使用方法

### USB音频实时处理
```bash
# 默认长笛音色
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000

# 小提琴音色
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000 --instrument violin

# 单簧管音色
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000 --instrument clarinet
```

### 麦克风测试
```bash
python demos/realtime/test_simple_sine.py
```

### 波表合成质量测试
```bash
python demos/realtime/test_additive_synth.py
```

---

## 📝 文档维护原则

### 核心原则
1. **活跃维护** - 只维护 TECHNICAL.md 和 DEVELOPMENT.md
2. **向后兼容** - 旧文档归档但不删除
3. **简洁实用** - 避免重复内容
4. **及时更新** - 功能变更立即更新文档

### 更新优先级
- **必须更新**: TECHNICAL.md, DEVELOPMENT.md, README.md
- **选择更新**: guides/, research/, technical/
- **不需更新**: archive/

---

## 🗂️ 文档类型说明

### TECHNICAL.md - 技术文档
**内容**:
- 核心算法原理
- 系统架构设计
- 性能优化技巧
- 配置参数说明

**更新频率**: 每次技术变更

### DEVELOPMENT.md - 开发日志
**内容**:
- 功能开发进度
- 已知问题和解决方案
- 下一步计划
- 版本更新记录

**更新频率**: 每个开发阶段

### guides/ - 使用指南
**内容**:
- 配置指南
- 迁移指南
- 最佳实践

**更新频率**: 按需更新

### research/ - 研究文档
**内容**:
- 技术调研报告
- 方案对比分析
- 路线图规划

**更新频率**: 研究完成时

### technical/ - 技术细节
**内容**:
- 详细架构图
- 硬件对比
- 部署分析

**更新频率**: 重大架构变更时

### archive/ - 历史归档
**内容**:
- 已过时的文档
- 历史版本记录
- 重组报告

**更新频率**: 不更新（只读）

---

## 🔗 相关资源

### 代码模块
- [swift_f0/core.py](../swift_f0/core.py) - 音高检测核心
- [swift_f0/realtime/](../swift_f0/realtime/) - 实时处理模块
- [swift_f0/realtime/additive_synthesizer.py](../swift_f0/realtime/additive_synthesizer.py) - 波表合成器
- [swift_f0/realtime/wavetable_generator.py](../swift_f0/realtime/wavetable_generator.py) - 波表生成器

### 测试数据
- [test_data/audio_output/](../test_data/audio_output/) - 测试音频输出
- [wavetables/](../wavetables/) - 预生成波表

### 配置
- [config/realtime_config.yaml](../config/realtime_config.yaml) - 实时处理配置

---

*文档维护: 只更新活跃文档（TECHNICAL.md, DEVELOPMENT.md），其他文档按需参考*
