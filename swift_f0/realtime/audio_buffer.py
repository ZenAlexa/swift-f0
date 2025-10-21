"""
Ring buffer implementation for real-time audio processing.

This module provides a lock-free ring buffer for efficient audio streaming.
"""

import numpy as np
from typing import Optional, Tuple
import threading


class RingBuffer:
    """
    Thread-safe ring buffer for audio data.

    Optimized for real-time audio with minimal latency.
    """

    def __init__(self, capacity: int, channels: int = 1, dtype=np.float32):
        """
        Initialize ring buffer.

        Args:
            capacity: Buffer capacity in samples
            channels: Number of audio channels
            dtype: Data type for audio samples
        """
        self.capacity = capacity
        self.channels = channels
        self.dtype = dtype

        # Allocate buffer with extra space to avoid wrapping complexity
        self.buffer = np.zeros((capacity * 2, channels), dtype=dtype)
        self.write_pos = 0
        self.read_pos = 0
        self.lock = threading.Lock()

    def write(self, data: np.ndarray) -> bool:
        """
        Write audio data to buffer.

        Args:
            data: Audio data to write [samples, channels]

        Returns:
            True if successful, False if buffer overflow
        """
        with self.lock:
            n_samples = data.shape[0]

            # Check available space
            available = self._get_available_write_space()
            if n_samples > available:
                return False  # Buffer overflow

            # Write data (handle wrap-around)
            end_pos = self.write_pos + n_samples
            if end_pos <= self.capacity:
                self.buffer[self.write_pos:end_pos] = data
            else:
                # Wrap around
                first_part = self.capacity - self.write_pos
                self.buffer[self.write_pos:self.capacity] = data[:first_part]
                self.buffer[0:n_samples - first_part] = data[first_part:]

            self.write_pos = end_pos % self.capacity
            return True

    def read(self, n_samples: int) -> Optional[np.ndarray]:
        """
        Read audio data from buffer.

        Args:
            n_samples: Number of samples to read

        Returns:
            Audio data or None if insufficient samples
        """
        with self.lock:
            available = self._get_available_read_samples()
            if n_samples > available:
                return None

            # Read data (handle wrap-around)
            end_pos = self.read_pos + n_samples
            if end_pos <= self.capacity:
                data = self.buffer[self.read_pos:end_pos].copy()
            else:
                # Wrap around
                first_part = self.capacity - self.read_pos
                data = np.concatenate([
                    self.buffer[self.read_pos:self.capacity],
                    self.buffer[0:n_samples - first_part]
                ])

            self.read_pos = end_pos % self.capacity
            return data

    def peek(self, n_samples: int) -> Optional[np.ndarray]:
        """
        Peek at audio data without consuming it.

        Args:
            n_samples: Number of samples to peek

        Returns:
            Audio data or None if insufficient samples
        """
        with self.lock:
            available = self._get_available_read_samples()
            if n_samples > available:
                return None

            # Read without advancing read position
            end_pos = self.read_pos + n_samples
            if end_pos <= self.capacity:
                return self.buffer[self.read_pos:end_pos].copy()
            else:
                # Wrap around
                first_part = self.capacity - self.read_pos
                return np.concatenate([
                    self.buffer[self.read_pos:self.capacity],
                    self.buffer[0:n_samples - first_part]
                ])

    def _get_available_write_space(self) -> int:
        """Get available space for writing."""
        if self.write_pos >= self.read_pos:
            return self.capacity - (self.write_pos - self.read_pos) - 1
        else:
            return self.read_pos - self.write_pos - 1

    def _get_available_read_samples(self) -> int:
        """Get available samples for reading."""
        if self.write_pos >= self.read_pos:
            return self.write_pos - self.read_pos
        else:
            return self.capacity - self.read_pos + self.write_pos

    def get_fill_level(self) -> float:
        """Get buffer fill level as percentage (0.0 to 1.0)."""
        with self.lock:
            return self._get_available_read_samples() / self.capacity

    def reset(self):
        """Reset buffer to empty state."""
        with self.lock:
            self.buffer.fill(0)
            self.write_pos = 0
            self.read_pos = 0