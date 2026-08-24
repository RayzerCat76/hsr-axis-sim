# Simulator Binding Gap Inventory: real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only_evidence_report_v0_1

Inventory ID: `real_video_trace_001_botu_dilemma_binding_gap_inventory_v0_1`  
Version: `0.1`  
Source evidence report: `hsr_axis_sim/data/manual_video_traces/reports/real_video_trace_001_botu_dilemma_evidence_report_v0_1.json`

## Planning Boundary

> Planning inventory only, not an executable replay. Generic engine support does not verify a real-character binding. No combat values or semantics are inferred.

## Global Blockers

- Initial SP, energy, speed/AV, HP, toughness, buffs/debuffs, enemy state, and RNG are not known from accepted evidence.
- No accepted real-character bindings exist for Tingyun, Pela, Remembrance Trailblazer, Mem, or Naxia.
- Unknown targets and target scopes cannot be recovered from this video alone.

## Ordered Binding Assessments

| Step | Actor | Action | Statuses | Executable now |
|---:|---|---|---|---|
| 1 | tingyun | ultimate | generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked | `false` |
| 2 | pela | skill | generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked | `false` |
| 3 | remembrance_trailblazer | skill | generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked | `false` |
| 4 | tingyun | skill | generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked | `false` |
| 5 | pela | ultimate | generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked | `false` |
| 6 | naxia | ultimate | generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked | `false` |
| 7 | naxia | basic_plus_extra_skill | generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, unresolved_composite_action, video_insufficient, blocked | `false` |
| 8 | mem | advance_naxia | generic_primitive_available, missing_character_binding, missing_initial_state, unresolved_action_advance, video_insufficient, blocked | `false` |
| 9 | naxia | skill_plus_extra_skill | generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, unresolved_composite_action, video_insufficient, blocked | `false` |

## Prebattle Assessment

### pela / technique

- Semantic: 佩拉秘技开怪 (`prebattle_technique`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: normal action execution and target legality; generic buffs/debuffs
- Missing verified character-kit semantics: Verified Pela technique effects, target scope, and combat-entry binding.
- Missing initialization/resource data: Initial enemy state and prebattle debuff state.
- Unresolved trigger/composite behavior: Technique combat-entry effects are not bound.
- Evidence limitations: The accepted trace records technique use but not validated effect values or scope.
- Binding explanation: Generic technique-adjacent primitives exist, but no verified Pela binding or target scope is accepted.
- Minimum future work:
  - character_binding: Add verified Pela technique data and binding.
  - initial_state: Obtain initial enemy and prebattle state from authoritative evidence.

## Step Details

### Step 1: tingyun / ultimate

- Target status: unknown target
- Semantic: 停云终结技 (`ultimate_interrupt`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: skill/ultimate action categories; ultimate interrupt windows; energy and skill-point resources; target legality and action generation
- Missing verified character-kit semantics: Verified Tingyun ultimate target rule, resource cost, effects, and binding.
- Missing initialization/resource data: Initial Tingyun energy and team state.
- Unresolved trigger/composite behavior: Ultimate interrupt is observed, but its real-character effect is not bound.
- Evidence limitations: The accepted trace does not identify Tingyun ultimate target or resulting state.
- Binding explanation: Generic ultimate windows exist, but the recorded Tingyun action has no verified target or kit binding.
- Minimum future work:
  - character_binding: Add verified Tingyun ultimate data and binding.
  - target_evidence: Obtain Tingyun ultimate target evidence.
  - initial_state: Obtain accepted initial combat state.

### Step 2: pela / skill

- Target status: unknown target
- Semantic: 佩拉战技 (`normal_skill`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: normal action execution and action generation; skill/ultimate action categories; target legality and action generation; generic buffs/debuffs
- Missing verified character-kit semantics: Verified Pela skill effects, costs, debuff behavior, and binding.
- Missing initialization/resource data: Initial SP, enemy state, and buff/debuff state.
- Unresolved trigger/composite behavior: Skill effect and debuff outcome are not bound.
- Evidence limitations: The accepted trace does not identify Pela skill target or outcome.
- Binding explanation: Generic skill and debuff primitives exist, but real Pela semantics and target evidence are absent.
- Minimum future work:
  - character_binding: Add verified Pela skill data and binding.
  - target_evidence: Obtain Pela skill target evidence.
  - initial_state: Obtain accepted initial combat state.

### Step 3: remembrance_trailblazer / skill

- Target status: unknown target and companion state
- Semantic: 记忆主战技 (`normal_skill`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: normal action execution and action generation; skill/ultimate action categories; target legality and action generation; extra turns and trigger hooks
- Missing verified character-kit semantics: Verified Remembrance Trailblazer skill and companion binding.
- Missing initialization/resource data: Initial SP, companion state, and enemy state.
- Unresolved trigger/composite behavior: Companion-related behavior and triggers are not bound.
- Evidence limitations: The accepted trace does not validate target or companion state.
- Binding explanation: Generic skill and trigger hooks exist, but companion semantics are unverified.
- Minimum future work:
  - character_binding: Add verified Remembrance Trailblazer and companion data/binding.
  - target_evidence: Obtain Remembrance Trailblazer skill target evidence.
  - initial_state: Obtain accepted initial combat state.

### Step 4: tingyun / skill

- Target status: unknown target
- Semantic: 停云战技 (`normal_skill`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: normal action execution and action generation; skill/ultimate action categories; target legality and action generation; generic buffs/debuffs; energy and skill-point resources
- Missing verified character-kit semantics: Verified Tingyun skill target rule, costs, buff effects, and binding.
- Missing initialization/resource data: Initial SP, energy, and buff state.
- Unresolved trigger/composite behavior: Skill buff effects are not bound.
- Evidence limitations: The accepted trace does not identify Tingyun skill target or resulting buff state.
- Binding explanation: Generic support primitives exist, but Tingyun's real skill semantics and target are unverified.
- Minimum future work:
  - character_binding: Add verified Tingyun skill data and binding.
  - target_evidence: Obtain Tingyun skill target evidence.
  - initial_state: Obtain accepted initial combat state.

### Step 5: pela / ultimate

- Target status: target scope unknown
- Semantic: 佩拉终结技 (`ultimate_interrupt`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: skill/ultimate action categories; ultimate interrupt windows; generic buffs/debuffs; damage/toughness scaffolds
- Missing verified character-kit semantics: Verified Pela ultimate scope, debuff values, resource cost, and binding.
- Missing initialization/resource data: Initial energy, enemy state, and debuff state.
- Unresolved trigger/composite behavior: Ultimate debuff and resulting combat effects are not bound.
- Evidence limitations: Target scope and resulting debuff values are not validated.
- Binding explanation: Generic ultimate and debuff primitives exist, but scope and real Pela effects remain unknown.
- Minimum future work:
  - character_binding: Add verified Pela ultimate data and binding.
  - target_evidence: Obtain Pela ultimate target-scope evidence.
  - initial_state: Obtain accepted initial combat state.

### Step 6: naxia / ultimate

- Target status: unknown target
- Semantic: 那刻夏终结技 (`ultimate_interrupt`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: skill/ultimate action categories; ultimate interrupt windows; target legality and action generation; damage/toughness scaffolds
- Missing verified character-kit semantics: Verified Naxia ultimate target rule, damage/effects, and binding.
- Missing initialization/resource data: Initial energy, enemy state, and combat state.
- Unresolved trigger/composite behavior: Resulting combat state and conditions are not bound.
- Evidence limitations: The accepted trace does not validate target or resulting combat state.
- Binding explanation: Generic ultimate and damage scaffolds exist, but no Naxia kit binding or target evidence exists.
- Minimum future work:
  - character_binding: Add verified Naxia ultimate data and binding.
  - target_evidence: Obtain Naxia ultimate target evidence.
  - initial_state: Obtain accepted initial combat state.

### Step 7: naxia / basic_plus_extra_skill

- Target status: unknown target
- Semantic: 那刻夏普攻 + 额外战技 (`composite_action_placeholder`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, unresolved_composite_action, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: normal action execution and action generation; skill/ultimate action categories; extra turns and trigger hooks; damage/toughness scaffolds
- Missing verified character-kit semantics: Verified Naxia basic action, extra-skill condition, and binding.
- Missing initialization/resource data: Initial resources, trigger state, and enemy state.
- Unresolved trigger/composite behavior: basic_plus_extra_skill is a composite placeholder and has no executable split.
- Evidence limitations: The accepted trace does not identify internal split, targets, or trigger conditions.
- Binding explanation: Generic action and trigger primitives do not define this composite placeholder.
- Minimum future work:
  - character_binding: Add verified Naxia basic and extra-skill bindings.
  - composite_behavior: Specify evidence-backed executable split for basic_plus_extra_skill.
  - initial_state: Obtain accepted initial combat state.

### Step 8: mem / advance_naxia

- Target status: source records Naxia; advance semantics unresolved
- Semantic: 迷迷拉条那刻夏 (`action_advance_placeholder`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_initial_state, unresolved_action_advance, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: generic action advance/immediate action primitives; extra turns and trigger hooks; target legality and action generation
- Missing verified character-kit semantics: Verified Mem action-advance rule, charge/trigger condition, timing, and binding.
- Missing initialization/resource data: Initial action order, speed/AV, companion charge, and trigger state.
- Unresolved trigger/composite behavior: Mem advances Naxia, but exact amount, timing rule, charge/trigger condition, and binding are unresolved.
- Evidence limitations: The accepted trace establishes sequence only and supplies no advance amount or immediate-action claim.
- Binding explanation: Generic advance primitives exist, but no percentage, immediate-action claim, or Mem binding is accepted.
- Minimum future work:
  - character_binding: Add verified Mem action-advance data and binding.
  - action_advance_behavior: Obtain evidence for Mem advance amount, timing, and trigger conditions.
  - initial_state: Obtain accepted initial combat state.

### Step 9: naxia / skill_plus_extra_skill

- Target status: unknown target
- Semantic: 那刻夏战技 + 额外战技 (`composite_action_placeholder`)
- Binding statuses: generic_primitive_available, missing_character_binding, missing_target_evidence, missing_initial_state, unresolved_composite_action, video_insufficient, blocked
- Executable now: `false`
- Generic engine primitives: normal action execution and action generation; skill/ultimate action categories; extra turns and trigger hooks; damage/toughness scaffolds
- Missing verified character-kit semantics: Verified Naxia skill, extra-skill condition, and binding.
- Missing initialization/resource data: Initial resources, trigger state, and enemy state.
- Unresolved trigger/composite behavior: skill_plus_extra_skill is a composite placeholder and has no executable split.
- Evidence limitations: The accepted trace does not identify internal split, targets, or trigger conditions.
- Binding explanation: Generic action and trigger primitives do not define this composite placeholder.
- Minimum future work:
  - character_binding: Add verified Naxia skill and extra-skill bindings.
  - composite_behavior: Specify evidence-backed executable split for skill_plus_extra_skill.
  - initial_state: Obtain accepted initial combat state.

## Deduplicated Minimum Future Work

### action_advance_behavior

- Obtain evidence for Mem advance amount, timing, and trigger conditions.

### character_binding

- Add verified Mem action-advance data and binding.
- Add verified Naxia basic and extra-skill bindings.
- Add verified Naxia skill and extra-skill bindings.
- Add verified Naxia ultimate data and binding.
- Add verified Pela skill data and binding.
- Add verified Pela technique data and binding.
- Add verified Pela ultimate data and binding.
- Add verified Remembrance Trailblazer and companion data/binding.
- Add verified Tingyun skill data and binding.
- Add verified Tingyun ultimate data and binding.

### composite_behavior

- Specify evidence-backed executable split for basic_plus_extra_skill.
- Specify evidence-backed executable split for skill_plus_extra_skill.

### initial_state

- Obtain accepted initial combat state.
- Obtain initial enemy and prebattle state from authoritative evidence.

### target_evidence

- Obtain Naxia ultimate target evidence.
- Obtain Pela skill target evidence.
- Obtain Pela ultimate target-scope evidence.
- Obtain Remembrance Trailblazer skill target evidence.
- Obtain Tingyun skill target evidence.
- Obtain Tingyun ultimate target evidence.

