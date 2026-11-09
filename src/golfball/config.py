"""Single source of truth for paths, audio settings and the GC3 column mapping."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
CLIPS_DIR = PROCESSED_DIR / "audio"
INDEX_PATH = PROCESSED_DIR / "shots.parquet"

# Audio storage format (D5). Impact transients carry energy up to ~20 kHz, so 48 kHz.
SAMPLE_RATE = 48_000
CLIP_PRE_S = 0.05   # seconds kept before the impact onset
CLIP_POST_S = 0.45  # seconds kept after it (captures the ring down)
MIN_GAP_S = 3.0     # two real shots are never closer than this
ONSET_THRESHOLD = 0.2  # fraction of the session's peak amplitude

# Ball models in the study. MVP compares two very different balls first (D9).
BALL_MODELS = ["prov1", "prov1x", "tp5", "tp5x", "chrome_tour", "srixon_zstar",
               "srixon_soft_feel", "distance_ball"]

# GC3 export -> our column names. Foresight software versions name columns
# differently (L6), so only this dict should need editing.
GC3_COLUMNS = {
    "Ball Speed": "ball_speed_mph",
    "Launch Angle": "launch_deg",
    "Side Angle": "side_deg",
    "Total Spin": "total_spin_rpm",
    "Back Spin": "back_spin_rpm",
    "Side Spin": "side_spin_rpm",
    "Spin Axis": "spin_axis_deg",
    "Carry": "carry_yd",
    "Club Speed": "club_speed_mph",
    "Smash Factor": "smash",
    "Angle of Attack": "aoa_deg",
    "Club Path": "club_path_deg",
}

# Calculated by GC3 software from launch data, identical physics for every ball,
# so they carry no ball-specific signal and are excluded from features (D2).
GC3_CALCULATED_EXCLUDE = ["Peak Height", "Descent Angle", "Total", "Offline", "Hang Time"]
