# Tingyun Ultimate Partial Binding Audit: tingyun_ultimate_partial_resource_interrupt_shell_v0_1

> PARTIAL RESOURCE/INTERRUPT SHELL ONLY. No damage buff, damage, toughness, real-video target, or complete Ultimate semantics are implemented.

## Bound Atomic Fields

- `tingyun.ultimate.energy_cost`
- `tingyun.ultimate.target_energy_restore`
- `tingyun.ultimate.target_scope`

## Deliberately Not Bound

- `damage_buff_duration_decrement_and_expiration`
- `damage_buff_magnitude`
- `observed_real_video_target`
- `real_video_initial_energy_and_combat_state`
- `tingyun.ultimate.damage_buff_duration`
- `tingyun.ultimate.observed_target`

## Generic Primitives Used

- single-ally target validation
- actor Energy consumption
- selected-target Energy gain with max-Energy clamp
- Ultimate interrupt execution

## Synthetic Fixture Result

- Tingyun Energy: 130 -> 0
- Selected ally Energy: 40 -> 90
- SP: 3 -> 3
- Global AV: 17 -> 17
- Interrupt: `true`
- Should end turn: `false`
- Normal turn ended: `false`

## Real Trace Status

- Executable: `false`
- The observed real-video target and initial Energy state are unknown.
- Damage-buff magnitude, duration decrement, and expiration semantics are not bound.
- This shell is synthetic-only and is not a complete Tingyun Ultimate or kit.
