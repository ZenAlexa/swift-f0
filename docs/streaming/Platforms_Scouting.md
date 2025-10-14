# Platforms Scouting: ESP32-S3, Raspberry Pi, K210

This note summarizes initial feasibility for streaming F0 + MIDI on three targets.

## ESP32-S3
- CPU: Dual-core Xtensa LX7 @ up to 240 MHz; RAM typically <512 KB SRAM + PSRAM optional.
- Pros: Integrated USB, BLE, relatively strong DSP instructions.
- Cons: Python (MicroPython) unsuitable for heavy DSP/ML; ONNX/TFLite runtime impractical.
- Path:
  - Use classic DSP pitch trackers (YIN/aubio-port) in C, fixed-point where possible.
  - Implement minimal state machine for note events.
  - MIDI over USB or BLE-MIDI; latency target <20 ms.
  - No on-device Auto-tune/Key detection initially; offload to host.

## Raspberry Pi (Zero 2W/3/4)
- CPU: ARM Cortex-A53/A72; RAM >= 512 MB.
- Pros: Full Linux; Python + ONNX Runtime feasible; sounddevice + rtmidi available.
- Cons: Need RT tuning to avoid xruns.
- Path:
  - Reuse Python streaming stack in this repo with ONNX Runtime INT8 model.
  - Configure ALSA/JACK; optional PREEMPT_RT; set CPU governor performance.
  - Target <50 ms end-to-end on Pi 4; Zero 2W may be ~60–80 ms with tuning.

## Kendryte K210
- CPU: Dual-core RISC-V 64-bit @ 400–600 MHz; on-chip KPU (neural net accelerator).
- Pros: KPU for CNN-like workloads.
- Cons: Toolchain expects models compiled to KPU ops; ONNX Runtime not supported directly; Python impractical.
- Path:
  - Convert SwiftF0 CNN into KPU-compatible model (layer support permitting), or redesign a lightweight CNN.
  - Implement audio capture + ring buffer + state machine in C.
  - MIDI over UART/USB bridge.

## Recommendation
- Short term demo: macOS/Linux desktop (Python) — use this repo’s streaming pipeline.
- Near term: Raspberry Pi 4 — same stack with tuning + INT8 model.
- ESP32-S3/K210: C/C++ reimplementation with classical DSP or KPU-compiled model; scope as separate firmware project.

