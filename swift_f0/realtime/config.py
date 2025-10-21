"""
Configuration management for real-time processing.

This module handles loading and validation of configuration parameters
from the central config file.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class AudioConfig:
    """Audio I/O configuration."""
    backend: str = "sounddevice"
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 256
    device_in: Optional[int] = None
    device_out: Optional[int] = None


@dataclass
class BufferConfig:
    """Buffer configuration."""
    size: int = 8192
    read_ahead: int = 512


@dataclass
class PitchConfig:
    """Pitch detection configuration."""
    window_size: int = 1024
    hop_size: int = 256
    confidence_threshold: float = 0.85
    min_frequency: float = 80.0
    max_frequency: float = 800.0


@dataclass
class SynthesisConfig:
    """Synthesis configuration."""
    method: str = "soundfont"
    soundfont_path: str = "soundfonts/GeneralUser-GS.sf2"
    default_instrument: int = 0
    volume: float = 0.8
    simple_waveform: str = "sine"
    simple_harmonics: int = 3


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    latency_mode: str = "balanced"
    thread_priority: str = "high"
    cpu_limit: int = 50


@dataclass
class DebugConfig:
    """Debug configuration."""
    enable_stats: bool = True
    stats_interval: float = 1.0
    bypass_synthesis: bool = False
    save_recordings: bool = False
    recording_path: str = "recordings/"


@dataclass
class RealtimeConfig:
    """Complete real-time configuration."""
    audio: AudioConfig = field(default_factory=AudioConfig)
    buffer: BufferConfig = field(default_factory=BufferConfig)
    pitch_detection: PitchConfig = field(default_factory=PitchConfig)
    synthesis: SynthesisConfig = field(default_factory=SynthesisConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)

    # Computed properties
    @property
    def latency_ms(self) -> float:
        """Calculate expected latency in milliseconds."""
        # Input chunk + window + processing + output
        chunk_latency = (self.audio.chunk_size / self.audio.sample_rate) * 1000
        window_latency = (self.pitch_detection.window_size / self.audio.sample_rate) * 1000
        return chunk_latency + window_latency

    @property
    def soundfont_absolute_path(self) -> str:
        """Get absolute path to soundfont file."""
        # If already absolute, return as is
        if os.path.isabs(self.synthesis.soundfont_path):
            return self.synthesis.soundfont_path

        # Otherwise, resolve relative to project root
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / self.synthesis.soundfont_path)


class ConfigManager:
    """Manages loading and validation of configuration."""

    DEFAULT_CONFIG_PATH = "config/realtime_config.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file (uses default if None)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = RealtimeConfig()
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file."""
        # Find config file
        config_file = self._find_config_file()

        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = yaml.safe_load(f)

                # Parse configuration sections
                if 'audio' in data:
                    self.config.audio = AudioConfig(**data['audio'])

                if 'buffer' in data:
                    self.config.buffer = BufferConfig(**data['buffer'])

                if 'pitch_detection' in data:
                    self.config.pitch_detection = PitchConfig(**data['pitch_detection'])

                if 'synthesis' in data:
                    syn_data = data['synthesis']
                    # Handle nested simple synthesis config
                    simple_config = syn_data.pop('simple', {})
                    self.config.synthesis = SynthesisConfig(
                        **syn_data,
                        simple_waveform=simple_config.get('waveform', 'sine'),
                        simple_harmonics=simple_config.get('harmonics', 3)
                    )

                if 'performance' in data:
                    self.config.performance = PerformanceConfig(**data['performance'])

                if 'debug' in data:
                    self.config.debug = DebugConfig(**data['debug'])

                print(f"Configuration loaded from: {config_file}")

            except Exception as e:
                print(f"Error loading config file: {e}")
                print("Using default configuration")
        else:
            print(f"Config file not found: {self.config_path}")
            print("Using default configuration")

    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in various locations."""
        # Try multiple locations
        project_root = Path(__file__).parent.parent.parent
        search_paths = [
            Path(self.config_path),  # As given
            project_root / self.config_path,  # Relative to project root
            Path.cwd() / self.config_path,  # Relative to current directory
        ]

        for path in search_paths:
            if path.exists():
                return str(path)

        return None

    def validate(self) -> bool:
        """
        Validate configuration parameters.

        Returns:
            True if configuration is valid
        """
        errors = []

        # Audio validation
        if self.config.audio.sample_rate != 16000:
            errors.append("Sample rate must be 16000 Hz for SwiftF0")

        if self.config.audio.channels not in [1, 2]:
            errors.append("Channels must be 1 (mono) or 2 (stereo)")

        # Pitch detection validation
        if self.config.pitch_detection.window_size < self.config.pitch_detection.hop_size:
            errors.append("Window size must be >= hop size")

        if self.config.pitch_detection.confidence_threshold < 0 or \
           self.config.pitch_detection.confidence_threshold > 1:
            errors.append("Confidence threshold must be between 0 and 1")

        # Synthesis validation
        if self.config.synthesis.method == "soundfont":
            sf_path = self.config.soundfont_absolute_path
            if not os.path.exists(sf_path):
                errors.append(f"Soundfont file not found: {sf_path}")

        if self.config.synthesis.volume < 0 or self.config.synthesis.volume > 1:
            errors.append("Volume must be between 0 and 1")

        # Print errors if any
        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    def get_config(self) -> RealtimeConfig:
        """Get the current configuration."""
        return self.config

    def update(self, section: str, **kwargs):
        """
        Update configuration parameters.

        Args:
            section: Configuration section ('audio', 'buffer', etc.)
            **kwargs: Parameters to update
        """
        if hasattr(self.config, section):
            config_section = getattr(self.config, section)
            for key, value in kwargs.items():
                if hasattr(config_section, key):
                    setattr(config_section, key, value)
                else:
                    print(f"Warning: Unknown parameter '{key}' in section '{section}'")
        else:
            print(f"Warning: Unknown configuration section '{section}'")

    def save(self, path: Optional[str] = None):
        """
        Save current configuration to file.

        Args:
            path: Path to save configuration (uses original path if None)
        """
        save_path = path or self.config_path

        # Convert to dictionary
        config_dict = {
            'audio': self.config.audio.__dict__,
            'buffer': self.config.buffer.__dict__,
            'pitch_detection': self.config.pitch_detection.__dict__,
            'synthesis': {
                'method': self.config.synthesis.method,
                'soundfont_path': self.config.synthesis.soundfont_path,
                'default_instrument': self.config.synthesis.default_instrument,
                'volume': self.config.synthesis.volume,
                'simple': {
                    'waveform': self.config.synthesis.simple_waveform,
                    'harmonics': self.config.synthesis.simple_harmonics
                }
            },
            'performance': self.config.performance.__dict__
        }

        # Save to file
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
            print(f"Configuration saved to: {save_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")


# Global configuration instance
_config_manager = None


def get_config() -> RealtimeConfig:
    """Get global configuration instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()


def load_config(path: Optional[str] = None) -> RealtimeConfig:
    """Load configuration from file."""
    global _config_manager
    _config_manager = ConfigManager(path)
    return _config_manager.get_config()