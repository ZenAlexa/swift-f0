# SwiftF0 文档索引

欢迎来到SwiftF0音色转换和自动调音项目的文档中心！

---

## 📖 快速导航

### 🚀 新手入门

**从这里开始**：

- **[快速入门指南（中文）](zh-cn/QUICKSTART_CN.md)** ⭐推荐
  - 10分钟上手教程
  - 命令行和Python示例
  - 常见问题排查

### 📚 完整文档

- **[完整功能文档](TIMBRE_TRANSFORM_README.md)**
  - 128种GM音色列表
  - API完整参考
  - 高级定制示例
  - 性能指标

### 🏗️ 技术深度

- **[系统架构](ARCHITECTURE.md)**
  - 完整数据流图
  - 算法详解（STFT, CNN, Auto-Tune）
  - 计算复杂度分析
  - 并行化潜力

### 💻 硬件部署

- **[边缘设备部署分析](EDGE_DEPLOYMENT_ANALYSIS.md)** ⭐重要
  - ESP32-S3可行性评估
  - 模型参数详解
  - 内存和算力分析
  - 优化方案（流式处理、量化、剪枝）

- **[硬件平台对比](HARDWARE_COMPARISON.md)**
  - ESP32-S3 vs K210 vs 树莓派 vs Jetson
  - 性能、成本、功耗对比
  - 完整BOM清单
  - 技术栈对比

### 🗺️ 项目规划

- **[AI卡祖笛开发路线图](AI_KAZOO_ROADMAP.md)**
  - Phase 1-6完整规划
  - 硬件选型建议
  - 技术研究方向
  - 商业化策略

- **[项目总结](PROJECT_SUMMARY.md)**
  - 交付内容清单
  - 核心问题解答
  - 应用场景示例
  - 后续开发建议

---

## 📑 按主题分类

### 音色转换

相关文档：
- [快速入门指南](zh-cn/QUICKSTART_CN.md) - 基础用法
- [完整功能文档](TIMBRE_TRANSFORM_README.md) - 128种音色列表

关键功能：
```python
export_to_midi_enhanced(notes, "output.mid", instrument="trumpet")
```

### 自动调音

相关文档：
- [快速入门指南](zh-cn/QUICKSTART_CN.md) - 自动调音示例
- [系统架构](ARCHITECTURE.md) - Krumhansl-Schmuckler算法详解

关键功能：
```python
export_to_midi_enhanced(notes, "output.mid", auto_tune=True)
```

### 卡祖笛优化

相关文档：
- [快速入门指南](zh-cn/QUICKSTART_CN.md) - 卡祖笛模式
- [完整功能文档](TIMBRE_TRANSFORM_README.md) - 卡祖笛推荐音色

关键功能：
```python
kazoo_notes = optimize_for_kazoo(notes)
export_to_midi_enhanced(kazoo_notes, "kazoo.mid", instrument="oboe")
```

### 硬件集成

相关文档：
- [硬件平台对比](HARDWARE_COMPARISON.md) - 选型指南
- [边缘设备部署分析](EDGE_DEPLOYMENT_ANALYSIS.md) - 技术细节
- [AI卡祖笛开发路线图](AI_KAZOO_ROADMAP.md) - 实施计划

推荐平台：
- **MVP原型**: 树莓派 Zero 2W ($15)
- **便携产品**: K210 ($5)
- **最终产品**: 树莓派4 ($55)

---

## 🎯 按角色推荐

### 如果你是...

#### 🎨 **音乐爱好者**

推荐阅读：
1. [快速入门指南](zh-cn/QUICKSTART_CN.md)
2. [完整功能文档](TIMBRE_TRANSFORM_README.md) - 音色列表

你可能感兴趣：
- 改变MIDI音色
- 移调到适合自己的音域
- 自动修正跑调

#### 💻 **软件开发者**

推荐阅读：
1. [快速入门指南](zh-cn/QUICKSTART_CN.md)
2. [系统架构](ARCHITECTURE.md)
3. [项目总结](PROJECT_SUMMARY.md)

你可能感兴趣：
- API接口设计
- 算法实现细节
- 性能优化方案

#### 🔧 **硬件工程师**

推荐阅读：
1. [硬件平台对比](HARDWARE_COMPARISON.md)
2. [边缘设备部署分析](EDGE_DEPLOYMENT_ANALYSIS.md)
3. [AI卡祖笛开发路线图](AI_KAZOO_ROADMAP.md)

你可能感兴趣：
- 硬件选型依据
- 内存和算力需求
- 优化实现方案

#### 🚀 **创业者/产品经理**

推荐阅读：
1. [项目总结](PROJECT_SUMMARY.md)
2. [AI卡祖笛开发路线图](AI_KAZOO_ROADMAP.md)
3. [硬件平台对比](HARDWARE_COMPARISON.md)

你可能感兴趣：
- 产品功能特性
- 开发时间和成本
- 商业化路径

---

## 📊 文档统计

| 文档 | 字数 | 阅读时间 | 难度 |
|------|------|---------|------|
| 快速入门指南 | ~5000 | 10分钟 | ⭐ 入门 |
| 完整功能文档 | ~8000 | 20分钟 | ⭐⭐ 中级 |
| 系统架构 | ~12000 | 30分钟 | ⭐⭐⭐ 高级 |
| 边缘设备部署分析 | ~15000 | 40分钟 | ⭐⭐⭐⭐ 专家 |
| 硬件平台对比 | ~10000 | 25分钟 | ⭐⭐ 中级 |
| AI卡祖笛开发路线图 | ~13000 | 35分钟 | ⭐⭐⭐ 高级 |
| 项目总结 | ~9000 | 20分钟 | ⭐⭐ 中级 |

---

## 🔗 相关资源

### 外部文档

- [SwiftF0原始项目](https://github.com/lars76/swift-f0)
- [ONNX Runtime文档](https://onnxruntime.ai/docs/)
- [MIDI规范](https://www.midi.org/specifications)
- [Krumhansl-Schmuckler算法论文](https://scholar.google.com/scholar?q=krumhansl+schmuckler+key+finding)

### 工具和库

- [librosa](https://librosa.org/) - 音频分析库
- [mido](https://mido.readthedocs.io/) - MIDI处理库
- [matplotlib](https://matplotlib.org/) - 可视化库

### 硬件资源

- [树莓派官方文档](https://www.raspberrypi.org/documentation/)
- [K210开发文档](https://maixpy.sipeed.com/)
- [ESP32-S3技术手册](https://docs.espressif.com/projects/esp-idf/)
- [Jetson开发者套件](https://developer.nvidia.com/embedded/jetson-nano-developer-kit)

---

## 🆕 最近更新

**2025-01-13**:
- ✨ 新增边缘设备部署分析文档
- ✨ 新增硬件平台完整对比
- ✨ 完善AI卡祖笛开发路线图
- 📝 更新项目总结文档

**2025-01-12**:
- ✨ 新增完整功能文档
- ✨ 新增系统架构文档
- 🐛 修复文档链接

---

## 💬 文档反馈

发现文档问题？有改进建议？

- 📝 [提交Issue](https://github.com/yourusername/swift-f0/issues)
- ✏️ [编辑此文档](https://github.com/yourusername/swift-f0/edit/main/docs/README.md)
- 💬 加入讨论（Discord待建立）

---

## 📜 文档许可

所有文档采用 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) 许可证。

代码部分采用 MIT License。

---

**文档持续更新中... 🚀**

*最后更新: 2025-01-13*
