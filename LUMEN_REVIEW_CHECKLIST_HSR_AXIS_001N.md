# LUMEN REVIEW CHECKLIST — HSR-AXIS-001N Damage Formula V1

Use this checklist after Codex returns the 001N package.

## 1. Test suite

Run:

```bash
pytest -q
```

Expected: all tests pass.

Then run:

```bash
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
```

Expected: all golden replays pass, including the new calculated-damage V1 replay.

## 2. Backward compatibility

Verify:

- `DealDamage(amount=...)` still deals exact fixed damage.
- Existing `damage_rng_mvp.json` still passes.
- Existing enemy AI, ultimate, trigger, toughness, and buff duration replays still pass.

## 3. Formula decomposition

Check that calculated damage is decomposed into clear stages, not one unreadable expression:

- base damage
- damage bonus
- crit
- defense multiplier
- resistance multiplier
- vulnerability / damage taken

## 4. Buff/debuff stat_mods

Verify existing stat_mods still work:

- `atk_pct`
- `atk_flat`
- `crit_rate`
- `crit_dmg`
- `dmg_bonus`

Verify new stat_mods are tested if implemented:

- `def_reduction`
- `def_ignore`
- `all_res_pen`
- `<element>_res_pen`
- `vulnerability`
- `<element>_dmg_bonus`
- `<damage_type>_dmg_bonus`

## 5. Defense and resistance

Check:

- Defense multiplier is isolated in a named helper function.
- Resistance multiplier is isolated in a named helper function.
- The clamping behavior, if any, is explicit and documented.
- Negative resistance behavior is not accidentally hidden.

## 6. Crit RNG

Check:

- `forced_rng.crit = true` forces crit when `can_crit = true`.
- `forced_rng.crit = false` forces no crit.
- `can_crit = false` overrides forced crit.
- Existing RNG behavior is not broken.

## 7. Events and replay debugging

Check that `damage_dealt` events still contain required fields and preferably include new debug metadata:

- source_id
- target_id
- amount
- damage_type
- element
- is_crit
- formula_parts/debug if implemented

## 8. Scope control

Reject or ask for fix if Codex added:

- Huroka/Yatta/HoneyHunter importer
- Beam Search or AI search
- UI
- full real character kits
- full break damage / super break
- major action timeline rewrites
- unrelated refactors

## 9. Likely next task

If 001N passes, the next task should be:

**HSR-AXIS-001O — Break Damage / Elemental Break Effects MVP**

Recommended:

- Codex Reasoning: HIGH
- ChatGPT Model: GPT-5.5 Thinking
