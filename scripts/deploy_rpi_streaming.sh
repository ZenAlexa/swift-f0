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

if [ -f "$PROJECT_DIR/swift_f0/model_int8.onnx" ]; then
  cp "$PROJECT_DIR/swift_f0/model_int8.onnx" "$PROJECT_DIR/swift_f0/model.onnx"
fi

for cpu in 0 1 2 3; do
  if [ -f "/sys/devices/system/cpu/cpu${cpu}/cpufreq/scaling_governor" ]; then
    sudo bash -c "echo performance > /sys/devices/system/cpu/cpu${cpu}/cpufreq/scaling_governor"
  fi
done

echo "Setup completed. Run examples/streaming/realtime_demo.py to start streaming."
