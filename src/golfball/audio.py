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
                  min_gap_s: float = config.MIN_GAP_ONSET_S) -> np.ndarray:
    """Candidate sound events: first sample above threshold * peak, then a dead time of min_gap_s.

    Deliberately over-sensitive. Ball drops and voices get picked up too;
    align_to_shots() uses the GC3 timestamps to choose the real impacts (D15).
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


def align_to_shots(audio: np.ndarray, sr: int, onsets: np.ndarray, shot_times_s: np.ndarray,
                   tol_s: float = config.ALIGN_TOLERANCE_S) -> np.ndarray:
    """Pick one onset per GC3 shot by matching the rhythm of shots, not just their count.

    The phone and GC3 clocks differ by an unknown offset, so every (onset, shot)
    pairing is tried as the offset. The offset that matches the most shots, with
    the smallest timing error, wins. Within each shot's window the loudest
    candidate is the impact. Raises if any shot has no impact near it.
    """
    from golfball.ingest import AlignmentError  # local import avoids a cycle
    t = onsets / sr
    shot_times_s = np.asarray(shot_times_s, dtype=float)
    best = None
    for offset in {round(o - s, 2) for o in t for s in shot_times_s}:
        err = np.abs(t[None, :] - (shot_times_s[:, None] + offset)).min(axis=1)
        score = ((err <= tol_s).sum(), -err[err <= tol_s].sum())
        if best is None or score > best[0]:
            best = (score, offset)
    offset = best[1]
    loud = np.array([np.abs(audio[o:o + int(0.05 * sr)]).max() for o in onsets])
    picked = []
    for i, st in enumerate(shot_times_s):
        near = np.flatnonzero(np.abs(t - (st + offset)) <= tol_s)
        if len(near) == 0:
            raise AlignmentError(f"no impact within {tol_s}s of GC3 shot {i + 1}")
        picked.append(onsets[near[np.argmax(loud[near])]])
    return np.array(picked)


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
