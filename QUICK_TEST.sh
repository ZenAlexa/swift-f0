#!/bin/bash
# 紧急修复快速测试脚本

echo "========================================================================"
echo "🚨 紧急修复测试 - 爆音/噪音问题"
echo "========================================================================"
echo ""
echo "已应用的紧急修复:"
echo "  ✅ Fix 1: 音符数量限制（MAX_ACTIVE_NOTES = 4）"
echo "  ✅ Fix 4: 降低默认增益（0.8 → 0.3）"
echo "  ✅ 输出 headroom 保持 -10.5dB"
echo ""
echo "测试配置:"
echo "  - 增益: 0.05 (-26dB, 极度保守)"
echo "  - 置信度: 0.95 (更严格)"
echo "  - Split 阈值: 1.5 半音 (减少分裂)"
echo "  - Grace period: 15 帧 (240ms)"
echo "  - Min frames: 7 (112ms, 更稳定)"
echo ""
echo "========================================================================"
echo ""

# 查找 SoundFont 文件
SF2_PATH=""
if [ -f "soundfonts/GeneralUser-GS.sf2" ]; then
    SF2_PATH="$(pwd)/soundfonts/GeneralUser-GS.sf2"
elif [ -f "soundfonts/FluidR3_GM.sf2" ]; then
    SF2_PATH="$(pwd)/soundfonts/FluidR3_GM.sf2"
else
    echo "❌ 错误: 未找到 SoundFont 文件"
    echo "请将 .sf2 文件放到 soundfonts/ 目录"
    exit 1
fi

echo "使用 SoundFont: $SF2_PATH"
echo ""
echo "测试步骤:"
echo "  1. 启动后保持安静 3 秒（观察是否静音）"
echo "  2. 哼唱单音 \"啊啊啊\" 2 秒（观察音色）"
echo "  3. 停止哼唱（观察是否快速静音）"
echo "  4. 哼唱音阶变化（观察是否爆音）"
echo ""
echo "预期结果:"
echo "  ✅ 安静时绝对静音"
echo "  ✅ 哼唱时听到清晰的单一音高（不是噪音）"
echo "  ✅ 停止后 ~200ms 内静音"
echo "  ✅ 音阶变化时无持续爆音"
echo "  ✅ 终端输出包含活跃音符数（应 ≤ 4）"
echo ""
read -p "按 Enter 开始测试..."

python examples/streaming/realtime_demo.py \
  --audio \
  --sf2 "$SF2_PATH" \
  --instrument 68 \
  --gain 0.05 \
  --confidence-threshold 0.95 \
  --split-threshold 1.5 \
  --grace-frames 15 \
  --min-note-frames 7 \
  --gate-open-db -35 \
  --sample-rate 44100

echo ""
echo "========================================================================"
echo "测试完成"
echo "========================================================================"
echo ""
echo "如果仍有问题，请运行诊断脚本:"
echo "  python DEBUG_CAPTURE.py --duration 10"
echo ""
echo "然后将以下文件发给我分析:"
echo "  - debug_midi_events.txt"
echo "  - debug_active_notes.txt"
echo "  - debug_pitch_frames.txt"
