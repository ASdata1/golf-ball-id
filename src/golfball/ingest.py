"""Turn one raw session folder into validated shot index rows plus FLAC clips.

Expected raw layout (read only, never edited after the session):
    data/raw/<session_id>/
        session.yaml    mic_id, mic_distance_m, environment, temp_c, notes
        recording.wav   one continuous recording of the whole session
        gc3.csv         Foresight export, one row per shot
        plan.csv        shot plan from scripts/make_plan.py, with manual columns filled in
"""
from pathlib import Path

import pandas as pd
import yaml

from golfball import audio, config
from golfball.schema import SHOT_INDEX


class AlignmentError(ValueError):
    """Shot counts disagree between plan, GC3 export and detected impacts."""


def load_gc3(path: Path) -> pd.DataFrame:
    """Read a GC3 export, keep only measured columns and rename them (D2)."""
    df = pd.read_csv(path)
    df = df.drop(columns=[c for c in config.GC3_CALCULATED_EXCLUDE if c in df.columns])
    missing = set(config.GC3_COLUMNS) - set(df.columns)
    if missing:
        raise KeyError(f"{path}: GC3 columns not found {sorted(missing)}; update config.GC3_COLUMNS")
    return df[list(config.GC3_COLUMNS)].rename(columns=config.GC3_COLUMNS).astype(float)


def ingest_session(session_dir: Path, clips_dir: Path = config.CLIPS_DIR) -> pd.DataFrame:
    """Align plan, GC3 rows and audio onsets by order; refuse to guess if counts differ (D6)."""
    session_id = session_dir.name
    meta = yaml.safe_load((session_dir / "session.yaml").read_text())
    plan = pd.read_csv(session_dir / "plan.csv", keep_default_na=False)
    gc3 = load_gc3(session_dir / "gc3.csv")
    rec, sr = audio.load_mono(session_dir / "recording.wav")
    onsets = audio.detect_onsets(rec, sr)

    counts = {"plan": len(plan), "gc3": len(gc3), "onsets": len(onsets)}
    if len(set(counts.values())) != 1:
        raise AlignmentError(f"{session_id}: shot counts differ {counts}")

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
