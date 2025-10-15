# SwiftF0 实时性能优化建议

**版本**：v1.0  
**日期**：2025-10-13

---

## 1. ONNX 模型优化清单

1. **图优化**
   - 设置 `SessionOptions.graph_optimization_level = ORT_ENABLE_ALL`；
   - 启用 `add_free_dimension_override_by_name("audio", 1024)` 锁定窗口大小；
   - 预热 `InferenceSession`，缓存优化后图。
2. **线程配置**
   - `intra_op_num_threads = 2`、`inter_op_num_threads = 1`（树莓派 4 核）；  
   - 绑定 CPU（`taskset -c 2`）避免与音频线程争用。
3. **IO Binding**
   - 使用 `io_binding.bind_input` 绑定预分配 `OrtValue`；
   - 消除 Python ↔ C 内存复制。
4. **量化**
   - `quantize_dynamic(model, weight_type=QuantType.QInt8)`；
   - 若存在精度损失，保留首层/末层为 FP16。
5. **缓存复用**
   - 预分配滑动窗口内存，避免 `np.append`；
   - 利用 `numpy.lib.stride_tricks.as_strided` 构建视图，减少复制。

---

## 2. 系统级优化步骤

| 步骤 | 命令 | 目的 |
| --- | --- | --- |
| 固定 CPU 频率 | `echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor` | 避免频率波动 |
| 提升优先级 | `sudo chrt -f 90 python realtime_demo.py` | 确保音频线程实时调度 |
| 关闭省电 | `sudo systemctl disable --now bluetooth`（如不需 BLE） | 释放 CPU |
| 温控 | 安装散热片 + 风扇，启用 `vcgencmd measure_temp` 监控 | 防止降频 |
| PREEMPT_RT | 安装 `linux-image-rt`，配置 `/boot/config.txt` 中 `threadirqs=1` | 降低调度延迟 |
| HugePages | `sudo sysctl -w vm.nr_hugepages=32`（可选） | 减少 TLB miss |

---

## 3. 量化工具使用指南

```bash
python -m venv .venv
source .venv/bin/activate
pip install onnxruntime onnx onnxruntime-tools

python tools/export_calibration_dataset.py --input data/wavs --output calib.npz

python -m onnxruntime.quantization.quantize_static \
    --model swift_f0/model.onnx \
    --calib_data calib.npz \
    --quant_format QDQ \
    --per_channel \
    --activation_type QInt8 \
    --weight_type QInt8 \
    --output swift_f0/model_int8.onnx
```

验证命令：

```bash
python benchmarks/benchmark_inference.py --model swift_f0/model.onnx
python benchmarks/benchmark_inference.py --model swift_f0/model_int8.onnx
```

---

## 4. 树莓派部署脚本

参见 `scripts/deploy_rpi_streaming.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/swift-f0}"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/.venv}"

sudo apt-get update
sudo apt-get install -y python3-venv python3-dev portaudio19-dev \
    libatlas-base-dev libasound2-dev build-essential git

if [ ! -d "$PROJECT_DIR" ]; then
  git clone https://github.com/Zenalexa/swift-f0.git "$PROJECT_DIR"
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip wheel setuptools
pip install -r "$PROJECT_DIR/requirements.txt"
pip install onnxruntime==1.18.0 onnx onnxruntime-tools sounddevice python-rtmidi

cp "$PROJECT_DIR/swift_f0/model_int8.onnx" "$PROJECT_DIR/swift_f0/model.onnx"

sudo bash -c 'echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
sudo bash -c 'echo performance > /sys/devices/system/cpu/cpu1/cpufreq/scaling_governor'
sudo bash -c 'echo performance > /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor'
sudo bash -c 'echo performance > /sys/devices/system/cpu/cpu3/cpufreq/scaling_governor'

echo "Setup completed. Run examples/streaming/realtime_demo.py to start streaming."
```

---

## 5. 性能监控脚本示例

```bash
python tools/monitor_latency.py --duration 120 --output logs/latency.jsonl
```

该脚本需记录：

- `audio_callback_us`、`inference_us`、`note_latency_ms`；  
- CPU、内存、温度；  
- dropouts 次数。

---

## 6. 优化路线图

1. **阶段 1**：完成 INT8 量化与线程配置，桌面端延迟 <20ms；  
2. **阶段 2**：移植树莓派，验证端到端延迟 <50ms；  
3. **阶段 3**：启用 PREEMPT_RT、CPU 亲和性、io_binding；  
4. **阶段 4**：根据 Profiling 决定是否引入 C++ 后处理或 Rust 模块；  
5. **阶段 5**：部署监控报警（温度过高、延迟超标自动降级）。

---

## 7. 结论

通过图优化、量化、线程与系统配置的组合策略，SwiftF0 流式系统可在树莓派 Zero 2W 上达到 <50ms 延迟目标，同时保证 CPU 占用 <50%、内存 <100MB，满足 AI 卡祖笛项目的实时上线需求。
