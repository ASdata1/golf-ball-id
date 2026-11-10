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
ONSET_THRESHOLD = 0.1  # fraction of session peak; low on purpose, GC3 timestamps pick the real impacts (D15)
MIN_GAP_ONSET_S = 1.0  # dead time between candidate sounds (ring down of a single impact)

# Ball models in the study. MVP compares two very different balls first (D9).
BALL_MODELS = ["prov1", "prov1x", "tp5", "tp5x", "chrome_tour", "srixon_zstar",
               "srixon_soft_feel", "distance_ball"]

# GC3 export -> our column names. Foresight software versions name columns
# differently (L6), so only this dict should need editing.
GC3_COLUMNS = {
    "Ball Speed": "ball_speed_mph",
    "Launch Angle": "launch_deg",
    "Launch Direction": "side_deg",
    "Total Spin": "total_spin_rpm",
    "Back Spin": "back_spin_rpm",
    "Side Spin": "side_spin_rpm",
    "Spin Axis Tilt": "spin_axis_deg",
    "Carry": "carry_yd",
    "Club Speed": "club_speed_mph",
    "Smash Factor": "smash",
    "Angle of Attack": "aoa_deg",
    "Club Path": "club_path_deg",
}

# Foresight writes directions as text suffixes ("6.3 R", "4.5 DN", "4.6 I-O").
# Right, up and in-to-out are positive.
GC3_SIGN = {"R": 1, "L": -1, "UP": 1, "DN": -1, "I-O": 1, "O-I": -1}

# Calculated by GC3 software from launch data, identical physics for every ball,
# so they carry no ball-specific signal and are excluded from features (D2).
GC3_CALCULATED_EXCLUDE = ["Peak Height", "Descent Angle", "Total", "Offline", "Curve", "Hang Time"]

# Impact matching (D15): an audio impact must sit within this many seconds of
# where the GC3 timestamp says the shot happened.
ALIGN_TOLERANCE_S = 2.0
