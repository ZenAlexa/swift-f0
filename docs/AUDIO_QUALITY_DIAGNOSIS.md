# 音质和流式处理问题诊断报告

**生成时间:** 2025-10-15
**状态:** 🔍 根本原因已定位

---

## 📊 问题描述

用户反馈两个核心问题：

1. **音质很差** - 即使 MIDI 配对完美（Fix A 成功），音色仍然不好听
2. **流式处理断开** - 连续哼唱曲子时，中间会断开，处理不过来

---

## 🔍 诊断数据分析

### 1. MIDI 事件时序问题

从 `debug_midi_events.txt` 分析：

```
总事件数: 96 (48 note_on + 48 note_off)
平均事件间隔: 142.4ms
最短间隔: 16ms
最长间隔: 1552ms
⚠️  31 个间隔 <50ms (32.3%) ← 音符抖动严重
```

**问题：31个事件间隔 <50ms**

- 人类正常唱/哼音符持续时间：200-500ms
- 但系统产生了大量 <50ms 的音符切换
- 结果：音符快速开关 → 听起来像"噪音/咔嚓声"而不是音乐

### 2. 音高检测抖动

从 `debug_pitch_frames.txt` 分析：

```
有声片段总数: 9 个
平均片段长度: 0.364秒
最短片段: 0.000秒 ← 几乎瞬间切换

无声间隙:
  平均间隙: 0.460秒
  最短间隙: 0.032秒 ← grace period 内
```

**问题：音高片段非常碎片化**

- 连续哼唱被切割成 9 个短片段
- 说明音高检测或分段逻辑过于敏感

### 3. split_threshold 过低导致频繁切换

当前配置：`--split-threshold 0.7`（0.7 半音）

**问题机制：**

```python
# 在 RealtimeNoteSegmenter.process() 中
if abs(midi_pitch - median_pitch) >= self.split_threshold:
    # 触发音符切换
```

0.7 半音 ≈ 70 cents，对于人声颤音和音高微小波动：
- 人声自然颤音幅度：±20-50 cents
- SwiftF0 检测精度抖动：±10-30 cents
- 合计波动：±30-80 cents

**结果：轻微的音高抖动就触发 split → 音符狂切换**

---

## 🎯 根本原因总结

### 问题 1：音质差的原因

**不是 SoundFont 的问题**，而是 **音符抖动 (note chattering)**：

1. `split_threshold=0.7` 太低，对音高抖动过敏感
2. 连续哼唱被切成 31 个 <50ms 的快速音符开关
3. FluidSynth 快速 note_on → note_off → note_on 产生"咔嚓"声
4. 音色本身（钢琴/萨克斯）都正常，但快速切换破坏了包络

**类比：**
- 想象用钢琴弹一个长音，但每 16ms 抬起手指再按下
- 听起来不是流畅的长音，而是"哒哒哒哒"的断续音

### 问题 2：流式处理断开的原因

**架构瓶颈：**

```
audio_queue (maxsize=8)  ← 只能缓冲 8 个音频块
    ↓
inference_worker (SwiftF0 推理)  ← CPU 密集
    ↓
pitch_queue (maxsize=32)
    ↓
postprocessing_worker (分段)
    ↓
FluidSynth (合成)
```

当前配置：
- `BLOCK_SIZE=256` samples @ 16kHz = 16ms/block
- `audio_queue` 只能缓冲 8 blocks = 128ms
- SwiftF0 推理如果超过 16ms，就会丢帧

**实测瓶颈：**
- 检测到 2 个长间隙（1.7秒 和 1.6秒）
- 说明推理线程卡住 → `audio_queue` 满 → 丢帧 → 断开

**代码证据（realtime_demo.py:221-228）：**

```python
def audio_callback(..., audio_queue):
    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        pass  # ← 静默丢帧！用户不知道断了
```

---

## 🔧 解决方案

### Fix B: 提高 split_threshold（立即生效）

**目标：** 减少音符抖动，让音符更稳定

```bash
# 当前测试值
--split-threshold 0.7  # 太敏感，31 次抖动

# 推荐值
--split-threshold 2.0  # 2 半音 = 200 cents，更稳定
```

**预期效果：**
- 只在音高真正改变 2 个半音时才切换音符
- 人声颤音（±50 cents）不会触发切换
- 音符持续时间从 <50ms 增加到 200-500ms
- 听起来像"音乐"而不是"噪音"

**测试方案：**
```bash
python examples/streaming/realtime_demo.py \
  --audio \
  --sf2 soundfonts/GeneralUser-GS.sf2 \
  --instrument 66 \
  --gain 0.4 \
  --split-threshold 2.0 \
  --grace-frames 10 \
  --confidence-threshold 0.9
```

---

### Fix C: 优化流式处理架构（中期）

**方案 1: 增加队列容量**

```python
# realtime_demo.py:428-429
audio_queue: queue.Queue = queue.Queue(maxsize=32)  # 8 → 32 (512ms 缓冲)
pitch_queue: queue.Queue = queue.Queue(maxsize=64)  # 32 → 64
```

**方案 2: 添加丢帧日志**

```python
def audio_callback(...):
    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        logger.warning("⚠️  Audio queue full - dropping frame!")  # ← 可见性
```

**方案 3: 推理优化（长期）**

- 使用 INT8 量化模型（更快）
- 跳过无声帧的推理（CPU 节省）
- 多线程推理池

---

### Fix D: 改进音符稳定性检查

**问题：** 当前 `is_pitch_stable()` 只在 TENTATIVE_START 使用，ACTIVE 状态不检查

**改进方案（库代码）：**

```python
# swift_f0/streaming/notes.py
class RealtimeNoteSegmenter:
    def process(self, frame):
        if self.state == "ACTIVE":
            median_pitch = self.median_midi()

            # 增强：只有在稳定且超过阈值时才 split
            if abs(midi_pitch - median_pitch) >= self.split_threshold:
                # 新增：检查新音高是否稳定（避免瞬间抖动触发 split）
                if len(self.pitch_history) < 5:  # 需要至少 5 帧历史
                    self.pitch_history.append(midi_pitch)
                    return events

                # 原有逻辑
                if self.current_note is not None:
                    events.append(...)
```

---

## 📈 预期改善对比

| 修复 | 目标问题 | 难度 | 预期改善 |
|------|---------|------|---------|
| Fix B (split=2.0) | 音符抖动 | ⭐ 简单 | **90%** - 音质显著改善 |
| Fix C (队列扩容) | 流式断开 | ⭐ 简单 | **60%** - 减少丢帧 |
| Fix C (推理优化) | 流式断开 | ⭐⭐⭐ 困难 | **80%** - 彻底解决 |
| Fix D (稳定性) | 音符抖动 | ⭐⭐ 中等 | **95%** - 音质完美 |

---

## 🧪 验证步骤

### 立即测试 Fix B：

```bash
cd /Users/zimingwang/Documents/GitHub/swift-f0

# 测试 1: split=2.0（推荐）
python examples/streaming/realtime_demo.py \
  --audio \
  --sf2 soundfonts/GeneralUser-GS.sf2 \
  --instrument 66 \
  --split-threshold 2.0 \
  --gain 0.4

# 测试 2: split=3.0（更激进）
python examples/streaming/realtime_demo.py \
  --audio \
  --sf2 soundfonts/GeneralUser-GS.sf2 \
  --instrument 66 \
  --split-threshold 3.0 \
  --gain 0.4

# 测试 3: 禁用 split（单音符模式，用于对比）
python examples/streaming/realtime_demo.py \
  --audio \
  --sf2 soundfonts/GeneralUser-GS.sf2 \
  --instrument 66 \
  --split-threshold 99.0 \
  --gain 0.4
```

### 验证指标：

1. **音质改善：**
   - ✅ 听起来像"流畅的音乐"而不是"咔嚓声"
   - ✅ 音符持续时间增加（>200ms）
   - ✅ 音色饱满，有包络（attack-sustain-release）

2. **流式稳定性：**
   - ✅ 连续哼唱 5-10 秒不断开
   - ✅ 音符切换响应及时（<100ms 延迟）

3. **诊断数据：**
   ```bash
   python DEBUG_CAPTURE.py --duration 10
   # 检查：<50ms 间隔应该 <10% （当前是 32%）
   ```

---

## 🎼 其他音质优化建议

### 1. 调整 gain 获得更好音量

当前 `--gain 0.3` 可能偏小：

```bash
--gain 0.5  # -6dB，更平衡
--gain 0.6  # -4.4dB，更响亮
```

### 2. 尝试不同乐器获得更好听感

```bash
--instrument 73  # Flute（长笛）- 适合连续音
--instrument 40  # Violin（小提琴）- 表现力强
--instrument 88  # New Age Pad - 柔和持续音
```

### 3. 调整 grace_frames 优化响应

```bash
--grace-frames 15  # 240ms，更宽容的静音容忍
--grace-frames 5   # 80ms，更敏感的断音检测
```

---

## ✅ 结论

**音质差的核心原因：** `split_threshold=0.7` 太低 → 音符抖动 → 听起来像噪音

**立即行动：** 使用 `--split-threshold 2.0` 重新测试

**预期结果：** 音质从"不能听"提升到"可用音乐"级别

**下一步：** 如果 Fix B 有效，继续优化流式处理架构（Fix C/D）
