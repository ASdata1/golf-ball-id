from golfball.plan import make_shot_plan

MODELS = ["prov1", "tp5", "distance_ball"]


def test_every_block_contains_each_model_exactly_once():
    plan = make_shot_plan(MODELS, "7i", n_blocks=10)
    assert (plan.groupby("block").ball_model.apply(sorted).apply(tuple) == tuple(sorted(MODELS))).all()


def test_order_is_actually_randomised_across_blocks():
    plan = make_shot_plan(MODELS, "7i", n_blocks=10)
    orders = plan.groupby("block").ball_model.apply(tuple)
    assert orders.nunique() > 1


def test_physical_balls_rotate_and_seed_is_reproducible():
    plan = make_shot_plan(MODELS, "7i", n_blocks=6, balls_per_model=3, seed=1)
    assert plan[plan.ball_model == "prov1"].ball_id.nunique() == 3
    assert plan.equals(make_shot_plan(MODELS, "7i", n_blocks=6, balls_per_model=3, seed=1))


def test_session_plan_keeps_clubs_contiguous_and_balances_balls():
    from golfball.plan import make_session_plan
    plan = make_session_plan(["tp5", "srixon_soft_feel"], {"sw": 16, "7i": 8}, seed=3)
    assert len(plan) == 48 and plan.shot_no.tolist() == list(range(1, 49))
    assert (plan.club != plan.club.shift()).sum() == 2  # exactly one switch between clubs
    for _, seg in plan.groupby("club"):
        counts = seg.ball_id.value_counts()
        assert counts.max() - counts.min() <= 1  # units balanced within each club
    assert plan.block.is_monotonic_increasing


def test_session_plan_club_order_varies_with_seed():
    from golfball.plan import make_session_plan
    firsts = {make_session_plan(["tp5"], {"sw": 2, "7i": 2}, seed=s).club.iloc[0] for s in range(20)}
    assert firsts == {"sw", "7i"}
