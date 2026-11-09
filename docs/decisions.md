# Decision and limitation log

Each entry records what I decided, why, what I gave up, and how I'd explain it in an interview.
New entries go at the bottom; old ones are never rewritten, only superseded.

---

## Decisions

### D1. Frame the task as a hierarchy, not one flat classifier
**Decision:** Predict construction (urethane tour vs ionomer distance) first, then spin family (low vs high spin tour ball), then exact model.
**Why:** Balls in the same family (Pro V1 vs TP5) differ by a few hundred rpm of driver spin. That is smaller than one amateur's shot to shot noise. A flat 6 way accuracy would hide *where* the signal runs out.
**Trade off:** More models to train and explain.
**Interview line:** "The interesting result isn't one accuracy number, it's how far down the hierarchy the physics lets you go."

### D2. Exclude GC3 peak height, descent angle, total, offline and hang time
**Decision:** Only measured launch and club data are features.
**Why:** On the GC3 these values are calculated from launch data with one flight model for every ball. They contain zero ball specific information and are just deterministic copies of the inputs.
**Trade off:** Lose the trajectory features I originally wanted.
**Interview line:** "I checked how each feature was produced before using it. Half the 'flight' columns were model outputs, not measurements."

### D3. Use the carry residual as the real aerodynamic feature (planned, outdoor sessions)
**Decision:** Outdoors, log actual carry (rangefinder) and compute `actual - GC3 predicted`.
**Why:** Dimple pattern lift and drag is exactly what GC3's generic model ignores, so the residual isolates the ball's aerodynamics.
**Trade off:** Rangefinder carry is noisy (±2 to 3 yd) and wind adds noise; needs many shots.

### D4. Permuted block collection design, grouped CV by session
**Decision:** Each block hits every ball model once in random order. Evaluation splits by session, never by shot.
**Why:** If all Pro V1s were hit first, the model would learn warm-up and fatigue, not the ball. Random shot splits leak session conditions (room, temperature, mic position) across train and test.
**Trade off:** Grouped CV gives lower, but honest, scores.
**Interview line:** "My first worry was the model learning the day rather than the ball."

### D5. Audio storage: lossless FLAC per shot plus a Parquet index
**Decision:** Raw session recording is immutable. Per shot clips are 48 kHz, 24 bit mono FLAC. One Parquet row per shot links labels, launch data, audio path, SHA-256 hash and recording metadata.
**Why:** FLAC is lossless at about half the size of WAV; MP3 would throw away the high frequency content that likely separates cover materials. Files plus a metadata index is the same pattern Hugging Face Datasets and most audio ML pipelines use. Hashes detect silent corruption or edits.
**Alternatives:** HDF5/Zarr (one big file, harder to inspect, poor with DVC diffs); storing waveforms inside Parquet (bloats every tabular query).
**Trade off:** Many small files; acceptable at this scale (thousands, not millions).

### D6. One continuous recording, split by onset detection, and fail on count mismatch
**Decision:** Record each session as one file, detect impacts by amplitude, align to GC3 rows and plan rows by order. If the three counts differ, ingestion stops.
**Why:** Starting/stopping a recording per shot is error prone at the range. Aligning by order is only safe if counts match, so a mismatch is an error, not something to guess around.
**Trade off:** A missed GC3 read means editing the session by hand before it can be ingested.

### D7. Labels come from a pre generated shot plan, not memory
**Decision:** `scripts/make_plan.py` produces the shot order before the session; I follow it.
**Why:** Removes the most likely labelling error (forgetting which ball I hit). The seed is stored in `session.yaml` so the plan is reproducible.

### D8. Rotate 3 physical balls per model
**Decision:** `ball_id` rotates (prov1_a, prov1_b, prov1_c).
**Why:** Stops one ball's scuffs or manufacturing variance standing in for the whole model. Also lets me test whether the model separates *balls* or *models*.

### D9. MVP compares two very different balls with one club
**Decision:** First milestone is Pro V1 vs a distance ball, 7 iron, two sessions.
**Why:** If the pipeline can't separate the easiest pair, nothing harder will work. Proves the plumbing before scaling collection.

### D10. Data versioned with DVC; experiment tracking added when modelling starts
**Decision:** `data/` is gitignored and tracked by DVC. MLflow is set up before the first model, not later.
**Why:** Audio can't live in git. Every result must trace back to commit + config + data version.

---

## Limitations

**L1. One golfer.** The model learns my swing. It says nothing about other players without new data.
**L2. GC3 can't see face angle or impact location.** Strike location changes spin a lot. Mitigation: foot powder spray and a manual `impact_zone` per shot.
**L3. Mic and room acoustics.** Sound depends on mic position, room and mat vs grass. Mitigation: fixed mic distance, mic_id and environment logged, 30 s of room noise per session. Cross environment generalisation is not claimed.
**L4. Phone audio processing.** Many phone apps apply automatic gain and noise suppression, which can erase subtle differences. Use a raw recording mode or a USB mic.
**L5. Ball wear.** Covers scuff over a session; tracked via ball_id and shot order but not measured directly.
**L6. GC3 export format.** Column names vary by Foresight software version; mapping lives in one place (`config.GC3_COLUMNS`).
**L7. Simple onset detector.** Amplitude threshold works when impacts are the loudest sound. A neighbouring bay's shots could trigger false onsets; the count check catches this but doesn't fix it.
**L8. Sample size.** Hand collected data will be hundreds to low thousands of shots, so models should stay small and results reported with confidence intervals.

---

## Later decisions

### D11. One week collection plan: 7 sessions of about 50 shots, every model in every session
**Decision:** Session 1 is the Pro V1 vs distance ball MVP, then the pipeline is checked on real data before continuing. Sessions 2 to 7 hit the same small set of models (Pro V1, Pro V1x, distance ball) every time.
**Why:** Evaluation is grouped by session (D4), so a model that appears in only one session is perfectly confounded with that session and can't be tested fairly. Keeping the distance ball in every session gives an easy anchor class to check each session's data is sane. Checking after session 1 stops a mic or alignment problem silently ruining a whole week.
**Trade off:** Fewer ball models in week one (about 100 shots each rather than 50 each across six models). Breadth comes in a later week.
**Interview line:** "I designed the collection around how I was going to evaluate, not the other way round."

### D12. Treat session 1 as a pilot and size the rest of the study from it
**Decision:** Use session 1's shot to shot spread in spin, ball speed and launch to run a power calculation before fixing shots per model for the week.
**Why:** No prior estimate of my own 7 iron variability exists. Without it, "100 shots per model" is a guess.
**Interview line:** "I ran a pilot to estimate variance, then sized the experiment from it."

## Design of experiments assessment
The design is a **randomised complete block design**: each block of shots contains every ball model once in random order, and sessions are a second, larger blocking factor. Strike zone, temperature and ball wear are recorded as covariates.

**L9. Not blinded.** I know which ball I'm hitting, so I could swing differently without meaning to. Blinding is impractical solo; mitigated with an identical pre shot routine. A helper teeing up balls would fix it.
**L10. Pseudo replication.** Shots are subsamples, not independent replicates. The true replicates of "ball model" are the physical balls (3 per model) and the sessions. Results generalise to *these* balls in *these* sessions; leave one ball out and leave one session out evaluation tests how far beyond that they go.
**L11. Systematic ball rotation.** Ball units rotate by block number rather than at random, so unit and block position are linked. Minor, but a fully random unit assignment would be cleaner.
**L12. Strike zone is subjective.** It's a hand recorded covariate, so it adds noise and possible bias.

### D13. Pilot pair changed to TP5 vs Srixon Soft Feel (supersedes the pair in D9)
**Why:** Same logic as D9, a urethane tour ball against a soft ionomer ball, so it should be the easiest separation. These are the balls I'm actually using, and Soft Feel's low compression makes it the strongest candidate for an audio signal.

### D14. Session 1 protocol deviation, logged rather than hidden
**What happened:** I hit one TP5 and one Soft Feel, strictly alternating, instead of the randomised plan with 3 balls per model.
**Effect:** Fine for the pilot's main jobs (testing the pipeline, estimating shot to shot spread). But ball model and individual ball are fully confounded in this session, so any difference is "this TP5 vs this Soft Feel", not "TP5 vs Soft Feel". Strict alternation still balances warm up and fatigue across both balls; randomisation is only lost as protection against periodic patterns.
**Action:** plan.csv is rewritten to record what was actually hit, with a deviation note in session.yaml. Session 1 is excluded from the leave one ball out evaluation.
**Interview line:** "My first session didn't follow the protocol. I recorded exactly what happened and limited what I claimed from it."
