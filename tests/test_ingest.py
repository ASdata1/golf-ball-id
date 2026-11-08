import pandas as pd
import pandera.errors
import pytest

from golfball import config
from golfball.ingest import AlignmentError, build_index, ingest_session


def test_session_becomes_one_validated_row_per_shot(session_dir, tmp_path):
    df = ingest_session(session_dir, tmp_path / "clips")
    assert len(df) == 4 and df.shot_id.is_unique
    assert (tmp_path / df.audio_path.iloc[0]).exists()


def test_calculated_gc3_metrics_never_reach_the_index(session_dir, tmp_path):
    df = ingest_session(session_dir, tmp_path / "clips")
    assert "Peak Height" not in df.columns and "peak_height" not in df.columns


def test_count_mismatch_fails_loudly_instead_of_guessing(session_dir, tmp_path):
    gc3 = pd.read_csv(session_dir / "gc3.csv")
    gc3.iloc[:-1].to_csv(session_dir / "gc3.csv", index=False)  # GC3 missed a shot
    with pytest.raises(AlignmentError, match="counts differ"):
        ingest_session(session_dir, tmp_path / "clips")


def test_implausible_launch_data_is_rejected(session_dir, tmp_path):
    gc3 = pd.read_csv(session_dir / "gc3.csv")
    gc3["Total Spin"] = 50_000  # unit error or misread
    gc3.to_csv(session_dir / "gc3.csv", index=False)
    with pytest.raises(pandera.errors.SchemaError):
        ingest_session(session_dir, tmp_path / "clips")


def test_unknown_ball_label_is_rejected(session_dir, tmp_path):
    plan = pd.read_csv(session_dir / "plan.csv")
    plan.loc[0, "ball_model"] = "pro_v1"  # typo
    plan.to_csv(session_dir / "plan.csv", index=False)
    with pytest.raises(pandera.errors.SchemaError):
        ingest_session(session_dir, tmp_path / "clips")


def test_build_index_writes_parquet_that_reads_back(session_dir, tmp_path):
    out = tmp_path / "processed" / "shots.parquet"
    build_index(session_dir.parent, out)
    assert len(pd.read_parquet(out)) == 4
