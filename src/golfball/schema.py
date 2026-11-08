"""Data contract for the shot index. Every row = one shot = one audio clip (D5)."""
import pandera.pandas as pa

from golfball import config

SHOT_INDEX = pa.DataFrameSchema(
    {
        "shot_id": pa.Column(str, unique=True),
        "session_id": pa.Column(str),
        "shot_no": pa.Column(int, pa.Check.ge(1)),
        "ball_model": pa.Column(str, pa.Check.isin(config.BALL_MODELS)),
        "ball_id": pa.Column(str),
        "club": pa.Column(str),
        "impact_zone": pa.Column(str, nullable=True),
        "valid": pa.Column(bool),
        "audio_path": pa.Column(str),
        "audio_sha256": pa.Column(str, pa.Check.str_length(64, 64)),
        "sample_rate": pa.Column(int, pa.Check.eq(config.SAMPLE_RATE)),
        "onset_s": pa.Column(float, pa.Check.ge(0)),
        "mic_id": pa.Column(str),
        "mic_distance_m": pa.Column(float, pa.Check.in_range(0.1, 5)),
        "environment": pa.Column(str, pa.Check.isin(["indoor", "outdoor"])),
        # Launch data: physically plausible ranges catch unit or parsing errors.
        "ball_speed_mph": pa.Column(float, pa.Check.in_range(20, 200)),
        "launch_deg": pa.Column(float, pa.Check.in_range(-10, 60)),
        "total_spin_rpm": pa.Column(float, pa.Check.in_range(0, 15000)),
        "carry_yd": pa.Column(float, pa.Check.in_range(0, 350)),
    },
    strict=False,  # other GC3 columns are allowed through
    coerce=True,
)
