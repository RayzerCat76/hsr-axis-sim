# Tingyun Ultimate Current-Contract Effect-Order Proof

> NON-EXECUTABLE CURRENT-CONTRACT PROOF. Release-game effect order and duration semantics remain unknown; this report does not authorize a Tingyun DMG buff.

Conclusion: `proven_irrelevant_under_current_simulator_contract`  
Derived generic readiness: `blocked_by_duration_semantics`  
Accepted-video readiness: `blocked_by_unknown_target_and_trace_level`

## Pinned Sources

| Source | Path | SHA-256 |
|---|---|---|
| action | `sim/action.py` | `ad6994e79d8c8833304df4d4cc67ea84c07db988f4b9365840e0707dd5100f34` |
| buffs | `sim/buffs.py` | `7095d592ee4466396bcd2224d740aa780271e7f539cd9751949ee41c1f5837b5` |
| effects | `sim/effects.py` | `3adb44ababa1725933c82a105706b388239d895a98f159db5c4691a12dfa9618` |
| enemy_ai | `sim/enemy_ai.py` | `98d735e7cb03ae108106f5e09d52908bc81da4815e19cea2725ef44ae7d9dd9e` |
| events | `sim/events.py` | `79e9a95d0788a1b87980f9de1fa58c48feccd34f4730a67798d6feb832f93525` |
| regression_manifest | `data/regression_manifest.json` | `acfb663d7dbd93f3b0bdba9838a8b2a0712df144da14aae513830c406f142a02` |
| reviewed_registry | `real_bindings/registry_v0_2.json` | `0cd0c9f9d4594654aaae91fa834988a4a373674d8e6397e757165d4f76fd11b8` |
| semantic_readiness_input | `data/manual_video_traces/normalized_character_facts/tingyun_ultimate_damage_buff_semantic_readiness_v0_1.json` | `29ece44c9bc051590c308f7b6774ce192a47e11ec5176cf5adf645336c3025f1` |
| semantic_readiness_report | `data/manual_video_traces/real_binding_audits/tingyun_ultimate_damage_buff_semantic_readiness_v0_1.json` | `d401cb85ff580d563ff44e415c1bd379957caa6e5a7a6f0353e68aef6e802a21` |
| state | `sim/state.py` | `7d91095f082e60da27730b713fed3b08e47d0f3c422c26ae18a507c63a8b236a` |
| targets | `sim/targets.py` | `42384f5b561b99df5f16828784538a5e692ba75d75e0fdcf374c8045642361dc` |
| tingyun_partial_binding | `real_bindings/tingyun_ultimate_v0_1.py` | `d852cb0fee019a08e57d33f39f5d88c8774cbe018ea9a600ad6d334afa8007f5` |
| turn_context | `sim/turn_context.py` | `a670688d83bf986c5b5edeb094124454d1e69c58c2953c2e11f79d133f68aeaa` |
| unit | `sim/unit.py` | `f4e100a12d1ae160fc58f9ef874fe188851d7f29284acef4c51273792f41eb62` |

## Current Observable Contract

- snapshot_fields: `action_result, state, turn_context`
- state_fields: `enemy_ai_cursors, enemy_ai_plans, event_dispatch_count, event_dispatch_limit, extra_turn_stack, global_av, logs, max_skill_points, pending_events, skill_points, trigger_fire_counts, triggers, units`
- unit_fields: `all_res, atk, base_speed, break_effect, buffs, crit_dmg, crit_rate, current_av, current_toughness, debuffs, defense, dmg_bonus, element, energy, fire_res, hp, ice_res, id, imaginary_res, is_alive, is_broken, level, lightning_res, max_energy, max_hp, max_toughness, name, physical_res, quantum_res, speed, team, weaknesses, wind_res`
- buff_fields: `data, duration_type, id, kind, max_stacks, name, remaining_turns, source_id, stacks, target_id`
- event_fields: `data, type`
- trigger_fields: `condition, effects, enabled, event_type, id, max_triggers_per_action, owner_id`
- turn_context_fields: `actions_taken, actor_id, forced_rng, is_extra_turn, is_interrupt, should_end_turn`
- action_result_fields: `return_type, returned_same_context`
- excluded_fields: `none`

## Synthetic Comparisons

| Case | Energy | Max | Existing probe | Equal | Snapshot SHA-256 |
|---|---:|---:|---|---|---|
| at_cap_existing_probe_refresh | 100 | 100 | `true` | `true` | `5f8fbdbd967ca8182604bf7652be03f41def839e3463c348eeb15a624f594ee3` |
| at_cap_no_existing_probe | 100 | 100 | `false` | `true` | `9304b4a5e2ca012a54fe3b07eb69a8123c3970e0a44a52ce6dacdbdea0d2e409` |
| below_cap_existing_probe_refresh | 10 | 100 | `true` | `true` | `6c5ce18d29c86199e7b70c4ed39f8c2af5a1e6972b9d27218fddb8107de9befb` |
| below_cap_no_existing_probe | 10 | 100 | `false` | `true` | `dfacf38c6e95e66f4061d5531ed5f21c7306c5ef67e9e6c73c16ec0044dc104e` |
| near_cap_existing_probe_refresh | 80 | 100 | `true` | `true` | `5f8fbdbd967ca8182604bf7652be03f41def839e3463c348eeb15a624f594ee3` |
| near_cap_no_existing_probe | 80 | 100 | `false` | `true` | `9304b4a5e2ca012a54fe3b07eb69a8123c3970e0a44a52ce6dacdbdea0d2e409` |

## Proof Boundary

- Invalid configurations, exceptions, and future engine changes are outside the proof.
- No current primitive event exposes intermediate state between action_started and action_finished.
- Release-game effect order remains unknown.
- Same-current-turn duration semantics remain unresolved.
- The accepted-video target and Tingyun trace level remain unknown.
- The conclusion applies only to the pinned current simulator code and valid static GainEnergy/AddBuff configuration.

- Release-game order known: `false`
- Same-current-turn duration resolved: `false`
- Accepted-video target: `null`
- Accepted-video trace level: `null`
- Simulator binding allowed: `false`
