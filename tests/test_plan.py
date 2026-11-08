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
