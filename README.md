# HSR Axis Simulator

Deterministic action-value simulator core for a Honkai: Star Rail inspired action-axis project. The current package focuses on timeline mechanics that can later support golden replay validation and axis optimization.

## How to run tests

```bash
python -m pytest -q
```

## Implemented

- Unit speed and base action value.
- Normal timeline actor selection by lowest current action value.
- Global action-value advancement and normal turn reset.
- Generic action effects for advance, delay, speed change, immediate action, extra turns, skill points, and energy.
- Generic buff/debuff storage, refresh, stacking, removal, and duration expiration.
- MVP calculated damage from effective stats and deterministic forced crit.
- MVP toughness, weakness, break, break delay, and break recovery behavior.
- MVP event hooks and generic trigger effects.
- Normalized data-driven character, skill, team, and trigger loading.
- LIFO extra-turn stack behavior.
- MVP golden replay validation from manually-authored JSON traces.
- Pytest coverage for the simulator core.

## Replay validation

Golden replay JSON files live in `hsr_axis_sim/data/golden_replays`.

Run the multi-step replay from Python:

```python
from hsr_axis_sim.sim import ReplayValidator

validator = ReplayValidator()
replay = validator.load_replay(
    "hsr_axis_sim/data/golden_replays/bronya_seele_multistep_mvp.json"
)
result = validator.validate(replay)
print(result.passed, result.mismatches)
```

Run the same replay from the command line:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/bronya_seele_multistep_mvp.json
```

Run the buff-duration replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/buff_duration_mvp.json
```

Run the damage/RNG replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/damage_rng_mvp.json
```

Run the Damage Formula V1 replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/damage_formula_v1_mvp.json
```

Run the toughness/break replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/toughness_break_mvp.json
```

Run the break damage / elemental break replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/break_damage_elemental_mvp.json
```

Run the trigger replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/trigger_on_kill_extra_turn_mvp.json
```

Run the data-loaded replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/data_loaded_bronya_seele_mvp.json
```

Run the interrupt ultimate replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/ultimate_interrupt_mvp.json
```

Run the enemy AI replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/enemy_ai_mvp.json
```

Run the representative character kit replay:

```bash
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/golden_replays/character_kit_001_mvp.json
```

The validator checks selected actors, global action value, skill points, extra-turn stack, and selected unit fields after each replayed action.

## Buff duration semantics

- `target_normal_turns` decrements only when the status holder completes a normal turn.
- Extra turns do not decrement `target_normal_turns`.
- Actions that include `DoesNotEndTurn` keep the active turn open and do not expire current-turn statuses yet.
- `current_turn` statuses expire when the active turn actually ends.
- Buffs and debuffs are generic simulator statuses; `data.stat_mods` can affect MVP calculated damage.

## Damage Formula V1

`DealDamage(amount=...)` preserves fixed damage behavior and bypasses calculated formula stages.

If `DealDamage` uses calculated fields such as `multiplier`, Damage Formula V1 runs named stages:

```text
base_damage = scaling_stat_value * multiplier + flat_damage
after_bonus = base_damage * (1 + damage_bonus)
after_crit = after_bonus * crit_multiplier
after_defense = after_crit * defense_multiplier
after_resistance = after_defense * resistance_multiplier
final_damage = after_resistance * (1 + vulnerability)
```

Defense multiplier is an explicit MVP formula:

```text
attacker_level_factor = attacker_level * 10 + 200
effective_target_defense = max(0, target_defense * (1 - def_reduction) * (1 - def_ignore))
defense_multiplier = attacker_level_factor / (attacker_level_factor + effective_target_defense)
```

Resistance multiplier is `1 - (target_resistance - resistance_penetration)`. Resistance is intentionally not clamped in this MVP, so negative effective resistance can increase damage.

If `can_crit` is true and replay or context `forced_rng.crit` is true, crit uses `(1 + crit_dmg)`. Missing forced crit defaults to `False`; no random behavior is used yet.

Buffs and debuffs can modify stats with `data.stat_mods`, including `atk_pct`, `atk_flat`, `dmg_bonus`, `crit_rate`, `crit_dmg`, `break_effect`, `break_damage_bonus`, `def_reduction`, `def_ignore`, `all_res_pen`, `<element>_res_pen`, `vulnerability`, `<element>_dmg_bonus`, and `<damage_type>_dmg_bonus`.

## Toughness / Break MVP

- Units can define `weaknesses`, `max_toughness`, `current_toughness`, and `is_broken`.
- `DealToughnessDamage` reduces toughness only when the effect element matches a weakness, unless `ignore_weakness=True`.
- Toughness is clamped at 0.
- Crossing from positive toughness to 0 sets `is_broken=True`.
- Breaking a unit delays it by `target.base_av * break_delay_percent`.
- A broken unit recovers to full toughness when it completes its next normal turn.
- Extra turns do not recover broken state in this MVP.

## Break Damage / Elemental Break Effects MVP

`DealToughnessDamage` can opt into break damage with `deal_break_damage=true`. Break damage only occurs when toughness crosses from positive to 0 and the target becomes newly broken.

Break damage uses a separate named pipeline:

```text
base_break_damage = level_break_base(attacker.level)
after_element = base_break_damage * element_break_multiplier
after_toughness = after_element * toughness_factor
after_break_effect = after_toughness * (1 + break_effect)
after_break_bonus = after_break_effect * (1 + break_damage_bonus)
after_defense = after_break_bonus * defense_multiplier
after_resistance = after_defense * resistance_multiplier
final_break_damage = after_resistance * (1 + vulnerability)
```

`apply_elemental_break_effect=true` applies a generic debuff such as `quantum_break_entanglement` or `fire_break_burn` with `mvp_no_dot_tick=true`. Real DoT ticking, super break, freeze behavior, and imprisonment behavior are intentionally not implemented yet.

## Event / Trigger MVP

Replays can define generic triggers under `initial_state.triggers`. Triggers match emitted events and execute existing generic effects as if the trigger owner were the actor.

Supported MVP event types include `action_started`, `action_finished`, `damage_dealt`, `unit_defeated`, `weakness_break`, `turn_started`, and `turn_ended`.

Supported condition types are `always`, `event_actor_is_owner`, `event_source_is_owner`, `event_target_is_owner`, `event_killer_is_owner`, and `field_equals`.

Trigger ordering is deterministic by trigger id. Dispatch has a fixed event limit to stop recursive loops, and `max_triggers_per_action` limits repeated firings of the same trigger during one explicit action.

## Data Layer MVP

Sample normalized data lives in `hsr_axis_sim/data/sample_characters` and `hsr_axis_sim/data/sample_teams`.

Character JSON defines base stats, executable skill effects, and optional trigger templates. Team JSON instantiates units from character ids, applies initial state values and stat overrides, and sets initial skill points.

Skill effects can use semantic target references instead of hard-coded unit ids. Supported `target_ref` values include `actor`, `self`, `action_targets`, `selected_targets`, `all_allies`, `alive_allies`, `all_enemies`, `alive_enemies`, and event refs such as `event_source`, `event_target`, `event_killer`, and `event_victim`.

The replay validator can load data-driven teams with:

```json
"data_sources": {
  "characters_dir": "hsr_axis_sim/data/sample_characters",
  "team": "hsr_axis_sim/data/sample_teams/bronya_seele_team.json"
}
```

Replay steps can then use `skill_id` for the currently selected actor instead of embedding a full action spec.

Character JSON may optionally include an `enemy_ai` block with a deterministic skill pattern. Data-loaded team construction attaches enemy AI plans per unit instance and initializes per-unit cursors.

## Action Generation MVP

`legal_action_choices_for_actor(state, actor_id, skills)` enumerates deterministic one-step action choices for a live actor from loaded `SkillSpec` data. `skills` may be a list or insertion-ordered dict of `SkillSpec` values.

The generator gates skills only by MVP resource metadata: negative `sp_delta` requires enough state skill points, and negative `energy_delta` requires enough actor energy. It then uses `legal_target_groups(...)` and `action_from_skill(..., validate_targets=True)` to build unexecuted `Action` candidates in stable skill-then-target order.

`legal_actions_for_actor(...)` returns only the generated `Action` objects. This layer is a search prerequisite; it does not score choices, choose enemy behavior, infer costs from arbitrary effects, or execute actions.

## Ultimate / Interrupt Window MVP

`legal_ultimate_choices(state, skill_lookup, window=None)` enumerates affordable ultimate choices for live units in deterministic unit, skill, then target order. It reuses the same `SkillSpec` resource gating and target legality as normal action generation.

`execute_interrupt_action(state, action, forced_rng=None)` executes an off-turn interrupt action without calling `Timeline.next_turn`, advancing global AV, resetting the actor's normal timeline position, ticking target-normal-turn statuses, or expiring current-turn statuses. Interrupt actions must use `ends_turn=False`; turn-ending interrupt actions fail clearly.

Replay steps can use `"step_type": "interrupt"` with `actor_id`, `skill_id`, and `target_ids` to validate an ultimate between normal turns.

## Enemy AI MVP

`choose_enemy_action(state, skill_lookup, actor_id, forced_rng=None)` selects a deterministic enemy action from the actor's attached `EnemyAIPlan` without mutating state. `execute_enemy_ai_action(...)` executes that choice through the normal `Action.execute` pathway and advances the actor's AI cursor only after successful execution.

Supported target strategies are `first_legal`, `last_legal`, `lowest_hp_legal`, `highest_hp_legal`, `explicit`, and `forced_rng_target`. All strategies use the skill's `target_type` and existing target legality.

Replay normal steps can use `"use_enemy_ai": true` to let the validator select and execute the enemy action instead of providing a manual `skill_id`.

## Character Kit 001 MVP

Manually authored representative kit data lives in `hsr_axis_sim/data/character_kits/kit_001_mechanic_representatives`.

The kit includes placeholder MVP characters for a kill-chain carry, turn-pull support, energy battery support, and break support. These specs use only generic data-driven skills, effects, target refs, buffs/debuffs, triggers, ultimate timing, and toughness/break mechanics.

`toughness_damage_bonus` and `break_efficiency` are supported as MVP stat mods for increasing `DealToughnessDamage` before break evaluation. These are representative mechanics, not exact live-server character implementations.

## External Import Adapter MVP

`hsr_axis_sim/adapters` is an offline-first adapter layer for converting external-style fixture JSON into normalized simulator character JSON. HSR-AXIS-001Q does not scrape live websites or make network requests.

Run the sample fixture importer:

```bash
python3 -m hsr_axis_sim.adapters.external_import \
  --input hsr_axis_sim/data/raw/external_sample/sample_external_character.json \
  --output hsr_axis_sim/data/imported_samples/imported_external_character.json
```

The adapter validates effect types through the existing schema and records warnings for unsupported or unparsed source fields. Huroka/Yatta/HoneyHunter-style support should build on this fixture-based normalization after the adapter contract is stable.

## Manual Video Trace Protocol MVP

Manual video trace files are human-created replay JSON files. The project does not scrape, download, OCR, or parse videos.

Use `hsr_axis_sim/data/manual_video_traces/templates/manual_video_trace_template.json` when transcribing a Bilibili/no-reset axis video by hand. Record observed actors, skills, targets, HP, energy, SP, current AV, and assumptions. Use `forced_rng` for observed random outcomes such as crits, enemy targets, hit/resist outcomes, or anything else needed to reproduce the trace.

A trace should pass both lint and replay validation before being trusted:

```bash
python3 -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python3 -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
```

## Target Legality MVP

`legal_target_groups(state, actor_id, target_type)` returns deterministic selected-target groups for a skill. `normalize_and_validate_target_ids(...)` validates one selected target group and raises `TargetValidationError` for illegal selections.

Supported target types are `self`, `none`, `single_enemy`, `single_ally`, `single_other_ally`, `single_any`, `all_enemies`, `all_allies`, and `all_units`.

Data-loaded replay steps using `skill_id` validate selected targets against the loaded skill's `target_type`. Inline replay actions remain backward compatible.

## Intentionally not implemented

- Full damage formula.
- Real character data or character-specific logic.
- External website scraping or data import.
- Enemy AI.
- Axis search or score optimization.
