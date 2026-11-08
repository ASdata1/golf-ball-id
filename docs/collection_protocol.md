# Collection protocol

## Before the session
1. `python scripts/make_plan.py <YYYY-MM-DD_NN> --club 7i --models prov1 distance_ball --blocks 25`
2. Fill in `session.yaml`: mic_id, mic_distance_m, environment, temp_c.
3. Mark balls with their ball_id (e.g. a dot pattern) so you can grab the right one.
4. Fix the mic position: same distance and angle from the ball every session (1 m, behind and to the side, is a good start). Turn off automatic gain.

## During
1. Start one recording (48 kHz). Stay quiet for 30 s first: that is your noise sample.
2. Warm up with a ball **not** in the study.
3. Hit in plan order. One shot every 10 s or so. Avoid practice swings that hit the mat near the mic.
4. After each shot, note impact zone (foot powder spray) and set `valid = False` for duffs or GC3 misreads. **Do not delete rows.**
5. Cap at about 60 shots to limit fatigue.

## After
1. Export the session from Foresight as CSV and save it as `gc3.csv`.
2. Save the recording as `recording.wav` in the same folder.
3. `python scripts/build_index.py`. If it reports a count mismatch, fix the raw files by hand and log what you did in `session.yaml` notes.
4. `dvc add data/raw && dvc push`, then commit the `.dvc` file.

## Targets
- MVP: 2 sessions, 7 iron, Pro V1 vs distance ball, 50 shots per model.
- Next: add a tour ball pair (Pro V1 vs Pro V1x), then a wedge chip and a putt protocol for audio.
