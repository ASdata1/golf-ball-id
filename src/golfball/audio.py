"""Split one continuous session recording into per-shot FLAC clips (D5, D6)."""
import hashlib
from pathlib import Path

import numpy as np
import soundfile as sf

from golfball import config


def load_mono(path: Path) -> tuple[np.ndarray, int]:
    """Read audio as float32 mono. Refuses the wrong sample rate rather than resampling silently."""
    audio, sr = sf.read(path, dtype="float32", always_2d=True)
    if sr != config.SAMPLE_RATE:
        raise ValueError(f"{path}: expected {config.SAMPLE_RATE} Hz, got {sr} Hz")
    return audio.mean(axis=1), sr


def detect_onsets(audio: np.ndarray, sr: int,
                  threshold: float = config.ONSET_THRESHOLD,
                  min_gap_s: float = config.MIN_GAP_S) -> np.ndarray:
    """Sample indices of impacts: first sample above threshold * peak, then a dead time of min_gap_s.

    Deliberately simple. Impacts are by far the loudest transients in a
    session, so an amplitude threshold works; anything subtler is a later iteration.
    """
    env = np.abs(audio)
    above = np.flatnonzero(env >= threshold * env.max())
    onsets, last = [], -np.inf
    min_gap = int(min_gap_s * sr)
    for i in above:
        if i - last >= min_gap:
            onsets.append(i)
            last = i
    return np.array(onsets, dtype=int)


def cut_clip(audio: np.ndarray, sr: int, onset: int) -> np.ndarray:
    """Fixed-length window around an onset, zero padded at the recording edges."""
    pre, post = int(config.CLIP_PRE_S * sr), int(config.CLIP_POST_S * sr)
    clip = np.zeros(pre + post, dtype=np.float32)
    start, end = onset - pre, onset + post
    src = audio[max(start, 0):min(end, len(audio))]
    offset = max(0, -start)
    clip[offset:offset + len(src)] = src
    return clip


def write_flac(clip: np.ndarray, sr: int, path: Path) -> str:
    """Write a lossless 24-bit FLAC and return its SHA-256 so the index can detect tampering or corruption."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, clip, sr, format="FLAC", subtype="PCM_24")
    return hashlib.sha256(path.read_bytes()).hexdigest()
