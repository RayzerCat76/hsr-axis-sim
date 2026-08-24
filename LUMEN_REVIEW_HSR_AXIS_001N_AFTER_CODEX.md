# LUMEN REVIEW — HSR-AXIS-001N Damage Formula V1

## Verdict

**Accepted. HSR-AXIS-001N passes and can proceed to 001O.**

This version successfully upgrades the previous placeholder damage scaffold into a clearer V1 combat-stat pipeline while preserving all existing simulator behavior.

## Local verification

I ran the full pytest suite in a pytest-enabled environment:

```text
156 passed in 2.77s
```

I also ran compileall:

```text
python -m compileall -q hsr_axis_sim
```

Result: passed.

## Golden replay verification

I ran every replay under `hsr_axis_sim/data/golden_replays/*.json`:

```text
PASS bronya_seele_multistep_mvp: checked 3 step(s).
PASS bronya_seele_timeline_mvp: checked 1 step(s).
PASS buff_duration_mvp: checked 2 step(s).
PASS damage_formula_v1_mvp: checked 1 step(s).
PASS damage_rng_mvp: checked 1 step(s).
PASS data_loaded_bronya_seele_mvp: checked 3 step(s).
PASS enemy_ai_mvp: checked 2 step(s).
PASS toughness_break_mvp: checked 2 step(s).
PASS trigger_on_kill_extra_turn_mvp: checked 2 step(s).
PASS ultimate_interrupt_mvp: checked 3 step(s).
```

## What passed review

### 1. Fixed damage backward compatibility is preserved

`DealDamage(amount=...)` still bypasses calculated formula stages and deals exact fixed damage. Existing golden replays remain stable.

### 2. Damage formula is now decomposed into named stages

The formula is readable and extendable:

```text
base_damage = scaling_stat_value * multiplier + flat_damage
after_bonus = base_damage * (1 + damage_bonus)
after_crit = after_bonus * crit_multiplier
after_defense = after_crit * defense_multiplier
after_resistance = after_defense * resistance_multiplier
final_damage = after_resistance * (1 + vulnerability)
```

This is the right level for V1: not claiming full official HSR accuracy, but structured enough for future expansion.

### 3. Buff/debuff stat pipeline works

The following stat modifiers are supported through `data.stat_mods`:

```text
atk_pct
atk_flat
crit_rate
crit_dmg
dmg_bonus
def_reduction
def_ignore
all_res_pen
<element>_res_pen
vulnerability
<element>_dmg_bonus
<damage_type>_dmg_bonus
```

This is sufficient for the next few simulator layers.

### 4. Defense and resistance are isolated

`calculate_defense_multiplier(...)` and `calculate_resistance_multiplier(...)` are separated helpers. That makes future formula refinement safer.

### 5. Forced crit behavior is preserved

`forced_rng.crit` remains deterministic, and `can_crit=False` correctly overrides forced crit.

### 6. Damage events now contain useful debug metadata

`damage_dealt` events include:

```text
source_id
target_id
amount
damage_type
element
is_crit
formula_parts
```

This will be important when we start comparing simulator output to Bilibili video traces.

## Known limitations to keep explicit

These are acceptable for 001N and should not be treated as bugs:

1. This is still not the full official HSR damage formula.
2. Break damage is not implemented yet.
3. Super break is not implemented yet.
4. DoT, blast, bounce, follow-up-specific formula, and real kit special cases are intentionally absent.
5. Resistance is intentionally not clamped; negative effective resistance can increase damage.
6. Crit is still deterministic through `forced_rng`, not random simulation.

## Important note for next task

I noticed one small data-layer issue that should be fixed soon:

`UnitInstanceSpec` has a top-level `level` field, but `instantiate_unit(...)` currently does not appear to apply `unit_ref.level` to the created `Unit`. Since 001N and 001O both depend on unit level for damage-style formulas, 001O should include a small pre-flight fix:

```text
if unit_ref.level is not None:
    stats.level = unit_ref.level
```

Then add a data-loader test proving a team JSON unit ref can override level cleanly.

This does not block 001N acceptance because base character stats can still carry level, but it should be corrected before we rely on data-loaded video builds.

## Next task

Proceed to:

**HSR-AXIS-001O — Break Damage / Elemental Break Effects MVP**

Recommended execution settings:

```text
Codex Reasoning: HIGH
ChatGPT Model: GPT-5.5 Thinking
Reason: Break damage touches toughness, damage formula, status application, events, replay validation, and future break-team AI scoring. Incorrect break semantics would poison later video validation and search results.
```
