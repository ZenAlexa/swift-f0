# 音频输出测试文件

本目录存放各种测试生成的音频文件。

## 目录结构

### `wavetable_synthesis/`
波表合成器生成的测试音频，用于验证不同乐器音色的合成质量。

**命名规范**: `test_{instrument}_{note}.wav`
- `instrument`: sine, flute, violin, clarinet
- `note`: C4, E4, G4, C5 等音符

**文件列表**:
- `test_flute_*.wav` - 长笛音色测试（8个谐波）
- `test_violin_*.wav` - 小提琴音色测试（16个谐波，1/n衰减）
- `test_clarinet_*.wav` - 单簧管音色测试（奇数谐波强调）
- `test_sine_*.wav` - 纯正弦波基准测试

**生成方式**:
```bash
python demos/realtime/test_additive_synth.py
```

**用途**:
- 验证波表生成质量
- 对比不同乐器音色特征
- 音频质量回归测试

---

*最后更新: 2024-10-22*
