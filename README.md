# Golf ball ID

Can you tell which golf ball was hit (Pro V1, TP5, a distance ball...) from launch monitor data and the sound of impact?

**Status:** data pipeline built and tested; collecting MVP data (Pro V1 vs distance ball, 7 iron).

## Approach
- **Data:** Foresight GC3 launch and club data plus impact audio recorded on every shot, collected under a randomised block design.
- **Storage:** one lossless FLAC clip per shot, indexed in a validated Parquet table that links audio, labels, launch data and recording conditions. Versioned with DVC.
- **Modelling (next):** hierarchical classification (construction → spin family → model), evaluated with session grouped cross validation.

Key decisions and known limitations are logged in [`docs/decisions.md`](docs/decisions.md).

## Layout
```
src/golfball/   config, shot plan, audio splitting, schema, ingestion
scripts/        make_plan.py (before a session), build_index.py (after)
tests/          pytest suite using synthetic sessions
docs/           decision log and collection protocol
data/           raw (immutable) and processed (regenerable); DVC tracked
```

## Run
```bash
pip install -e ".[dev]"
pytest
python scripts/make_plan.py 2026-11-15_01 --club 7i --models prov1 distance_ball
# ...hit the session, drop gc3.csv and recording.wav into data/raw/2026-11-15_01/
python scripts/build_index.py
```
