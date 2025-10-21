# SwiftF0 文档中心

> 版本: v0.2.0-realtime | 更新: 2024-10-21

## 📚 核心文档

| 文档 | 说明 | 更新频率 |
|------|------|----------|
| [DEVELOPMENT.md](DEVELOPMENT.md) | 开发状态和进度 | 每次开发后更新 |
| [TECHNICAL.md](TECHNICAL.md) | 技术架构和实现 | 重大改动时更新 |
| [CHANGELOG.md](changelog.md) | 版本历史 | 每个版本更新 |

## 🚀 快速开始

### 安装
```bash
pip install -r requirements_realtime.txt
```

### 运行测试
```bash
python demos/realtime/test_simple_sine.py
```

### 配置
编辑 `config/realtime_config.yaml`

## 📂 项目结构

```
swift_f0/
├── core.py                # 音高检测
├── realtime/             # 实时处理
│   ├── config.py        # 配置管理
│   ├── audio_stream.py  # 音频流
│   └── simple_synthesizer.py # 合成器
└── model.onnx           # CNN模型

demos/realtime/          # 演示程序
config/                  # 配置文件
docs/                    # 文档（本目录）
```

## 🔗 其他资源

### 指南文档
- [guides/realtime_setup.md](guides/realtime_setup.md) - 实时系统设置

### 技术报告（归档）
- `archive/` - 历史文档和报告

## 📝 文档规范

1. **DEVELOPMENT.md** - 记录每次开发进度
2. **TECHNICAL.md** - 更新技术实现细节
3. **CHANGELOG.md** - 记录版本变更
4. 不创建新的MD文件，只更新现有文档

---
*主要维护: DEVELOPMENT.md 和 TECHNICAL.md*