# SoundFonts Directory

Place your `.sf2` or `.sf3` SoundFont files here for audio synthesis.

---

## Current Files

- `GeneralUser-GS.sf2` (31MB) - High quality, recommended for most use cases

---

## Download More SoundFonts

### Option 1: FluidR3 GM (142MB, comprehensive)
```bash
curl -L https://member.keymusician.com/Member/FluidR3_GM/FluidR3_GM.tar.gz -o FluidR3_GM.tar.gz
tar -xzf FluidR3_GM.tar.gz
mv FluidR3_GM.sf2 soundfonts/
```

### Option 2: MuseScore General (35MB, compressed SF3)
```bash
curl -L https://github.com/musescore/MuseScore/raw/master/share/sound/MuseScore_General.sf3 \
     -o soundfonts/MuseScore_General.sf3
```

---

## Usage

```bash
# Use with realtime demo
python examples/streaming/realtime_demo.py \
    --audio \
    --sf2 soundfonts/GeneralUser-GS.sf2 \
    --instrument 68

# Use different soundfont
python examples/streaming/realtime_demo.py \
    --audio \
    --sf2 soundfonts/FluidR3_GM.sf2 \
    --instrument 56
```

---

## Quality Comparison

| SoundFont | Size | Quality | Instruments | Best For |
|-----------|------|---------|-------------|----------|
| GeneralUser-GS | 31MB | High | 128 GM | Balanced quality/size |
| FluidR3 GM | 142MB | Very High | 128 GM | Maximum quality |
| MuseScore General | 35MB | Good | 128 GM | Compressed, fast load |

---

**Note**: Files in this directory are ignored by git (see `.gitignore`).
Team members should download their own SoundFonts.
