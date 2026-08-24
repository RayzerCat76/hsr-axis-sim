# 002L Reference — Accepted Tingyun Ultimate Atomic Facts

Use only the accepted normalized artifact:

`hsr_axis_sim/data/manual_video_traces/normalized_character_facts/real_video_trace_001_atomic_facts_v0_1.json`

Pinned SHA-256:

`b17a5f295cb8902883d6e8ddaa70c626bdbddf60572db8ce28da6eb3c555491f`

## Facts allowed in the executable partial shell

### `tingyun.ultimate.target_scope`

- normalized value: `single_ally`
- verification: `corroborated`
- action category: `ultimate`
- timing classification: `ultimate_interrupt`

### `tingyun.ultimate.energy_cost`

- normalized value: `130`
- unit: Energy
- verification: `corroborated`

### `tingyun.ultimate.target_energy_restore`

- normalized value: `50`
- unit: Energy
- verification: `corroborated`

## Facts that must remain outside execution in 002L

### `tingyun.ultimate.damage_buff_duration`

- normalized value: `2 turns`
- value is sourced, but exact simulator decrement/expiration semantics are not yet reviewed for this real binding;
- do not add a buff in 002L.

### `tingyun.ultimate.observed_target`

- normalized value: `null`
- verification: `missing`
- do not infer the real-video target.

## Binding boundary

002L may implement only:

- one selected ally as a synthetic/test target;
- Tingyun consumes 130 Energy;
- selected ally gains 50 Energy, clamped by existing generic energy rules;
- execution is an Ultimate interrupt;
- no normal turn ends;
- no AV or global time advances.

002L must not implement:

- the DMG-increase buff;
- buff magnitude;
- buff duration/decrement behavior;
- a real-video target;
- damage or toughness;
- Tingyun's complete Ultimate or kit;
- registration in normal character data/action generation;
- real-trace execution.
