# LUMEN REVIEW — HSR-AXIS-001M Enemy AI / Enemy Action Pattern MVP

## Verdict

**PASS — HSR-AXIS-001M is accepted.**

This version successfully adds a deterministic enemy action-pattern layer without breaking the existing simulator, replay validator, target legality system, ultimate windows, trigger system, or data-driven character loading.

## Local verification run by Lumen

I unpacked the submitted package and ran:

```bash
pytest -q
```

Result:

```text
151 passed in 2.48s
```

I also ran every golden replay through the replay CLI:

```bash
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
```

Result:

```text
PASS bronya_seele_multistep_mvp: checked 3 step(s).
PASS bronya_seele_timeline_mvp: checked 1 step(s).
PASS buff_duration_mvp: checked 2 step(s).
PASS damage_rng_mvp: checked 1 step(s).
PASS data_loaded_bronya_seele_mvp: checked 3 step(s).
PASS enemy_ai_mvp: checked 2 step(s).
PASS toughness_break_mvp: checked 2 step(s).
PASS trigger_on_kill_extra_turn_mvp: checked 2 step(s).
PASS ultimate_interrupt_mvp: checked 3 step(s).
```

## What passed review

### 1. Enemy AI plan model is clean enough for MVP

The new `EnemyPatternStep` and `EnemyAIPlan` abstractions are simple and appropriate for this stage. They support fixed enemy patterns without pulling the project into full real HSR enemy scripting too early.

Accepted target strategies:

- `first_legal`
- `last_legal`
- `lowest_hp_legal`
- `highest_hp_legal`
- `explicit`
- `forced_rng_target`

This is enough to support deterministic replay validation and early enemy behavior tests.

### 2. Enemy AI selection is pure before execution

`choose_enemy_action(...)` does not mutate HP, AV, SP, or cursor state. This is important because future AI search will need to inspect possible actions without committing to them.

### 3. Cursor advancement is correctly tied to successful execution

`execute_enemy_ai_action(...)` increments the enemy cursor only after action execution succeeds. Tests confirm that failed skill lookup does not advance the cursor.

This matters for future replay debugging and search backtracking.

### 4. Replay Validator integration is controlled

`use_enemy_ai` is supported only on normal replay steps. This is correct for MVP because enemy AI should not be mixed with ultimate interrupt steps, extra-turn steps, or special replay operations before the semantics are explicitly designed.

### 5. Data-loaded enemy AI works

The submitted `generic_enemy.json`, `enemy_ai_team.json`, and `enemy_ai_mvp.json` prove that enemy AI can be loaded from character/team data and replayed through the validator.

### 6. Existing behavior was not broken

All prior golden replays still pass, including ultimate interrupt, trigger on kill, damage RNG, toughness break, buff duration, and data-loaded Bronya/Seele MVP.

## Known limitations that are acceptable for 001M

These should not block acceptance:

1. Enemy AI is deterministic pattern-only.
2. No taunt/aggro probability model yet.
3. No random enemy skill choice except forced replay metadata.
4. No blast/bounce target model.
5. No real HSR enemy phase scripting.
6. `repeat=False` reuses the final step after the cursor passes the end.
7. `use_enemy_ai` is currently normal-step only.

All of these are acceptable because 001M was scoped as an MVP enemy action-pattern layer.

## Issues to keep in mind later

### A. Enemy AI should eventually become search-compatible

Right now `choose_enemy_action` is pure, which is good. Later, when adding Beam Search, enemy AI execution should be represented as a deterministic transition that can be cloned/replayed safely.

### B. Taunt/aggro should not be added yet

It is tempting to add real HSR target probability now, but that should wait until we have a dedicated RNG/aggro task. Otherwise the enemy AI layer will mix fixed replay behavior and probabilistic behavior too early.

### C. Damage is now the next bottleneck

The enemy AI layer can choose and execute actions, but current calculated damage is still a simplified scaffold. Before real video validation, the project needs a stronger damage formula model.

## Gate decision

**HSR-AXIS-001M is accepted.**

Safe to begin:

**HSR-AXIS-001N — Damage Formula V1 / Combat Stat Pipeline MVP**

Do not start Huroka import, Beam Search, UI, full enemy scripting, or real character batch import yet.
