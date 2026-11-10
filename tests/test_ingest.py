import pandas as pd
import pandera.errors
import pytest

from golfball import config
from golfball.ingest import AlignmentError, build_index, ingest_session, load_gc3


def test_session_becomes_one_validated_row_per_shot(session_dir, tmp_path):
    df = ingest_session(session_dir, tmp_path / "clips")
    assert len(df) == 4 and df.shot_id.is_unique
    assert (tmp_path / df.audio_path.iloc[0]).exists()


def test_calculated_gc3_metrics_never_reach_the_index(session_dir, tmp_path):
    df = ingest_session(session_dir, tmp_path / "clips")
    assert "Peak Height" not in df.columns and "peak_height" not in df.columns


def test_gc3_parser_handles_foresight_format(session_dir):
    gc3 = load_gc3(session_dir / "gc3.csv")
    assert len(gc3) == 4  # Average row dropped
    assert gc3.side_spin_rpm.iloc[0] == -500 and gc3.aoa_deg.iloc[0] == -4.5  # L and DN are negative
    assert gc3.club_path_deg.iloc[0] == 4.6
    assert gc3.shot_time_s.iloc[0] == 0


def test_count_mismatch_fails_loudly_instead_of_guessing(session_dir, tmp_path):
    lines = (session_dir / "gc3.csv").read_text().splitlines()
    (session_dir / "gc3.csv").write_text("\n".join(lines[:-2] + lines[-1:]))  # GC3 missed a shot
    with pytest.raises(AlignmentError, match="counts differ"):
        ingest_session(session_dir, tmp_path / "clips")


def test_implausible_launch_data_is_rejected(session_dir, tmp_path):
    path = session_dir / "gc3.csv"
    path.write_text(path.read_text().replace(",6020,", ",50000,"))  # unit error or misread
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


def test_gc3_parser_reads_multiple_club_sections_in_time_order(tmp_path):
    hdr = ",Date,Time,Carry,Ball Speed,Launch Angle,Launch Direction,Side Spin,Back Spin,Total Spin,Spin Axis Tilt,Club Speed,Smash Factor,Angle of Attack,Club Path,"
    row = lambda n, t: f"{n},11/10/2026,9:{t} PM Greenwich Mean Time,50.0,60.0,30.0,1.0 R,100 L,8000,8100,1.0 R,60.0,1.0,5.0 DN,2.0 I-O,"
    text = "\n".join(["Aman Shah,Shot Analysis", "", "7i,", hdr, row(1, "10:30"), row(2, "11:00"), "Average,,,",
                      "SW,", hdr, row(1, "00:00"), row(2, "00:30"), "Average,,,"])
    (tmp_path / "gc3.csv").write_text(text)
    gc3 = load_gc3(tmp_path / "gc3.csv")
    assert gc3.club_gc3.tolist() == ["SW", "SW", "7i", "7i"]  # sorted by time, not file order
    assert gc3.shot_time_s.tolist() == [0, 30, 630, 660]
