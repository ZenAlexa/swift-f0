# SwiftF0 音色转换快速入门指南

## 🎯 10分钟上手

### 步骤1: 准备测试音频（30秒）

如果你还没有音频文件，可以用手机录制一段哼唱：
- 打开手机录音app
- 哼唱一段简单旋律（比如"小星星"）
- 保存为 `test_singing.wav` 或 `test_singing.m4a`
- 传到电脑上

或者使用测试生成脚本：
```bash
python3 test_timbre_demo.py
```

### 步骤2: 基础转换（2分钟）

```bash
# 1. 默认钢琴音色
python demo_timbre_transform.py test_singing.wav

# 输出: test_singing_output.mid
```

用任何MIDI播放器播放生成的文件：
- **macOS**: 直接双击打开（QuickTime或GarageBand）
- **Windows**: Windows Media Player
- **在线播放**: 访问 https://signal.vercel.app/edit 上传MIDI

### 步骤3: 尝试不同音色（3分钟）

```bash
# 小号音色（明亮）
python demo_timbre_transform.py test_singing.wav -i trumpet -o trumpet.mid

# 长笛音色（柔和）
python demo_timbre_transform.py test_singing.wav -i flute -o flute.mid

# 双簧管音色（鼻音，接近卡祖笛）
python demo_timbre_transform.py test_singing.wav -i oboe -o oboe.mid

# 萨克斯音色（爵士感）
python demo_timbre_transform.py test_singing.wav -i alto_sax -o sax.mid
```

听听哪个音色最符合你的需求！

### 步骤4: 移调测试（2分钟）

```bash
# 原始音高太低？升高5个半音
python demo_timbre_transform.py test_singing.wav -t 5 -o higher.mid

# 太高？降低3个半音
python demo_timbre_transform.py test_singing.wav -t -3 -o lower.mid

# 升高一个八度（12个半音）
python demo_timbre_transform.py test_singing.wav -t 12 -o octave_up.mid
```

### 步骤5: 自动调音（3分钟）

```bash
# 自动修正跑调的音符
python demo_timbre_transform.py test_singing.wav --auto-tune -o perfect.mid

# 轻微修正（保留一些原始味道）
python demo_timbre_transform.py test_singing.wav --auto-tune --strength 0.5 -o slight_fix.mid

# 完全修正 + 改音色 + 移调组合拳
python demo_timbre_transform.py test_singing.wav \
    --auto-tune --strength 1.0 \
    -i trumpet \
    -t 3 \
    -o perfect_trumpet_higher.mid
```

## 🎺 卡祖笛专用快速流程

### 一键卡祖笛优化

```bash
# 自动优化到卡祖笛音域 + 选择合适音色
python demo_timbre_transform.py test_singing.wav --kazoo -o kazoo.mid

# 卡祖笛 + 自动调音（双重优化）
python demo_timbre_transform.py test_singing.wav --kazoo --auto-tune -o kazoo_perfect.mid
```

### 批量生成多种卡祖笛音色

```bash
python demo_timbre_transform.py test_singing.wav --batch

# 输出目录: test_singing_output_batch/
# 包含9个MIDI文件，分别使用不同音色：
# - oboe（双簧管）
# - trumpet（小号）
# - harmonica（口琴）
# - clarinet（单簧管）
# - accordion（手风琴）
# - bassoon（巴松）
# - english_horn（英国管）
# - muted_trumpet（弱音小号）
# - shanai（唢呐）
```

然后听听哪个音色最像你想要的卡祖笛效果！

## 📝 Python脚本示例

如果你想在代码中使用，这里有完整示例：

### 示例1: 基础音色转换

```python
from swift_f0 import SwiftF0, segment_notes
from swift_f0.music_enhanced import export_to_midi_enhanced

# 1. 加载音频并检测音高
detector = SwiftF0()
result = detector.detect_from_file("my_singing.wav")

# 2. 分割成音符
notes = segment_notes(result)

# 3. 导出不同音色
export_to_midi_enhanced(notes, "piano.mid", instrument="acoustic_grand_piano")
export_to_midi_enhanced(notes, "trumpet.mid", instrument="trumpet")
export_to_midi_enhanced(notes, "flute.mid", instrument="flute")

print(f"✓ 检测到 {len(notes)} 个音符")
```

### 示例2: 自动调音

```python
from swift_f0 import SwiftF0, segment_notes
from swift_f0.music_enhanced import export_to_midi_enhanced, detect_key

# 检测音高
detector = SwiftF0()
result = detector.detect_from_file("singing.wav")
notes = segment_notes(result)

# 检测调性
key, mode = detect_key(notes)
print(f"检测到的调性: {key} {mode}")

# 导出原始版本和自动调音版本对比
export_to_midi_enhanced(notes, "original.mid")
export_to_midi_enhanced(notes, "autotuned.mid",
                       auto_tune=True,
                       auto_tune_strength=1.0)

print("✓ 已生成对比文件，用MIDI播放器对比效果")
```

### 示例3: 卡祖笛优化

```python
from swift_f0 import SwiftF0, segment_notes
from swift_f0.music_enhanced import optimize_for_kazoo, export_to_midi_enhanced

# 检测音高
detector = SwiftF0()
result = detector.detect_from_file("voice.wav")
notes = segment_notes(result)

# 优化到卡祖笛范围
kazoo_notes = optimize_for_kazoo(notes)

# 导出为卡祖笛版本
export_to_midi_enhanced(
    kazoo_notes,
    "kazoo_output.mid",
    instrument="oboe",           # 使用双簧管模拟卡祖笛
    pitch_range=(52, 76),        # E3-E5
    auto_tune=True,              # 可选：自动修正音准
)

print(f"✓ 原始音符: {len(notes)} 个")
print(f"✓ 卡祖笛优化后: {len(kazoo_notes)} 个")
```

### 示例4: 批量处理多个文件

```python
import os
from swift_f0 import SwiftF0, segment_notes
from swift_f0.music_enhanced import export_to_midi_enhanced

# 批量处理文件夹中的所有音频
detector = SwiftF0()
audio_folder = "my_recordings"
output_folder = "midi_output"

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(audio_folder):
    if filename.endswith(('.wav', '.mp3', '.m4a', '.flac')):
        input_path = os.path.join(audio_folder, filename)
        output_name = os.path.splitext(filename)[0] + '.mid'
        output_path = os.path.join(output_folder, output_name)

        try:
            # 处理
            result = detector.detect_from_file(input_path)
            notes = segment_notes(result)

            # 导出
            export_to_midi_enhanced(
                notes,
                output_path,
                instrument="trumpet",
                transpose=0,
                auto_tune=True
            )

            print(f"✓ {filename} → {output_name} ({len(notes)} 音符)")
        except Exception as e:
            print(f"✗ {filename} 处理失败: {e}")

print(f"\n✓ 完成！所有MIDI文件保存在: {output_folder}/")
```

## 🎮 高级参数调优

### 调节音符分割敏感度

如果音符切分太碎或太粗：

```bash
# 更敏感（音符更多更短）
python demo_timbre_transform.py song.wav --threshold 0.5

# 更宽容（音符更少更长）
python demo_timbre_transform.py song.wav --threshold 1.2
```

### 过滤短音符

去除杂音和短颤音：

```bash
# 只保留长于0.1秒的音符
python demo_timbre_transform.py song.wav --min-duration 0.1

# 只保留长于0.2秒的音符（更激进）
python demo_timbre_transform.py song.wav --min-duration 0.2
```

### 改变播放速度

```bash
# 快速播放（140 BPM）
python demo_timbre_transform.py song.wav --tempo 140

# 慢速播放（80 BPM）
python demo_timbre_transform.py song.wav --tempo 80
```

## 🎵 推荐音色组合

根据不同场景推荐：

### 卡祖笛硬件项目
```bash
推荐音色: oboe, trumpet, harmonica
移调: 0 到 +3（根据实际硬件）
自动调音: 开启（strength 0.8-1.0）
音域限制: E3-E5 (52-76)
```

### 音乐教学
```bash
推荐音色: acoustic_grand_piano, flute, violin
移调: ±5（根据学生音域）
自动调音: 开启（strength 1.0，显示标准音准）
```

### 创意编曲
```bash
推荐音色: synth_bass_1, lead_2_sawtooth, pad_2_warm
移调: ±12（尝试不同八度）
自动调音: 关闭（保留原始表现力）
```

### 电话彩铃/铃声制作
```bash
推荐音色: music_box, xylophone, celesta
移调: +7 到 +12（明亮清脆）
自动调音: 开启（strength 1.0）
tempo: 130-140（欢快节奏）
```

## 🔧 故障排查

### 问题1: "No notes detected"

**原因**: 输入音频太短、太安静或噪音太大

**解决方案**:
```bash
# 降低检测阈值
python demo_timbre_transform.py song.wav --threshold 1.0

# 减小最小音符时长
python demo_timbre_transform.py song.wav --min-duration 0.02
```

### 问题2: 音符切分太碎

**原因**: 分割阈值太低

**解决方案**:
```bash
# 提高阈值，使音符更连贯
python demo_timbre_transform.py song.wav --threshold 1.2
```

### 问题3: MIDI文件没有声音

**原因**: MIDI播放器没有加载正确音色库

**解决方案**:
- 使用在线播放器: https://signal.vercel.app/edit
- 或导入到DAW (GarageBand, FL Studio等)

### 问题4: 音高太高/太低

**原因**: 需要移调

**解决方案**:
```bash
# 降低一个八度
python demo_timbre_transform.py song.wav -t -12

# 升高5个半音
python demo_timbre_transform.py song.wav -t 5
```

## 📚 下一步

- 阅读完整文档: [TIMBRE_TRANSFORM_README.md](TIMBRE_TRANSFORM_README.md)
- 查看系统架构: [ARCHITECTURE.md](ARCHITECTURE.md)
- 浏览128种音色列表: 查看 `swift_f0/music_enhanced.py`
- 运行完整测试: `python test_timbre_demo.py`

## 💡 实用小技巧

1. **快速试听不同音色**: 使用 `--batch` 参数一次生成多个版本，然后挑选最好的

2. **找到最佳移调值**: 从-5到+5逐个试听，找到最舒服的音域

3. **自动调音强度调节**: 从0.5开始，如果还有跑调就提高到0.8或1.0

4. **组合使用**: `--kazoo --auto-tune -t 2` 可以同时应用多个优化

5. **批量处理**: 写个简单的bash循环处理整个文件夹的音频

```bash
for file in recordings/*.wav; do
    python demo_timbre_transform.py "$file" --kazoo --auto-tune
done
```

---

**祝你玩得开心！如有问题欢迎提Issue 🎵**
