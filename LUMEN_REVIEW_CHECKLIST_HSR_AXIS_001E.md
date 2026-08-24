# LUMEN REVIEW CHECKLIST — HSR-AXIS-001E

Use this checklist after Codex returns the 001E package.

## Scope control

- [ ] Did Codex avoid Huroka/Yatta/HoneyHunter scraping?
- [ ] Did Codex avoid real full character kit implementation?
- [ ] Did Codex avoid AI axis search / beam search?
- [ ] Did Codex preserve all previous 001A–001D behavior?

## Tests to run locally

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_timeline_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_multistep_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/buff_duration_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/damage_rng_mvp.json
```

## Damage behavior

- [ ] Fixed `DealDamage(amount=...)` still works exactly as before.
- [ ] Calculated damage mode exists and is deterministic.
- [ ] No-crit calculated damage matches the documented MVP formula.
- [ ] Forced-crit calculated damage matches the documented MVP formula.
- [ ] Damage defaults are deterministic, not random.
- [ ] HP does not go below 0.
- [ ] Units become `is_alive=False` at 0 HP.

## Stats / buffs

- [ ] Unit constructors remain backward compatible.
- [ ] Effective stats aggregate base stats plus buff/debuff stat mods.
- [ ] `atk_pct`, `atk_flat`, `dmg_bonus`, `crit_rate`, and `crit_dmg` are covered by tests.
- [ ] Buff duration and damage interaction is tested.
- [ ] Expired buffs no longer affect damage.

## Forced RNG / replay

- [ ] Replay steps can include `forced_rng`.
- [ ] Forced crit true/false affects calculated damage.
- [ ] Replays without `forced_rng` still pass.
- [ ] CLI validation works for the new damage replay.

## Design quality

- [ ] Damage formula is isolated in `damage.py` or equivalent.
- [ ] RNG behavior is isolated in `rng.py` or equivalent.
- [ ] `effects.py` does not become an unmaintainable formula dump.
- [ ] The formula is clearly documented as MVP, not final full HSR.

## Decision

- [ ] PASS: proceed to 001F.
- [ ] FIX REQUIRED: specify exact failing tests or design issue.

Potential next task after 001E:

**HSR-AXIS-001F — Toughness / Weakness / Break MVP**
