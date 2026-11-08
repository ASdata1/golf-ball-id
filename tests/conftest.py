"""Synthetic session fixture: fake impacts in noise plus a matching GC3 export and plan."""
import numpy as np
import pandas as pd
import pytest
import soundfile as sf

from golfball import config
from golfball.plan import make_shot_plan

IMPACT_TIMES_S = [2.0, 7.0, 12.5, 18.0]


def fake_recording(times_s, sr=config.SAMPLE_RATE, length_s=22.0, seed=0):
    """Low noise floor with a decaying 3 kHz 'click' at each impact time."""
    rng = np.random.default_rng(seed)
    audio = rng.normal(0, 0.005, int(length_s * sr)).astype(np.float32)
    t = np.arange(int(0.2 * sr)) / sr
    click = (0.8 * np.exp(-t * 60) * np.sin(2 * np.pi * 3000 * t)).astype(np.float32)
    for ts in times_s:
        i = int(ts * sr)
        audio[i:i + len(click)] += click
    return audio


def fake_gc3(n):
    """GC3-style export with real column names, including calculated ones we must drop."""
    df = pd.DataFrame({k: np.linspace(1, 2, n) for k in config.GC3_COLUMNS})
    df["Ball Speed"], df["Launch Angle"] = 120.0, 16.0
    df["Total Spin"], df["Carry"] = 6500.0, 165.0
    df["Peak Height"] = 30.0
    return df


@pytest.fixture
def session_dir(tmp_path):
    d = tmp_path / "raw" / "2026-11-15_01"
    d.mkdir(parents=True)
    n = len(IMPACT_TIMES_S)
    sf.write(d / "recording.wav", fake_recording(IMPACT_TIMES_S), config.SAMPLE_RATE, subtype="PCM_24")
    fake_gc3(n).to_csv(d / "gc3.csv", index=False)
    make_shot_plan(["prov1", "distance_ball"], "7i", n_blocks=2).to_csv(d / "plan.csv", index=False)
    (d / "session.yaml").write_text("mic_id: test\nmic_distance_m: 1.0\nenvironment: indoor\n")
    return d
