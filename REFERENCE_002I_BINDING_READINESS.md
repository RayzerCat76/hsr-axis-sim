# Atomic Character Fact Binding Readiness: real_video_trace_001_atomic_character_facts_v0_1

> Non-executable atomic fact normalization only. No record is a character kit, effect, trigger, executable action, or simulator-binding authorization.

## Normalization Vocabularies

- action_categories: basic_attack, memosprite_skill, passive_trigger, skill, summon_skill, technique_attack, ultimate
- target_scopes: all_allies, all_enemies, bounce_from_selected_enemy, companion_mem, random_enemy, self, single_ally, single_enemy, unknown
- resource_kinds: charge, energy, none, skill_point
- timing_classifications: action_advance_target, additional_skill_cast, immediate_action_self, non_recursive_additional_cast, normal_action, ultimate_interrupt, unknown
- duration_anchors: fixed_turn_count, source_turn_end, source_turn_start, target_turn_end, target_turn_start, unknown, until_target_turn_start
- readiness_statuses: not_ready, source_and_trace_ready_engine_review_required, source_ready_trace_blocked

## Atomic Facts

| Fact | Actor | Action | Field | Value | Status | Sources |
|---|---|---|---|---|---|---|
| anaxa.basic.extra_skill_non_recursive | naxia | basic_plus_extra_skill | additional_skill_recursive | false | verified_structured_data | gachabase_anaxa |
| anaxa.basic.extra_skill_trigger | naxia | basic_plus_extra_skill | additional_skill_trigger | "after_basic_or_skill_hits_qualitative_disclosure_target" | corroborated | gachabase_anaxa, hoyolab_anaxa_v3_2 |
| anaxa.basic.sp_delta | naxia | basic_plus_extra_skill | basic_skill_point_delta | 1 | verified_structured_data | gachabase_anaxa |
| anaxa.basic.trace_conditions | naxia | basic_plus_extra_skill | observed_target_and_trigger_state | null | missing | local_evidence_report |
| anaxa.skill.extra_skill_non_recursive | naxia | skill_plus_extra_skill | additional_skill_recursive | false | verified_structured_data | gachabase_anaxa |
| anaxa.skill.extra_skill_trigger | naxia | skill_plus_extra_skill | additional_skill_trigger | "after_basic_or_skill_hits_qualitative_disclosure_target" | corroborated | gachabase_anaxa, hoyolab_anaxa_v3_2 |
| anaxa.skill.sp_delta | naxia | skill_plus_extra_skill | skill_point_delta | -1 | verified_structured_data | gachabase_anaxa |
| anaxa.skill.target_scope | naxia | skill_plus_extra_skill | target_scope | "bounce_from_selected_enemy" | corroborated | gachabase_anaxa, hoyolab_anaxa_v3_2 |
| anaxa.skill.toughness_native | naxia | skill_plus_extra_skill | initial_target_toughness_value | null | verified_structured_data | gachabase_anaxa |
| anaxa.skill.trace_conditions | naxia | skill_plus_extra_skill | observed_targets_trigger_state_and_level | null | missing | local_evidence_report |
| anaxa.ultimate.energy_cost | naxia | ultimate | energy_cost | 140 | verified_structured_data | gachabase_anaxa |
| anaxa.ultimate.sublimation_duration | naxia | ultimate | sublimation_duration_anchor | "until_target_turn_start" | corroborated | gachabase_anaxa, hoyolab_anaxa_v3_2 |
| anaxa.ultimate.target_scope | naxia | ultimate | target_scope | "all_enemies" | corroborated | gachabase_anaxa, hoyolab_anaxa_v3_2 |
| anaxa.ultimate.toughness_native | naxia | ultimate | toughness_value | null | verified_structured_data | gachabase_anaxa |
| anaxa.ultimate.trace_state | naxia | ultimate | trace_level_and_resulting_state | null | missing | local_evidence_report |
| mem.support.charge_cost | mem | advance_naxia | charge_consumption_cost | null | missing | None |
| mem.support.charge_readiness_threshold | mem | advance_naxia | charge_readiness_threshold | 100 | corroborated | gachabase_rtb_4_1, hoyolab_rtb_v3_0 |
| mem.support.duration | mem | advance_naxia | support_duration | 3 | corroborated | gachabase_rtb_4_1, hoyolab_rtb_v3_0 |
| mem.support.own_immediate_action | mem | advance_naxia | mem_own_timing | "immediate_action_self" | corroborated | gachabase_rtb_4_1, hoyolab_rtb_v3_0 |
| mem.support.self_target_suppression | mem | advance_naxia | self_target_suppresses_action_advance | true | corroborated | gachabase_rtb_4_1, hoyolab_rtb_v3_0 |
| mem.support.target_action_advance | mem | advance_naxia | selected_ally_action_advance | 100 | corroborated | gachabase_rtb_4_1, hoyolab_rtb_v3_0 |
| mem.support.trace_charge_state | mem | advance_naxia | observed_charge_and_timeline_state | null | missing | local_evidence_report |
| pela.skill.dispel_count | pela | skill | dispel_count | 1 | corroborated | gachabase_pela, hoyolab_pela_v2_1 |
| pela.skill.energy_generation | pela | skill | energy_generation | 30 | verified_structured_data | gachabase_pela |
| pela.skill.observed_target_and_level | pela | skill | observed_target_and_trace_level | null | missing | local_evidence_report |
| pela.skill.sp_delta | pela | skill | skill_point_delta | -1 | verified_structured_data | gachabase_pela |
| pela.skill.target_scope | pela | skill | target_scope | "single_enemy" | corroborated | gachabase_pela, hoyolab_pela_v2_1 |
| pela.skill.toughness_native | pela | skill | toughness_value | null | verified_structured_data | gachabase_pela |
| pela.technique.debuff_scope | pela | technique | debuff_target_scope | "all_enemies" | corroborated | gachabase_pela, hoyolab_pela_v2_1 |
| pela.technique.target_scope | pela | technique | target_scope | "random_enemy" | corroborated | gachabase_pela, hoyolab_pela_v2_1 |
| pela.technique.trace_assumptions | pela | technique | trace_level_and_build | null | missing | local_evidence_report |
| pela.ultimate.energy_cost | pela | ultimate | energy_cost | 110 | verified_structured_data | gachabase_pela |
| pela.ultimate.exposed_duration | pela | ultimate | exposed_duration | 2 | corroborated | gachabase_pela, hoyolab_pela_v2_1 |
| pela.ultimate.target_scope | pela | ultimate | target_scope | "all_enemies" | corroborated | gachabase_pela, hoyolab_pela_v2_1 |
| pela.ultimate.trace_assumptions | pela | ultimate | trace_level_and_resulting_state | null | missing | local_evidence_report |
| rtb.skill.observed_companion_state | remembrance_trailblazer | skill | observed_mem_state_before_skill | null | missing | local_evidence_report |
| rtb.skill.present_mem_charge_gain | remembrance_trailblazer | skill | present_mem_charge_gain | 10 | corroborated | gachabase_rtb_4_1, hoyolab_rtb_v3_0 |
| rtb.skill.sp_delta | remembrance_trailblazer | skill | skill_point_delta | -1 | verified_structured_data | gachabase_rtb_4_1 |
| rtb.skill.target_scope | remembrance_trailblazer | skill | target_scope | "companion_mem" | corroborated | gachabase_rtb_4_1, hoyolab_rtb_v3_0 |
| tingyun.skill.benediction_duration | tingyun | skill | benediction_duration | 3 | corroborated | gachabase_tingyun, hoyolab_tingyun_v1 |
| tingyun.skill.observed_target_and_level | tingyun | skill | observed_target_and_trace_level | null | missing | local_evidence_report |
| tingyun.skill.sp_delta | tingyun | skill | skill_point_delta | -1 | verified_structured_data | gachabase_tingyun |
| tingyun.skill.target_scope | tingyun | skill | target_scope | "single_ally" | corroborated | gachabase_tingyun, hoyolab_tingyun_v1 |
| tingyun.ultimate.damage_buff_duration | tingyun | ultimate | damage_buff_duration | 2 | corroborated | gachabase_tingyun, hoyolab_tingyun_v1 |
| tingyun.ultimate.energy_cost | tingyun | ultimate | energy_cost | 130 | corroborated | gachabase_tingyun, hoyolab_tingyun_v1 |
| tingyun.ultimate.observed_target | tingyun | ultimate | observed_target | null | missing | local_evidence_report |
| tingyun.ultimate.target_energy_restore | tingyun | ultimate | target_energy_restore | 50 | corroborated | gachabase_tingyun, hoyolab_tingyun_v1 |
| tingyun.ultimate.target_scope | tingyun | ultimate | target_scope | "single_ally" | corroborated | gachabase_tingyun, hoyolab_tingyun_v1 |

## Exact Field Provenance

### anaxa.basic.extra_skill_non_recursive

- Registry fact(s): anaxa_basic_extra_skill_structure
- Provenance: gachabase_anaxa: Structured Talent explicitly denies recursion.
- Version: current structured data; 3.4 raw revision unavailable
- Unresolved: Downgraded from compound corroboration.
- Simulator binding allowed: `false`

### anaxa.basic.extra_skill_trigger

- Registry fact(s): anaxa_basic_extra_skill_structure
- Provenance: gachabase_anaxa: Structured Talent gives exact trigger.; hoyolab_anaxa_v3_2: Version 3.2 guide corroborates trigger.
- Version: 3.2 mechanic applicable to 3.4
- Unresolved: Trace Qualitative Disclosure state unknown.
- Simulator binding allowed: `false`

### anaxa.basic.sp_delta

- Registry fact(s): anaxa_basic_extra_skill_structure
- Provenance: gachabase_anaxa: Structured Basic resource field lists +1 SP.
- Version: current structured data; 3.4 raw revision unavailable
- Unresolved: Downgraded from compound corroboration.
- Simulator binding allowed: `false`

### anaxa.basic.trace_conditions

- Registry fact(s): anaxa_basic_extra_skill_trace_conditions
- Provenance: local_evidence_report: Composite target and condition absent.
- Version: 3.4 trace
- Unresolved: Composite remains non-executable.
- Simulator binding allowed: `false`

### anaxa.skill.extra_skill_non_recursive

- Registry fact(s): anaxa_skill_extra_skill_structure
- Provenance: gachabase_anaxa: Structured Talent denies recursion.
- Version: current structured data; 3.4 raw revision unavailable
- Unresolved: Downgraded from compound corroboration.
- Simulator binding allowed: `false`

### anaxa.skill.extra_skill_trigger

- Registry fact(s): anaxa_skill_extra_skill_structure
- Provenance: gachabase_anaxa: Structured Talent gives exact trigger.; hoyolab_anaxa_v3_2: Guide corroborates trigger.
- Version: 3.2 mechanic applicable to 3.4
- Unresolved: Qualitative Disclosure state unknown.
- Simulator binding allowed: `false`

### anaxa.skill.sp_delta

- Registry fact(s): anaxa_skill_extra_skill_structure
- Provenance: gachabase_anaxa: Structured Skill resource field lists -1 SP.
- Version: current structured data; 3.4 raw revision unavailable
- Unresolved: Downgraded from compound corroboration.
- Simulator binding allowed: `false`

### anaxa.skill.target_scope

- Registry fact(s): anaxa_skill_extra_skill_structure
- Provenance: gachabase_anaxa: Structured Skill defines selected target and bounces.; hoyolab_anaxa_v3_2: Version 3.2 guide defines same bounce pattern.
- Version: 3.2 mechanic applicable to 3.4
- Unresolved: Observed targets and bounce path unknown.
- Simulator binding allowed: `false`

### anaxa.skill.toughness_native

- Registry fact(s): anaxa_skill_extra_skill_structure
- Provenance: gachabase_anaxa: Gachabase displays Break (In-Game) 10 for selected target.
- Version: current structured data; 3.4 raw revision unavailable
- Unresolved: No documented conversion or bounce toughness values.
- Simulator binding allowed: `false`

### anaxa.skill.trace_conditions

- Registry fact(s): anaxa_skill_extra_skill_trace_conditions
- Provenance: local_evidence_report: Targets, trigger state, and level absent.
- Version: 3.4 trace
- Unresolved: Composite remains non-executable.
- Simulator binding allowed: `false`

### anaxa.ultimate.energy_cost

- Registry fact(s): anaxa_ultimate_structure
- Provenance: gachabase_anaxa: Structured resource field lists 140.
- Version: current structured data; 3.4 raw revision unavailable
- Unresolved: Downgraded from compound corroboration; trace energy unknown.
- Simulator binding allowed: `false`

### anaxa.ultimate.sublimation_duration

- Registry fact(s): anaxa_ultimate_structure
- Provenance: gachabase_anaxa: Structured text gives target-turn-start expiry.; hoyolab_anaxa_v3_2: Guide gives same expiry.
- Version: 3.2 mechanic applicable to 3.4
- Unresolved: Target turn state absent.
- Simulator binding allowed: `false`

### anaxa.ultimate.target_scope

- Registry fact(s): anaxa_ultimate_structure
- Provenance: gachabase_anaxa: Structured Ultimate is AoE.; hoyolab_anaxa_v3_2: Version 3.2 guide confirms all enemies.
- Version: 3.2 mechanic applicable to 3.4
- Unresolved: Enemy state unknown.
- Simulator binding allowed: `false`

### anaxa.ultimate.toughness_native

- Registry fact(s): anaxa_ultimate_structure
- Provenance: gachabase_anaxa: Gachabase displays Break (In-Game) 20 AoE.
- Version: current structured data; 3.4 raw revision unavailable
- Unresolved: No documented conversion to simulator units.
- Simulator binding allowed: `false`

### anaxa.ultimate.trace_state

- Registry fact(s): anaxa_ultimate_trace_state
- Provenance: local_evidence_report: Resulting state absent.
- Version: 3.4 trace
- Unresolved: Control RES and enemy state unknown.
- Simulator binding allowed: `false`

### mem.support.charge_cost

- Registry fact(s): mem_support_action_structure
- Provenance: None
- Version: 3.4 trace requirement
- Unresolved: No accepted field-specific provenance directly establishes consumption; threshold is not inherited as cost.
- Simulator binding allowed: `false`

### mem.support.charge_readiness_threshold

- Registry fact(s): mem_support_action_structure
- Provenance: gachabase_rtb_4_1: Structured Talent uses 100% readiness.; hoyolab_rtb_v3_0: Version 3.0 guide uses 100% readiness.
- Version: 3.0 core applicable to 3.4
- Unresolved: Threshold is not evidence of consumption.
- Simulator binding allowed: `false`

### mem.support.duration

- Registry fact(s): mem_support_action_structure
- Provenance: gachabase_rtb_4_1: Structured skill gives three turns.; hoyolab_rtb_v3_0: Guide gives three turns.
- Version: 3.0 core applicable to 3.4
- Unresolved: Duration decrement semantics need later review.
- Simulator binding allowed: `false`

### mem.support.own_immediate_action

- Registry fact(s): mem_support_action_structure
- Provenance: gachabase_rtb_4_1: Structured Talent says Mem immediately takes action.; hoyolab_rtb_v3_0: Version 3.0 guide says Mem immediately takes action.
- Version: 3.0 core applicable to 3.4
- Unresolved: This timing applies to Mem, not the selected ally.
- Simulator binding allowed: `false`

### mem.support.self_target_suppression

- Registry fact(s): mem_support_action_structure
- Provenance: gachabase_rtb_4_1: Structured Memosprite Skill includes self-target exception.; hoyolab_rtb_v3_0: Version 3.0 guide includes same exception.
- Version: 3.0 core applicable to 3.4
- Unresolved: Not activated in trace because accepted target is Naxia.
- Simulator binding allowed: `false`

### mem.support.target_action_advance

- Registry fact(s): mem_support_action_structure
- Provenance: gachabase_rtb_4_1: Structured Memosprite Skill specifies 100%.; hoyolab_rtb_v3_0: Version 3.0 guide specifies 100%.
- Version: 3.0 core applicable to 3.4
- Unresolved: This is target advance, not Mem's own immediate action.
- Simulator binding allowed: `false`

### mem.support.trace_charge_state

- Registry fact(s): mem_support_trace_charge_state
- Provenance: local_evidence_report: Charge and timing state absent.
- Version: 3.4 trace
- Unresolved: Charge history and AV state remain unknown.
- Simulator binding allowed: `false`

### pela.skill.dispel_count

- Registry fact(s): pela_skill_structure
- Provenance: gachabase_pela: Structured text states one buff.; hoyolab_pela_v2_1: Guide states one buff.
- Version: stable pre-3.4 core
- Unresolved: Enemy buff state unknown.
- Simulator binding allowed: `false`

### pela.skill.energy_generation

- Registry fact(s): pela_skill_structure
- Provenance: gachabase_pela: Structured resource field lists 30 Energy.
- Version: current structured data; exact 3.4 revision unavailable
- Unresolved: Downgraded from compound corroboration; one exact-field source.
- Simulator binding allowed: `false`

### pela.skill.observed_target_and_level

- Registry fact(s): pela_skill_trace_target_and_level
- Provenance: local_evidence_report: Target and level absent.
- Version: 3.4 trace
- Unresolved: Target and trace level remain unknown.
- Simulator binding allowed: `false`

### pela.skill.sp_delta

- Registry fact(s): pela_skill_structure
- Provenance: gachabase_pela: Structured resource field lists -1 SP.
- Version: current structured data; exact 3.4 revision unavailable
- Unresolved: Downgraded from compound corroboration: guide did not directly expose SP field.
- Simulator binding allowed: `false`

### pela.skill.target_scope

- Registry fact(s): pela_skill_structure
- Provenance: gachabase_pela: Structured field specifies one enemy.; hoyolab_pela_v2_1: Guide specifies one enemy.
- Version: stable pre-3.4 core
- Unresolved: Observed target unknown.
- Simulator binding allowed: `false`

### pela.skill.toughness_native

- Registry fact(s): pela_skill_structure
- Provenance: gachabase_pela: Gachabase displays Break (In-Game) 20.
- Version: current structured data; exact 3.4 revision unavailable
- Unresolved: No documented conversion to simulator toughness units.
- Simulator binding allowed: `false`

### pela.technique.debuff_scope

- Registry fact(s): pela_technique_structure
- Provenance: gachabase_pela: Structured text specifies all enemies.; hoyolab_pela_v2_1: Guide specifies all-enemy DEF reduction.
- Version: stable pre-3.4 core
- Unresolved: None
- Simulator binding allowed: `false`

### pela.technique.target_scope

- Registry fact(s): pela_technique_structure
- Provenance: gachabase_pela: Structured technique text specifies a random enemy.; hoyolab_pela_v2_1: Version 2.1 guide specifies random-enemy damage.
- Version: stable pre-3.4 core
- Unresolved: None
- Simulator binding allowed: `false`

### pela.technique.trace_assumptions

- Registry fact(s): pela_technique_trace_assumptions
- Provenance: local_evidence_report: No accepted build or trace level.
- Version: 3.4 trace
- Unresolved: Build, trace level, and enemy state remain unknown.
- Simulator binding allowed: `false`

### pela.ultimate.energy_cost

- Registry fact(s): pela_ultimate_structure
- Provenance: gachabase_pela: Structured resource field lists 110.
- Version: current structured data; exact 3.4 revision unavailable
- Unresolved: Downgraded from compound corroboration; trace energy unknown.
- Simulator binding allowed: `false`

### pela.ultimate.exposed_duration

- Registry fact(s): pela_ultimate_structure
- Provenance: gachabase_pela: Structured text gives two turns.; hoyolab_pela_v2_1: Guide gives two turns.
- Version: stable pre-3.4 core
- Unresolved: Duration anchor requires later engine review.
- Simulator binding allowed: `false`

### pela.ultimate.target_scope

- Registry fact(s): pela_ultimate_structure
- Provenance: gachabase_pela: Structured Ultimate is AoE.; hoyolab_pela_v2_1: Guide Ultimate targets all enemies.
- Version: stable pre-3.4 core
- Unresolved: Resulting enemy state unknown.
- Simulator binding allowed: `false`

### pela.ultimate.trace_assumptions

- Registry fact(s): pela_ultimate_trace_assumptions
- Provenance: local_evidence_report: Level and resulting state absent.
- Version: 3.4 trace
- Unresolved: Do not use level-10 DEF value as trace value.
- Simulator binding allowed: `false`

### rtb.skill.observed_companion_state

- Registry fact(s): rtb_skill_companion_state
- Provenance: local_evidence_report: Mem state is not validated.
- Version: 3.4 trace
- Unresolved: Cannot choose summon versus restore/charge branch.
- Simulator binding allowed: `false`

### rtb.skill.present_mem_charge_gain

- Registry fact(s): rtb_skill_structure
- Provenance: gachabase_rtb_4_1: Structured branch grants 10% Charge.; hoyolab_rtb_v3_0: Version 3.0 guide grants 10% Charge.
- Version: 3.0 core applicable to 3.4
- Unresolved: Only applies if Mem is already present.
- Simulator binding allowed: `false`

### rtb.skill.sp_delta

- Registry fact(s): rtb_skill_structure
- Provenance: gachabase_rtb_4_1: Structured resource field lists -1 SP.
- Version: 4.1 structured snapshot; 3.4 raw revision unavailable
- Unresolved: Downgraded from compound corroboration; guide did not directly expose SP field.
- Simulator binding allowed: `false`

### rtb.skill.target_scope

- Registry fact(s): rtb_skill_structure
- Provenance: gachabase_rtb_4_1: Structured skill targets/summons Mem.; hoyolab_rtb_v3_0: Version 3.0 guide targets/summons Mem.
- Version: 3.0 core applicable to 3.4
- Unresolved: Pre-skill companion state unknown.
- Simulator binding allowed: `false`

### tingyun.skill.benediction_duration

- Registry fact(s): tingyun_skill_structure
- Provenance: gachabase_tingyun: Structured text gives three turns.; hoyolab_tingyun_v1: Guide gives three turns.
- Version: stable 1.0 core applicable to 3.4
- Unresolved: Duration decrement semantics need later review.
- Simulator binding allowed: `false`

### tingyun.skill.observed_target_and_level

- Registry fact(s): tingyun_skill_trace_target_and_level
- Provenance: local_evidence_report: Target and level absent.
- Version: 3.4 trace
- Unresolved: Target and trace level remain unknown.
- Simulator binding allowed: `false`

### tingyun.skill.sp_delta

- Registry fact(s): tingyun_skill_structure
- Provenance: gachabase_tingyun: Structured resource field lists -1 SP.
- Version: current structured data; exact 3.4 revision unavailable
- Unresolved: Downgraded from compound corroboration.
- Simulator binding allowed: `false`

### tingyun.skill.target_scope

- Registry fact(s): tingyun_skill_structure
- Provenance: gachabase_tingyun: Structured skill targets one ally.; hoyolab_tingyun_v1: Guide targets one ally.
- Version: stable 1.0 core applicable to 3.4
- Unresolved: Observed ally unknown.
- Simulator binding allowed: `false`

### tingyun.ultimate.damage_buff_duration

- Registry fact(s): tingyun_ultimate_structure
- Provenance: gachabase_tingyun: Structured field specifies two turns.; hoyolab_tingyun_v1: Guide specifies two turns.
- Version: stable 1.0 core applicable to 3.4
- Unresolved: Exact duration decrement semantics require later engine review.
- Simulator binding allowed: `false`

### tingyun.ultimate.energy_cost

- Registry fact(s): tingyun_ultimate_cost
- Provenance: gachabase_tingyun: Structured data lists 130.; hoyolab_tingyun_v1: Guide lists 130.
- Version: stable 1.0 core applicable to 3.4
- Unresolved: Trace energy state unknown.
- Simulator binding allowed: `false`

### tingyun.ultimate.observed_target

- Registry fact(s): tingyun_ultimate_trace_target
- Provenance: local_evidence_report: Step 1 target is unknown.
- Version: 3.4 trace
- Unresolved: Do not infer target.
- Simulator binding allowed: `false`

### tingyun.ultimate.target_energy_restore

- Registry fact(s): tingyun_ultimate_structure
- Provenance: gachabase_tingyun: Structured data specifies 50 target Energy.; hoyolab_tingyun_v1: Guide specifies 50 target Energy.
- Version: stable 1.0 core applicable to 3.4
- Unresolved: Target is unknown.
- Simulator binding allowed: `false`

### tingyun.ultimate.target_scope

- Registry fact(s): tingyun_ultimate_structure
- Provenance: gachabase_tingyun: Structured data specifies one ally.; hoyolab_tingyun_v1: Guide specifies one ally.
- Version: stable 1.0 core applicable to 3.4
- Unresolved: Observed ally remains unknown.
- Simulator binding allowed: `false`

## Toughness Source Conventions

- anaxa.skill.toughness_native: native `10` in `gachabase_break_in_game_display_selected_target`; normalized `None`; Native selected-target display retained without conversion.
- anaxa.ultimate.toughness_native: native `20` in `gachabase_break_in_game_display_aoe`; normalized `None`; Native AoE display retained without conversion.
- pela.skill.toughness_native: native `20` in `gachabase_break_in_game_display`; normalized `None`; Source-native display retained; no conversion is assumed.

## Mem Timing and Charge Separation

- mem.support.charge_cost: `charge_consumption_cost` = `None` (missing)
- mem.support.charge_readiness_threshold: `charge_readiness_threshold` = `100` (corroborated)
- mem.support.duration: `support_duration` = `3` (corroborated)
- mem.support.own_immediate_action: `mem_own_timing` = `immediate_action_self` (corroborated)
- mem.support.self_target_suppression: `self_target_suppresses_action_advance` = `True` (corroborated)
- mem.support.target_action_advance: `selected_ally_action_advance` = `100` (corroborated)
- mem.support.trace_charge_state: `observed_charge_and_timeline_state` = `None` (missing)

## Binding Readiness Matrix

| Item | Actor | Action | Resolved | Partial | Missing/conflicting | Status |
|---|---|---|---:|---:|---:|---|
| prebattle | pela | technique | 2 | 0 | 1 | not_ready |
| step_1 | tingyun | ultimate | 4 | 0 | 1 | not_ready |
| step_2 | pela | skill | 5 | 0 | 1 | not_ready |
| step_3 | remembrance_trailblazer | skill | 3 | 0 | 1 | not_ready |
| step_4 | tingyun | skill | 3 | 0 | 1 | not_ready |
| step_5 | pela | ultimate | 3 | 0 | 1 | not_ready |
| step_6 | naxia | ultimate | 4 | 0 | 1 | not_ready |
| step_7 | naxia | basic_plus_extra_skill | 3 | 0 | 1 | not_ready |
| step_8 | mem | advance_naxia | 5 | 0 | 2 | not_ready |
| step_9 | naxia | skill_plus_extra_skill | 5 | 0 | 1 | not_ready |

## Readiness Blockers

### prebattle: pela / technique

- Trace blockers: Initial enemy state and prebattle debuff state.; The accepted trace records technique use but not validated effect values or scope.; target scope unknown
- Source/version blockers: Build, trace level, and enemy state remain unknown.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

### step_1: tingyun / ultimate

- Trace blockers: Initial Tingyun energy and team state.; The accepted trace does not identify Tingyun ultimate target or resulting state.; unknown target
- Source/version blockers: Do not infer target.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

### step_2: pela / skill

- Trace blockers: Initial SP, enemy state, and buff/debuff state.; The accepted trace does not identify Pela skill target or outcome.; unknown target
- Source/version blockers: Target and trace level remain unknown.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

### step_3: remembrance_trailblazer / skill

- Trace blockers: Initial SP, companion state, and enemy state.; The accepted trace does not validate target or companion state.; unknown target and companion state
- Source/version blockers: Cannot choose summon versus restore/charge branch.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

### step_4: tingyun / skill

- Trace blockers: Initial SP, energy, and buff state.; The accepted trace does not identify Tingyun skill target or resulting buff state.; unknown target
- Source/version blockers: Target and trace level remain unknown.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

### step_5: pela / ultimate

- Trace blockers: Initial energy, enemy state, and debuff state.; Target scope and resulting debuff values are not validated.; target scope unknown
- Source/version blockers: Do not use level-10 DEF value as trace value.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

### step_6: naxia / ultimate

- Trace blockers: Initial energy, enemy state, and combat state.; The accepted trace does not validate target or resulting combat state.; unknown target
- Source/version blockers: Control RES and enemy state unknown.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

### step_7: naxia / basic_plus_extra_skill

- Trace blockers: Initial resources, trigger state, and enemy state.; The accepted trace does not identify internal split, targets, or trigger conditions.; unknown target
- Source/version blockers: Composite remains non-executable.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

### step_8: mem / advance_naxia

- Trace blockers: Initial action order, speed/AV, companion charge, and trigger state.; The accepted trace establishes sequence only and supplies no advance amount or immediate-action claim.
- Source/version blockers: Charge history and AV state remain unknown.; No accepted field-specific provenance directly establishes consumption; threshold is not inherited as cost.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

### step_9: naxia / skill_plus_extra_skill

- Trace blockers: Initial resources, trigger state, and enemy state.; The accepted trace does not identify internal split, targets, or trigger conditions.; unknown target
- Source/version blockers: Composite remains non-executable.
- Engine review blockers: Character-specific binding and engine capability review have not been performed.
- Simulator binding allowed: `false`

## Candidate Actions for Later Binding Review

- Acquire accepted trace targets, builds, initial resources, enemy state, and Mem Charge history.
- Keep Mem own immediate action separate from selected-ally action advance during any later design review.
- Review character-specific bindings only after every required atom and trace blocker is resolved.
- Review source-native toughness conventions and define a documented conversion only if authoritative engine mapping exists.
