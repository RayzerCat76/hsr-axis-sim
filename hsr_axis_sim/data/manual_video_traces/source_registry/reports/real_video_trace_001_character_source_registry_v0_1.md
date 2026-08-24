# Character Source Registry: real_video_trace_001_character_source_registry_v0_1

> Non-executable source registry only. Sourced facts are provenance records, not simulator bindings or character-kit implementations.

## Source Catalog

| Source ID | Type | Publisher | Version | Language | Locator |
|---|---|---|---|---|---|
| gachabase_anaxa | structured_game_database | Gachabase | current release dataset | en | https://hsr.gachabase.net/characters/1405/anaxa/release |
| gachabase_anaxa_zh | structured_game_database | Gachabase | current release dataset | zh-CN | https://hsr.gachabase.net/characters/1405/anaxa/release?lang=chs |
| gachabase_pela | structured_game_database | Gachabase | 4.3.0 current dataset | en | https://hsr.gachabase.net/characters/1106/pela/release |
| gachabase_rtb_4_1 | structured_game_database | Gachabase | 4.1.0 | en | https://hsr.gachabase.net/characters/8008/stelle-remembrance/release/4.1.0/14727034?lang=en |
| gachabase_tingyun | structured_game_database | Gachabase | current release dataset; stable core cross-checked to v1.0 | en | https://hsr.gachabase.net/characters/1202/tingyun/release |
| hoyolab_anaxa_v3_2 | community_mechanics_reference | HoYoLAB community | 3.2 | en | https://www.hoyolab.com/article/38626552 |
| hoyolab_pela_v2_1 | community_mechanics_reference | HoYoLAB community | 2.1 | en | https://www.hoyolab.com/article/26916596 |
| hoyolab_rtb_v3_0 | community_mechanics_reference | HoYoLAB community | 3.0 | en | https://www.hoyolab.com/article/36418277 |
| hoyolab_tingyun_v1 | community_mechanics_reference | HoYoLAB community | 1.0 | en | https://www.hoyolab.com/article/18920104 |
| local_evidence_report | manual_video_evidence | hsr-axis-simulator | 3.4 trace context | zh-CN/en | local://hsr_axis_sim/data/manual_video_traces/reports/real_video_trace_001_botu_dilemma_evidence_report_v0_1.json |

## Character Identity and Aliases

| Internal ID | Chinese | English | Aliases | Data ID | Status |
|---|---|---|---|---|---|
| mem | 迷迷 | Mem | Mem, 迷迷 | unresolved | corroborated |
| naxia | 那刻夏 | Anaxa | Naxia, Anaxa, Anaxagoras | 1405 | corroborated |
| pela | 佩拉 | Pela | Pela, Pelageya Sergeyevna | 1106 | corroborated |
| remembrance_trailblazer | 开拓者（记忆） | Remembrance Trailblazer | Remembrance Trailblazer, RMC, RTB | 8008 | corroborated |
| tingyun | 停云 | Tingyun | Tingyun | 1202 | corroborated |

## Coverage by Trace Item

| Item | Actor | Action | Verified | Partial | Missing/conflicting | Blocker resolution |
|---|---|---|---:|---:|---:|---|
| prebattle | pela | technique | 1 | 0 | 1 | partially_resolved |
| step_1 | tingyun | ultimate | 2 | 0 | 1 | partially_resolved |
| step_2 | pela | skill | 1 | 0 | 1 | partially_resolved |
| step_3 | remembrance_trailblazer | skill | 1 | 0 | 1 | partially_resolved |
| step_4 | tingyun | skill | 1 | 0 | 1 | partially_resolved |
| step_5 | pela | ultimate | 1 | 0 | 1 | partially_resolved |
| step_6 | naxia | ultimate | 1 | 0 | 1 | partially_resolved |
| step_7 | naxia | basic_plus_extra_skill | 1 | 0 | 1 | partially_resolved |
| step_8 | mem | advance_naxia | 1 | 0 | 1 | partially_resolved |
| step_9 | naxia | skill_plus_extra_skill | 1 | 0 | 1 | partially_resolved |

## Field-Level Fact Provenance

### anaxa_basic_extra_skill_structure

- Actor/action: `naxia` / `basic_plus_extra_skill`
- Field: `action_and_trigger_structure` = {"basic_skill_point_delta": 1, "basic_target_type": "single_enemy", "defeated_target_reroute": "random_enemy", "extra_skill_point_delta": 0, "extra_skill_trigger": "after_basic_or_skill_hits_qualitative_disclosure_target", "recursive_trigger": false}
- Status: `corroborated`; version: 3.2 release mechanic applicable to 3.4
- Evidence: The sourced talent explains a non-recursive, zero-SP additional Skill after qualifying Basic/Skill use.
- Provenance: gachabase_anaxa, hoyolab_anaxa_v3_2
- Unresolved notes: Accepted trace does not establish target, Qualitative Disclosure, hit state, or reroute conditions.
- Simulator binding allowed: `false`

### anaxa_basic_extra_skill_trace_conditions

- Actor/action: `naxia` / `basic_plus_extra_skill`
- Field: `observed_target_and_trigger_state` = null
- Status: `missing`; version: 3.4 trace
- Evidence: The source mechanic is known but its trace preconditions are not.
- Provenance: local_evidence_report
- Unresolved notes: The placeholder must not be split into executable actions.
- Simulator binding allowed: `false`

### anaxa_skill_extra_skill_structure

- Actor/action: `naxia` / `skill_plus_extra_skill`
- Field: `action_and_trigger_structure` = {"energy_generation": 6, "extra_skill_point_delta": 0, "extra_skill_trigger": "after_basic_or_skill_hits_qualitative_disclosure_target", "initial_target_toughness_reduction": 10, "recursive_trigger": false, "skill_skill_point_delta": -1, "skill_target_type": "single_enemy_plus_four_bounces"}
- Status: `corroborated`; version: 3.2 release mechanic applicable to 3.4
- Evidence: Skill consumes one SP, uses one designated target plus four bounces, and can trigger the sourced non-recursive extra Skill.
- Provenance: gachabase_anaxa, hoyolab_anaxa_v3_2
- Unresolved notes: Targets, enemy count, bounce allocation, Qualitative Disclosure, and trace level are unknown.
- Simulator binding allowed: `false`

### anaxa_skill_extra_skill_trace_conditions

- Actor/action: `naxia` / `skill_plus_extra_skill`
- Field: `observed_targets_trigger_state_and_trace_level` = null
- Status: `missing`; version: 3.4 trace
- Evidence: No accepted target, bounce path, trigger state, or level exists.
- Provenance: local_evidence_report
- Unresolved notes: The placeholder must remain non-executable.
- Simulator binding allowed: `false`

### anaxa_ultimate_structure

- Actor/action: `naxia` / `ultimate`
- Field: `action_structure` = {"category": "ultimate", "control_res_exception": true, "duration": "until_start_of_target_turn", "energy_cost": 140, "state": "Sublimation", "target_scope": "all_enemies", "toughness_reduction": 20, "weakness_types": 7}
- Status: `corroborated`; version: 3.2 release mechanic applicable to 3.4
- Evidence: Anaxa ultimate applies Sublimation to all enemies and deals AoE damage.
- Provenance: gachabase_anaxa, hoyolab_anaxa_v3_2
- Unresolved notes: Trace level, enemy Control RES, weaknesses, and resulting state are unknown.
- Simulator binding allowed: `false`

### anaxa_ultimate_trace_state

- Actor/action: `naxia` / `ultimate`
- Field: `trace_level_and_resulting_combat_state` = null
- Status: `missing`; version: 3.4 trace
- Evidence: All-enemy kit scope is sourced, but concrete enemy state and damage are absent.
- Provenance: local_evidence_report
- Unresolved notes: No executable enemy-state transition can be selected.
- Simulator binding allowed: `false`

### mem_support_action_structure

- Actor/action: `mem` / `advance_naxia`
- Field: `action_structure` = {"charge_cost_percent": 100, "charge_ready_behavior": "Mem_immediately_takes_action_then_selects_ally", "support_duration_turns": 3, "target_action_advance_percent": 100, "target_type": "one_designated_ally"}
- Status: `corroborated`; version: 3.0 core mechanic applicable to recorded 3.4 trace
- Evidence: At full charge Mem immediately takes its own action; Lemme! Help You! advances one selected ally by 100% and grants support.
- Provenance: gachabase_rtb_4_1, hoyolab_rtb_v3_0
- Unresolved notes: Trace target Naxia is accepted, but charge history, precise scheduling state, and skill-level support multiplier are absent.
- Simulator binding allowed: `false`

### mem_support_trace_charge_state

- Actor/action: `mem` / `advance_naxia`
- Field: `observed_charge_trigger_and_timeline_state` = null
- Status: `missing`; version: 3.4 trace
- Evidence: Kit structure resolves advance versus immediate-action terminology, not the trace's initialization.
- Provenance: local_evidence_report
- Unresolved notes: Cannot reproduce scheduling without charge history and AV/speed state.
- Simulator binding allowed: `false`

### pela_skill_structure

- Actor/action: `pela` / `skill`
- Field: `action_structure` = {"category": "skill", "energy_generation": 30, "removes_buff_count": 1, "skill_point_delta": -1, "target_type": "single_enemy", "toughness_reduction": 20}
- Status: `corroborated`; version: stable pre-3.4 core mechanic
- Evidence: Pela skill is a one-enemy skill that consumes one SP and removes one buff.
- Provenance: gachabase_pela, hoyolab_pela_v2_1
- Unresolved notes: Observed target, trace level, enemy buffs, and resulting state are unknown.
- Simulator binding allowed: `false`

### pela_skill_trace_target_and_level

- Actor/action: `pela` / `skill`
- Field: `observed_target_and_trace_level` = null
- Status: `missing`; version: 3.4 trace
- Evidence: No accepted target or trace-level value exists.
- Provenance: local_evidence_report
- Unresolved notes: Damage coefficient and actual dispel outcome cannot be bound.
- Simulator binding allowed: `false`

### pela_technique_structure

- Actor/action: `pela` / `technique`
- Field: `action_structure` = {"base_chance_percent": 100, "category": "technique_attack", "damage_target": "random_enemy", "debuff_scope": "all_enemies", "def_reduction_percent": 20, "duration_turns": 2}
- Status: `corroborated`; version: stable pre-3.4 core mechanic corroborated through current data
- Evidence: Technique attacks into combat, damages a random enemy, and applies the sourced all-enemy DEF debuff.
- Provenance: gachabase_pela, hoyolab_pela_v2_1
- Unresolved notes: Trace does not establish Pela trace level, enemy state, or successful application outcomes.
- Simulator binding allowed: `false`

### pela_technique_trace_assumptions

- Actor/action: `pela` / `technique`
- Field: `trace_level_and_build` = null
- Status: `missing`; version: 3.4 trace
- Evidence: No accepted build assumption exists.
- Provenance: local_evidence_report
- Unresolved notes: Required before applying level-dependent damage or effect-hit calculations.
- Simulator binding allowed: `false`

### pela_ultimate_structure

- Actor/action: `pela` / `ultimate`
- Field: `action_structure` = {"base_chance_percent": 100, "category": "ultimate", "debuff": "Exposed", "def_reduction_percent_at_level_10": 40, "duration_turns": 2, "energy_cost": 110, "target_scope": "all_enemies"}
- Status: `corroborated`; version: stable pre-3.4 core mechanic
- Evidence: Ultimate attacks all enemies and attempts to apply Exposed for two turns.
- Provenance: gachabase_pela, hoyolab_pela_v2_1
- Unresolved notes: Trace level, enemy resistances, and actual application results are unknown.
- Simulator binding allowed: `false`

### pela_ultimate_trace_assumptions

- Actor/action: `pela` / `ultimate`
- Field: `trace_level_and_resulting_debuff_state` = null
- Status: `missing`; version: 3.4 trace
- Evidence: No accepted level or post-action enemy state exists.
- Provenance: local_evidence_report
- Unresolved notes: Do not use level-10 values as trace values without build evidence.
- Simulator binding allowed: `false`

### rtb_skill_companion_state

- Actor/action: `remembrance_trailblazer` / `skill`
- Field: `observed_mem_state_before_skill` = null
- Status: `missing`; version: 3.4 trace
- Evidence: The applicable branch cannot be selected from accepted evidence.
- Provenance: local_evidence_report
- Unresolved notes: Do not infer summon versus restore/charge branch.
- Simulator binding allowed: `false`

### rtb_skill_structure

- Actor/action: `remembrance_trailblazer` / `skill`
- Field: `action_structure` = {"category": "summon_skill", "skill_point_delta": -1, "target": "Mem", "when_absent": "summon_Mem", "when_present": {"grant_charge_percent": 10, "restore_mem_hp_percent_at_level_10": 60}}
- Status: `corroborated`; version: 3.0 core mechanic corroborated; applicable to recorded 3.4 trace
- Evidence: Skill summons Mem or restores Mem and grants charge when already present.
- Provenance: gachabase_rtb_4_1, hoyolab_rtb_v3_0
- Unresolved notes: The accepted trace does not establish whether Mem was already present or the skill level.
- Simulator binding allowed: `false`

### tingyun_skill_structure

- Actor/action: `tingyun` / `skill`
- Field: `action_structure` = {"buff_name": "Benediction", "category": "skill", "duration_turns": 3, "most_recent_recipient_only": true, "skill_point_delta": -1, "target_type": "single_ally"}
- Status: `corroborated`; version: stable 1.0 core mechanic applicable to 3.4
- Evidence: Skill applies level-dependent Benediction to one ally for three turns.
- Provenance: gachabase_tingyun, hoyolab_tingyun_v1
- Unresolved notes: Trace target, level-dependent values, and active prior recipient are unknown.
- Simulator binding allowed: `false`

### tingyun_skill_trace_target_and_level

- Actor/action: `tingyun` / `skill`
- Field: `observed_target_and_trace_level` = null
- Status: `missing`; version: 3.4 trace
- Evidence: No accepted target, trace level, or prior Benediction state exists.
- Provenance: local_evidence_report
- Unresolved notes: Buff values and recipient cannot be bound.
- Simulator binding allowed: `false`

### tingyun_ultimate_cost

- Actor/action: `tingyun` / `ultimate`
- Field: `energy_cost` = 130
- Status: `corroborated`; version: stable 1.0 core mechanic applicable to 3.4
- Evidence: Ultimate energy cost is corroborated.
- Provenance: gachabase_tingyun, hoyolab_tingyun_v1
- Unresolved notes: Initial and current energy in the trace remain unknown.
- Simulator binding allowed: `false`

### tingyun_ultimate_structure

- Actor/action: `tingyun` / `ultimate`
- Field: `action_structure` = {"category": "ultimate", "damage_buff_duration_turns": 2, "restores_target_energy": 50, "target_type": "single_ally"}
- Status: `corroborated`; version: stable 1.0 core mechanic applicable to 3.4
- Evidence: Ultimate targets one ally, restores 50 Energy, and grants a two-turn level-dependent DMG buff.
- Provenance: gachabase_tingyun, hoyolab_tingyun_v1
- Unresolved notes: The accepted video target and Tingyun trace level remain unknown.
- Simulator binding allowed: `false`

### tingyun_ultimate_trace_target

- Actor/action: `tingyun` / `ultimate`
- Field: `observed_target` = null
- Status: `missing`; version: 3.4 trace
- Evidence: The action permits a single ally but the observed ally is not accepted evidence.
- Provenance: local_evidence_report
- Unresolved notes: Do not infer the target from team role or animation.
- Simulator binding allowed: `false`

## Conflicts and Version Ambiguities

- No recorded source conflicts; version-specific missing assumptions remain listed below.

## Unresolved Source Gaps

- anaxa_basic_extra_skill_trace_conditions
- anaxa_skill_extra_skill_trace_conditions
- anaxa_ultimate_trace_state
- mem_support_trace_charge_state
- pela_skill_trace_target_and_level
- pela_technique_trace_assumptions
- pela_ultimate_trace_assumptions
- rtb_skill_companion_state
- tingyun_skill_trace_target_and_level
- tingyun_ultimate_trace_target

## Recommended Research Actions

- Capture authoritative in-game 3.4 skill text or a version-locked 3.4 game-data snapshot for every scoped character.
- Obtain the exact trace builds, trace levels, eidolons, and initial combat state.
- Record Anaxa Qualitative Disclosure and Mem charge/timeline preconditions for the observed actions.
- Resolve accepted video targets and enemy state without inferring from role or animation.
