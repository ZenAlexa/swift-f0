# AI卡祖笛硬件项目开发路线图

基于SwiftF0音色转换和自动调音技术栈

---

## 📋 项目概述

**目标**: 开发一个智能卡祖笛硬件设备，能够：
1. 实时捕获用户哼唱/演唱
2. 自动音高检测和修正
3. 转换为卡祖笛音色
4. 输出MIDI信号或直接音频合成
5. 支持多种音色和效果

**技术栈**:
- 核心算法: SwiftF0（本项目）
- 音频处理: librosa, soundfile
- MIDI处理: mido, python-rtmidi
- 硬件平台: 树莓派 / Jetson Nano / STM32

---

## 🎯 Phase 1: MVP软件原型（✅ 已完成）

**时间**: 已完成
**状态**: ✅ 100%

### 已实现功能

- [x] 音高检测 (SwiftF0核心)
- [x] 音符分割
- [x] 128种GM音色支持
- [x] 移调功能
- [x] 自动调音（Krumhansl-Schmuckler算法）
- [x] 卡祖笛音域优化
- [x] 批量处理工具
- [x] 命令行界面

### 技术指标

- 延迟: ~150ms（5秒音频）
- 精度: 亚半音级别
- 支持格式: WAV, MP3, FLAC等

### 交付物

- `swift_f0/music_enhanced.py` - 核心扩展模块
- `demo_timbre_transform.py` - 演示脚本
- `test_timbre_demo.py` - 测试套件
- 完整文档（README, QUICKSTART, ARCHITECTURE）

---

## 🚀 Phase 2: 实时处理引擎（规划中）

**时间**: 2-3周
**优先级**: 🔥 高

### 目标

将批处理系统改造为实时流式处理系统，延迟降低到 **<50ms**。

### 技术挑战

1. **流式音频缓冲**
   - 使用环形缓冲区(Ring Buffer)
   - 1024样本窗口（64ms @ 16kHz）
   - 重叠分析（50% overlap）

2. **模型优化**
   - ONNX Runtime优化（INT8量化）
   - 批处理推理（多帧并行）
   - GPU加速（CUDA/TensorRT）

3. **音频I/O**
   - PyAudio/SoundDevice实时流
   - JACK Audio Connection Kit（Linux）
   - CoreAudio（macOS）

### 实现任务

- [ ] 设计环形缓冲区架构
- [ ] 实现流式音高检测器
- [ ] 优化ONNX模型推理速度
- [ ] 实现实时音符分割
- [ ] 实现MIDI实时输出
- [ ] 延迟基准测试（目标<50ms）

### 代码框架

```python
class RealtimeKazooProcessor:
    """实时卡祖笛音频处理器"""

    def __init__(self, sample_rate=16000, buffer_size=1024):
        self.detector = SwiftF0()
        self.buffer = RingBuffer(size=sample_rate)  # 1秒缓冲
        self.midi_out = MidiOutput()
        self.current_note = None

    def process_audio_chunk(self, chunk):
        """处理音频块（回调函数）"""
        # 1. 添加到缓冲区
        self.buffer.append(chunk)

        # 2. 检测音高（使用最近256样本）
        if self.buffer.ready():
            audio = self.buffer.get_analysis_window()
            result = self.detector.detect_from_array(audio, 16000)

            # 3. 实时判决当前音符
            if result.voicing[-1]:  # 最新帧有声
                pitch_midi = self._hz_to_midi(result.pitch_hz[-1])

                # 4. Note On/Off逻辑
                if self.current_note is None:
                    self.midi_out.note_on(pitch_midi, velocity=80)
                    self.current_note = pitch_midi
                elif abs(pitch_midi - self.current_note) > 0.8:
                    self.midi_out.note_off(self.current_note)
                    self.midi_out.note_on(pitch_midi, velocity=80)
                    self.current_note = pitch_midi
            else:
                if self.current_note:
                    self.midi_out.note_off(self.current_note)
                    self.current_note = None

    def start_realtime(self):
        """启动实时处理"""
        import sounddevice as sd
        sd.InputStream(
            callback=self.process_audio_chunk,
            channels=1,
            samplerate=16000,
            blocksize=1024
        ).start()
```

### 性能目标

| 指标 | 目标值 |
|------|--------|
| 端到端延迟 | <50ms |
| CPU占用 | <30% (树莓派4) |
| 音高精度 | ±10 cents |
| Note On延迟 | <20ms |

---

## 🔧 Phase 3: 硬件原型v1（规划中）

**时间**: 3-4周
**优先级**: 🔥 高

### 硬件选型

#### 方案A: 树莓派4（推荐入门）

**优点**:
- 生态成熟，开发容易
- GPIO丰富，扩展性强
- 价格适中（$35-55）

**缺点**:
- 性能有限（CPU推理可能吃力）
- 功耗较高

**配置**:
- 树莓派4B (4GB RAM)
- USB麦克风
- 3.5mm音频输出或USB MIDI接口
- 可选: 小型OLED屏幕

#### 方案B: Jetson Nano（推荐最终产品）

**优点**:
- GPU加速（128核CUDA）
- 性能强劲（实时推理无压力）
- 功耗合理（5-10W）

**缺点**:
- 价格较高（$99）
- 生态不如树莓派

**配置**:
- Jetson Nano 4GB
- I2S MEMS麦克风（高质量）
- 板载音频输出
- MIDI接口（UART转USB）

#### 方案C: STM32（超低功耗版本）

**优点**:
- 超低功耗（<1W）
- 成本极低（$5-10）
- 可做成便携设备

**缺点**:
- 需要模型量化（INT8/INT16）
- 开发难度高（C/C++）
- 功能受限

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      AI卡祖笛硬件原型v1                        │
└─────────────────────────────────────────────────────────────┘

  [麦克风输入] → [音频ADC] → [树莓派/Jetson]
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              [音频预处理]   [显示屏]      [按钮控制]
                    │           (状态)        (音色切换)
                    ▼
           [SwiftF0音高检测]
                    │
                    ▼
            [实时音符分割器]
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
    [自动调音]           [音域限制]
          │                   │
          └─────────┬─────────┘
                    ▼
             [MIDI生成器]
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
    [USB MIDI输出]      [板载合成器]
          │                   │
          ▼                   ▼
    [电脑/合成器]        [音频输出]
```

### 功能规划

#### 核心功能

- [ ] 实时音高检测（<50ms延迟）
- [ ] 自动调音（可开关）
- [ ] 音色切换（至少5种）
- [ ] 移调（±12半音）
- [ ] 音域限制（E3-E5）

#### 交互设计

- [ ] 按钮1: 电源开关
- [ ] 按钮2: 音色切换（循环）
- [ ] 按钮3: 自动调音开关
- [ ] 旋钮1: 移调调节（-12到+12）
- [ ] 旋钮2: 音量调节
- [ ] LED指示: 电源、检测状态、MIDI活动

#### 显示内容

- [ ] 当前音高（Hz + MIDI音符名）
- [ ] 当前音色
- [ ] 自动调音状态
- [ ] 移调值
- [ ] 电池电量（如果是便携版）

### 物料清单（BOM）

**树莓派方案**:

| 部件 | 型号 | 数量 | 单价 | 总价 |
|------|------|------|------|------|
| 主控 | 树莓派4B 4GB | 1 | $55 | $55 |
| 麦克风 | USB麦克风 | 1 | $10 | $10 |
| 显示屏 | 0.96" OLED (I2C) | 1 | $5 | $5 |
| 按钮 | 轻触开关 | 5 | $0.5 | $2.5 |
| 旋钮 | 旋转编码器 | 2 | $2 | $4 |
| 外壳 | 3D打印 | 1 | $10 | $10 |
| 电源 | 5V 3A USB-C | 1 | $8 | $8 |
| 杂项 | 线材、电阻等 | - | - | $5 |
| **总计** | | | | **~$100** |

### 软件架构

```python
# kazoo_hardware.py
class KazooHardwareController:
    def __init__(self):
        self.processor = RealtimeKazooProcessor()
        self.display = OLEDDisplay()
        self.buttons = ButtonController()
        self.settings = {
            'instrument': 'oboe',
            'transpose': 0,
            'auto_tune': True,
            'volume': 80,
        }

    def button_callback(self, button_id):
        if button_id == 2:  # 音色切换
            self.cycle_instrument()
        elif button_id == 3:  # 自动调音开关
            self.toggle_auto_tune()

    def cycle_instrument(self):
        instruments = ['oboe', 'trumpet', 'harmonica', 'clarinet', 'flute']
        idx = instruments.index(self.settings['instrument'])
        self.settings['instrument'] = instruments[(idx + 1) % len(instruments)]
        self.display.show_message(f"音色: {self.settings['instrument']}")

    def run(self):
        # 启动实时处理
        self.processor.start_realtime()

        # 主循环
        while True:
            # 更新显示
            self.update_display()

            # 检查按钮
            self.buttons.poll()

            time.sleep(0.01)
```

---

## 🎨 Phase 4: UI/UX优化（规划中）

**时间**: 2周
**优先级**: 🟡 中

### Web配置界面

使用Flask创建配置界面：

```python
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('config.html', settings=kazoo.settings)

@app.route('/api/set_instrument', methods=['POST'])
def set_instrument():
    instrument = request.json['instrument']
    kazoo.settings['instrument'] = instrument
    return {'status': 'ok'}

@app.route('/api/set_transpose', methods=['POST'])
def set_transpose():
    transpose = request.json['transpose']
    kazoo.settings['transpose'] = transpose
    return {'status': 'ok'}

# 在树莓派上运行web服务器
# 用户通过手机/电脑访问 http://raspberrypi.local:5000 配置
```

### 移动App（可选）

- iOS/Android配置app
- 蓝牙通信（BLE）
- 预设管理（保存/加载配置）
- 固件更新OTA

---

## 🌐 Phase 5: 云端服务（规划中）

**时间**: 3-4周
**优先级**: 🟢 低（可选）

### 功能设计

1. **用户账号系统**
   - 注册/登录
   - 预设同步
   - 使用统计

2. **云端处理**（降级方案）
   - 硬件性能不足时
   - 上传音频到云端
   - 云端处理后返回MIDI

3. **社区功能**
   - 分享演奏录音
   - 预设市场（用户自定义音色配置）
   - 排行榜

### 技术栈

- 后端: FastAPI (Python)
- 数据库: PostgreSQL + Redis
- 存储: S3
- 部署: AWS Lambda / Google Cloud Run
- CDN: CloudFlare

---

## 📊 Phase 6: 商业化（远期）

**时间**: 持续
**优先级**: 💡 长期

### 产品定位

**目标用户**:
1. 音乐爱好者（非专业）
2. 音乐教师/学生
3. 街头艺人
4. 儿童教育

**定价策略**:
- 硬件设备: $150-200（小批量生产）
- 订阅服务: $5/月（云端高级功能）
- 企业授权: $500/年（教育机构）

### 营销渠道

- Kickstarter众筹
- YouTube/B站演示视频
- 音乐教育展会
- 开源社区（GitHub）

### 收入模型

1. **硬件销售**（主要收入）
2. **云服务订阅**（MRR）
3. **企业授权**（B2B）
4. **广告/赞助**（免费版）

---

## 🔬 技术研究方向（长期）

### 1. 音色克隆

使用深度学习克隆真实卡祖笛音色：

- 收集真实卡祖笛录音数据集
- 训练WaveNet/Tacotron模型
- 实时神经音频合成

### 2. 多人和声

支持多个设备协同演奏：

- WiFi/蓝牙网络同步
- 延迟补偿算法
- 和声检测和自动伴奏

### 3. AI作曲助手

基于用户哼唱生成完整编曲：

- 旋律 → 和弦进行
- 自动配器（鼓、贝斯、和声）
- 风格迁移（爵士/摇滚/古典）

### 4. 手势控制

通过摄像头/IMU传感器控制效果：

- 手势识别（挥手改变音色）
- 倾斜控制音高弯曲
- 震动增强颤音

---

## 📝 里程碑时间表

```
2025 Q1:
  ✅ Phase 1: MVP软件原型（已完成）

2025 Q2:
  🔄 Phase 2: 实时处理引擎（进行中）
     Week 1-2: 环形缓冲区和流式架构
     Week 3-4: ONNX优化和延迟测试

2025 Q3:
  🔄 Phase 3: 硬件原型v1
     Week 1-2: 硬件采购和组装
     Week 3-4: 软件集成和测试
     Week 5-6: 外壳设计和3D打印

2025 Q4:
  🔄 Phase 4: UI/UX优化
  🔄 Phase 5: 云端服务（可选）

2026:
  🔄 Phase 6: 小批量生产和商业化
```

---

## 🎯 当前优先级排序

### P0 - 立即开始（本月）

1. **实时处理引擎开发**
   - 这是从软件原型到硬件的关键一步
   - 需要先验证延迟能否达标

2. **延迟基准测试**
   - 在不同硬件平台测试
   - 确定最终硬件方案

### P1 - 短期（1-2个月）

1. **硬件原型采购**
   - 订购树莓派4或Jetson Nano
   - 购买麦克风、显示屏等配件

2. **3D外壳设计**
   - 在TinkerCAD或Fusion 360设计
   - 本地打印或Shapeways订购

### P2 - 中期（3-6个月）

1. **Web配置界面**
2. **移动App原型**
3. **用户测试和反馈**

---

## 🤝 开源vs闭源策略

### 建议：混合模式

**开源部分**（构建社区）:
- 核心算法（SwiftF0扩展）
- 实时处理引擎
- 硬件设计图纸
- 基础固件

**闭源部分**（商业化）:
- 云端服务后端
- 移动App
- 高级音色包
- 企业版功能

**许可证建议**:
- 核心代码: MIT License
- 硬件设计: CERN Open Hardware License
- 商业服务: 专有许可证

---

## 📚 技术学习路径

如果你是硬件新手，推荐学习路径：

### Week 1-2: 树莓派入门
- 安装Raspberry Pi OS
- GPIO编程基础
- I2C/SPI通信
- 音频输入/输出

### Week 3-4: 实时音频处理
- PyAudio/SoundDevice
- 环形缓冲区实现
- 延迟测量和优化

### Week 5-6: MIDI编程
- python-rtmidi库
- MIDI消息格式
- USB MIDI接口配置

### Week 7-8: 嵌入式优化
- ONNX Runtime配置
- 多线程/异步编程
- 性能分析工具（perf, cProfile）

---

## 🔗 参考资源

### 硬件
- [树莓派官方文档](https://www.raspberrypi.org/documentation/)
- [Jetson Nano开发者套件](https://developer.nvidia.com/embedded/jetson-nano-developer-kit)
- [音频HAT推荐](https://www.hifiberry.com/)

### 软件
- [PyAudio文档](https://people.csail.mit.edu/hubert/pyaudio/)
- [python-rtmidi教程](https://spotlightkid.github.io/python-rtmidi/)
- [ONNX Runtime嵌入式指南](https://onnxruntime.ai/docs/tutorials/mobile/)

### 相似项目
- [Eigenharp](https://www.eigenlabs.com/) - 电子管乐控制器
- [ROLI Seaboard](https://roli.com/products/seaboard) - MPE键盘
- [Artiphon INSTRUMENT 1](https://artiphon.com/) - 多功能MIDI控制器

---

## 💬 社区和支持

加入讨论：
- GitHub Issues: 提问和Bug报告
- Discord服务器: 实时讨论（待建立）
- Reddit: r/WeAreTheMusicMakers

---

**让我们一起打造史上最智能的卡祖笛！🎺🤖**

更新日期: 2025-01-13
版本: v1.0
