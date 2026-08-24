# Tingyun Ultimate DMG-Buff Semantic Readiness Review

> NON-EXECUTABLE SEMANTIC READINESS REVIEW. This report does not add a buff, select a target or trace level, or authorize real-video execution.

## Readiness Axes

- Generic binding: `blocked_by_both_semantics`
- Accepted video binding: `blocked_by_unknown_target_and_trace_level`
- Accepted video semantic readiness: `blocked_by_both_semantics`
- Simulator binding allowed: `false`

## Validated Inputs

| Role | Path | SHA-256 |
|---|---|---|
| historical_fact_review | `data/manual_video_traces/normalized_character_facts/tingyun_ultimate_damage_buff_review_v0_1.json` | `0ab56b31a2d9545ae80a2978c92c6a886393c6ceb00f7cc3d45eccf1f8d8ab2f` |
| historical_readiness_report | `data/manual_video_traces/real_binding_audits/tingyun_ultimate_damage_buff_readiness_v0_1.json` | `8cbdbec44c0132a7cc0c0eb4029357fe1f9feaa84f49b23ad79dc5d797eaf696` |
| magnitude_intake | `data/manual_video_traces/normalized_character_facts/tingyun_ultimate_damage_buff_magnitude_intake_v0_1.json` | `10a949ca4ff924fda8afe428a26bf8140a0b58e9116ad8a2b19346b6321ab376` |
| magnitude_report | `data/manual_video_traces/real_binding_audits/tingyun_ultimate_damage_buff_magnitude_intake_v0_1.json` | `0db037a12c3b51226dce79cb333d49170ca7963cb420dfe94bf385a531b2cfba` |
| reviewed_binding_registry | `real_bindings/registry_v0_2.json` | `0cd0c9f9d4594654aaae91fa834988a4a373674d8e6397e757165d4f76fd11b8` |
| source_registry | `data/manual_video_traces/source_registry/sources_v0_1.json` | `9a0fd2878e8b8bc6aec8afc6102c84627e00b08367399a21f3d9188a2a3f5408` |

## Semantic Claims

| Field | Status | Value |
|---|---|---|
| accepted_video_target | missing | null |
| accepted_video_trace_level | missing | null |
| duration_count | verified | 2 |
| effect_order | unresolved | null |
| magnitude_table | verified | "validated_levels_1_through_15" |
| same_current_turn_duration | unresolved | null |
| target_scope | verified | "selected_single_ally" |

## Magnitude Integration

- Validated levels: `1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15`
- Percentages: `20, 23, 26, 29, 32, 35, 38.75, 42.5, 46.25, 50, 53, 56, 59, 62, 65`
- Selected magnitude level: `null`

## Current Engine Boundary

- duration_type: `"target_normal_turns"`
- duration_count: `2`
- cast_interrupt_decrements: `false`
- already_active_target_turn_decrements_at_end: `true`
- extra_turn_decrements: `false`
- non_ending_action_decrements: `false`
- game_equivalence_verified: `false`
- expiration_boundary: `"The engine removes the buff at the end of the second target normal turn counted after application; an already-active target normal turn counts when it ends."`
- assessment_notes: `"This records current implementation behavior only and does not assert matching release-game semantics."`

## Blockers

Generic:
- Effect order relative to target Energy restoration is unresolved and not proven irrelevant to every event contract.
- Same-current-turn duration behavior is unresolved against release-game evidence.

Accepted video:
- Generic effect-order and duration semantics remain unresolved.
- The accepted video's Tingyun Ultimate trace level is unknown.
- The accepted video's selected ally is unknown.

## Controlled Interaction Protocols

### effect_order_controlled_interaction

Does target Energy restoration occur before or after DMG-buff application?

Result: `not_run`

1. Record the complete pre-cast state and trigger subscriptions.
1. Cast Tingyun Ultimate as an interrupt on the selected ally.
1. Capture ordered effect and trigger events from the same action boundary.
1. Repeat until the ordering observation is reproducible.

### same_current_turn_duration_controlled_interaction

Does the end of an ally's already-active normal turn consume the first count of a two-turn Tingyun Ultimate DMG buff?

Result: `not_run`

1. Record the selected ally's active normal-turn state.
1. Cast Tingyun Ultimate during that normal turn.
1. Record buff duration immediately after application and after the current turn ends.
1. Record the next two selected-ally normal-turn boundaries and exact expiration point.
1. Repeat with the Ultimate cast outside the ally's active turn as a control.

