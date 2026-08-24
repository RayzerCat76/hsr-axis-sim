# LUMEN REVIEW CHECKLIST — HSR-AXIS-001J

Use this checklist after Codex returns the 001J implementation.

## Must pass locally

Run:

```bash
python -m pytest -q
```

Run all golden replays:

```bash
for f in hsr_axis_sim/data/golden_replays/*.json; do
  python -m hsr_axis_sim.sim.replay "$f"
done
```

## Functional checks

- [ ] `legal_target_groups` exists and is tested.
- [ ] `normalize_and_validate_target_ids` exists and is tested.
- [ ] `self` target type normalizes to `[actor_id]`.
- [ ] `none` target type rejects explicit targets.
- [ ] `single_enemy` requires exactly one alive enemy.
- [ ] `single_ally` requires exactly one alive ally.
- [ ] `single_other_ally` rejects self.
- [ ] `single_any` accepts exactly one alive unit.
- [ ] `all_enemies` uses no selected target ids for now.
- [ ] `all_allies` uses no selected target ids for now.
- [ ] Unknown target ids fail clearly.
- [ ] Dead single targets fail clearly.
- [ ] Too many selected targets fail clearly.
- [ ] Missing single target fails clearly.

## Integration checks

- [ ] `action_from_skill` remains backward compatible when validation is not requested.
- [ ] `action_from_skill(..., state=state, validate_targets=True)` validates and normalizes targets.
- [ ] Replay validator uses target validation for data-loaded `skill_id` steps.
- [ ] Existing golden replays still pass.
- [ ] Existing `target_ref` behavior from 001I still works.

## Scope checks

Codex must NOT implement these in 001J:

- [ ] No AI search / beam search.
- [ ] No Huroka or Yatta importer.
- [ ] No real character batch import.
- [ ] No taunt / aggro probability.
- [ ] No bounce / blast adjacency.
- [ ] No enemy AI.
- [ ] No full damage formula rewrite.

## Likely next task after 001J

If 001J passes, likely next task is one of:

- **001K: Action Generator MVP** — enumerate legal actions for a state using loaded skill specs, SP/energy availability, and legal target groups.
- **001K-alt: Resource-Gated Skill Legality MVP** — validate SP/energy before generating legal actions.

Do not choose until 001J code is reviewed.
