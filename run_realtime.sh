#!/bin/bash
# Quick script to run real-time demos with correct Python path

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Run the script passed as argument
if [ $# -eq 0 ]; then
    echo "Running default test..."
    python "${SCRIPT_DIR}/demos/realtime/test_simple.py"
else
    python "$@"
fi