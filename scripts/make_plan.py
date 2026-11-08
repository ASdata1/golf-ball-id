"""Create plan.csv for a new session. Print it or open on your phone at the range.

    python scripts/make_plan.py 2026-11-15_01 --club 7i --models prov1 distance_ball --blocks 20
"""
import argparse
import zlib

from golfball import config
from golfball.plan import make_shot_plan

p = argparse.ArgumentParser()
p.add_argument("session_id")
p.add_argument("--club", required=True)
p.add_argument("--models", nargs="+", required=True, choices=config.BALL_MODELS)
p.add_argument("--blocks", type=int, default=20)
p.add_argument("--seed", type=int, default=None, help="defaults to a hash of session_id")
a = p.parse_args()

seed = a.seed if a.seed is not None else zlib.crc32(a.session_id.encode())
out = config.RAW_DIR / a.session_id
out.mkdir(parents=True, exist_ok=True)
make_shot_plan(a.models, a.club, a.blocks, seed=seed).to_csv(out / "plan.csv", index=False)
(out / "session.yaml").write_text(
    "mic_id: phone_raw\nmic_distance_m: 1.0\nenvironment: indoor\ntemp_c:\nnotes: ''\n"
    f"plan_seed: {seed}\n"
)
print(f"Wrote plan and session.yaml template to {out}")
