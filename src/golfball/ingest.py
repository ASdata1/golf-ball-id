"""Turn one raw session folder into validated shot index rows plus FLAC clips.

Expected raw layout (read only, never edited after the session):
    data/raw/<session_id>/
        session.yaml    mic_id, mic_distance_m, environment, temp_c, notes
        recording.wav   one continuous recording of the whole session
        gc3.csv         Foresight export, one row per shot
        plan.csv        shot plan from scripts/make_plan.py, with manual columns filled in
"""
import io
from pathlib import Path

import pandas as pd
import yaml

from golfball import audio, config
from golfball.schema import SHOT_INDEX


class AlignmentError(ValueError):
    """Shot counts disagree between plan, GC3 export and detected impacts."""


def _signed(value) -> float:
    """'6.3 R' -> 6.3, '118 L' -> -118, '4.5 DN' -> -4.5, '' -> NaN."""
    parts = str(value).split()
    if not parts or parts[0] == "nan":
        return float("nan")
    return float(parts[0]) * (config.GC3_SIGN[parts[1]] if len(parts) > 1 else 1)


def load_gc3(path: Path) -> pd.DataFrame:
    """Read a Foresight session export, which has one section per club: a club label
    row, a header row, shot rows, then an Average row. Drops calculated columns (D2),
    turns direction suffixes into signs, adds club and shot_time_s, sorts by time."""
    lines = path.read_text().splitlines()
    starts = [i for i, l in enumerate(lines) if l.startswith(",Date,")]
    if not starts:
        raise KeyError(f"{path}: no Foresight header row found")
    sections = []
    for i in starts:
        club = lines[i - 1].split(",")[0].strip()
        body = [lines[i]]
        for l in lines[i + 1:]:
            if not l.split(",")[0].strip().isdigit():
                break  # Average row, blank line or next club label
            body.append(l)
        sec = pd.read_csv(io.StringIO("\n".join(body)), dtype=str).rename(columns=str.strip)
        sec["club_gc3"] = club
        sections.append(sec)
    df = pd.concat(sections, ignore_index=True)
    missing = set(config.GC3_COLUMNS) - set(df.columns)
    if missing:
        raise KeyError(f"{path}: GC3 columns not found {sorted(missing)}; update config.GC3_COLUMNS")
    out = df[list(config.GC3_COLUMNS)].map(_signed).rename(columns=config.GC3_COLUMNS)
    clock = pd.to_datetime(df["Date"] + " " + df["Time"].str.extract(r"(\d+:\d+:\d+ [AP]M)")[0],
                           format="%m/%d/%Y %I:%M:%S %p")
    out["club_gc3"] = df["club_gc3"]
    out["shot_time_s"] = (clock - clock.min()).dt.total_seconds()
    return out.sort_values("shot_time_s", kind="stable").reset_index(drop=True)


def ingest_session(session_dir: Path, clips_dir: Path = config.CLIPS_DIR) -> pd.DataFrame:
    """Match plan rows to GC3 rows by order, and GC3 rows to audio impacts by timestamp (D6, D15)."""
    session_id = session_dir.name
    meta = yaml.safe_load((session_dir / "session.yaml").read_text())
    plan = pd.read_csv(session_dir / "plan.csv", keep_default_na=False)
    gc3 = load_gc3(session_dir / "gc3.csv")
    rec, sr = audio.load_mono(session_dir / "recording.wav")
    if len(plan) != len(gc3):
        raise AlignmentError(f"{session_id}: shot counts differ plan={len(plan)} gc3={len(gc3)}")
    plan_clubs, gc3_clubs = plan.club.str.lower().tolist(), gc3.club_gc3.str.lower().tolist()
    if plan_clubs != gc3_clubs:
        bad = next(i for i, (p, g) in enumerate(zip(plan_clubs, gc3_clubs)) if p != g)
        raise AlignmentError(f"{session_id}: club order differs from shot {bad + 1} "
                             f"(plan {plan_clubs[bad]}, GC3 {gc3_clubs[bad]})")
    onsets = audio.align_to_shots(rec, sr, audio.detect_onsets(rec, sr), gc3.shot_time_s.to_numpy())

    rows = []
    for (_, p), (_, g), onset in zip(plan.iterrows(), gc3.iterrows(), onsets):
        shot_id = f"{session_id}_{int(p.shot_no):04d}"
        clip_path = clips_dir / session_id / f"{shot_id}.flac"
        sha = audio.write_flac(audio.cut_clip(rec, sr, onset), sr, clip_path)
        rows.append({
            "shot_id": shot_id, "session_id": session_id, "shot_no": int(p.shot_no),
            "ball_model": p.ball_model, "ball_id": p.ball_id, "club": p.club,
            "impact_zone": p.impact_zone or None,
            "valid": str(p.valid).strip().lower() in ("true", "1", "yes"),
            "audio_path": str(clip_path.relative_to(clips_dir.parent)),
            "audio_sha256": sha, "sample_rate": sr, "onset_s": onset / sr,
            "mic_id": meta["mic_id"], "mic_distance_m": float(meta["mic_distance_m"]),
            "environment": meta["environment"], "temp_c": meta.get("temp_c"),
            **g.to_dict(),
        })
    return SHOT_INDEX.validate(pd.DataFrame(rows))


def build_index(raw_dir: Path = config.RAW_DIR, out_path: Path = config.INDEX_PATH) -> pd.DataFrame:
    """Rebuild the full index from every raw session. Processed data is always regenerable from raw."""
    sessions = sorted(d for d in raw_dir.iterdir() if (d / "session.yaml").exists())
    index = SHOT_INDEX.validate(pd.concat([ingest_session(s, out_path.parent / "audio") for s in sessions],
                                          ignore_index=True))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    index.to_parquet(out_path, index=False)
    return index
