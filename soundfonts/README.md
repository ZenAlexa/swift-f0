# SoundFont Files

This directory contains SoundFont (.sf2) files used for high-quality MIDI playback.

## Current Files

- **GeneralUser-GS.sf2** (30.8 MB)
  - Full General MIDI soundfont with 128 instruments
  - Source: [GeneralUser GS](http://schristiancollins.com/generaluser.php)
  - License: Free for personal and commercial use

## Usage

These soundfonts are used with FluidSynth or other MIDI synthesizers for audio rendering:

```bash
# Example: Convert MIDI to audio using FluidSynth
fluidsynth -ni soundfonts/GeneralUser-GS.sf2 output.mid -F output.wav -r 44100
```

## Adding New SoundFonts

To add additional soundfont files:

1. Place the `.sf2` file in this directory
2. Update this README with file information
3. Add to `.gitignore` if the file is large (>50MB)

## Notes

- Large soundfonts (>50MB) should be downloaded separately and not committed to git
- Consider using Git LFS for version-controlled large files
- Keep a reference document for where to download soundfonts
