# SwiftF0 文档中心

> 版本: v0.3.0 | 更新: 2024-10-21

## 📚 核心文档

| 文档 | 说明 | 状态 |
|------|------|------|
| [DEVELOPMENT.md](DEVELOPMENT.md) | 开发进度和记录 | ✅ 活跃 |
| [TECHNICAL.md](TECHNICAL.md) | 技术架构细节 | ✅ 活跃 |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | 项目价值总结 | ✅ 完成 |

## 🎯 项目成果

### 核心功能
- ✅ **实时音高检测** - CNN模型389KB，精度<1%
- ✅ **USB音频集成** - 支持ESP32/开发板输入
- ✅ **实时音色合成** - 正弦波合成，可扩展
- ✅ **低延迟处理** - 标准80ms，可优化至20ms

### 性能指标
- 📊 模型大小: 389KB
- ⚡ 延迟: 20-80ms
- 🎯 精度: <1% 误差
- 💾 内存: ~50MB

## 🚀 快速开始

### USB音频处理
```bash
# 运行实时处理
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000
```

### 麦克风测试
```bash
python demos/realtime/test_simple_sine.py
```

## 📂 项目结构

```
swift_f0/
├── core.py                     # 音高检测核心
├── model.onnx                  # CNN模型
├── realtime/                   # 实时处理
│   ├── config.py              # 配置管理
│   ├── audio_stream.py        # 音频流
│   ├── simple_synthesizer.py  # 音色合成
│   └── usb_processor.py       # USB处理器
└── usb_audio/                  # USB音频
    └── receiver.py            # 数据接收

demos/realtime/                # 演示程序
├── run_usb_audio.py          # 主程序
└── test_simple_sine.py       # 测试程序
```

## 📝 文档维护原则

1. **集中管理** - 所有文档在 docs/ 目录
2. **版本控制** - 更新现有文档，避免创建新文件
3. **简洁清晰** - 技术文档注重实用性

---
*核心维护: DEVELOPMENT.md (进度) | TECHNICAL.md (技术)*