# LUMEN REVIEW CHECKLIST — HSR-AXIS-001G

Use this checklist after Codex completes 001G.

## Scope control

- [ ] Did not scrape Huroka/Yatta/HoneyHunter.
- [ ] Did not implement all real character kits.
- [ ] Did not implement enemy AI.
- [ ] Did not implement AI axis search.
- [ ] Did not implement full HSR damage formula.
- [ ] Did not hard-code Seele or any real HSR character logic.

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
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/trigger_on_kill_extra_turn_mvp.json
```

## Event model

- [ ] Generic `Event` model exists.
- [ ] Event data is structured and deterministic.
- [ ] Events are emitted by damage.
- [ ] Events are emitted by unit defeat.
- [ ] Events are emitted by weakness break.
- [ ] Action lifecycle events exist if implemented.

## Trigger model

- [ ] Generic `Trigger` model exists.
- [ ] Trigger has owner.
- [ ] Trigger has event type.
- [ ] Trigger has condition.
- [ ] Trigger can execute generic effects.
- [ ] Trigger ordering is deterministic.
- [ ] Trigger recursion protection exists.
- [ ] `max_triggers_per_action` or equivalent exists and is tested.

## Condition language

- [ ] `always` supported.
- [ ] `event_actor_is_owner` supported.
- [ ] `event_source_is_owner` supported.
- [ ] `event_target_is_owner` supported.
- [ ] `event_killer_is_owner` supported.
- [ ] `field_equals` supported.
- [ ] Unsupported conditions fail clearly.

## Trigger behavior

- [ ] On-kill trigger fires when owner kills.
- [ ] On-kill trigger does not fire when another unit kills.
- [ ] Trigger can grant extra turn.
- [ ] Trigger can gain energy or add buff.
- [ ] Weakness-break trigger works.
- [ ] Recursive loop protection works.

## Replay Validator

- [ ] Can load triggers from replay JSON.
- [ ] Can deserialize trigger effects.
- [ ] Can check `extra_turn_stack` after trigger resolution.
- [ ] Can check trigger-related logs or another observable proof.
- [ ] Existing replays still pass.
- [ ] New trigger replay passes.

## Regression risk

- [ ] Existing action value tests still pass.
- [ ] Existing buff duration tests still pass.
- [ ] Existing damage/RNG tests still pass.
- [ ] Existing toughness/break tests still pass.
- [ ] Existing Replay Validator mismatch tests still pass.

## Review decision

- [ ] Accept 001G.
- [ ] Require 001G-FIX before moving on.

Suggested next task after acceptance: **HSR-AXIS-001H: Targeting / Aggro / Taunt MVP** or **HSR-AXIS-001H: HSR Damage Formula v1**, depending on whether the next validation replay needs enemy target selection or accurate damage numbers first.
