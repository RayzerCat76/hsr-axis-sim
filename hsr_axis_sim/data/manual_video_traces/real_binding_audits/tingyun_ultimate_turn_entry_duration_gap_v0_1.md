# Tingyun Ultimate Turn-Entry Duration Evidence and Engine-Gap Audit

> NON-EXECUTABLE DURATION EVIDENCE/GAP AUDIT. The turn-entry correction is accepted project-domain input pending independent frame verification; no runtime policy is selected.

Conclusion: `turn_entry_claim_normalized_current_engine_gap_confirmed_runtime_change_blocked`  
Accepted project-domain boundary: `target_normal_turn_entry`  
Generic readiness: `blocked_by_duration_semantics`

## Evidence Status

| Claim | Value | Status |
|---|---|---|
| bilibili_candidate | `"BV1yz4y1t79s"` | candidate_identified_page_or_frames_not_retrieved |
| duration_count_2 | `2` | source_cross_checked |
| extra_action_consumption | `null` | unresolved_not_infer_from_normal_turn_entry |
| extra_turn_consumption | `null` | unresolved_not_infer_from_normal_turn_entry |
| same_id_refresh_active_turn | `null` | unresolved |
| turn_entry_settlement | `"target_normal_turn_entry"` | accepted_project_domain_correction_pending_independent_frame_verification |
| turn_started_event_order | `null` | unresolved |
| zero_counter_effect_lifetime | `null` | unresolved |

## Current Engine Audit

- normal_turn_actor_selection: `"Timeline._select_next_normal_actor"`
- normal_turn_started_emission: `"Timeline.next_turn emits turn_started after selecting the normal actor"`
- extra_turn_started_emission: `"Timeline.next_turn emits turn_started for a popped extra-turn actor"`
- target_normal_turn_tick_boundary: `"Timeline.end_turn after a normal turn"`
- current_turn_expiration_boundary: `"Timeline.end_turn for every unit after normal or extra turn end"`
- same_id_refresh_behavior: `"_add_status directly refreshes remaining_turns when refresh_policy is refresh"`
- buff_application_turn_marker_present: `false`
- target_normal_turn_entry_tick_path_present: `false`
- current_engine_conforms_to_accepted_boundary: `false`

## Gap Classification

| Gap | Status | Summary |
|---|---|---|
| GAP_EXTRA_ACTION_CONSUMPTION | unresolved | Non-turn extra-action consumption cannot be inferred from normal-turn-entry wording. |
| GAP_EXTRA_TURN_CONSUMPTION | unresolved | Granted extra-turn consumption cannot be inferred from normal-turn-entry wording. |
| GAP_GLOBAL_MIGRATION_IMPACT | unresolved | Changing the shared target_normal_turns contract requires a separate global migration audit. |
| GAP_SAME_ID_REFRESH_AT_ACTIVE_TURN | unresolved | Same-ID refresh semantics during an already-active turn are not verified. |
| GAP_TARGET_NORMAL_TURN_TICK_BOUNDARY | proven_current_engine_gap | Accepted project-domain settlement is target normal-turn entry; pinned engine mutation is target normal-turn end. |
| GAP_TURN_STARTED_EVENT_ORDER | unresolved | Release-game decrement/removal order relative to turn_started is not verified. |
| GAP_ZERO_COUNTER_EFFECT_LIFETIME | unresolved | Effect activity during the entered turn when the counter reaches zero is not verified. |

## Synthetic Boundary Matrix

| Case | Evidence boundary | Current engine boundary | Decidable | Unsafe runtime assertion | Checkpoints |
|---|---|---|---|---|---|
| action_advanced_into_next_normal_turn | target_normal_turn_entry | target_normal_turn_end_or_absent_for_non_normal_turn_boundary | `false` | `true` | `{"after_action_advance": 2, "after_normal_turn_end": 1, "after_normal_turn_entry": 2}` |
| applied_before_next_normal_turn | target_normal_turn_entry | target_normal_turn_end_or_absent_for_non_normal_turn_boundary | `false` | `true` | `{"after_application": 2, "after_normal_turn_end": 1, "after_normal_turn_entry": 2}` |
| applied_during_active_normal_turn | target_normal_turn_entry | target_normal_turn_end_or_absent_for_non_normal_turn_boundary | `false` | `true` | `{"after_active_normal_turn_end": 1, "after_interrupt_application": 2, "before_application_after_entry": null}` |
| evidence_model_counter_transitions | target_normal_turn_entry | target_normal_turn_end_or_absent_for_non_normal_turn_boundary | `false` | `true` | `{"current_engine_after_end_from_1": null, "current_engine_after_entry_from_1": 1, "evidence_model_candidate_transition_1_to_0": "target_normal_turn_entry", "evidence_model_candidate_transition_2_to_1": "target_normal_turn_entry"}` |
| granted_extra_turn | target_normal_turn_entry | target_normal_turn_end_or_absent_for_non_normal_turn_boundary | `false` | `true` | `{"after_extra_turn_end": 2, "after_extra_turn_entry": 2}` |
| non_ending_extra_action | target_normal_turn_entry | target_normal_turn_end_or_absent_for_non_normal_turn_boundary | `false` | `true` | `{"after_non_ending_action": 2}` |
| same_id_refresh_during_active_normal_turn | target_normal_turn_entry | target_normal_turn_end_or_absent_for_non_normal_turn_boundary | `false` | `true` | `{"after_active_normal_turn_end": 1, "after_entry_before_refresh": 1, "after_same_id_refresh": 2}` |

## Runtime Boundary

- Old 002Q obsolete: `true`
- End-turn dual policy selected: `false`
- Executable release-game duration policy: `null`
- Independent frame verification: `pending`
- Accepted-video readiness: `blocked_by_unknown_target_and_trace_level`
- Accepted-video target: `null`
- Accepted-video trace level: `null`
- Simulator binding allowed: `false`
