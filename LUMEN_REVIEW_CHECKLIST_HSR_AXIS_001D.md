# LUMEN REVIEW CHECKLIST — HSR-AXIS-001D

Use this checklist after Codex finishes 001D.

## Must pass locally

Run:

```bash
python -m pytest -q
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_multistep_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/buff_duration_mvp.json
```

Expected:

- All pytest tests pass.
- Both replay CLI commands return PASS.

## Scope control

Reject or send back for repair if Codex added any of these in 001D:

- Huroka scraping/import.
- Yatta/HoneyHunter import.
- Full HSR damage formula.
- Real character kit hardcoding.
- AI search or beam search.
- Large UI work.
- Unnecessary dependency bloat.

## Buff model checks

Confirm:

- Buff/debuff objects have id, target, source, kind, duration_type, remaining_turns, stacks.
- Buffs/debuffs are stored on units or in a clearly queryable state collection.
- Reapplying a buff is deterministic.
- Stacks are capped at max_stacks.
- Refresh behavior is explicit.
- RemoveBuff/RemoveDebuff are implemented and tested.

## Duration checks

Confirm:

- `target_normal_turns` ticks only at the target unit's normal turn end.
- `target_normal_turns` does not tick on extra turns.
- `current_turn` survives `DoesNotEndTurn`.
- `current_turn` expires when the current turn truly ends.
- Expiration removes the buff/debuff cleanly.

## Timeline integration checks

Confirm:

- TurnContext marks extra turns clearly.
- Timeline.end_turn owns duration ticking/expiration.
- Existing immediate action and extra turn tests still pass.
- Adding buff duration did not change accepted 001A/001B/001C behavior.

## Replay validator checks

Confirm:

- Replay expectations can check buffs and debuffs.
- Empty expected buffs/debuffs means none should exist.
- Unsupported buff expectation fields produce mismatches rather than crashes.
- `buff_duration_mvp.json` actually proves the intended duration behavior.

## Packaging check

Confirm:

- `hsr_axis_sim/__init__.py` exists.
- `python -m pytest -q` works from the repo root.

## Decision standard

001D passes only if buff/debuff state is deterministic and replay-checkable.

Do not proceed to Huroka import or real character kits until 001D passes.
