# SwiftF0 项目状态 - 实时音色转换系统

## 🎯 当前工作链路

### 实时音频处理流程
```
麦克风输入 → 音高检测(SwiftF0) → 音色合成 → 扬声器输出
```

### 核心文件依赖
```
demos/realtime/test_simple_sine.py  # 主测试程序
    │
    ├── swift_f0/core.py            # 音高检测核心
    │   └── model.onnx              # CNN模型
    │
    ├── swift_f0/realtime/          # 实时处理模块
    │   ├── config.py               # 配置管理
    │   ├── audio_stream.py         # 音频流处理
    │   └── simple_synthesizer.py   # 音色合成
    │
    └── config/realtime_config.yaml # 配置文件
```

## ✅ 已实现功能

1. **实时音高检测** - 延迟 ~80ms
2. **简单波形合成** - 正弦波/方波/锯齿波
3. **Soundfont支持** - 128种GM乐器（可选）
4. **配置系统** - YAML配置文件
5. **跨平台音频** - sounddevice支持

## 📁 项目结构（精简后）

### 核心代码
```
swift_f0/
├── __init__.py
├── core.py                 # 音高检测
├── music.py                # 音符分段
├── music_enhanced.py       # 高级功能（离线）
├── model.onnx              # ONNX模型
└── realtime/               # 实时模块
    ├── __init__.py
    ├── config.py           # 配置管理
    ├── audio_stream.py     # 音频流
    ├── simple_synthesizer.py # 合成器
    └── audio_buffer.py     # 缓冲器（备用）
```

### 配置和资源
```
config/
└── realtime_config.yaml    # 实时处理配置

soundfonts/
└── GeneralUser-GS.sf2      # GM音色库(30MB)
```

### 演示和测试
```
demos/
├── basic/                  # 基础示例
├── advanced/               # 高级功能
├── tutorials/              # 教程
└── realtime/               # 实时演示
    ├── test_simple.py      # 基础测试
    └── test_simple_sine.py # 正弦波测试
```

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install sounddevice PyYAML numpy onnxruntime

# 2. 运行测试
python demos/realtime/test_simple_sine.py
```

## ⚙️ 关键参数

| 参数 | 当前值 | 说明 |
|------|--------|------|
| 采样率 | 16000 Hz | SwiftF0要求 |
| 块大小 | 256 samples | 16ms延迟 |
| 窗口大小 | 1024 samples | 64ms |
| 总延迟 | ~80ms | 可接受范围 |
| CPU占用 | ~20% | 单核 |

## 🔧 与开发板集成

当前系统已为开发板集成做好准备：

1. **音频接口**: 通过 `device_id` 配置指定开发板
2. **数据格式**: PCM 16bit, 16kHz, Mono
3. **缓冲管理**: 256样本/块，适合实时传输

```yaml
# config/realtime_config.yaml
audio:
  device_in: 2  # 开发板设备ID
  device_out: 3 # 输出设备ID
```

## 📊 性能优化建议

1. **降低延迟**: 减小 `chunk_size` 到 128
2. **提高稳定性**: 增大 `buffer_size`
3. **降低CPU**: 使用 `simple` 合成方法

## 🗑️ 已清理文件

以下文件已被归档（添加 .bak 后缀）：
- `stream_processor.py` - 早期复杂版本
- `timbre_engine.py` - 早期复杂版本
- `microphone_timbre_transform.py` - 使用弃用模块

## 📝 下一步计划

1. **优化延迟** - 目标 <50ms
2. **完善合成** - 改进音色质量
3. **硬件对接** - 与开发板通信协议
4. **效果处理** - 添加混响等效果

---

*最后更新: 2024*