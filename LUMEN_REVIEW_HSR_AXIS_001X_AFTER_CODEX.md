# LUMEN REVIEW — HSR-AXIS-001X Scenario Config V1 / Search Constraints MVP

## Verdict

**PASS. HSR-AXIS-001X is accepted and safe to proceed to 001Y.**

001X successfully adds a conservative scenario-level search constraint layer without changing the combat-core mechanics. The implementation fits the intended scope: constraints filter already-generated legal choices, scenario JSON can carry constraints, a constrained sample scenario exists, and existing golden replays / manual video trace / scenario CLI paths still pass.

## Validation run by Lumen

Environment: pytest-enabled sandbox.

```bash
python -m compileall -q hsr_axis_sim
python -m pytest hsr_axis_sim/tests -q
```

Result:

```text
245 passed in 3.49s
```

Golden replay CLI:

```text
PASS break_damage_elemental_mvp: checked 1 step(s).
PASS bronya_seele_multistep_mvp: checked 3 step(s).
PASS bronya_seele_timeline_mvp: checked 1 step(s).
PASS buff_duration_mvp: checked 2 step(s).
PASS character_kit_001_mvp: checked 3 step(s).
PASS damage_formula_v1_mvp: checked 1 step(s).
PASS damage_rng_mvp: checked 1 step(s).
PASS data_loaded_bronya_seele_mvp: checked 3 step(s).
PASS enemy_ai_mvp: checked 2 step(s).
PASS toughness_break_mvp: checked 2 step(s).
PASS trigger_on_kill_extra_turn_mvp: checked 2 step(s).
PASS ultimate_interrupt_mvp: checked 3 step(s).
```

Manual video trace:

```text
PASS manual_video_trace_sample_mvp: manual video trace lint passed.
PASS manual_video_trace_sample_mvp: checked 3 step(s).
```

Scenario CLI smoke tests passed for:

```text
basic_search_mvp.json --format markdown
basic_search_mvp.json --format markdown --include-snapshots
basic_search_mvp.json --format json
constrained_search_mvp.json --format markdown
constrained_search_mvp.json --format json
```

Observed constrained scenario behavior:

```text
Best score: 102100.000
Best terminal reason: constraints_no_choices
Search terminated reason: constraints_no_choices
Best-axis step targets only enemy_1; disabled enemy_2 does not appear.
```

## What was implemented correctly

### 1. Constraint model

`SearchConstraints` now supports:

```text
allowed_actor_ids
disabled_actor_ids
allowed_skill_ids
disabled_skill_ids
allowed_skill_ids_by_actor
disabled_skill_ids_by_actor
allowed_target_ids
disabled_target_ids
max_choices_per_node
```

This is enough for the MVP search-space filtering layer.

### 2. Filtering happens after legal action generation

The implementation calls `legal_action_choices_for_actor(...)` first, then applies `filter_action_choices(...)`. That is the right direction: constraints do not bypass existing resource checks, target legality, or skill legality.

### 3. Target filtering is strict for grouped targets

For multi-target groups, the full target set must pass `allowed_target_ids`, and any intersection with `disabled_target_ids` removes the choice. This is conservative and safe.

### 4. Deterministic branch cap

`max_choices_per_node` uses a stable sort key:

```text
(actor_id, skill_id, joined target ids)
```

This is good for reproducibility, even if it means the branch cap is not score-aware yet.

### 5. Scenario JSON parsing works

`constrained_search_mvp.json` loads constraints correctly and proves the constrained scenario path works through the CLI.

### 6. Enemy AI remains unconstrained

Enemy AI plan execution is not accidentally blocked by player-side search constraints. This matches the 001X MVP requirement.

### 7. No combat-core drift

I did not see evidence that 001X rewrote timeline, damage, toughness, buff duration, target legality, enemy AI, or evaluator semantics. Existing test/replay coverage still passes.

## Notes / limitations to keep in mind

These are not blockers for 001X.

1. **Reports do not include constraints metadata yet.**
   The scenario object stores constraints, and tests check constrained behavior. That is acceptable for this MVP, but later reports should probably show active constraint metadata for debugging.

2. **Actor constraints are strict filters, not auto-skip rules.**
   If the next actor is disabled or not allowed, the branch can terminate with `constraints_no_choices`; the search does not automatically advance time to a later allowed actor. This is acceptable for 001X but should be documented in user-facing scenario examples.

3. **Unknown actor/skill/target IDs are not validated against the loaded battle state.**
   This is okay for now because constraints are filters, but a later scenario linter could warn when a constraint references an ID that does not exist in the scenario.

4. **No forced-prefix scripting yet.**
   This was intentionally left out. It may be useful later for “follow this opening line, then search from there,” but it is not the next most urgent task.

5. **No batch regression command yet.**
   We are now running many separate commands manually. That should be the next step.

## Decision

**001X accepted. Proceed to HSR-AXIS-001Y.**

Recommended next task:

```text
HSR-AXIS-001Y: Batch Scenario Regression Runner MVP
```

Purpose: run golden replays, manual video trace lint/replay, and search scenarios from one command, then produce a compact pass/fail regression report before we begin larger real-video calibration work.
