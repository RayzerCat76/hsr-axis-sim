# Tingyun Ultimate DMG-Buff Magnitude Evidence Intake

> NON-EXECUTABLE MAGNITUDE EVIDENCE INTAKE. No row authorizes simulator binding or selection of a real-video trace level.

Intake status: `captured_exact_table`  
Readiness: `blocked_by_both`

## Accepted Sources

- `kqm_srl_commit_de0e5c09`: `KQM-git/SRL` commit `de0e5c09c8dbba9577367ad86e991fe91c4f0e36`, `src/data/characters/Tingyun.json`, `skills[name="Amidst the Rejoicing Clouds"].params[*][2]`. Pinned repository commit dated 2025-11-03; it corroborates rows at its snapshot level only.
- `mar7th_starrailres_v4_3_commit_7b349e39`: `Mar-7th/StarRailRes` commit `7b349e39ee0f6f3bf814567995829b99c95e7a93`, `index_new/en/character_skills.json`, `content["120203"].params[*][2]`. Pinned commit message states Update to version 4.3; this does not prove byte identity with 3.4.

## Context-Only Sources

- `gachabase_tingyun_v4_3_context`: Gachabase Tingyun release page (v4.3.0 release page context); `Ultimate Lv. 10 display: target DMG increase 50%, duration 2 turns, Energy restoration 50`. This source is not used as a complete table.

## Raw Source Tables

### kqm_srl_commit_de0e5c09

- Raw level 1: ratio 0.2
- Raw level 2: ratio 0.23
- Raw level 3: ratio 0.26
- Raw level 4: ratio 0.29
- Raw level 5: ratio 0.32
- Raw level 6: ratio 0.35
- Raw level 7: ratio 0.3875
- Raw level 8: ratio 0.425
- Raw level 9: ratio 0.4625
- Raw level 10: ratio 0.5
- Raw level 11: ratio 0.53
- Raw level 12: ratio 0.56
- Raw level 13: ratio 0.59
- Raw level 14: ratio 0.62
- Raw level 15: ratio 0.65
### mar7th_starrailres_v4_3_commit_7b349e39

- Raw level 1: ratio 0.2
- Raw level 2: ratio 0.23
- Raw level 3: ratio 0.26
- Raw level 4: ratio 0.29
- Raw level 5: ratio 0.32
- Raw level 6: ratio 0.35
- Raw level 7: ratio 0.3875
- Raw level 8: ratio 0.425
- Raw level 9: ratio 0.4625
- Raw level 10: ratio 0.5
- Raw level 11: ratio 0.53
- Raw level 12: ratio 0.56
- Raw level 13: ratio 0.59
- Raw level 14: ratio 0.62
- Raw level 15: ratio 0.65

## Normalized Table

- Trace level 1: 20%
- Trace level 2: 23%
- Trace level 3: 26%
- Trace level 4: 29%
- Trace level 5: 32%
- Trace level 6: 35%
- Trace level 7: 38.75%
- Trace level 8: 42.5%
- Trace level 9: 46.25%
- Trace level 10: 50%
- Trace level 11: 53%
- Trace level 12: 56%
- Trace level 13: 59%
- Trace level 14: 62%
- Trace level 15: 65%

## Acquisition Attempts

- None. The accepted tables are recorded above.

## Normalization

- Raw source rows are decimal ratios; normalized rows multiply each ratio by 100 and store unit `percent`.

## Blockers

- No magnitude-source blocker remains; readiness is still blocked by separately unresolved effect-order and duration-semantics evidence.

## Preserved Unknowns

- `damage_buff_application_order_relative_to_energy_restore`
- `real_video_selected_ally`
- `real_video_trace_level`
- `same_current_turn_duration_behavior`

- Real-video trace level: `null`.
- Simulator binding allowed: `false`.
