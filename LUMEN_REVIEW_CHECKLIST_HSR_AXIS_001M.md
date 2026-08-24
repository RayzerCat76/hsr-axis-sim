# LUMEN REVIEW CHECKLIST — HSR-AXIS-001M

Use this checklist after Codex returns the 001M Enemy AI / Enemy Action Pattern MVP package.

## Must pass commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
```

## Core acceptance checks

- [ ] Existing 001A–001L tests still pass.
- [ ] All old golden replays still pass unchanged.
- [ ] New `enemy_ai_mvp.json` replay passes.
- [ ] Enemy AI schema is optional and does not break existing character JSON.
- [ ] Enemy AI plans are per unit instance, not shared globally by character template.
- [ ] Enemy AI cursor is per unit instance.
- [ ] `choose_enemy_action` does not mutate state.
- [ ] `execute_enemy_ai_action` increments cursor only after successful execution.
- [ ] Failed enemy action execution does not advance cursor.
- [ ] Target strategies use existing target legality.
- [ ] Dead targets are not selected.
- [ ] Dead enemy actor fails clearly.
- [ ] Missing AI plan fails clearly.
- [ ] Missing skill ID in pattern fails clearly.
- [ ] `use_enemy_ai: true` in Replay Validator only works for normal steps, not interrupt steps.

## Target strategy checks

- [ ] `first_legal` chooses the first legal target group.
- [ ] `last_legal` chooses the last legal target group.
- [ ] `lowest_hp_legal` chooses the legal target with lowest HP.
- [ ] `highest_hp_legal` chooses the legal target with highest HP.
- [ ] `explicit` validates the provided `target_ids`.
- [ ] `forced_rng_target` uses replay forced RNG and validates legality.
- [ ] all-target and none-target skills resolve cleanly to `[]`.

## Scope guardrails

Reject or request fix if Codex does any of the following:

- [ ] Starts Beam Search or scoring.
- [ ] Adds Huroka/Yatta importers.
- [ ] Rewrites Timeline or Action execution core unnecessarily.
- [ ] Adds full HSR damage formula.
- [ ] Hard-codes real enemy names or real encounter behavior.
- [ ] Uses random target selection without forced replay control.
- [ ] Breaks existing `build_battle_state_from_files` call sites.

## Expected limitations that are acceptable for MVP

- Enemy AI is deterministic and simple.
- Real HSR enemy phase scripting is not implemented.
- Multi-action enemy turns are not implemented unless already supported by existing action mechanics.
- Enemy random behavior is only modeled through forced replay metadata.
- Taunt-weighted random targeting can be deferred to a later task.

## Next likely task after 001M

If 001M passes, proceed to:

**HSR-AXIS-001N: Damage Formula / Stat Pipeline Expansion MVP**

Recommended setup will likely be:

```text
Codex Reasoning: High
ChatGPT Model recommendation: GPT-5.5 Thinking
Reason: damage formula correctness is central to validating against Bilibili gameplay videos.
```
