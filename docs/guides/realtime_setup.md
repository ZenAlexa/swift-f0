# Real-time Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
# Install real-time requirements
pip install -r requirements_realtime.txt
```

### 2. Test Audio Setup

```bash
# Test basic functionality
python demos/realtime/test_simple.py
```

### 3. Configure Settings

Edit `config/realtime_config.yaml` to adjust:
- Audio device selection
- Buffer sizes for latency tuning
- Synthesis method and instruments

## System Requirements

- Python 3.8+
- Microphone or audio input device
- ~350MB RAM
- Low-latency audio drivers recommended

## Configuration

All settings are in `config/realtime_config.yaml`:

```yaml
audio:
  sample_rate: 16000    # Don't change (SwiftF0 requirement)
  chunk_size: 256       # Smaller = lower latency, higher CPU

synthesis:
  method: "simple"      # Use "simple" for testing
  soundfont_path: "soundfonts/GeneralUser-GS.sf2"
```

## Troubleshooting

### No audio input/output

Check available devices:
```python
import sounddevice as sd
print(sd.query_devices())
```

Then set device IDs in config:
```yaml
audio:
  device_in: 2   # Your mic device ID
  device_out: 3  # Your speaker device ID
```

### High latency

Reduce chunk size:
```yaml
audio:
  chunk_size: 128  # Lower latency but higher CPU
```

### Audio dropouts

Increase buffer size:
```yaml
buffer:
  size: 16384  # Larger buffer, more stable
```

## Testing Checklist

1. ✅ Audio input working (mic test)
2. ✅ Pitch detection responding
3. ✅ Synthesis producing sound
4. ✅ Latency acceptable (<100ms)
5. ✅ No audio dropouts

## Next Steps

Once basic testing works:

1. **Optimize latency**: Tune buffer sizes
2. **Test instruments**: Try different synthesis settings
3. **Integrate with hardware**: Connect your development board
4. **Add features**: Auto-tune, effects, etc.

## Integration with Development Board

If your colleague's board appears as a USB audio device:

```yaml
audio:
  device_in: "USB Audio Device"  # Or device ID
```

If using serial/custom protocol, extend `AudioStream`:

```python
class BoardAudioStream(AudioStream):
    def __init__(self, port="/dev/ttyUSB0"):
        # Initialize serial connection
        # Override audio input methods
        pass
```

## Performance Tips

1. **Close other applications** to reduce system load
2. **Use wired connection** for development board
3. **Disable unnecessary features** in config
4. **Monitor CPU usage** and adjust accordingly

---

Ready to test? Run:
```bash
python demos/realtime/test_simple.py
```