# LUMEN REVIEW — HSR-AXIS-001D After Codex

## Verdict

**PASS. HSR-AXIS-001D is accepted and the project can move to HSR-AXIS-001E.**

I inspected the uploaded package and ran the test suite locally.

## Local verification

From the project root:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
```

Result:

```text
52 passed in 1.41s
```

I also ran every golden replay currently included:

```bash
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_multistep_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_timeline_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/buff_duration_mvp.json
```

Results:

```text
PASS bronya_seele_multistep_mvp: checked 3 step(s).
PASS bronya_seele_timeline_mvp: checked 1 step(s).
PASS buff_duration_mvp: checked 2 step(s).
```

## What 001D successfully added

### 1. Generic Buff / Debuff records

The project now has a real `Buff` model with:

- `id`
- `name`
- `target_id`
- `source_id`
- `kind`
- `duration_type`
- `remaining_turns`
- `stacks`
- `max_stacks`
- generic `data`

This is the right level for this stage: store simulator-readable status metadata without trying to implement every real HSR character effect yet.

### 2. Duration semantics

The implementation now distinguishes:

- `target_normal_turns`
- `current_turn`

The important boundary cases are covered:

- target-normal-turn buffs tick only after the holder's normal turn ends;
- extra turns do not tick target-normal-turn duration;
- `DoesNotEndTurn` keeps current-turn buffs alive;
- current-turn buffs expire only when the active turn actually ends.

This is essential for Bronya-like, Sparkle-like, Seele-like, Qingque-like, and Boothill-like future cases.

### 3. Buff / Debuff replay checking

Replay expectations can now check:

- buffs
- debuffs
- empty buff/debuff collections
- status `remaining_turns`
- status `stacks`
- status `source_id`
- status `kind`
- status `duration_type`

This is the correct direction for video-derived golden replay validation.

### 4. Non-regression maintained

The older 001A/001B/001C behavior still passes:

- action value timeline
- speed change
- action advance / delay
- immediate action
- extra turns
- replay validator
- multi-step Bronya-like + Seele-like replay

## Design notes and cautions

### Accepted simplification

`current_turn` statuses currently expire for all units when a turn ends. For the current MVP, this is acceptable because we are using `current_turn` as a generic “active turn window” marker. Later, if real kits require source-specific or target-specific current-turn expiration, we may need more precise duration modes.

### Important future limitation

Buffs are stored but do not yet affect stats or damage. That is intentional for 001D, but it means the next step should not be AI search or Huroka import yet. The next step should be a damage/stat system MVP.

### Replay validator is ready for damage checks, but damage is still placeholder

`DealDamage(amount=...)` is still fixed-damage. This is fine for timeline validation, but not enough for Bilibili video matching. We now need deterministic damage calculation, forced crit handling, and stat-modifying buff aggregation.

## Recommendation

Proceed to:

**HSR-AXIS-001E — Damage / Stats / Forced RNG MVP**

Do not scrape Huroka yet. Do not implement AI search yet. Do not add full real character kits yet.

001E should make damage calculable and deterministic enough that a future golden replay can verify HP changes, crit/no-crit, and buffed vs unbuffed attacks.
