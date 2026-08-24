# LUMEN REVIEW — HSR-AXIS-001J AFTER CODEX

## Verdict

**HSR-AXIS-001J passes and is accepted.**

The implementation successfully adds target legality and deterministic legal target group generation without jumping ahead into AI search, Huroka import, enemy AI, blast/bounce, or full HSR-specific targeting.

## Local validation run by Lumen

From the submitted project root:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
```

Result:

```text
116 passed in 2.75s
```

Golden replay CLI sweep:

```bash
for f in hsr_axis_sim/data/golden_replays/*.json; do
  python -m hsr_axis_sim.sim.replay "$f"
done
```

Result:

```text
PASS bronya_seele_multistep_mvp: checked 3 step(s).
PASS bronya_seele_timeline_mvp: checked 1 step(s).
PASS buff_duration_mvp: checked 2 step(s).
PASS damage_rng_mvp: checked 1 step(s).
PASS data_loaded_bronya_seele_mvp: checked 3 step(s).
PASS toughness_break_mvp: checked 2 step(s).
PASS trigger_on_kill_extra_turn_mvp: checked 2 step(s).
```

## What was implemented correctly

### 1. Target legality module

`hsr_axis_sim/sim/targeting.py` now provides:

- `TargetValidationError`
- `legal_target_groups(state, actor_id, target_type)`
- `normalize_and_validate_target_ids(state, actor_id, target_type, target_ids)`

This is the right architecture. It separates target legality from effect execution and keeps target checking usable for replay validation and future AI search.

### 2. Required target types are covered

The MVP target types are implemented:

- `self`
- `none`
- `single_enemy`
- `single_ally`
- `single_other_ally`
- `single_any`
- `all_enemies`
- `all_allies`
- `all_units`

For AoE target types, selected target ids are intentionally rejected for now, and effect-level `target_ref` remains responsible for actual affected units. This is acceptable for the current architecture.

### 3. Replay validator integration is correct

Data-loaded replay steps using `skill_id` now call `action_from_skill(..., state=state, validate_targets=True)`. This means illegal replay target choices fail before the action executes, which is exactly what we want for future video replay validation.

### 4. Backward compatibility preserved

Older inline replay/action behavior remains backward compatible when target validation is not requested. This kept all older golden replays passing.

### 5. Scope control was good

Codex did not implement:

- AI search / beam search
- Huroka/Yatta importers
- real character batch import
- taunt / aggro probability
- random target selection
- blast / bounce targeting
- enemy AI
- full damage formula rewrite

This is correct.

## Minor limitations to carry forward

These are acceptable for 001J, but should remain visible:

1. `all_enemies`, `all_allies`, and `all_units` currently return `[[]]` as selected-target groups. The actual affected targets must be resolved by effect `target_ref`.
2. `single_ally` intentionally includes self for now.
3. Resource legality is not checked by the target validator. This belongs in 001K.
4. Target legality is based on `SkillSpec.target_type`, not inferred from effect-level `target_ref`. This is acceptable and should not be changed casually.

## Next task recommendation

Proceed to:

**HSR-AXIS-001K: Action Generator / Resource-Gated Skill Legality MVP**

The goal of 001K is to turn the current target legality system into something future AI search can actually use:

> Given the current state and a loaded actor's skill specs, enumerate all legal action choices, including target groups, while filtering out actions that are unaffordable due to SP or energy.

This should still not be AI search. It is the last major setup step before a simple DFS/beam-search prototype becomes feasible.
