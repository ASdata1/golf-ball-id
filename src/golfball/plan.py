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
