# LUMEN REVIEW CHECKLIST — HSR-AXIS-001O Break Damage / Elemental Break Effects MVP

Use this checklist after Codex returns the 001O package.

## 1. Test suite

Run:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
```

Expected: all tests pass.

Then run:

```bash
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
```

Expected: all golden replays pass, including the new break-damage/elemental-break replay.

## 2. Backward compatibility

Verify:

- Existing `toughness_break_mvp.json` still passes unchanged.
- Existing normal damage replays still pass unchanged.
- Existing action-value, buff, trigger, ultimate, enemy AI, data-loaded, target legality, and action-generator tests still pass.
- `DealToughnessDamage` defaults do not suddenly change old HP expectations.

## 3. Unit level override fix

Check:

- `UnitInstanceSpec.level` is actually applied in `instantiate_unit(...)`.
- There is a test for top-level unit-ref level override.
- Existing `stat_overrides["level"]` path is not broken if previously supported.

## 4. Break damage trigger correctness

Check break damage only occurs when:

- target had positive toughness before the hit
- toughness reaches 0 on this hit
- weakness matches or `ignore_weakness=True`
- target was not already broken

Reject or ask for fix if break damage happens on every toughness hit.

## 5. Formula structure

Check that break damage is decomposed into named stages, ideally in a dedicated module such as `break_damage.py`:

- level base
- element multiplier
- toughness factor
- break effect
- break damage bonus
- defense
- resistance
- vulnerability

Magic numbers should be named and documented as MVP placeholders.

## 6. Stat modifiers

Verify tests cover:

- `break_effect`
- `break_damage_bonus`
- defense/resistance/vulnerability interaction if implemented

## 7. Elemental break status MVP

Check:

- Elemental break effects are represented as debuffs/statuses.
- Debuff ids are deterministic, e.g. `quantum_break_entanglement`.
- Metadata includes element/source and a clear marker that real DoT ticking is not implemented.
- No hidden DoT tick engine was added in this task.

## 8. Events and replay debugging

Check that `weakness_break` or related events include enough debug metadata:

- source_id
- target_id
- element
- break_damage_amount if applicable
- elemental_break_effect_id if applicable
- formula_parts if available

Do not require perfect final schema yet, but it should be usable for replay diagnosis.

## 9. Scope control

Reject or ask for fix if Codex added:

- Huroka/Yatta/HoneyHunter importer
- Beam Search or AI search
- UI
- full real character kits
- full DoT ticking system
- super break
- unrelated timeline/ultimate/enemy AI rewrites

## 10. Likely next task

If 001O passes, the next task should likely be:

**HSR-AXIS-001P — Real Character Mechanics MVP: Seele-like and Bronya-like upgraded from toy examples**

Recommended:

```text
Codex Reasoning: HIGH
ChatGPT Model: GPT-5.5 Thinking
```

Reason: once break damage exists, the simulator has enough generic infrastructure to start validating real-ish character mechanics without jumping directly to full data import or AI search.
