# Golf ball ID

Can you tell which golf ball was hit (Titleist Pro V1, TaylorMade TP5, Srixon Soft Feel...) from launch monitor data and the sound of impact? A self-collected dataset from a Foresight GC3 and a phone microphone, built as a designed experiment.

**Status:** pipeline working on real data · pilot session analysed · main data collection in progress

## Pilot result

First session: 24 full 7 irons, TP5 vs Srixon Soft Feel, alternating.

**The two balls were indistinguishable on every launch measure.** Back spin differed by 38 rpm (p = 0.81). After adjusting for club speed, attack angle, path and launch, the 95% interval for the difference was roughly −320 to +220 rpm, so any real difference on this shot is probably smaller than 300 rpm. Audio showed a weak hint (the Soft Feel had less high-frequency energy, d = 0.44) but nothing conclusive at 12 shots per ball.

Shot to shot spin varied by about 390 rpm, which sizes the rest of the study: about 26 shots per ball to detect a 300 rpm difference, about 100 for 150 rpm. Full write-up in [`docs/pilot_session1.md`](docs/pilot_session1.md).

**What changed because of it:** full irons are probably the wrong shot for this question, so partial wedges (where cover material matters most) are being added, and the audio setup is being fixed after the phone was found to be limiting impact loudness.

## Key decisions

All decisions and limitations are logged with reasoning in [`docs/decisions.md`](docs/decisions.md). The ones that shaped the project most:

- **Only measured data is used.** The GC3 *calculates* peak height and descent angle from launch data, using the same physics for every ball, so those columns carry no ball-specific information and are excluded.
- **Randomised block design, evaluated by session.** Balls are interleaved in random order within blocks so warm-up and fatigue can't line up with a ball, and models will be tested on sessions they never saw so they can't learn "the day" instead of "the ball".
- **A pilot first.** The first session was used to estimate variance and size the study rather than guessing.
- **Audio matched by timing, not counting.** On real data the impact detector also picked up ball drops and other sounds. Impacts are now matched to shots using the rhythm of GC3 timestamps (worst error 0.5 s across 24 shots).

## How it's built

- **Collection:** `scripts/make_plan.py` generates a randomised shot plan before each session, so ball labels never depend on memory.
- **Storage:** each session's raw recording is kept untouched. Each shot becomes a lossless 48 kHz / 24-bit FLAC clip, indexed in a Parquet table linking ball label, launch and club data, audio path, SHA-256 hash and recording conditions.
- **Validation:** a pandera schema rejects impossible values (e.g. 50,000 rpm spin), unknown ball names and mismatched shot counts before anything reaches a model.
- **Tests:** `pytest` covers the GC3 parser, impact detection and alignment, shot plan randomisation and the end-to-end ingest, using synthetic sessions.
- **Data versioning:** audio and launch data are kept out of git (DVC planned once several sessions exist).

```
src/golfball/   config, shot plan, audio processing, schema, ingestion
scripts/        make_plan.py (before a session), build_index.py (after)
tests/          pytest suite on synthetic sessions
docs/           decision log, pilot report, collection protocol
```

## Run it

```bash
pip install -e ".[dev]"
pytest
python scripts/make_plan.py 2026-11-15_01 --club 7i --models tp5 srixon_soft_feel
# hit the session, put gc3.csv and recording.wav in data/raw/2026-11-15_01/
python scripts/build_index.py
```

## What's next

1. Six more sessions with 3 balls per model and a wedge protocol, plus a better audio setup.
2. A baseline classifier on launch data, then on audio features, evaluated with leave-one-session-out and leave-one-ball-out splits, tracked in MLflow.
3. Publish the dataset on Hugging Face. As far as I know, no labelled golf impact audio dataset exists.
