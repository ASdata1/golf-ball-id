"""Generate a randomised shot plan so ball labels never depend on memory (D7, D4)."""
import numpy as np
import pandas as pd

PLAN_COLUMNS = ["shot_no", "block", "ball_model", "ball_id", "club",
                "impact_zone", "valid", "notes"]


def make_shot_plan(models: list[str], club: str, n_blocks: int,
                   balls_per_model: int = 3, seed: int = 0) -> pd.DataFrame:
    """Permuted-block design: every block hits each model once, in random order.

    Interleaving models within a block stops warm-up, fatigue and swing drift
    from lining up with a ball model. Physical balls (ball_id) rotate so no
    single ball's wear or manufacturing variance stands in for its model.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for block in range(n_blocks):
        for model in rng.permutation(models):
            unit = chr(ord("a") + block % balls_per_model)
            rows.append({"block": block, "ball_model": model,
                         "ball_id": f"{model}_{unit}", "club": club})
    plan = pd.DataFrame(rows)
    plan.insert(0, "shot_no", range(1, len(plan) + 1))
    # Filled in by hand during the session.
    plan["impact_zone"] = ""   # centre / heel / toe / high / low (L2)
    plan["valid"] = True       # set False for duffs or GC3 misreads
    plan["notes"] = ""
    return plan[PLAN_COLUMNS]


def make_session_plan(models: list[str], segments: dict[str, int],
                      balls_per_model: int = 3, seed: int = 0) -> pd.DataFrame:
    """Split-plot plan (D17): each club is a segment of consecutive shots (the whole plot),
    segment order is randomised, and balls are randomised in permuted blocks inside each
    segment (the sub plot). Physical ball units are shuffled, not rotated in a fixed
    pattern, which fixes L11.

    segments maps club -> number of blocks, e.g. {"sw": 16, "7i": 8}.
    """
    rng = np.random.default_rng(seed)
    clubs = list(segments)
    rng.shuffle(clubs)
    parts, block_offset = [], 0
    for club in clubs:
        part = make_shot_plan(models, club, segments[club], balls_per_model,
                              seed=int(rng.integers(2**32)))
        for model in models:  # balanced but random ball unit assignment
            idx = part.index[part.ball_model == model]
            units = np.resize([chr(ord("a") + u) for u in range(balls_per_model)], len(idx))
            part.loc[idx, "ball_id"] = [f"{model}_{u}" for u in rng.permutation(units)]
        part["block"] += block_offset
        block_offset = part["block"].max() + 1
        parts.append(part)
    plan = pd.concat(parts, ignore_index=True)
    plan["shot_no"] = range(1, len(plan) + 1)
    return plan[PLAN_COLUMNS]
