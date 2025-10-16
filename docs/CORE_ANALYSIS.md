# 核心模块深度分析

## 目录
1. [音频处理管道概览](#音频处理管道概览)
2. [核心模块详解](#核心模块详解)
3. [潜在问题点分析](#潜在问题点分析)
4. [性能瓶颈识别](#性能瓶颈识别)

---

## 音频处理管道概览

### 完整数据流程

```
麦克风输入 (44.1kHz)
    ↓
重采样到 16kHz (sounddevice)
    ↓
256 样本块 (16ms)
    ↓
[1] EnergyGate 能量门控
    ↓
[2] SwiftF0Streamer 滑动窗口
    ↓
[3] SwiftF0 ONNX 模型推理
    ↓
[4] PitchFrame 输出
    ↓
[5] RealtimeNoteSegmenter 状态机
    ↓
[6] NoteEvent (note_on/note_off)
    ↓
[7] RealtimeAdditiveSynth 合成
    ↓
扬声器输出 (44.1kHz)
```

### 延迟预算分析

| 阶段 | 延迟 | 说明 |
|------|------|------|
| 麦克风 → 缓冲 | ~16ms | 256 样本 @ 16kHz |
| EnergyGate | <1ms | 纯计算，RMS 平滑 |
| SwiftF0 推理 | ~10-20ms | ONNX CPU 推理 |
| Note Segmenter | 80-160ms | **主要瓶颈** |
| 合成器 | <5ms | 实时生成波形 |
| 输出缓冲 | ~6ms | 256 样本 @ 44.1kHz |
| **总计** | **112-207ms** | **不可接受** |

---

## 核心模块详解

### 1. SwiftF0 核心检测器 (`swift_f0/core.py`)

#### 关键参数（硬编码）

```python
TARGET_SAMPLE_RATE = 16000  # 固定 16kHz，不可更改
HOP_LENGTH = 256            # 16ms/帧，模型架构决定
FRAME_LENGTH = 1024         # STFT 窗口大小
STFT_PADDING = 384          # 对称填充
CENTER_OFFSET = 127.5       # 时间戳对齐偏移
```

**关键发现：**
- `HOP_LENGTH = 256` 是**硬编码**在 ONNX 模型中的
- 这意味着**最小时间分辨率 = 16ms**，无法改变
- 每次推理需要 1024 个样本（64ms 的音频）

#### 音高检测流程

```python
def extract_pitch_and_confidence(self, audio_16k: np.ndarray):
    # 1. 输入验证和填充
    if len(audio_16k) < MIN_AUDIO_LENGTH:  # 256 样本
        audio_16k = np.pad(...)

    # 2. ONNX 推理（核心计算）
    ort_inputs = {self.pitch_input_name: audio_16k[None, :].astype(np.float32)}
    outputs = self.pitch_session.run(None, ort_inputs)

    # 3. 提取结果
    return outputs[0][0], outputs[1][0]  # pitch_hz, confidence
```

**关键发现：**
- 模型每次推理返回**多个帧**（不是单帧）
- 输入 N 个样本，输出 `(N - STFT_PADDING*2) // HOP_LENGTH` 帧
- 例如：1024 样本 → `(1024-768)/256 = 1` 帧

#### Voicing 决策逻辑

```python
def _compute_voicing(self, pitch_hz, confidence):
    return (
        (confidence > self.confidence_threshold)  # 默认 0.9
        & (pitch_hz >= self.fmin)                 # 默认 46.875 Hz
        & (pitch_hz <= self.fmax)                 # 默认 2093.75 Hz
    )
```

**潜在问题：**
- `confidence_threshold = 0.9` **过高**，导致漏检
- 这是在 DEMO 中降低到 0.75-0.85 的原因

---

### 2. SwiftF0Streamer 流式包装器 (`swift_f0/streaming/inference.py`)

#### 架构设计

```python
class SwiftF0Streamer:
    def __init__(self, detector: SwiftF0, enable_energy_gate=True, ...):
        self.window_size = 1024  # 滑动窗口大小
        self.hop = 256           # 每次滑动距离
        self.buffer = np.zeros(1024, dtype=np.float32)  # 环形缓冲
        self.energy_gate = EnergyGate(...)  # 能量门控
```

#### 核心处理循环

```python
def process_chunk(self, chunk: np.ndarray) -> PitchFrame:
    # 步骤 1: 能量门控（Layer 1 VAD）
    gate_open = self.energy_gate.process(chunk)  # RMS 检测

    # 步骤 2: 滑动窗口更新
    self.buffer[:-self.hop] = self.buffer[self.hop:]  # 左移 256 样本
    self.buffer[-self.hop:] = chunk                   # 追加新数据

    # 步骤 3: SwiftF0 推理（即使 gate 关闭也执行）
    pitch_hz, conf = self.detector.extract_pitch_and_confidence(self.buffer)

    # 步骤 4: 提取最新帧
    p = float(pitch_hz[-1])
    c = float(conf[-1])

    # 步骤 5: 多层 AND 逻辑
    voiced = (
        gate_open                                # Layer 1: 能量门
        and (c > self.detector.confidence_threshold)  # Layer 2: 模型置信度
        and (p >= self.detector.fmin)           # Layer 3: 频率下限
        and (p <= self.detector.fmax)           # Layer 3: 频率上限
    )

    # 步骤 6: 生成时间戳
    t = (self.frame_index * self.hop + self.center_offset) / self.sr
    self.frame_index += 1

    return PitchFrame(timestamp=t, pitch_hz=p, confidence=c, voiced=voiced)
```

#### EnergyGate 实现细节

```python
class EnergyGate:
    def __init__(
        self,
        open_threshold_db=-40.0,   # -40dB 开启阈值
        hysteresis_db=5.0,         # 5dB 迟滞
        hold_time_ms=150.0,        # 150ms 保持时间
        sample_rate=16000,
        hop_length=256,
    ):
        # 转换为线性振幅
        self.open_threshold = 10 ** (open_threshold_db / 20.0)   # 0.01
        self.close_threshold = 10 ** ((open_threshold_db - hysteresis_db) / 20.0)  # 0.00562

        # 保持帧数
        self.hold_frames = int((hold_time_ms / 1000.0) / (hop_length / sample_rate))
        # = int((0.15 / 1.0) / (256 / 16000)) = int(9.375) = 9 帧 = 144ms

        # RMS 平滑窗口
        self.rms_window_size = max(1, int(0.02 * sample_rate / hop_length))  # 20ms
        # = int(0.02 * 16000 / 256) = int(1.25) = 1 帧
        self.rms_history = []

        # 状态
        self.is_open = False
        self.hold_counter = 0
```

**EnergyGate 状态机：**

```python
def process(self, audio_chunk: np.ndarray) -> bool:
    # 1. 计算 RMS 能量
    rms = np.sqrt(np.mean(audio_chunk ** 2))

    # 2. 平滑处理（20ms 窗口）
    self.rms_history.append(rms)
    if len(self.rms_history) > self.rms_window_size:
        self.rms_history.pop(0)
    smoothed_rms = np.mean(self.rms_history)

    # 3. 迟滞状态机
    if not self.is_open:
        # 门关闭 → 超过 open_threshold 则开启
        if smoothed_rms > self.open_threshold:
            self.is_open = True
            self.hold_counter = self.hold_frames  # 重置保持计数
    else:
        # 门开启 → 低于 close_threshold 且保持时间结束则关闭
        if smoothed_rms < self.close_threshold:
            self.hold_counter -= 1
            if self.hold_counter <= 0:
                self.is_open = False
        else:
            self.hold_counter = self.hold_frames  # 重置保持计数

    return self.is_open
```

**关键发现：**
- `rms_window_size = 1` → **实际上没有平滑**！
- 计算：`int(0.02 * 16000 / 256) = int(1.25) = 1`
- 这意味着 EnergyGate 对单帧噪声非常敏感

---

### 3. RealtimeNoteSegmenter 状态机 (`swift_f0/streaming/notes.py`)

#### 状态机设计

```
IDLE (空闲)
  ↓ voiced frame
TENTATIVE_START (试探起始)
  ↓ 积累 min_note_frames (5帧=80ms)
  ↓ 稳定性检查 (CV < 10%)
ACTIVE (活跃音符)
  ↓ pitch 偏移 > split_threshold (2.0 半音)
  ↓ 或 unvoiced frame
TENTATIVE_END (试探结束)
  ↓ grace_period_frames (10帧=160ms)
IDLE
```

#### 关键参数（当前配置）

```python
def __init__(
    self,
    split_threshold: float = 2.0,      # FIX B: 0.7 → 2.0 (减少抖动)
    grace_period_frames: int = 10,     # PHASE 1: 2 → 10 (32ms → 160ms)
    min_note_frames: int = 5,          # PHASE 1: 3 → 5 (48ms → 80ms)
):
```

**延迟影响：**
- `min_note_frames = 5` → **80ms 确认延迟**（音符启动前等待）
- `grace_period_frames = 10` → **160ms 释放延迟**（停止哼唱到 note_off）
- 总延迟：**80 + 160 = 240ms**（最坏情况）

#### 音高稳定性检查

```python
def is_pitch_stable(self) -> bool:
    if len(self.pitch_history) < 3:
        return False

    # 计算变异系数 (CV = std / mean)
    pitch_array = np.array(self.pitch_history)
    mean_pitch = np.mean(pitch_array)
    std_pitch = np.std(pitch_array)

    if mean_pitch < 1e-6:
        return False

    cv = std_pitch / mean_pitch
    return cv < 0.10  # CV < 10% 才算稳定
```

**关键发现：**
- 这个检查在 `TENTATIVE_START → ACTIVE` 转换时执行
- 如果音高不稳定（CV ≥ 10%），会**继续等待**
- 最多等待 `min_note_frames * 2 = 10` 帧（160ms），然后超时重置
- **这是响应缓慢的核心原因之一**

#### 音高处理流程

```python
def process(self, frame: PitchFrame) -> Iterable[NoteEvent]:
    evts = []

    # 1. 处理 unvoiced 帧
    if not frame.voiced:
        if self.state in {"ACTIVE", "TENTATIVE_END"}:
            self.grace_counter += 1
            if self.grace_counter >= self.grace:  # 10 帧 = 160ms
                evts.append(NoteEvent(type="note_off", note=self.current_note, ...))
                self.reset()
        return evts

    # 2. 计算 MIDI 音高
    midi_pitch = self.hz_to_midi(frame.pitch_hz)

    # 3. 状态机处理
    if self.state == "IDLE":
        self.state = "TENTATIVE_START"
        self.note_start_time = frame.timestamp
        self.pitch_history = [midi_pitch]

    elif self.state == "TENTATIVE_START":
        self.pitch_history.append(midi_pitch)
        if len(self.pitch_history) >= self.min_frames:  # 5 帧
            if self.is_pitch_stable():  # CV < 10%
                pitch_midi = int(round(self.median_midi()))
                self.current_note = pitch_midi
                evts.append(NoteEvent(type="note_on", note=pitch_midi, ...))
                self.state = "ACTIVE"
            else:
                # 不稳定 → 继续等待或超时
                if len(self.pitch_history) > self.min_frames * 2:  # 10 帧
                    self.reset()  # 超时重置

    elif self.state == "ACTIVE":
        median_midi = self.median_midi()
        if abs(midi_pitch - median_midi) >= self.split_threshold:  # 2.0 半音
            # 音高变化 → 切换音符
            evts.append(NoteEvent(type="note_off", note=self.current_note, ...))
            new_pitch = int(round(midi_pitch))
            self.current_note = new_pitch
            self.pitch_history = [midi_pitch]
            self.note_start_time = frame.timestamp
            evts.append(NoteEvent(type="note_on", note=new_pitch, ...))
        else:
            # 音高稳定 → 更新历史
            self.pitch_history.append(midi_pitch)
            if len(self.pitch_history) > 32:
                self.pitch_history.pop(0)
        self.grace_counter = 0

    return evts
```

---

### 4. RealtimeAdditiveSynth 合成器 (`alternative_synthesis/realtime_synth.py`)

#### 架构设计

```python
class RealtimeAdditiveSynth:
    def __init__(
        self,
        sample_rate: int = 44100,
        block_size: int = 256,
        num_harmonics: int = 5,
    ):
        self.voices: Dict[int, ActiveVoice] = {}  # 活跃音符表
        self.attack_time = 0.005   # 5ms 起音
        self.release_time = 0.05   # 50ms 释放
        self.sustain_level = 0.8   # 80% 持续电平
```

#### 谐波合成算法

```python
def _generate_samples(self, num_frames: int) -> np.ndarray:
    output = np.zeros(num_frames, dtype=np.float32)
    dt = 1.0 / self.sample_rate

    for note, voice in self.voices.items():
        signal = np.zeros(num_frames, dtype=np.float32)

        # 生成 5 个谐波
        for h_idx in range(self.num_harmonics):
            h_freq = voice.frequency * (h_idx + 1)  # 基频的倍数
            h_amp = self.harmonic_amplitudes[h_idx]  # 谐波权重

            # 生成正弦波
            t = np.arange(num_frames) * dt
            phases = 2.0 * np.pi * h_freq * t + voice.phase
            harmonic = np.sin(phases) * h_amp

            signal += harmonic

        # 应用包络
        envelope = self._compute_envelope(voice, num_frames, dt)
        signal *= envelope * voice.velocity * self.master_volume

        output += signal

        # 更新相位（防止相位跳跃）
        voice.phase += 2.0 * np.pi * voice.frequency * num_frames * dt
        voice.phase = voice.phase % (2.0 * np.pi)

    # 软削波
    output = np.tanh(output * 1.2)
    return output
```

**关键发现：**
- 合成器本身**性能优秀**，延迟 <5ms
- 谐波合成算法正确，音质良好
- **不是音质问题的根源**

---

## 潜在问题点分析

### 🔴 问题 1: EnergyGate RMS 平滑失效

**位置：** `swift_f0/streaming/inference.py:82`

```python
self.rms_window_size = max(1, int(0.02 * sample_rate / hop_length))
# = max(1, int(0.02 * 16000 / 256))
# = max(1, int(1.25))
# = max(1, 1)
# = 1
```

**问题：**
- 窗口大小 = 1，意味着**没有平滑**
- 单帧噪声会直接触发 gate 开启
- 导致频繁的 gate 开/关切换

**影响：**
- 噪声环境下误触发
- 可能产生"电流声"（频繁的 note_on/note_off）

**解决方案：**
```python
# 强制至少 3 帧（48ms）平滑
self.rms_window_size = max(3, int(0.02 * sample_rate / hop_length))
```

---

### 🔴 问题 2: 音高稳定性检查过于严格

**位置：** `swift_f0/streaming/notes.py:61-100`

```python
def is_pitch_stable(self) -> bool:
    if len(self.pitch_history) < 3:
        return False  # 需要至少 3 个样本

    cv = std_pitch / mean_pitch
    return cv < 0.10  # CV < 10%
```

**问题：**
- 人声哼唱很难做到 CV < 10%（尤其是起音阶段）
- 即使是稳定的乐器音，起音时也会有较大波动
- 导致音符启动延迟（等待稳定 → 超时 → 重置 → 再等待）

**实测数据（假设）：**
- 正常哼唱的 CV ≈ 8-15%
- 乐器演奏的 CV ≈ 5-12%
- 噪声的 CV ≈ 30-100%

**影响：**
- 响应缓慢，无法识别快速旋律
- 部分有效音符被拒绝

**解决方案：**
```python
# 放宽到 15%，或者使用其他稳定性指标
return cv < 0.15

# 或者：结合置信度
stability_threshold = 0.10 + (1.0 - frame.confidence) * 0.10  # 动态阈值
return cv < stability_threshold
```

---

### 🔴 问题 3: min_note_frames 和 grace_period 过长

**位置：** `swift_f0/streaming/notes.py:32-36`

```python
def __init__(
    self,
    split_threshold: float = 2.0,
    grace_period_frames: int = 10,  # 160ms
    min_note_frames: int = 5,       # 80ms
):
```

**问题：**
- 80ms 确认 + 160ms 释放 = **240ms 延迟**
- 快速旋律（如八分音符 @ 120BPM = 250ms/音符）**无法识别**
- 用户反馈："他非常非常的不能够及时的识别我的声音的不同的音调的变化"

**计算示例：**
- 歌曲："小星星"，速度 120 BPM
- 八分音符时长 = 60/120/2 = 0.25s = 250ms
- 系统延迟 = 240ms
- 实际响应时间 = 音符结束后才识别 → **完全无法跟上**

**影响：**
- 快速旋律识别失败
- 只能识别长音（>300ms）
- 项目核心目标无法达成

**解决方案：**
```python
# FAST_DEMO.py 的配置
min_note_frames: int = 2,   # 32ms（激进）
grace_period_frames: int = 5,  # 80ms（平衡）

# 或者：自适应调整
# 连续音符 → 降低 grace_period
# 长音 → 提高 grace_period
```

---

### 🔴 问题 4: 置信度阈值过高

**位置：** `swift_f0/core.py:52`

```python
DEFAULT_CONFIDENCE_THRESHOLD = 0.9
```

**问题：**
- 0.9 阈值意味着只接受模型"非常确定"的结果
- 人声哼唱的实际置信度 ≈ 0.7-0.85
- 导致大量有效音高被标记为 unvoiced

**影响：**
- 漏检率高
- 用户需要"用力"哼唱才能被识别
- 音符断断续续

**解决方案：**
```python
# DEMO 中已经降低到 0.75-0.85
CONFIDENCE_THRESHOLD = 0.80  # 平衡点
```

---

### 🟡 问题 5: 状态机在 ACTIVE 时仍使用 median

**位置：** `swift_f0/streaming/notes.py:143-157`

```python
if self.state == "ACTIVE":
    median_midi = self.median_midi()  # 动态计算中位数
    if abs(midi_pitch - median_midi) >= self.split_threshold:
        # 判断是否切换音符
```

**问题：**
- `pitch_history` 持续更新（最多 32 个值）
- `median_midi()` 会随着新音高的加入而漂移
- 可能导致误判（即使音高稳定，median 也在变化）

**影响：**
- 音符抖动（连续的 note_off/note_on）
- 音高跟踪不准确

**解决方案：**
```python
# 改为：与当前音符号比较，而不是与 median 比较
if abs(midi_pitch - self.current_note) >= self.split_threshold:
    # 切换音符
```

**注：** 这个问题可能不严重，因为 `split_threshold = 2.0` 半音，有一定容错空间。

---

### 🟡 问题 6: 每次都运行推理（即使 gate 关闭）

**位置：** `swift_f0/streaming/inference.py:250-253`

```python
# PHASE 1: 总是运行推理（维持时间一致性）
# 评估后：gate 关闭时不跳过推理（Phase 1 设计）
# Phase 2 可能在持续静音后添加自适应跳过
pitch_hz, conf = self.detector.extract_pitch_and_confidence(self.buffer)
```

**问题：**
- 即使 EnergyGate 关闭（静音），仍然执行 ONNX 推理
- 浪费 CPU 资源（~10-20ms）
- 可能导致噪声被识别为音高

**影响：**
- CPU 占用高
- 可能产生噪声音高（虽然会被 voiced=False 过滤）

**解决方案：**
```python
# Phase 2 优化：gate 关闭超过 N 帧后跳过推理
if self.enable_energy_gate and not gate_open:
    if self.silence_counter > 10:  # 160ms 持续静音
        # 跳过推理，返回 unvoiced frame
        return PitchFrame(timestamp=t, pitch_hz=0.0, confidence=0.0, voiced=False)
    self.silence_counter += 1
else:
    self.silence_counter = 0
```

---

## 性能瓶颈识别

### 延迟分解（当前实现）

| 组件 | 延迟 | 类型 | 可优化 |
|------|------|------|--------|
| 输入缓冲 | 16ms | 固定 | ❌ |
| EnergyGate | <1ms | 计算 | ✅ |
| SwiftF0 推理 | 10-20ms | 计算 | ❌ |
| min_note_frames | **80ms** | 算法 | ✅ |
| 稳定性检查 | 0-80ms | 算法 | ✅ |
| grace_period | **160ms** | 算法 | ✅ |
| 合成器 | <5ms | 计算 | ❌ |
| 输出缓冲 | 6ms | 固定 | ❌ |
| **总计（最坏）** | **357ms** | | |
| **总计（最好）** | **112ms** | | |

### 优化目标

| 优化方案 | 延迟 | 权衡 |
|----------|------|------|
| **当前** | 112-357ms | 稳定但慢 |
| **FAST_DEMO** | 48-96ms | 快但可能抖动 |
| **极致优化** | 32-64ms | 接近理论极限，抖动明显 |
| **理论极限** | 32ms | 2 帧确认（不稳定） |

---

## 关键结论

### 🎯 用户问题的根本原因

1. **响应缓慢** → `min_note_frames=5` (80ms) + `grace_period=10` (160ms)
2. **电流声/噪声** → `rms_window_size=1`（无平滑） + `confidence_threshold=0.9`（过高）
3. **音符识别不稳定** → `is_pitch_stable()` CV < 10%（过严格）

### ✅ 已经正确的部分

1. **SwiftF0 模型本身** → 音高检测准确
2. **RealtimeAdditiveSynth** → 合成质量优秀
3. **MIDI 配对（Fix A）** → note_on/note_off 正确匹配

### 🚀 推荐优化顺序

1. **立即修复：** 降低 `min_note_frames` 和 `grace_period`（已在 FAST_DEMO 中完成）
2. **次要修复：** 修复 EnergyGate 的 RMS 平滑窗口
3. **长期优化：** 重新设计稳定性检查（自适应阈值）
4. **性能优化：** gate 关闭时跳过推理

---

## 下一步行动

1. **测试 FAST_DEMO.py** → 验证是否解决响应缓慢问题
2. **如果仍有噪声** → 修复 EnergyGate RMS 平滑
3. **如果仍有漏检** → 调整置信度阈值或稳定性检查
4. **如果响应满意** → 微调参数平衡稳定性和响应速度

---

**生成时间:** 2025-10-16
**分析者:** Claude (Sonnet 4.5)
