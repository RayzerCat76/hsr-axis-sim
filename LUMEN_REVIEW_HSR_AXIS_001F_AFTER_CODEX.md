# LUMEN REVIEW — HSR-AXIS-001F AFTER CODEX

## Decision

**Accepted. HSR-AXIS-001F passes and can move to HSR-AXIS-001G.**

001F successfully adds the first deterministic Toughness / Weakness / Break MVP without expanding into real character kits, Huroka scraping, enemy AI, or AI axis search.

## Commands run by Lumen

From the project root:

```bash
python -m pytest -q
```

Result:

```text
71 passed in 2.39s
```

Golden replay CLI checks:

```bash
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_multistep_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_timeline_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/buff_duration_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/damage_rng_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/toughness_break_mvp.json
```

Result:

```text
PASS bronya_seele_multistep_mvp: checked 3 step(s).
PASS bronya_seele_timeline_mvp: checked 1 step(s).
PASS buff_duration_mvp: checked 2 step(s).
PASS damage_rng_mvp: checked 1 step(s).
PASS toughness_break_mvp: checked 2 step(s).
```

## Scope review

Passed:

- No website scraping.
- No real character-kit implementation.
- No full HSR damage formula.
- No enemy AI.
- No AI axis search.
- Existing replays still pass.
- Existing damage / RNG / buff / action-value mechanics were not broken.

## Implementation review

001F correctly adds:

- `Unit.element`
- `Unit.weaknesses`
- `Unit.max_toughness`
- `Unit.current_toughness`
- `Unit.is_broken`
- `DealToughnessDamage`
- `break_logic.py`
- break delay using `target.base_av * break_delay_percent`
- replay loading/checking for toughness and break fields
- `toughness_break_mvp.json`
- tests for weakness match, non-match, ignore weakness, clamp to zero, break delay, already-broken behavior, extra-turn non-recovery, and normal-turn recovery

## Important caveats to preserve

This is still an MVP scaffold, not full HSR break logic.

Known simplifications:

1. No break damage yet.
2. No element-specific break debuffs yet.
3. Break recovery currently happens at normal-turn end using the project’s MVP rule.
4. `DealToughnessDamage` currently requires an explicit `element`; later we can add a safe default to actor element if needed.
5. Negative toughness damage and negative break delay are not currently blocked. This is not a blocker for 001F because golden replays use valid data, but future schema validation should reject them.
6. No weakness implant / weakness ignore / toughness protection / locked toughness mechanics yet.

## Why 001F is acceptable

The goal of 001F was not to fully reproduce all HSR break behavior. The goal was to add a clean, testable scaffold so future Bilibili golden replays can start checking toughness and break timeline effects. This was achieved.

## Next task

Proceed to:

**HSR-AXIS-001G: Event Hooks / Trigger System MVP**

Reason:

Before real character data import or AI search, the simulator needs a generic way to express triggered mechanics such as:

- on kill
- on weakness break
- on damage dealt
- on turn start / turn end
- grant extra turn from a trigger
- gain energy from a trigger
- add buff/debuff from a trigger

This is required for Seele-like extra turns, follow-up attacks, break triggers, and many real HSR character kits.
