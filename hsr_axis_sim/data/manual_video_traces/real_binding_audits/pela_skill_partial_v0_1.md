# Pela Skill Partial Binding Audit: pela_skill_partial_resource_target_dispel_shell_v0_1

> PARTIAL BINDING SHELL ONLY. complete_game_skill=false; no damage or toughness semantics are implemented.

## Bound Atomic Fields

- `pela.skill.dispel_count`
- `pela.skill.energy_generation`
- `pela.skill.sp_delta`
- `pela.skill.target_scope`

## Deliberately Not Bound

- `build_assumptions`
- `damage_multiplier`
- `debuff_application`
- `eidolon_trace_light_cone_relic_team_interactions`
- `final_damage`
- `normalized_toughness`
- `observed_real_video_target`
- `pela.skill.observed_target_and_level`
- `pela.skill.toughness_native`
- `trace_level`

## Generic Primitives Used

- single-enemy target validation
- skill-point consumption
- actor energy gain
- ID-specific buff removal
- normal turn completion

## Generic Extensions Added

- None.

## Synthetic Fixture Result

- Removed buff: `alpha_guard`
- SP: 3 -> 2
- Pela Energy: 10 -> 40
- Target HP: 2000 -> 2000
- Target toughness: 60 -> 60
- Normal turn ended: `true`

## Real Trace Status

- Executable: `false`
- Observed real-video target is unknown.
- Damage, normalized toughness, trace level, build, and initial state remain unresolved.
- This shell is synthetic-only and is not a complete Pela skill or kit.
