# LUMEN REVIEW — HSR-AXIS-001H

## Verdict

**PASS. HSR-AXIS-001H is accepted.**

The data-driven character / skill schema MVP is now good enough to become the base for the next stage. It correctly avoids Huroka scraping and avoids real character kits. The implementation stays within scope: it adds normalized sample character JSON, sample team JSON, a data loader, skill-to-action conversion, a data-loaded golden replay, and tests.

## Verification run by Lumen

Environment: extracted submitted zip and ran tests in a pytest-enabled environment.

```text
python -m pytest -q
97 passed in 2.82s
```

Golden replay CLI checks:

```text
PASS bronya_seele_multistep_mvp: checked 3 step(s).
PASS bronya_seele_timeline_mvp: checked 1 step(s).
PASS buff_duration_mvp: checked 2 step(s).
PASS damage_rng_mvp: checked 1 step(s).
PASS data_loaded_bronya_seele_mvp: checked 3 step(s).
PASS toughness_break_mvp: checked 2 step(s).
PASS trigger_on_kill_extra_turn_mvp: checked 2 step(s).
```

## What passed

1. **Schema layer exists and is source-agnostic**
   - `CharacterSpec`, `BaseStatsSpec`, `SkillSpec`, `TriggerSpec`, `TeamSpec`, and `UnitInstanceSpec` are present.
   - Skills are represented as executable effect specs, not natural-language text.
   - Unknown effect types are rejected early.

2. **Data loader works**
   - Sample characters load from JSON.
   - Team instances create concrete `Unit` objects.
   - Character-owned triggers attach to instantiated unit ids.
   - Duplicate unit ids and unknown character ids fail clearly.

3. **Replay validator integration works**
   - A replay can now use `data_sources` instead of raw inline `initial_state`.
   - A replay step can use `skill_id` for the current actor.
   - Data-loaded Bronya-like + Seele-like flow passes.

4. **No premature scope expansion**
   - No Huroka/Yatta/HoneyHunter scraping.
   - No Bilibili video parsing.
   - No real official character kits.
   - No AI axis search.

## Important limitation before 001I

The current schema still has a brittle target-binding problem.

Example from `seele_like.json`:

```json
{"type": "GainEnergy", "amount": 20, "target_ids": ["seele_like"]}
```

This only works because the team instantiates the unit with the same id as the character id. If the same character is instantiated as `seele_a`, `seele_b`, or any user-defined unit id, self-targeting effects will point to the wrong id.

For a real data-driven simulator, skill effects must not hard-code concrete unit ids inside character JSON. They need semantic target references such as:

```json
{"type": "GainEnergy", "amount": 20, "target_ref": "actor"}
{"type": "ImmediateAction", "target_ref": "action_targets"}
{"type": "AddDebuff", "target_ref": "event_target"}
```

This must be fixed before importing more characters or building Huroka adapters.

## Other notes

- `CharacterSpec.team` is acceptable for this MVP, but long-term the team side should belong primarily to `UnitInstanceSpec` / `TeamSpec`, not the character definition. A character template can be used for allies, enemies, summons, and test dummies. This does not need to block 001I.
- `sp_delta` and `energy_delta` are currently stored but the actual executable behavior is still driven by explicit effects such as `GainSkillPoint`, `ConsumeSkillPoint`, and `GainEnergy`. This is acceptable for now, but later we should either use these fields for validation or remove/rename them to avoid duplicated truth.
- The data schema intentionally remains an internal normalized schema, not an external-source schema. That is correct.

## Decision

001H passes. Proceed to:

**HSR-AXIS-001I — Target Resolver / Semantic Target References MVP**

Do not proceed to Huroka import, real character kits, or AI search until 001I passes.
