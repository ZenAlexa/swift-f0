# 文件结构迁移指南

**项目重组后的文件路径变更**

---

## 📋 文件迁移对照表

### 示例脚本

| 旧路径 | 新路径 | 说明 |
|--------|--------|------|
| `demo_timbre_transform.py` | `examples/demo_timbre_transform.py` | 命令行演示工具 |
| `test_timbre_demo.py` | `tests/test_timbre_demo.py` | 自动化测试脚本 |

### 文档文件

| 旧路径 | 新路径 | 说明 |
|--------|--------|------|
| `TIMBRE_TRANSFORM_README.md` | `docs/TIMBRE_TRANSFORM_README.md` | 完整功能文档 |
| `QUICKSTART_CN.md` | `docs/zh-cn/QUICKSTART_CN.md` | 中文快速入门 |
| `AI_KAZOO_ROADMAP.md` | `docs/AI_KAZOO_ROADMAP.md` | 硬件开发路线图 |
| `ARCHITECTURE.md` | `docs/ARCHITECTURE.md` | 系统架构文档 |
| `EDGE_DEPLOYMENT_ANALYSIS.md` | `docs/EDGE_DEPLOYMENT_ANALYSIS.md` | 边缘部署分析 |
| `HARDWARE_COMPARISON.md` | `docs/HARDWARE_COMPARISON.md` | 硬件平台对比 |
| `PROJECT_SUMMARY.md` | `docs/PROJECT_SUMMARY.md` | 项目总结 |

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `docs/README.md` | 文档索引和导航 |
| `.gitignore` | Git忽略规则（测试输出等） |

---

## 🔧 如何更新你的使用方式

### 1. 运行命令行工具

**旧方式**:
```bash
python demo_timbre_transform.py song.wav
```

**新方式**:
```bash
python examples/demo_timbre_transform.py song.wav
```

### 2. 运行测试

**旧方式**:
```bash
python test_timbre_demo.py
```

**新方式**:
```bash
python tests/test_timbre_demo.py
```

### 3. 阅读文档

**旧方式**:
- 直接打开根目录下的MD文件

**新方式**:
- 从 [docs/README.md](docs/README.md) 开始导航
- 中文文档在 [docs/zh-cn/](docs/zh-cn/)
- 所有技术文档在 [docs/](docs/)

### 4. Python导入（无需更改）

Python代码导入路径**保持不变**：

```python
# 这些导入仍然有效，无需修改
from swift_f0 import SwiftF0, segment_notes
from swift_f0.music_enhanced import export_to_midi_enhanced
```

---

## 📦 如果你Clone了旧版本

如果你之前克隆了项目，建议重新拉取：

```bash
# 保存你的修改（如果有）
git stash

# 拉取最新代码
git pull origin main

# 恢复你的修改（如果需要）
git stash pop
```

或者手动调整文件路径：

```bash
# 移动文件到新位置
mkdir -p examples tests docs/zh-cn

# 示例脚本
mv demo_timbre_transform.py examples/
mv test_timbre_demo.py tests/

# 文档
mv *_README.md docs/ 2>/dev/null
mv *_ANALYSIS.md docs/ 2>/dev/null
mv *_COMPARISON.md docs/ 2>/dev/null
mv *_SUMMARY.md docs/ 2>/dev/null
mv *_ROADMAP.md docs/ 2>/dev/null
mv QUICKSTART_CN.md docs/zh-cn/
```

---

## 🎯 为什么要重组

### 重组前的问题

```
swift-f0/
├── demo_timbre_transform.py      ❌ 根目录混乱
├── test_timbre_demo.py           ❌ 测试文件分散
├── AI_KAZOO_ROADMAP.md           ❌ 文档难以找到
├── ARCHITECTURE.md               ❌ 中英文混在一起
├── QUICKSTART_CN.md              ❌ 没有明确的入口
└── ... (10+ 文档文件)            ❌ 扁平化结构
```

### 重组后的优势

```
swift-f0/
├── README.md                     ✅ 清晰的入口
├── examples/                     ✅ 示例独立
├── tests/                        ✅ 测试独立
└── docs/                         ✅ 文档集中
    ├── README.md                ✅ 文档导航
    └── zh-cn/                   ✅ 中文独立
```

**好处**：
- ✅ **更专业**：符合Python项目标准结构
- ✅ **更清晰**：每个目录职责明确
- ✅ **更易维护**：文件分类清楚
- ✅ **更友好**：新手能快速找到需要的内容
- ✅ **更国际化**：中英文文档分离

---

## 🚀 快速导航

### 我想...

**运行示例**:
```bash
cd examples
python demo_timbre_transform.py --help
```

**运行测试**:
```bash
cd tests
python test_timbre_demo.py
```

**查看文档**:
- 中文入门: [docs/zh-cn/QUICKSTART_CN.md](docs/zh-cn/QUICKSTART_CN.md)
- 完整文档: [docs/README.md](docs/README.md)

**开发代码**:
```python
# 在任意位置导入（路径没变）
from swift_f0 import SwiftF0
from swift_f0.music_enhanced import export_to_midi_enhanced
```

---

## ❓ 常见问题

### Q1: 我的脚本报错找不到模块？

**A**: 确保你从项目根目录运行，或者将项目根目录加入Python路径：

```python
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from swift_f0 import SwiftF0
```

### Q2: 旧的文档链接失效了？

**A**: 使用新的文档导航：

- 主入口: [README.md](README.md)
- 文档索引: [docs/README.md](docs/README.md)

### Q3: 我想贡献代码，应该放在哪里？

**A**: 遵循新的目录结构：

- 示例脚本 → `examples/`
- 测试代码 → `tests/`
- 文档 → `docs/` (英文) 或 `docs/zh-cn/` (中文)
- 核心代码 → `swift_f0/`

---

## 📞 需要帮助？

如果你在迁移过程中遇到问题：

- 📖 查看 [README.md](README.md)
- 🐛 提交 [Issue](https://github.com/yourusername/swift-f0/issues)
- 💬 加入讨论（Discord待建立）

---

**迁移愉快！🎉**

*最后更新: 2025-10-13*
