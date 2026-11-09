import numpy as np
import pytest
import soundfile as sf

from golfball import audio, config
from conftest import IMPACT_TIMES_S, fake_recording

SR = config.SAMPLE_RATE


def test_detects_every_impact_once_at_the_right_time():
    onsets = audio.detect_onsets(fake_recording(IMPACT_TIMES_S), SR)
    np.testing.assert_allclose(onsets / SR, IMPACT_TIMES_S, atol=0.005)


def test_ring_down_is_not_counted_as_a_second_event():
    # Two clicks 0.5 s apart are within MIN_GAP_ONSET_S, so only the first counts.
    assert len(audio.detect_onsets(fake_recording([2.0, 2.5]), SR)) == 1


def test_alignment_picks_impacts_and_ignores_other_sounds():
    rec = fake_recording(IMPACT_TIMES_S, quiet_s=[0.5, 9.0, 20.0])
    candidates = audio.detect_onsets(rec, SR)
    assert len(candidates) > len(IMPACT_TIMES_S)  # extra sounds were detected...
    gc3_times = np.array(IMPACT_TIMES_S) - IMPACT_TIMES_S[0]  # different clock, same gaps
    picked = audio.align_to_shots(rec, SR, candidates, gc3_times)
    np.testing.assert_allclose(picked / SR, IMPACT_TIMES_S, atol=0.005)  # ...but only impacts kept


def test_alignment_fails_when_a_gc3_shot_has_no_impact():
    from golfball.ingest import AlignmentError
    rec = fake_recording(IMPACT_TIMES_S[:3])
    gc3_times = np.array(IMPACT_TIMES_S) - IMPACT_TIMES_S[0]
    with pytest.raises(AlignmentError, match="no impact"):
        audio.align_to_shots(rec, SR, audio.detect_onsets(rec, SR), gc3_times)


def test_clip_length_is_fixed_even_at_recording_edges():
    rec = fake_recording([0.01])
    expected = int((config.CLIP_PRE_S + config.CLIP_POST_S) * SR)
    assert len(audio.cut_clip(rec, SR, 0)) == expected
    assert len(audio.cut_clip(rec, SR, len(rec) - 1)) == expected


def test_flac_roundtrip_is_lossless_and_hash_is_stable(tmp_path):
    clip = audio.cut_clip(fake_recording([1.0]), SR, int(1.0 * SR))
    h1 = audio.write_flac(clip, SR, tmp_path / "a.flac")
    h2 = audio.write_flac(clip, SR, tmp_path / "b.flac")
    back, _ = sf.read(tmp_path / "a.flac", dtype="float32")
    assert h1 == h2 and len(h1) == 64
    np.testing.assert_allclose(back, clip, atol=2 ** -22)  # 24-bit quantisation only


def test_wrong_sample_rate_is_rejected(tmp_path):
    sf.write(tmp_path / "x.wav", np.zeros(44100, dtype=np.float32), 44100)
    with pytest.raises(ValueError, match="expected 48000"):
        audio.load_mono(tmp_path / "x.wav")
