from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional

import numpy as np


class BaseAudioSource:
    sample_rate: int
    block_size: int

    def frames(self) -> Generator[np.ndarray, None, None]:
        raise NotImplementedError

    def close(self) -> None:
        pass


@dataclass
class WavFileSource(BaseAudioSource):
    path: str
    sample_rate: int = 16000
    block_size: int = 256
    simulate_timing: bool = False

    def frames(self) -> Generator[np.ndarray, None, None]:
        """
        Stream a WAV (or any librosa-supported) file as mono float32 frames.
        If simulate_timing is True, yields in real time; otherwise as fast as possible.
        """
        p = Path(self.path)
        if not p.exists():
            raise FileNotFoundError(self.path)

        try:
            import librosa
        except ImportError as e:
            raise ImportError("WavFileSource requires librosa. pip install librosa") from e

        y, sr = librosa.load(str(p), sr=None, mono=True)
        if sr != self.sample_rate:
            y = librosa.resample(y.astype(np.float32), orig_sr=sr, target_sr=self.sample_rate)
        else:
            y = y.astype(np.float32)

        # chunking
        n = len(y)
        idx = 0
        if self.simulate_timing:
            import time
            period = self.block_size / self.sample_rate
            while idx < n:
                chunk = y[idx : idx + self.block_size]
                if len(chunk) < self.block_size:
                    pad = np.zeros(self.block_size - len(chunk), dtype=np.float32)
                    chunk = np.concatenate([chunk, pad])
                yield chunk
                idx += self.block_size
                time.sleep(period)
        else:
            while idx < n:
                chunk = y[idx : idx + self.block_size]
                if len(chunk) < self.block_size:
                    pad = np.zeros(self.block_size - len(chunk), dtype=np.float32)
                    chunk = np.concatenate([chunk, pad])
                yield chunk
                idx += self.block_size


class MicSource(BaseAudioSource):
    """
    Optional microphone source. Requires sounddevice.
    Use only when realtime capture is needed.
    """

    def __init__(self, sample_rate: int = 16000, block_size: int = 256) -> None:
        self.sample_rate = sample_rate
        self.block_size = block_size

    def frames(self) -> Generator[np.ndarray, None, None]:  # pragma: no cover (device dependent)
        import sounddevice as sd

        q: list[np.ndarray] = []

        def cb(indata, frames, time_info, status):
            if status and status.input_overflow:
                # In production, log overflow
                pass
            q.append(indata.copy().reshape(-1).astype(np.float32))

        with sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            callback=cb,
        ):
            while True:
                if q:
                    yield q.pop(0)

