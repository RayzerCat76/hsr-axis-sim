# LUMEN REVIEW — HSR-AXIS-001I Target Resolver / Semantic Target References

## Verdict

**PASS. HSR-AXIS-001I is accepted and safe to proceed to HSR-AXIS-001J.**

This version successfully removes the most dangerous early data-schema issue: effects no longer need to hard-code a specific instantiated unit id such as `seele_like` inside reusable character JSON. The implementation now supports semantic target references such as `actor`, `action_targets`, `all_allies`, `alive_enemies`, and event-derived references.

## Local verification performed by Lumen

I unpacked the submitted project and ran the test suite locally.

```text
python -m pytest -q
104 passed in 2.66s
```

I also ran every golden replay CLI currently included in the project:

```text
PASS bronya_seele_multistep_mvp: checked 3 step(s).
PASS bronya_seele_timeline_mvp: checked 1 step(s).
PASS buff_duration_mvp: checked 2 step(s).
PASS damage_rng_mvp: checked 1 step(s).
PASS data_loaded_bronya_seele_mvp: checked 3 step(s).
PASS toughness_break_mvp: checked 2 step(s).
PASS trigger_on_kill_extra_turn_mvp: checked 2 step(s).
```

## What was checked

### 1. `target_ref` support

Accepted target references include:

- `actor` / `self`
- `action_targets` / `selected_targets`
- `all_allies`
- `alive_allies`
- `all_enemies`
- `alive_enemies`
- `event_source`
- `event_target`
- `event_killer`
- `event_victim`

The important part is that sample character JSON now uses semantic refs rather than fixed unit ids. This makes the same character spec reusable across different unit instance ids.

### 2. Backward compatibility

Existing `target_ids` still work, and existing golden replays still pass. That is important because earlier 001B–001H work was not broken.

### 3. Event-trigger target refs

Trigger-generated synthetic actions now carry event data, allowing effects to target the event source/target/killer/victim. This is necessary for later mechanics such as on-kill, on-hit, on-break, follow-up, and mark-style effects.

### 4. Data-loaded replay

The data-loaded Bronya-like + Seele-like replay still passes after replacing hard-coded effect targets with semantic refs. This confirms the `target_ref` design is viable for reusable character data.

## Minor notes / accepted limitations

These are not blockers for 001I, but they define what 001J should address.

1. **`target_ref` resolves targets, but does not validate action legality.**  
   Example: a `single_enemy` skill can still be constructed with an ally target unless a future validation layer rejects it.

2. **`SkillSpec.target_type` is currently descriptive, not authoritative.**  
   It exists in JSON, but it does not yet generate legal target groups or reject illegal selected targets.

3. **No target shapes yet.**  
   Blast adjacency, bounce, random targets, taunt-weighted target choice, lowest-HP targeting, and enemy AI targeting are intentionally not implemented.

4. **`action_targets` requires explicit selected targets.**  
   That is correct for targeted single-target skills, but AoE skills should use `alive_enemies` / `all_enemies` rather than `action_targets`.

5. **No ally/enemy constraint enforcement yet.**  
   This is the next required layer before AI search can produce legal actions.

## Scope discipline

Codex did not jump into Huroka scraping, real character import, full damage formula, enemy AI, or beam search. That is correct.

## Next recommended task

Proceed to:

**HSR-AXIS-001J — Target Legality / Legal Action Target Generation MVP**

The purpose of 001J is to make `SkillSpec.target_type` executable: given a battle state, actor, and skill, the simulator should be able to say which target selections are legal and reject invalid selected targets.
