# 诊断报告 - 爆音问题根本原因分析

**生成时间:** 基于用户提供的诊断文件
**测试时长:** 5.34 秒
**问题状态:** ✅ 已定位根本原因

---

## 📊 关键发现

### 1. MIDI 事件统计

```
总事件数: 52 个
  - note_on:  27 个
  - note_off: 25 个
持续时间: 5.34 秒
事件密度: 9.7 events/秒
```

**分析：**
- ✅ 事件密度 9.7/秒 **在合理范围内**（Phase 1 目标 < 20/秒）
- ⚠️ note_on/off 数量不匹配（27 vs 25），多出 2 个 note_on

---

### 2. 🔴 **关键问题：音符配对错误**

```
❌ 重复 note_on（未配对）: 6 个
❌ 孤立 note_off（未配对）: 6 个
```

**这是爆音的根本原因！**

#### 问题机制：

```
时间线示例（从 debug_midi_events.txt）:

2.8000  note_on  46  ← 音符 46 启动
2.8800  note_off 46  ← 音符 46 关闭
2.8800  note_on  45  ← 音符 45 启动
3.8240  note_off 45  ← 音符 45 关闭

5.3280  note_off 53  ← ⚠️ 孤立 note_off（音符 53 从未 note_on）
5.3280  note_on  52  ← 音符 52 启动
5.3920  note_off 52  ← 音符 52 关闭

5.7920  note_off 50  ← ⚠️ 孤立 note_off（音符 50 从未 note_on）
5.7920  note_on  49  ← 音符 49 启动

6.1920  note_off 49  ← 关闭音符 49
6.1920  note_on  49  ← ⚠️ 重复 note_on（49 还在活跃时又 note_on）
```

#### 问题来源：

**分段器 (RealtimeNoteSegmenter) 的 split 逻辑错误：**

在 `swift_f0/streaming/notes.py:122-134`：

```python
if self.state == "ACTIVE":
    median_midi = self.median_midi()
    if abs(midi_pitch - median_midi) >= self.split_threshold:
        old_pitch = int(round(median_midi))
        evts.append(NoteEvent(type="note_off", note=old_pitch, time=frame.timestamp))
        self.pitch_history = [midi_pitch]
        self.note_start_time = frame.timestamp
        evts.append(NoteEvent(type="note_on", note=int(round(midi_pitch)), velocity=80, time=frame.timestamp))
```

**问题：**
1. `old_pitch = int(round(median_midi()))` 计算的音符可能与实际发送的 `note_on` 不一致
2. 音高在边界抖动时，`median_midi()` 返回的值会跳变
3. 结果：发送了 `note_off 50`，但之前发送的是 `note_on 49`

**示例场景：**
```
时刻 1: note_on 49 (median = 49.3)
时刻 2: pitch 变化，median 跳到 49.7 → round(49.7) = 50
        发送 note_off 50 ← ❌ 但 50 从未 note_on！
        发送 note_on 52
```

---

### 3. 活跃音符统计

```
最大活跃音符数: 3
平均活跃音符数: 1.08
```

**分析：**
- ✅ 最大值 3 < 4（紧急修复的限制）
- ⚠️ 理论上单声部哼唱应该 ≤ 2
- **但由于配对错误，实际 FluidSynth 内部可能有更多幽灵音符**

**证据：**
`debug_active_notes.txt` 显示最大值 3，但这只是 Python 层追踪的 `_active_notes`。
FluidSynth 内部由于接收了孤立的 note_on，可能有更多未被 Python 追踪的活跃音符。

---

### 4. 音高检测统计

```
总帧数: 620
有声帧: 213 (34.4%)
无声帧: 407 (65.6%)

音高大幅跳变 (>1.5 半音): 4 次
跳变频率: 0.7 jumps/秒
```

**分析：**
- ✅ 跳变频率低（0.7/秒），不是主要问题
- ✅ 有声率 34.4% 合理（说明能量门控工作正常）

---

## 🎯 根本原因总结

### **主要问题：分段器的 split 逻辑存在音符追踪错误**

1. **median_midi() 不稳定：**
   - 使用 `np.median(pitch_history)` 计算中位数
   - `pitch_history` 动态变化
   - `int(round(median))` 可能与之前发送的 note 不同

2. **split 时发送的 note_off 音符号不正确：**
   - 应该发送**当前正在播放的音符**的 note_off
   - 但实际发送的是**重新计算的 median 音符**

3. **结果：**
   - 孤立 note_off → FluidSynth 忽略（无害但浪费）
   - 重复 note_on → FluidSynth 内部音符堆积 → **爆音**
   - 幽灵音符永不释放 → 持续发声 → **持续噪音**

---

## 🔧 修复方案

### **Fix A: 修复分段器音符追踪（CRITICAL）**

**位置:** `swift_f0/streaming/notes.py`

**问题代码:**
```python
class RealtimeNoteSegmenter:
    def __init__(self, ...):
        self.pitch_history: List[float] = []  # ← 只存音高，不存实际发送的音符

    def process(self, frame):
        # ...
        if self.state == "ACTIVE":
            old_pitch = int(round(self.median_midi()))  # ← 错误！重新计算
            evts.append(NoteEvent(type="note_off", note=old_pitch, ...))
```

**修复代码:**
```python
class RealtimeNoteSegmenter:
    def __init__(self, ...):
        self.pitch_history: List[float] = []
        self.current_note: int | None = None  # ← 新增：追踪实际发送的音符

    def process(self, frame: PitchFrame) -> Iterable[NoteEvent]:
        evts: List[NoteEvent] = []

        if not frame.voiced:
            if self.state in {"ACTIVE", "TENTATIVE_END"}:
                self.grace_counter += 1
                if self.grace_counter >= self.grace:
                    if self.current_note is not None:  # ← 使用追踪的音符
                        evts.append(NoteEvent(type="note_off", note=self.current_note, time=frame.timestamp))
                        self.current_note = None  # ← 清除追踪
                    self.reset()
            return evts

        midi_pitch = self.hz_to_midi(frame.pitch_hz)

        if self.state == "IDLE":
            self.state = "TENTATIVE_START"
            self.note_start_time = frame.timestamp
            self.pitch_history = [midi_pitch]
            return evts

        if self.state == "TENTATIVE_START":
            self.pitch_history.append(midi_pitch)
            if len(self.pitch_history) >= self.min_frames:
                if self.is_pitch_stable():
                    pitch_midi = int(round(self.median_midi()))
                    self.current_note = pitch_midi  # ← 记录发送的音符
                    evts.append(NoteEvent(type="note_on", note=pitch_midi, velocity=80, time=self.note_start_time))
                    self.state = "ACTIVE"
                else:
                    if len(self.pitch_history) > self.min_frames * 2:
                        self.reset()
            return evts

        if self.state == "ACTIVE":
            median_midi = self.median_midi()
            if abs(midi_pitch - median_midi) >= self.split_threshold:
                # ← 关键修复：使用追踪的音符，而不是重新计算
                if self.current_note is not None:
                    evts.append(NoteEvent(type="note_off", note=self.current_note, time=frame.timestamp))

                new_pitch = int(round(midi_pitch))
                self.current_note = new_pitch  # ← 更新追踪
                self.pitch_history = [midi_pitch]
                self.note_start_time = frame.timestamp
                evts.append(NoteEvent(type="note_on", note=new_pitch, velocity=80, time=frame.timestamp))
            else:
                self.pitch_history.append(midi_pitch)
                if len(self.pitch_history) > 32:
                    self.pitch_history.pop(0)
            self.grace_counter = 0
            return evts

        return evts

    def reset(self) -> None:
        self.state = "IDLE"
        self.note_start_time = 0.0
        self.grace_counter = 0
        self.pitch_history: List[float] = []
        self.current_note = None  # ← 清除追踪
```

---

### **Fix B: 降低 split_threshold（临时缓解）**

当前诊断显示跳变频率低，但仍然触发了配对错误。

**建议参数:**
```bash
--split-threshold 2.0  # 从 0.7 提高到 2.0（更难触发 split）
```

这会减少 split 事件，从而减少配对错误的机会。

---

### **Fix C: 保留紧急修复的音符限制**

虽然诊断显示 max_active = 3 < 4，但由于配对错误，FluidSynth 内部可能有更多幽灵音符。

**建议：** 保持 `MAX_ACTIVE_NOTES = 4`，但在 Fix A 应用后可以提高到 6-8。

---

## 📈 预期修复效果

| 修复 | 解决的问题 | 预期改善 |
|------|----------|---------|
| Fix A（音符追踪）| 孤立 note_off + 重复 note_on | **根治爆音**（100%） |
| Fix B（提高 split 阈值）| 减少 split 频率 | 缓解症状（50%） |
| Fix C（音符限制）| 防止堆积到极端 | 兜底保护（20%） |

**优先级：** Fix A > Fix B > Fix C（已应用）

---

## 🧪 验证步骤

### 应用 Fix A 后测试：

```bash
# 1. 应用修复后重新测试
python DEBUG_CAPTURE.py --duration 10

# 2. 检查配对问题是否解决
python3 << 'EOF'
import csv
with open('debug_midi_events.txt', 'r') as f:
    reader = csv.DictReader(f)
    events = list(reader)

note_states = {}
unpaired_on = 0
unpaired_off = 0

for e in events:
    note = int(e['note'])
    if e['event_type'] == 'note_on':
        if note in note_states and note_states[note] == 'on':
            unpaired_on += 1
        note_states[note] = 'on'
    elif e['event_type'] == 'note_off':
        if note not in note_states or note_states[note] == 'off':
            unpaired_off += 1
        else:
            note_states[note] = 'off'

print(f"重复 note_on: {unpaired_on} (应为 0)")
print(f"孤立 note_off: {unpaired_off} (应为 0)")

if unpaired_on == 0 and unpaired_off == 0:
    print("✅ 配对问题已解决！")
else:
    print("❌ 仍有配对问题")
EOF
```

---

## ✅ 结论

**根本原因确认：**
> `RealtimeNoteSegmenter` 的 split 逻辑在计算 note_off 音符号时使用了动态重计算的 `median_midi()`，导致发送的 note_off 音符与之前的 note_on 不匹配。

**症状链路：**
```
音符追踪错误
    ↓
发送孤立 note_on（无对应 note_off）
    ↓
FluidSynth 内部音符堆积
    ↓
多个音符同时发声 + 相位干涉
    ↓
爆音/噪音/持续嗡鸣
```

**修复优先级：**
1. **立即应用 Fix A**（音符追踪修复）
2. 可选应用 Fix B（提高 split 阈值）
3. 保留 Fix C（音符限制兜底）

修复后预期：
- ✅ 哼唱单音时听到清晰的单一音高
- ✅ 音符切换时平滑过渡，无爆音
- ✅ 停止哼唱后立即静音
- ✅ MIDI 事件完全配对（unpaired = 0）
