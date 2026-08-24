# Reviewed Partial-Binding Registry Audit

Registry version: `0.2`  
Reviewed bindings: `2`

> All reviewed bindings are partial, synthetic-only shells. Raw binding dictionaries are not the reviewed public execution contract, and the real trace is non-executable.

| Binding | Actor | Action | Scope | Handler | Complete skill | Complete kit | Synthetic only | Real trace executable | Damage | Toughness |
|---|---|---|---|---|---|---|---|---|---|---|
| pela_skill_partial_resource_target_dispel_shell_v0_1 | pela | skill | partial_resource_target_dispel_shell | pela_skill_partial_v0_1 | `false` | `false` | `true` | `false` | not_implemented | not_implemented |

## pela_skill_partial_resource_target_dispel_shell_v0_1

- Accepted atomic digest: `b17a5f295cb8902883d6e8ddaa70c626bdbddf60572db8ce28da6eb3c555491f`
- Bound facts: pela.skill.target_scope, pela.skill.sp_delta, pela.skill.energy_generation, pela.skill.dispel_count
- Unresolved facts: pela.skill.observed_target_and_level, pela.skill.toughness_native
- Unresolved fields: damage_multiplier, final_damage, trace_level, build_assumptions, observed_real_video_target, normalized_toughness, debuff_application, eidolon_trace_light_cone_relic_team_interactions
| tingyun_ultimate_partial_resource_interrupt_shell_v0_1 | tingyun | ultimate | partial_resource_interrupt_shell | tingyun_ultimate_partial_v0_1 | `false` | `false` | `true` | `false` | not_implemented | not_implemented |

## tingyun_ultimate_partial_resource_interrupt_shell_v0_1

- Accepted atomic digest: `b17a5f295cb8902883d6e8ddaa70c626bdbddf60572db8ce28da6eb3c555491f`
- Bound facts: tingyun.ultimate.target_scope, tingyun.ultimate.energy_cost, tingyun.ultimate.target_energy_restore
- Unresolved facts: tingyun.ultimate.damage_buff_duration, tingyun.ultimate.observed_target
- Unresolved fields: damage_buff_magnitude, damage_buff_duration_decrement_and_expiration, observed_real_video_target, real_video_initial_energy_and_combat_state

## Real Trace Status

- Executable: `false`
- No registry entry authorizes real-video target inference or complete-skill/kit registration.
