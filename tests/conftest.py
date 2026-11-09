"""Synthetic session fixture: fake impacts in noise plus a matching GC3 export and plan."""
import numpy as np
import pandas as pd
import pytest
import soundfile as sf

from golfball import config
from golfball.plan import make_shot_plan

IMPACT_TIMES_S = [2.0, 7.0, 12.5, 18.0]


def fake_recording(times_s, sr=config.SAMPLE_RATE, length_s=22.0, seed=0, quiet_s=()):
    """Low noise floor with a decaying 3 kHz 'click' at each impact time,
    plus quieter clicks at quiet_s (ball drops, voices) that must be ignored."""
    rng = np.random.default_rng(seed)
    audio = rng.normal(0, 0.005, int(length_s * sr)).astype(np.float32)
    t = np.arange(int(0.2 * sr)) / sr
    click = (0.8 * np.exp(-t * 60) * np.sin(2 * np.pi * 3000 * t)).astype(np.float32)
    for ts, gain in [(t, 1.0) for t in times_s] + [(t, 0.3) for t in quiet_s]:
        i = int(ts * sr)
        audio[i:i + len(click)] += gain * click
    return audio


def write_fake_gc3(path, times_s, clock_offset_s=5000):
    """Foresight-style export: title rows, suffixed directions, an Average row,
    and a clock that is offset from the audio (only the gaps between shots agree)."""
    cols = ["", "Date", "Time", "Carry", "Total", "Peak Height", "Offline", "Ball Speed",
            "Launch Angle", "Launch Direction", "Side Spin", "Back Spin", "Total Spin",
            "Spin Axis Tilt", "Club Speed", "Smash Factor", "Angle of Attack", "Club Path"]
    lines = ["Aman Shah,Shot Analysis", "", "7i,", ",".join(cols) + ","]
    for i, t in enumerate(times_s, 1):
        secs = int(clock_offset_s + t)
        clock = f"9:{secs // 60 % 60:02d}:{secs % 60:02d} PM Greenwich Mean Time"
        lines.append(f"{i},11/09/2026,{clock},165.0,170.0,90.0,20.0 R,120.0,17.0,6.3 R,"
                     f"500 L,6000,6020,4.5 R,88.0,1.35,4.5 DN,4.6 I-O,")
    lines.append("Average,,,165.0,170.0,90.0,20.0 R,120.0,17.0,6.3 R,500 L,6000,6020,4.5 R,88.0,1.35,4.5 DN,4.6 I-O,")
    path.write_text("\n".join(lines) + "\n")


@pytest.fixture
def session_dir(tmp_path):
    d = tmp_path / "raw" / "2026-11-15_01"
    d.mkdir(parents=True)
    n = len(IMPACT_TIMES_S)
    rec = fake_recording(IMPACT_TIMES_S, quiet_s=[0.5, 9.0, 20.0])
    sf.write(d / "recording.wav", rec, config.SAMPLE_RATE, subtype="PCM_24")
    write_fake_gc3(d / "gc3.csv", IMPACT_TIMES_S)
    make_shot_plan(["prov1", "distance_ball"], "7i", n_blocks=2).to_csv(d / "plan.csv", index=False)
    (d / "session.yaml").write_text("mic_id: test\nmic_distance_m: 1.0\nenvironment: indoor\n")
    return d
