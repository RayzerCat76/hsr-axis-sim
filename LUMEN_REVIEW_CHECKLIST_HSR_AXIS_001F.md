# LUMEN REVIEW CHECKLIST — HSR-AXIS-001F

Use this checklist after Codex completes 001F.

## Scope control

- [ ] Did not scrape Huroka/Yatta/HoneyHunter.
- [ ] Did not implement full real character kits.
- [ ] Did not implement enemy AI.
- [ ] Did not implement AI axis search.
- [ ] Did not attempt full HSR break damage or element-specific break effects.

## Test commands

Run from the project root:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
pytest -q
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_timeline_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_multistep_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/buff_duration_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/damage_rng_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/toughness_break_mvp.json
```

## Unit model

- [ ] `Unit("id", "Name", "ally", 100)` remains valid.
- [ ] `element` field exists with safe default.
- [ ] `weaknesses` field exists with safe default.
- [ ] `max_toughness` field exists with safe default.
- [ ] `current_toughness` defaults to `max_toughness` when omitted.
- [ ] `is_broken` field exists with safe default.

## Toughness damage

- [ ] Matching weakness reduces toughness.
- [ ] Non-matching weakness does not reduce toughness.
- [ ] `ignore_weakness=True` bypasses weakness check.
- [ ] No-toughness units are safely ignored.
- [ ] Toughness never goes below 0.
- [ ] Already-broken units do not continue losing toughness.

## Break behavior

- [ ] Crossing from toughness > 0 to 0 sets `is_broken=True`.
- [ ] Break applies action delay using base AV and `break_delay_percent`.
- [ ] Break logs are readable.
- [ ] Broken units recover at the end of their next normal turn.
- [ ] Extra turns do not trigger toughness recovery.

## Replay Validator

- [ ] Can load unit toughness fields from JSON.
- [ ] Can check `current_toughness`.
- [ ] Can check `max_toughness`.
- [ ] Can check `is_broken`.
- [ ] Can deserialize `DealToughnessDamage`.
- [ ] Existing replays still pass.
- [ ] New `toughness_break_mvp.json` passes.

## Regression risk

- [ ] Existing action value tests still pass.
- [ ] Existing buff duration tests still pass.
- [ ] Existing damage/RNG tests still pass.
- [ ] Existing Replay Validator mismatch tests still pass.

## Review decision

- [ ] Accept 001F.
- [ ] Require 001F-FIX before moving on.

Suggested next task after acceptance: **HSR-AXIS-001G: Event Hooks / Trigger System MVP** for kill triggers, follow-up triggers, on-hit/on-kill/on-break hooks, and eventually Seele-like real behavior.
