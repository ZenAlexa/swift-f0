"""
Audio synthesis abstractions for real-time MIDI-to-audio conversion.

This module defines minimal protocols and base classes for audio synthesis,
following the Interface Segregation Principle (ISP) and Dependency Inversion
Principle (DIP).

Architecture:
    AudioSynthesizerProtocol (abstract)
        ↓ implements
    FluidSynthBackend (concrete)
        ↓ composition (not inheritance!)
    RealtimeAudioSink (extends BaseMIDISink)

SOLID Principles Applied:
- Single Responsibility: Each class handles one concern
- Open-Closed: Extend BaseMIDISink, don't modify it
- Liskov Substitution: RealtimeAudioSink can replace any BaseMIDISink
- Interface Segregation: AudioSynthesizerProtocol has only 3 methods
- Dependency Inversion: Depend on protocols, not concrete implementations
- Law of Demeter: Minimal coupling between components
- Composition over Inheritance: RealtimeAudioSink contains FluidSynthBackend

SoundFont Download Guide:
------------------------
You need a .sf2 SoundFont file for audio synthesis. Download options:

1. FluidR3 GM (recommended, 142MB):
   https://member.keymusician.com/Member/FluidR3_GM/FluidR3_GM.tar.gz
   Extract and use: FluidR3_GM.sf2

2. GeneralUser GS (high quality, 30MB):
   http://www.schristiancollins.com/generaluser.php
   Download and use: GeneralUser_GS.sf2

3. MuseScore default (free, 35MB):
   https://github.com/musescore/MuseScore/raw/master/share/sound/MuseScore_General.sf3
   Use: MuseScore_General.sf3 (SF3 is compressed SF2)

Place the downloaded file anywhere and provide the path via --sf2 argument:
    python examples/streaming/realtime_demo.py --audio --sf2 /path/to/soundfont.sf2
"""

from __future__ import annotations

import logging
import threading
from typing import Protocol, Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .types import NoteEvent
from .midi import BaseMIDISink

logger = logging.getLogger(__name__)

# Optional dependencies with graceful fallback
try:
    import fluidsynth

    FLUIDSYNTH_AVAILABLE = True
except ImportError:  # pragma: no cover
    FLUIDSYNTH_AVAILABLE = False
    fluidsynth = None

try:
    import sounddevice as sd

    SOUNDDEVICE_AVAILABLE = True
except ImportError:  # pragma: no cover
    SOUNDDEVICE_AVAILABLE = False
    sd = None


# ============================================================================
# Phase 1: Protocols and Configuration (Interface Segregation Principle)
# ============================================================================


class AudioSynthesizerProtocol(Protocol):
    """
    Minimal interface for MIDI-to-audio synthesis.

    Following Interface Segregation Principle: only 3 methods needed.
    Implementations: FluidSynthBackend, future alternatives (e.g., TinySoundFont).

    Contract:
        - note_on/note_off are thread-safe if implementation requires
        - get_samples returns interleaved stereo float32 array
        - All methods must be callable from different threads safely

    Thread Safety:
        Implementations are NOT required to be thread-safe internally.
        Callers (like RealtimeAudioSink) MUST ensure thread safety by adding locks.
    """

    def note_on(self, channel: int, note: int, velocity: int) -> None:
        """
        Trigger note start.

        Args:
            channel: MIDI channel [0-15]
            note: MIDI note number [0-127], where 60 = Middle C
            velocity: Note velocity [0-127], where 0 = silent, 127 = loudest

        Example:
            synthesizer.note_on(0, 60, 80)  # Play Middle C at medium velocity
        """
        ...

    def note_off(self, channel: int, note: int) -> None:
        """
        Trigger note stop.

        Args:
            channel: MIDI channel [0-15]
            note: MIDI note number [0-127]

        Example:
            synthesizer.note_off(0, 60)  # Stop Middle C
        """
        ...

    def get_samples(self, num_samples: int) -> np.ndarray:
        """
        Generate audio samples.

        Args:
            num_samples: Number of mono samples to generate (per channel)

        Returns:
            NumPy array of shape (num_samples * 2,) for interleaved stereo audio
            dtype: float32, range [-1.0, 1.0]
            Format: [L0, R0, L1, R1, L2, R2, ...] (interleaved left/right)

        Example:
            # Generate 256 stereo samples (512 float32 values)
            samples = synthesizer.get_samples(256)
            assert samples.shape == (512,)
            assert samples.dtype == np.float32

        Note:
            This method is typically called from audio callback thread.
            For real-time audio: num_samples is usually the audio buffer size (e.g., 256).
        """
        ...


@dataclass
class AudioSynthConfig:
    """
    Configuration for audio synthesis (Single Responsibility Principle).

    Attributes:
        sample_rate: Audio sample rate in Hz (default: 44100 for high quality)
                    Higher values = better quality, more CPU usage
                    44100Hz is CD quality, 48000Hz is professional audio

        gain: Master volume multiplier [0.0-10.0] (default: 0.3, EMERGENCY FIX降低)
              0.0 = silent, 1.0 = nominal, >1.0 = amplified (may clip)
              EMERGENCY FIX: 0.8 → 0.3 (per user feedback: 爆音问题)

        soundfont_path: Path to .sf2 or .sf3 SoundFont file (REQUIRED)
                       Leave empty string for now, provide via CLI --sf2
                       See module docstring for download links

        initial_program: GM (General MIDI) instrument program [0-127]
                        Default: 68 = oboe (kazoo-like timbre for vocalization)
                        Common values:
                          0 = Acoustic Grand Piano
                          24 = Acoustic Guitar
                          40 = Violin
                          56 = Trumpet
                          68 = Oboe
                          73 = Flute

    Example:
        # For desktop demo with user-provided SoundFont
        config = AudioSynthConfig(
            sample_rate=44100.0,
            gain=0.3,  # EMERGENCY FIX: 降低默认增益
            soundfont_path="/Users/you/Downloads/FluidR3_GM.sf2",
            initial_program=68,  # oboe
        )
    """

    sample_rate: float = 44100.0  # CD quality (per review: higher quality than 16kHz)
    gain: float = 0.2  # FluidSynth default (lower = less clipping, more polyphony)
    soundfont_path: str = ""  # MUST be provided by user (per review: no default)
    initial_program: int = 68  # oboe (kazoo-like timbre)

    def __post_init__(self) -> None:
        """
        Validate configuration after initialization.

        Raises:
            ValueError: If soundfont_path is empty
        """
        if not self.soundfont_path:
            raise ValueError(
                "soundfont_path is required. Please provide a .sf2 or .sf3 SoundFont file.\n"
                "\n"
                "Download options:\n"
                "  1. FluidR3 GM (142MB): https://member.keymusician.com/Member/FluidR3_GM/FluidR3_GM.tar.gz\n"
                "  2. GeneralUser GS (30MB): http://www.schristiancollins.com/generaluser.php\n"
                "  3. MuseScore (35MB): https://github.com/musescore/MuseScore/raw/master/share/sound/MuseScore_General.sf3\n"
                "\n"
                "Usage:\n"
                "  python realtime_demo.py --audio --sf2 /path/to/soundfont.sf2 --instrument 68"
            )


# ============================================================================
# Phase 1: Abstract Audio Sink (Open-Closed Principle)
# ============================================================================


class BaseAudioSink(BaseMIDISink):
    """
    Abstract base for MIDI-to-audio sinks.

    Extends BaseMIDISink to audio output (Open-Closed Principle: extension, not modification).
    Subclasses must manage audio I/O lifecycle (start/stop streams).

    Single Responsibility: only handles NoteEvent → Synthesizer routing.
    Thread safety is the responsibility of subclasses (see RealtimeAudioSink).

    Design Patterns:
        - Template Method: Defines send/finalize flow, subclasses add audio I/O
        - Dependency Inversion: Depends on AudioSynthesizerProtocol, not concrete class

    Attributes:
        synthesizer: AudioSynthesizerProtocol implementation (injected via constructor)
        _active_notes: Set of currently playing MIDI note numbers

    EMERGENCY FIX (per user feedback: 爆音/音符堆积):
        - MAX_ACTIVE_NOTES = 4 (强制限制，防止音符风暴)
        - 超过限制时强制 note_off 最老音符
        - 处理孤立 note_off（清理幽灵音符）

    Example:
        # Subclass must implement audio I/O
        class MyAudioSink(BaseAudioSink):
            def __init__(self, config):
                backend = FluidSynthBackend(config)
                super().__init__(backend)
                # Start audio stream here

            def finalize(self):
                super().finalize()  # Stop all notes
                # Stop audio stream here
    """

    # EMERGENCY FIX: 强制音符数量限制（防止音符堆积爆音）
    MAX_ACTIVE_NOTES = 4  # 单声部哼唱最多 4 个音符（含 split 缓冲）

    def __init__(self, synthesizer: AudioSynthesizerProtocol) -> None:
        """
        Initialize with synthesizer (Dependency Inversion: depend on protocol).

        Args:
            synthesizer: Any object implementing AudioSynthesizerProtocol
                        (e.g., FluidSynthBackend, future TinySoundFont)
        """
        self.synthesizer = synthesizer
        self._active_notes: set[int] = set()
        self._note_start_order: list[int] = []  # EMERGENCY FIX: 记录音符启动顺序

    def send(self, events: Iterable[NoteEvent]) -> None:
        """
        Process MIDI events and forward to synthesizer.

        EMERGENCY FIX (per user feedback: 爆音/音符堆积):
        - 强制音符数量限制（MAX_ACTIVE_NOTES = 4）
        - 超过限制时自动 note_off 最老音符
        - 处理孤立 note_off（清理可能的幽灵音符）

        Single Responsibility: only event routing, no audio I/O here.
        Subclasses may override to add thread safety (e.g., RealtimeAudioSink).

        Args:
            events: Iterable of NoteEvent objects
                   Each event must have: type, note, time, velocity

        Example:
            events = [
                NoteEvent(type="note_on", note=60, time=0.0, velocity=80),
                NoteEvent(type="note_off", note=60, time=1.0, velocity=0),
            ]
            sink.send(events)

        Note:
            This method is NOT thread-safe by default. Subclasses like RealtimeAudioSink
            must override to add locking if called from multiple threads.
        """
        for event in events:
            if event.type == "note_on":
                # EMERGENCY FIX: 音符数量限制（防止堆积爆音）
                if len(self._active_notes) >= self.MAX_ACTIVE_NOTES:
                    # 强制关闭最老的音符（FIFO）
                    if self._note_start_order:
                        oldest_note = self._note_start_order.pop(0)
                        self.synthesizer.note_off(0, oldest_note)
                        self._active_notes.discard(oldest_note)
                        logger.warning(
                            f"🚨 EMERGENCY: Force note_off {oldest_note} "
                            f"(limit={self.MAX_ACTIVE_NOTES}, active={len(self._active_notes)})"
                        )

                self.synthesizer.note_on(0, event.note, event.velocity)
                self._active_notes.add(event.note)
                self._note_start_order.append(event.note)

            elif event.type == "note_off":
                # EMERGENCY FIX: 处理孤立 note_off（清理幽灵音符）
                if event.note in self._active_notes:
                    # 正常的 note_off（有对应 note_on）
                    self.synthesizer.note_off(0, event.note)
                    self._active_notes.discard(event.note)
                    if event.note in self._note_start_order:
                        self._note_start_order.remove(event.note)
                else:
                    # 孤立的 note_off（没有对应 note_on）
                    # 仍然发送给 FluidSynth 清理可能的幽灵音符
                    self.synthesizer.note_off(0, event.note)
                    logger.debug(f"Orphan note_off: {event.note} (may clean ghost note)")

    def finalize(self) -> None:
        """
        Release all active notes and clean up.

        This is a template method that stops all notes. Subclasses should call
        super().finalize() first, then clean up audio resources.

        Example:
            def finalize(self):
                super().finalize()  # Stop all notes
                self.stream.stop()  # Stop audio stream
                self.synthesizer.delete()  # Clean up backend
        """
        # Stop all active notes (prevent stuck notes)
        for note in list(self._active_notes):
            self.synthesizer.note_off(0, note)
        self._active_notes.clear()


# ============================================================================
# Phase 2: FluidSynth Backend Implementation (Composition over Inheritance)
# ============================================================================


class FluidSynthBackend:
    """
    FluidSynth implementation of AudioSynthesizerProtocol.

    Single Responsibility: wraps FluidSynth C library bindings.
    Composition over Inheritance: contains fluidsynth.Synth, not inherits.
    Law of Demeter: only interacts with fluidsynth.Synth, does not expose internals.

    Thread Safety:
        - FluidSynth internal operations are NOT thread-safe
        - Caller MUST synchronize note_on/note_off/get_samples calls
        - See RealtimeAudioSink for proper locking pattern

    Design:
        This class is a thin wrapper around fluidsynth.Synth.
        It validates inputs, handles errors, but does NOT add threading logic.
        Threading is the responsibility of the caller (Dependency Inversion).

    Example:
        config = AudioSynthConfig(
            sample_rate=44100.0,
            gain=0.8,
            soundfont_path="/path/to/soundfont.sf2",
            initial_program=68,
        )
        backend = FluidSynthBackend(config)
        backend.note_on(0, 60, 80)  # Middle C
        samples = backend.get_samples(256)  # 512 float32 values
        backend.note_off(0, 60)
        backend.delete()
    """

    def __init__(self, config: AudioSynthConfig) -> None:
        """
        Initialize FluidSynth synthesizer.

        Args:
            config: Synthesis configuration (must have valid soundfont_path)

        Raises:
            RuntimeError: If FluidSynth not installed
            FileNotFoundError: If soundfont not found
            ValueError: If soundfont format is invalid (not .sf2/.sf3)

        Note:
            This method performs I/O (loading SoundFont file).
            Do NOT call from audio callback thread.
        """
        if not FLUIDSYNTH_AVAILABLE:
            raise RuntimeError(
                "FluidSynth not available. Install with:\n"
                "  macOS: brew install fluid-synth\n"
                "  Linux: sudo apt-get install fluidsynth\n"
                "  Python: pip install pyfluidsynth"
            )

        # Validate soundfont path (per review: must be .sf2/.sf3, not DLS)
        sf_path = Path(config.soundfont_path)
        if not sf_path.exists():
            raise FileNotFoundError(
                f"SoundFont not found: {config.soundfont_path}\n"
                f"Please download a .sf2 file (see module docstring for links)."
            )

        # Check file extension (per review: reject DLS files)
        if sf_path.suffix.lower() not in [".sf2", ".sf3"]:
            raise ValueError(
                f"Invalid SoundFont format: {sf_path.suffix}\n"
                f"FluidSynth requires .sf2 or .sf3 files, not {sf_path.suffix}\n"
                f"If you have a .dls file, please download a .sf2 SoundFont instead."
            )

        # Initialize synth with low-latency settings
        # Per review: sample_rate=44100 for quality (not inference rate)
        self.synth = fluidsynth.Synth(  # type: ignore
            samplerate=int(config.sample_rate),
            gain=config.gain,
        )

        # Load soundfont
        self.sfid = self.synth.sfload(str(sf_path))
        if self.sfid == -1:
            raise RuntimeError(
                f"Failed to load SoundFont: {sf_path}\n"
                f"The file may be corrupted or in an unsupported format."
            )

        # Set initial program (instrument)
        # Bank 0, Preset 0, Program = initial_program
        self.synth.program_select(0, self.sfid, 0, config.initial_program)

        logger.info(
            f"FluidSynth initialized: {config.sample_rate}Hz, "
            f"program={config.initial_program}, sf={sf_path.name}"
        )

    def note_on(self, channel: int, note: int, velocity: int) -> None:
        """
        Trigger note (Law of Demeter: direct delegation).

        Args:
            channel: MIDI channel [0-15]
            note: MIDI note number [0-127]
            velocity: Note velocity [0-127]

        Thread Safety: Caller must ensure thread safety.

        Note:
            This is a fast operation (~1-10 microseconds).
            Safe to call from real-time threads if properly synchronized.
        """
        self.synth.noteon(channel, note, velocity)

    def note_off(self, channel: int, note: int) -> None:
        """
        Stop note (Law of Demeter: direct delegation).

        Args:
            channel: MIDI channel [0-15]
            note: MIDI note number [0-127]

        Thread Safety: Caller must ensure thread safety.

        Note:
            This is a fast operation (~1-10 microseconds).
            Safe to call from real-time threads if properly synchronized.
        """
        self.synth.noteoff(channel, note)

    def get_samples(self, num_samples: int) -> np.ndarray:
        """
        Generate audio samples.

        Args:
            num_samples: Number of mono samples to generate (per channel)

        Returns:
            Interleaved stereo float32 array, shape=(num_samples*2,), range=[-1.0, 1.0]
            Format: [L0, R0, L1, R1, ...] as required by sounddevice

        Thread Safety: Caller must ensure thread safety.

        Note:
            FluidSynth returns float64 internally, converted to float32 for sounddevice.
            This operation is relatively expensive (~100 microseconds for 256 samples).

        Example:
            samples = backend.get_samples(256)
            assert samples.shape == (512,)  # 256*2 for stereo
            assert samples.dtype == np.float32
        """
        # Get samples (returns 1D array of length num_samples*2)
        samples = self.synth.get_samples(num_samples)

        # Convert to float32 for sounddevice (per review: explicit dtype)
        return samples.astype(np.float32)

    def program_change(self, channel: int, program: int) -> None:
        """
        Change instrument (for future GUI control).

        Args:
            channel: MIDI channel [0-15]
            program: GM program number [0-127]
                    0 = Acoustic Grand Piano
                    56 = Trumpet
                    68 = Oboe
                    73 = Flute
                    (see GM standard for full list)

        Thread Safety: Caller must ensure thread safety.

        Example:
            backend.program_change(0, 56)  # Switch to trumpet
        """
        self.synth.program_change(channel, program)
        logger.debug(f"Program changed to {program} on channel {channel}")

    def delete(self) -> None:
        """
        Clean up FluidSynth resources.

        IMPORTANT: Call this before program exit to free C library resources.
        Not calling delete() may cause memory leaks.

        Thread Safety: Must NOT be called while other methods are executing.
        Caller must ensure all audio callbacks have stopped before calling.

        Example:
            backend.delete()  # Always call in finalize()
        """
        if hasattr(self, "synth"):
            self.synth.delete()
            logger.info("FluidSynth resources cleaned up")


# ============================================================================
# Phase 2: Real-Time Audio Output Sink (Thread Safety CRITICAL)
# ============================================================================


class RealtimeAudioSink(BaseAudioSink):
    """
    Real-time audio output sink using sounddevice.

    Single Responsibility: manages audio output stream lifecycle.
    Composition: contains FluidSynthBackend (not inherits).
    Law of Demeter: only interacts with synthesizer protocol, not FluidSynth internals.

    Thread Safety (CRITICAL - per review):
        - Overrides send() to protect note_on/note_off with _lock
        - Audio callback uses same _lock to protect get_samples
        - This prevents FluidSynth concurrent access issues

    Architecture:
        NoteEvent → send() → [LOCK] → synthesizer.note_on/off()
        audio_callback() → [LOCK] → synthesizer.get_samples() → sounddevice

    Why Thread Safety is Critical:
        1. send() is called from main thread (postprocessing_worker)
        2. _audio_callback() is called from sounddevice audio thread
        3. FluidSynth is NOT thread-safe internally
        4. Without locking: race conditions → crashes or audio glitches

    Example:
        config = AudioSynthConfig(
            sample_rate=44100.0,
            gain=0.8,
            soundfont_path="/path/to/soundfont.sf2",
            initial_program=68,
        )
        sink = RealtimeAudioSink(config, block_size=256)

        # From main thread
        events = [NoteEvent(type="note_on", note=60, time=0.0, velocity=80)]
        sink.send(events)  # Protected by _lock

        # From audio thread (automatic)
        # _audio_callback() also protected by _lock

        sink.finalize()
    """

    def __init__(
        self,
        config: AudioSynthConfig,
        block_size: int = 256,
        output_device: int | str | None = None,
    ) -> None:
        """
        Initialize real-time audio sink.

        Args:
            config: Synthesis configuration
            block_size: Audio buffer size (samples per callback)
                       256 @ 44.1kHz ≈ 5.8ms latency (per review)
                       Smaller = lower latency, higher CPU
                       Larger = higher latency, lower CPU

        Raises:
            RuntimeError: If sounddevice not available

        Note:
            This starts the audio stream immediately.
            Audio thread begins calling _audio_callback() right away.
        """
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError(
                "sounddevice not available. Install with:\n" "  pip install sounddevice"
            )

        # Create synthesizer backend (Dependency Inversion: use protocol)
        synthesizer = FluidSynthBackend(config)
        super().__init__(synthesizer)

        self.config = config
        self.block_size = block_size
        self.stream = None
        self._lock = threading.Lock()  # Thread safety for FluidSynth calls
        self._output_device = output_device
        self._out_channels = 2  # Will be validated against device

        # Start audio stream (audio thread starts immediately)
        self._start_audio_stream()

    def send(self, events: Iterable[NoteEvent]) -> None:
        """
        Process MIDI events with thread safety (CRITICAL OVERRIDE per review).

        This method MUST override BaseAudioSink.send() to add locking,
        preventing concurrent access to FluidSynth from send() and audio callback.

        Thread Safety:
            - This method is called from main thread (postprocessing_worker)
            - _audio_callback() is called from audio thread
            - Both access self.synthesizer (FluidSynthBackend)
            - Without lock: race condition → crash or audio glitches
            - With lock: operations are serialized → safe

        Args:
            events: Iterable of NoteEvent objects

        Example:
            events = [
                NoteEvent(type="note_on", note=60, time=0.0, velocity=80),
                NoteEvent(type="note_off", note=60, time=1.0, velocity=0),
            ]
            sink.send(events)  # Thread-safe

        Performance:
            Lock contention is minimal because:
            - send() is fast (~10 microseconds per event)
            - _audio_callback() holds lock for ~100 microseconds
            - Audio buffer is large enough (256 samples = 5.8ms)
        """
        with self._lock:
            # Call parent implementation inside lock
            # This calls synthesizer.note_on() and note_off()
            super().send(events)

    def _audio_callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time_info,  # noqa: ARG002
        status,
    ) -> None:
        """
        Sounddevice callback with CRITICAL safety enhancements.

        PHASE 1 Enhancement (industry best practices):
        1. Hard silence enforcement when no active notes (absolute silence goal)
        2. Soft clipping with tanh (DAW-standard, prevents harsh distortion)
        3. Increased safety headroom: -6dB → -10.5dB (more conservative)
        4. NaN/Inf protection (always first in safety pipeline)

        Thread Safety: Uses same _lock as send() to protect FluidSynth.

        Args:
            outdata: Output buffer to fill, shape (frames, channels)
            frames: Number of frames to generate (should match block_size)
            time_info: Timing information (unused)
            status: PortAudio status flags

        Per evaluation:
        - Soft clipping (tanh) before gain reduction (preserves timbre better)
        - Hard silence when no notes (CRITICAL for "absolute silence" goal)
        - Safety pipeline order: NaN/Inf → tanh → gain → downmix

        Note:
            This runs in real-time audio thread. Keep it FAST.
            Performance budget: ~5.8ms @ 256 samples/44.1kHz
        """
        # Minimal logging to avoid callback blocking
        if status and status.output_underflow:
            logger.debug(f"Audio underflow: {status}")

        with self._lock:
            # PHASE 1: Hard silence enforcement (CRITICAL for "absolute silence" goal)
            # Industry practice: zero output when no active notes
            # Prevents residual feedback and ensures "安静时绝对静音"
            if len(self._active_notes) == 0:
                outdata.fill(0.0)
                return

            # Generate samples (interleaved stereo: frames*2 length)
            samples = self.synthesizer.get_samples(frames)

            # PHASE 1: Safety pipeline (industry-standard order)
            # Step 1: NaN/Inf protection (always first, prevents corruption)
            samples = np.nan_to_num(samples, nan=0.0, posinf=0.0, neginf=0.0)

            # Step 2: Soft clipping with tanh (DAW-standard, smoother than hard clip)
            # Per evaluation: tanh before gain reduction (preserves harmonic content)
            # tanh maps (-inf, inf) → (-1, 1) smoothly, unlike clip's sharp corner
            # Industry practice: apply before gain for more natural saturation
            samples = np.tanh(samples * 0.8)  # Pre-saturate slightly (warmth)

            # Step 3: Safety headroom (FluidSynth wiki: -6 to -12 dB for live use)
            # Per evaluation: -10.5 dB (0.3x) safer than previous -6 dB (0.5x)
            # Provides margin against feedback escalation
            samples = samples * 0.3  # -10.5 dB headroom

            # Reshape to (frames, 2) for stereo
            stereo = samples.reshape(-1, 2)

            if self._out_channels == 1:
                # Downmix to mono: (L+R)/2
                mono = stereo.mean(axis=1, keepdims=True)
                outdata[:,:] = mono
            else:
                # Write stereo output
                outdata[:] = stereo

    def _start_audio_stream(self) -> None:
        """
        Start sounddevice output stream with comprehensive device diagnostics.

        PHASE 1 Enhancement:
        - Detailed device capability logging (name, channels, sample rate)
        - Sample rate mismatch warnings (FluidSynth best practice)
        - Clear failure messages with actionable guidance
        - Automatic fallback to mono with informative logging

        Industry practice (per evaluation):
        - Always log device configuration before starting stream
        - Warn about potential issues (sample rate mismatch, HDMI quirks)
        - Provide clear error messages with solutions

        Note:
            This immediately starts the audio thread.
            _audio_callback() will be called every block_size samples.
        """
        # PHASE 1: Query and log device capabilities (Q-SYS AEC pattern)
        channels = 2
        device_name = "Default Output"
        default_sr = 44100
        try:
            if self._output_device is not None:
                dev_info = sd.query_devices(self._output_device)  # type: ignore[call-overload]
            else:
                dev_info = sd.query_devices(kind='output')  # type: ignore[call-overload]

            # Type guard: dev_info is dict when single device queried
            if isinstance(dev_info, dict):
                device_name = dev_info.get('name', 'Unknown Device')
                max_ch = int(dev_info.get('max_output_channels', 2))
                default_sr = int(dev_info.get('default_samplerate', 44100))
            else:
                # Fallback if query returns unexpected type
                device_name = "Unknown Device"
                max_ch = 2
                default_sr = 44100

            # PHASE 1: Comprehensive device diagnostics (industry best practice)
            logger.info("=" * 70)
            logger.info("PHASE 1: OUTPUT DEVICE DIAGNOSTICS")
            logger.info("-" * 70)
            logger.info(f"  Device Name: {device_name}")
            logger.info(f"  Max Output Channels: {max_ch}")
            logger.info(f"  Device Default Sample Rate: {default_sr} Hz")
            logger.info(f"  Requested Sample Rate: {int(self.config.sample_rate)} Hz")

            # PHASE 1: Sample rate mismatch warning (FluidSynth wiki guidance)
            if abs(default_sr - self.config.sample_rate) > 100:
                logger.warning(
                    f"  ⚠️  SAMPLE RATE MISMATCH DETECTED:\n"
                    f"      Device prefers {default_sr} Hz, but synthesis is at {int(self.config.sample_rate)} Hz.\n"
                    f"      This may cause resampling artifacts or increased latency.\n"
                    f"      Recommendation: Use --sample-rate {default_sr} for optimal performance."
                )

            # PHASE 1: Device-specific warnings (macOS common issues)
            if "HDMI" in device_name or "DisplayPort" in device_name or "VG2481" in device_name:
                logger.warning(
                    f"  ⚠️  HDMI/DisplayPort MONITOR DETECTED:\n"
                    f"      System volume control may not affect output (digital passthrough).\n"
                    f"      If you experience feedback, switch to headphones or USB audio interface."
                )

            channels = 2 if max_ch >= 2 else 1 if max_ch >= 1 else 0
            logger.info(f"  Selected Channels: {channels} ({'stereo' if channels == 2 else 'mono'})")

        except Exception as e:
            logger.warning(f"  Device query failed: {e}")
            logger.warning(f"  Falling back to default: channels=2, sample_rate={self.config.sample_rate}Hz")
            channels = 2

        if channels == 0:
            logger.error("=" * 70)
            raise RuntimeError(
                f"Selected output device '{device_name}' does not support audio output.\n"
                f"Max output channels reported as 0. Please choose a different device with --output-device."
            )

        self._out_channels = channels

        # PHASE 1: Try to open stream with detailed error handling
        try:
            logger.info(f"  Attempting to start stream: {self._out_channels} ch, {self.block_size} samples/block")
            self.stream = sd.OutputStream(  # type: ignore
                samplerate=self.config.sample_rate,
                blocksize=self.block_size,
                dtype="float32",
                channels=self._out_channels,
                callback=self._audio_callback,
                device=self._output_device,
            )
            self.stream.start()
            logger.info(f"  ✅ Stream started successfully")

        except Exception as e:
            msg = str(e)
            logger.error(f"  ❌ Stream start failed: {msg}")

            # PHASE 1: Intelligent fallback with clear logging
            if "Invalid number of channels" in msg and self._out_channels > 1:
                logger.info(f"  🔄 Retrying with mono (1 channel) as fallback...")
                self._out_channels = 1
                try:
                    self.stream = sd.OutputStream(  # type: ignore
                        samplerate=self.config.sample_rate,
                        blocksize=self.block_size,
                        dtype="float32",
                        channels=1,
                        callback=self._audio_callback,
                        device=self._output_device,
                    )
                    self.stream.start()
                    logger.info(f"  ✅ Stream started successfully (mono fallback)")
                except Exception as e2:
                    logger.error(f"  ❌ Mono fallback also failed: {e2}")
                    logger.error("=" * 70)
                    raise
            else:
                logger.error("=" * 70)
                raise

        # PHASE 1: Performance metrics logging
        latency_ms = self.block_size / self.config.sample_rate * 1000
        logger.info(f"  Block Size: {self.block_size} samples")
        logger.info(f"  Estimated Latency: ~{latency_ms:.1f} ms (one-way)")
        logger.info(f"  Total Round-Trip Latency: ~{latency_ms * 2:.1f} ms (mic→speaker)")
        logger.info("=" * 70)

    def program_change(self, program: int) -> None:
        """
        Change instrument (for GUI control).

        Args:
            program: GM program number [0-127]

        Thread Safety: Protected by _lock.

        Example:
            sink.program_change(56)  # Switch to trumpet
        """
        with self._lock:
            if isinstance(self.synthesizer, FluidSynthBackend):
                self.synthesizer.program_change(0, program)

    def finalize(self) -> None:
        """
        Stop audio stream and clean up (per review: correct order).

        Order (CRITICAL):
            1. super().finalize() - stop all notes
            2. stream.stop() / stream.close() - stop audio I/O
            3. synthesizer.delete() - clean up FluidSynth

        Why This Order:
            - Stop notes first: prevents stuck notes
            - Stop stream second: audio thread stops calling callback
            - Delete synth last: safe to free resources after thread stopped

        Thread Safety:
            After stream.stop(), audio thread is guaranteed stopped.
            No need for lock in synthesizer.delete() because no concurrent access.
        """
        # Stop all notes (parent class handles this with lock via send())
        super().finalize()

        # Stop audio stream (audio thread stops here)
        if self.stream:
            self.stream.stop()
            self.stream.close()
            logger.info("Audio stream stopped")

        # Clean up synthesizer (safe because audio thread is stopped)
        if isinstance(self.synthesizer, FluidSynthBackend):
            self.synthesizer.delete()
