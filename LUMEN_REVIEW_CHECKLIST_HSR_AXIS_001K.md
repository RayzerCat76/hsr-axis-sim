# LUMEN REVIEW CHECKLIST — HSR-AXIS-001K

Use this checklist after Codex returns the 001K implementation.

## Must pass locally

Run:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
```

Run all golden replays:

```bash
for f in hsr_axis_sim/data/golden_replays/*.json; do
  python -m hsr_axis_sim.sim.replay "$f"
done
```

## Functional checks

- [ ] New action generation module exists, preferably `sim/action_generator.py`.
- [ ] `ActionChoice` or equivalent structured result exists.
- [ ] `skill_affordability` or equivalent exists.
- [ ] `legal_action_choices_for_actor` exists.
- [ ] Generator uses `legal_target_groups` from 001J.
- [ ] Generator builds actions through `action_from_skill(..., validate_targets=True)`.
- [ ] Output order is deterministic: skill order, then target group order.
- [ ] Dead actors generate no actions.
- [ ] Unknown actors fail clearly.

## Resource checks

- [ ] Negative `sp_delta` requires enough skill points.
- [ ] Positive or zero `sp_delta` does not make skill illegal.
- [ ] Negative `energy_delta` requires enough actor energy.
- [ ] Positive or zero `energy_delta` does not make skill illegal.
- [ ] Resource checks use `SkillSpec` metadata, not brittle effect introspection.
- [ ] Action generation does not execute effects.

## Target generation checks

- [ ] `single_enemy` creates one choice per alive enemy.
- [ ] Dead targets are excluded.
- [ ] `self` normalizes target ids to `[actor_id]`.
- [ ] `all_enemies` / no-selected-target target types generate one choice with `target_ids == []`.
- [ ] Missing legal targets produces no choices for that skill rather than an invalid action.

## State mutation checks

- [ ] Generating legal actions does not mutate SP.
- [ ] Generating legal actions does not mutate energy.
- [ ] Generating legal actions does not mutate HP.
- [ ] Generating legal actions does not mutate AV.

## Scope checks

Codex must NOT implement these in 001K:

- [ ] No beam search.
- [ ] No DFS search.
- [ ] No scoring function.
- [ ] No Huroka/Yatta importer.
- [ ] No real character batch import.
- [ ] No enemy AI.
- [ ] No taunt/aggro probability.
- [ ] No random target selection.
- [ ] No blast/bounce targeting.
- [ ] No full damage formula rewrite.

## Likely next task after 001K

If 001K passes, likely next task:

**HSR-AXIS-001L: Search State Copy / One-Step Simulation Sandbox MVP**

Before real beam search, we need a safe way to copy a battle state, apply one generated action, and compare resulting states without mutating the original. This prevents future search from corrupting shared state.
