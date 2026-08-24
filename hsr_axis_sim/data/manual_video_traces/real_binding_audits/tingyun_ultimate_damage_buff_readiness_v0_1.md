# Tingyun Ultimate Damage-Buff Fact and Duration Review

> NON-EXECUTABLE EVIDENCE REVIEW. This report does not apply Tingyun's DMG buff, select a real-video target or trace level, or authorize simulator binding.

Readiness: `blocked_by_both`  
Review version: `0.1`

## Source Catalog

| Source | Type | Version | Locator |
|---|---|---|---|
| gachabase_tingyun | structured_game_database | current release dataset; stable core cross-checked to v1.0 | https://hsr.gachabase.net/characters/1202/tingyun/release |
| hoyolab_tingyun_v1 | community_mechanics_reference | 1.0 | https://www.hoyolab.com/article/18920104 |
| local_evidence_report | manual_video_evidence | 3.4 trace context | local://hsr_axis_sim/data/manual_video_traces/reports/real_video_trace_001_botu_dilemma_evidence_report_v0_1.json |

## Atomic Facts

| Fact | Value | Status | Version scope |
|---|---|---|---|
| tingyun.ultimate.damage_buff.application_order | null | unresolved | Release descriptions in accepted local provenance do not distinguish effect order. |
| tingyun.ultimate.damage_buff.duration_turns | 2 | corroborated | Stable v1.0 core mechanic treated as applicable to the recorded 3.4 trace. |
| tingyun.ultimate.damage_buff.magnitude_by_trace_level | null | missing | A release/live trace-level table is required; no table is preserved in accepted local provenance. |
| tingyun.ultimate.damage_buff.real_video_trace_level | null | missing | Recorded 3.4 trace only. |
| tingyun.ultimate.damage_buff.release_scope | "v1.0_release_core_applicable_to_3.4_with_current_structured_page_version_ambiguity" | corroborated | The v1.0 guide predates 3.4; the registered current structured page postdates 3.4. |
| tingyun.ultimate.damage_buff.target_scope | "selected_single_ally" | corroborated | Stable v1.0 core mechanic treated as applicable to the recorded 3.4 trace. |

## Field-Level Provenance

### tingyun.ultimate.damage_buff.application_order

- `gachabase_tingyun` (release_structured_data, does_not_distinguish): Accepted source-registry Ultimate summary. The accepted summary lists Energy restoration and the DMG buff but preserves no execution-order field.
- `hoyolab_tingyun_v1` (release_community_reference, does_not_distinguish): Accepted source-registry Ultimate summary. The accepted guide summary does not establish whether buff application precedes Energy restoration.
- Unresolved: A later binding must not choose effect order without a release-data locator or interaction test.

### tingyun.ultimate.damage_buff.duration_turns

- `gachabase_tingyun` (release_structured_data, supports_exact_field): Character 1202 release data > Ultimate effect description > duration. The accepted structured-source summary records a two-turn DMG buff.
- `hoyolab_tingyun_v1` (release_community_reference, supports_exact_field): Version 1.0 guide > Ultimate description > duration. The accepted v1.0 guide summary independently records two turns.
- Unresolved: The source summaries do not define the same-current-turn decrement edge.

### tingyun.ultimate.damage_buff.magnitude_by_trace_level

- `gachabase_tingyun` (release_structured_data, supports_context_only): Accepted source-registry summary only; exact Ultimate level-scaling field path was not preserved. The accepted record establishes that the DMG buff is level-dependent but does not preserve its level table.
- `hoyolab_tingyun_v1` (release_community_reference, supports_context_only): Accepted source-registry summary only; exact per-level magnitude locator was not preserved. The accepted guide record confirms a level-dependent buff but not a normalized per-level table.
- Unresolved: Do not infer level 1-12 magnitudes or assume a real-video trace level.

### tingyun.ultimate.damage_buff.real_video_trace_level

- `local_evidence_report` (accepted_manual_evidence, supports_exact_field): Step 1 accepted evidence > known and unknown fields. The accepted video evidence records the action but no Tingyun trace level.
- Unresolved: No real-video magnitude may be selected from a level table even after that table is sourced.

### tingyun.ultimate.damage_buff.release_scope

- `gachabase_tingyun` (release_structured_data, supports_exact_field): Registered source metadata > game_version and qualification_notes. The registered structured source is release data but its current snapshot postdates the trace.
- `hoyolab_tingyun_v1` (release_community_reference, supports_exact_field): Registered source metadata > game_version 1.0. The registered community guide is release-era v1.0 and predates the 3.4 trace.
- Unresolved: No accepted byte-identical 3.4 field snapshot is available.

### tingyun.ultimate.damage_buff.target_scope

- `gachabase_tingyun` (release_structured_data, supports_exact_field): Character 1202 release data > Ultimate target/effect description. The accepted source-registry record identifies the Ultimate as affecting one selected ally.
- `hoyolab_tingyun_v1` (release_community_reference, supports_exact_field): Version 1.0 guide > Ultimate description. The accepted v1.0 guide record independently identifies one ally.
- Unresolved: The accepted video does not identify which ally was selected.

## Duration-Semantics Review

- Verified duration: `2` turns.
- Engine duration type: `target_normal_turns`.
- Start: Immediately when the AddBuff effect applies and stores remaining_turns=2.
- Cast interrupt decrements: `false`.
- Current target normal turn decrements at end if already applied: `true`.
- Extra turns decrement: `false`.
- Non-ending actions decrement: `false`.
- Expiration boundary: The buff is removed at the end of the second target normal turn counted after application; if applied during the target's already-active normal turn, that current turn end is count one.
- Representation: `representable_with_source_unverified_same_turn_edge`.
- Verified game equivalence: `false`.
- Assessment: The engine represents a two-target-normal-turn counter without interrupt, extra-turn, or non-ending-action decrements. Accepted sources do not verify whether the game counts an already-active target turn, so equivalence at that edge remains a source question rather than a demonstrated engine defect.

## Binding Readiness

- Status: `blocked_by_both`.
- Simulator binding allowed: `false`.
- Blockers:
  - No accepted release/live per-trace-level DMG-increase magnitude table with field locator.
  - No accepted source distinguishes damage-buff application order from target Energy restoration.
  - The same-current-turn duration edge is deterministic in the engine but not verified against release behavior.
- Recommended research actions:
  - Capture a release-data effect sequence or controlled interaction test for buff-versus-Energy order.
  - Capture a version-qualified release-data level table for the Ultimate DMG-increase field.
  - Verify whether an Ultimate cast during the target's active normal turn consumes one duration count at that turn end.
- Research limitations:
  - Direct re-retrieval of the two registered external pages was unavailable in this environment; only accepted local source-registry records were used.
  - No magnitude or effect order was inferred from memory, animation, or the real video.
