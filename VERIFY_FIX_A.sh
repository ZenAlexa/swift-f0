#!/bin/bash
# 验证 Fix A（音符追踪修复）效果

echo "========================================================================"
echo "🔧 验证 Fix A - 音符追踪修复"
echo "========================================================================"
echo ""
echo "已应用的修复:"
echo "  ✅ Fix A: 音符追踪（current_note 字段）"
echo "  ✅ Fix 1: 音符数量限制（MAX_ACTIVE_NOTES = 4）"
echo "  ✅ Fix 4: 降低默认增益（0.8 → 0.3）"
echo ""
echo "测试目标:"
echo "  验证 MIDI 事件完全配对（重复 note_on = 0, 孤立 note_off = 0）"
echo ""
echo "========================================================================"
echo ""

# Step 1: 运行诊断捕获
echo "📊 Step 1: 运行诊断捕获（10 秒）"
echo ""
echo "请按照以下步骤测试:"
echo "  1-3秒: 保持安静"
echo "  3-5秒: 哼唱单音 \"啊啊啊\""
echo "  5-7秒: 保持安静"
echo "  7-10秒: 哼唱快速音阶 \"do-re-mi-fa-sol\""
echo ""
read -p "按 Enter 开始录制..."

python DEBUG_CAPTURE.py --duration 10

if [ $? -ne 0 ]; then
    echo "❌ 诊断捕获失败"
    exit 1
fi

echo ""
echo "========================================================================"
echo "📈 Step 2: 分析 MIDI 事件配对"
echo "========================================================================"
echo ""

python3 << 'EOF'
import csv

# 分析 MIDI 事件配对
with open('debug_midi_events.txt', 'r') as f:
    reader = csv.DictReader(f)
    events = list(reader)

if len(events) == 0:
    print("⚠️  警告: 未检测到任何 MIDI 事件（可能一直静音）")
    exit(0)

# 统计基本信息
total_events = len(events)
note_on_count = sum(1 for e in events if e['event_type'] == 'note_on')
note_off_count = sum(1 for e in events if e['event_type'] == 'note_off')
first_time = float(events[0]['timestamp'])
last_time = float(events[-1]['timestamp'])
duration = last_time - first_time
events_per_sec = total_events / duration if duration > 0 else 0

print("基本统计:")
print(f"  总事件数: {total_events}")
print(f"  note_on:  {note_on_count}")
print(f"  note_off: {note_off_count}")
print(f"  事件密度: {events_per_sec:.1f} events/秒")
print()

# 检查配对问题
note_states = {}
unpaired_on = 0
unpaired_off = 0
unpaired_on_notes = []
unpaired_off_notes = []

for e in events:
    note = int(e['note'])
    if e['event_type'] == 'note_on':
        if note in note_states and note_states[note] == 'on':
            unpaired_on += 1
            unpaired_on_notes.append(note)
        note_states[note] = 'on'
    elif e['event_type'] == 'note_off':
        if note not in note_states or note_states[note] == 'off':
            unpaired_off += 1
            unpaired_off_notes.append(note)
        else:
            note_states[note] = 'off'

print("配对检查:")
print(f"  重复 note_on（未配对）: {unpaired_on}")
if unpaired_on > 0:
    print(f"    涉及音符: {set(unpaired_on_notes)}")

print(f"  孤立 note_off（未配对）: {unpaired_off}")
if unpaired_off > 0:
    print(f"    涉及音符: {set(unpaired_off_notes)}")

print()

# 判断结果
if unpaired_on == 0 and unpaired_off == 0:
    print("✅ FIX A 成功！所有 MIDI 事件完全配对！")
    print()
    print("预期音色:")
    print("  - 哼唱单音时应听到清晰的单一音高（不是噪音）")
    print("  - 音符切换时平滑过渡，无爆音")
    print("  - 停止哼唱后立即静音")
    exit(0)
else:
    print("❌ FIX A 未完全生效，仍有配对问题")
    print()
    print("可能原因:")
    if unpaired_on > 0:
        print("  - 重复 note_on: 分段器仍在发送重复音符")
    if unpaired_off > 0:
        print("  - 孤立 note_off: 音符号计算仍不一致")
    print()
    print("建议:")
    print("  1. 检查 swift_f0/streaming/notes.py 是否正确应用了 Fix A")
    print("  2. 提高 --split-threshold 到 2.0 减少 split 频率")
    print("  3. 查看 debug_midi_events.txt 找出具体哪些音符有问题")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "🎉 测试通过！现在运行实际音频测试:"
    echo "========================================================================"
    echo ""

    # 查找 SoundFont 文件
    SF2_PATH=""
    if [ -f "soundfonts/GeneralUser-GS.sf2" ]; then
        SF2_PATH="$(pwd)/soundfonts/GeneralUser-GS.sf2"
    elif [ -f "soundfonts/FluidR3_GM.sf2" ]; then
        SF2_PATH="$(pwd)/soundfonts/FluidR3_GM.sf2"
    else:
        echo "❌ 错误: 未找到 SoundFont 文件"
        exit 1
    fi

    echo "使用 SoundFont: $SF2_PATH"
    echo ""
    read -p "按 Enter 启动音频测试（Ctrl+C 取消）..."

    python examples/streaming/realtime_demo.py \
      --audio \
      --sf2 "$SF2_PATH" \
      --instrument 68 \
      --gain 0.1 \
      --confidence-threshold 0.9 \
      --split-threshold 1.5 \
      --grace-frames 10 \
      --min-note-frames 5
fi

echo ""
echo "========================================================================"
echo "测试完成"
echo "========================================================================"
