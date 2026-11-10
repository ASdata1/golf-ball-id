"""Create plan.csv and a phone-friendly shot list for a new session.

    python scripts/make_plan.py 2026-11-11_01 --models tp5 srixon_soft_feel --segment sw:16 --segment 7i:8

Each --segment is CLUB:BLOCKS, one block = one shot with every ball model. Name each club
exactly as the GC3 software labels it, because ingestion checks the club order matches.
"""
import argparse
import zlib

from golfball import config
from golfball.plan import make_session_plan

p = argparse.ArgumentParser()
p.add_argument("session_id")
p.add_argument("--models", nargs="+", required=True, choices=config.BALL_MODELS)
p.add_argument("--segment", action="append", required=True, help="CLUB:BLOCKS, e.g. sw:16")
p.add_argument("--balls-per-model", type=int, default=3)
p.add_argument("--seed", type=int, default=None, help="defaults to a hash of session_id")
a = p.parse_args()

segments = {c: int(n) for c, n in (s.split(":") for s in a.segment)}
seed = a.seed if a.seed is not None else zlib.crc32(a.session_id.encode())
plan = make_session_plan(a.models, segments, a.balls_per_model, seed=seed)

out = config.RAW_DIR / a.session_id
out.mkdir(parents=True, exist_ok=True)
plan.to_csv(out / "plan.csv", index=False)
(out / "session.yaml").write_text(
    "mic_id: iphone_voice_memos_lossless\nmic_distance_m: 1.0\nenvironment: indoor\ntemp_c:\n"
    f"notes: ''\nplan_seed: {seed}\nsegments: {segments}\n"
)
lines = [f"# Shot list {a.session_id}", "",
         "Zone: C centre, H heel, T toe, Hi high, Lo low. X = duff or misread (still counts).", ""]
club = None
for r in plan.itertuples():
    if r.club != club:
        club = r.club
        lines += ["", f"## {club.upper()}  (change club in GC3 app now)", ""]
    lines.append(f"{r.shot_no:>2}. {r.ball_id}  [ ]  zone: ___")
(out / "shot_list.md").write_text("\n".join(lines) + "\n")
print(f"{len(plan)} shots, club order {list(dict.fromkeys(plan.club))} -> {out}")
