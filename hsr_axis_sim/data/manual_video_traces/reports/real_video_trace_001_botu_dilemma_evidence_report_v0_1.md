# Trace Evidence Report: real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only

Report ID: `real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only_evidence_report_v0_1`  
Version: `0.1`

## Source Video

- Platform: bilibili
- Title: 【3.4博徒困境】全网首发！0+1风套那刻夏逆属性2金0t砂金！
- URL: https://www.bilibili.com/video/BV1CXtVzaEQB?vd_source=ac236634092c9f9a4f4b0169249ce344

## Evidence Policy

> Evidence-only and non-executable. Media timestamps are not AV or simulator time. Unknown combat values remain unknown; no damage, SP, energy, HP, toughness, speed, target, buff, debuff, or RNG value is inferred beyond the accepted source trace.

## Scenario and Team

- Game: Honkai: Star Rail 3.4
- Scenario: 博徒困境, 第12层, 第一面
- Team: naxia (那刻夏), tingyun (停云), pela (佩拉), remembrance_trailblazer (记忆主)

## Prebattle Evidence

### pela / technique

- Semantic: 佩拉秘技开怪 (`prebattle_technique`)
- Media evidence range: 0.0-1.5 seconds
- Representative frames: t_000.0.jpg, t_000.5.jpg, t_001.0.jpg
- Frame confidence: `high`
- Known: Pela technique was used to engage combat.
- Unknown: Exact debuff state and target scope for this trace are not validated.
- Source notes: 佩拉秘技开怪
- Frame notes: Pela technique engagement and battle entry.

## Ordered Step Evidence

| Step | Media evidence range (s) | Actor | Action | Semantic label | Category | Confidence | Representative frames |
|---:|---|---|---|---|---|---|---|
| 1 | 2.0-5.5 | tingyun | ultimate | 停云终结技 | ultimate_interrupt | high | t_002.0.jpg, t_003.5.jpg, t_005.5.jpg |
| 2 | 6.0-7.0 | pela | skill | 佩拉战技 | normal_skill | high | t_006.0.jpg, t_006.5.jpg, t_007.0.jpg |
| 3 | 7.5-8.5 | remembrance_trailblazer | skill | 记忆主战技 | normal_skill | high | t_007.5.jpg, t_008.0.jpg, t_008.5.jpg |
| 4 | 9.0-9.5 | tingyun | skill | 停云战技 | normal_skill | high | t_009.0.jpg, t_009.5.jpg |
| 5 | 10.0-12.0 | pela | ultimate | 佩拉终结技 | ultimate_interrupt | high | t_010.0.jpg, t_011.0.jpg, t_012.0.jpg |
| 6 | 12.5-14.5 | naxia | ultimate | 那刻夏终结技 | ultimate_interrupt | high | t_012.5.jpg, t_013.5.jpg, t_014.5.jpg |
| 7 | 15.0-16.5 | naxia | basic_plus_extra_skill | 那刻夏普攻 + 额外战技 | composite_action_placeholder | medium | t_015.0.jpg, t_015.5.jpg, t_016.0.jpg, t_016.5.jpg |
| 8 | 17.0-17.5 | mem | advance_naxia | 迷迷拉条那刻夏 | action_advance_placeholder | medium | t_017.0.jpg, t_017.5.jpg |
| 9 | 17.5-19.0 | naxia | skill_plus_extra_skill | 那刻夏战技 + 额外战技 | composite_action_placeholder | medium | t_017.5.jpg, t_018.0.jpg, t_018.5.jpg, t_019.0.jpg |

## Step Details

### Step 1: tingyun / ultimate

- Target: `unknown` (confidence: `unknown`)
- Semantic: 停云终结技 (`ultimate_interrupt`)
- Media evidence range: 2.0-5.5 seconds
- Representative frames: t_002.0.jpg, t_003.5.jpg, t_005.5.jpg
- Frame confidence: `high`
- Known: Tingyun ultimate is observed as the first recorded action.
- Unknown: Target, energy state, buff value, and exact resulting state are not validated.
- Source notes: 停云终结技。Target and numeric state not safely observable.
- Frame notes: Tingyun ultimate animation.

### Step 2: pela / skill

- Target: `unknown` (confidence: `unknown`)
- Semantic: 佩拉战技 (`normal_skill`)
- Media evidence range: 6.0-7.0 seconds
- Representative frames: t_006.0.jpg, t_006.5.jpg, t_007.0.jpg
- Frame confidence: `high`
- Known: Pela skill is observed after Tingyun ultimate.
- Unknown: Target, skill point state, enemy state, and debuff outcome are not validated.
- Source notes: 佩拉战技。
- Frame notes: Pela skill action.

### Step 3: remembrance_trailblazer / skill

- Target: `unknown` (confidence: `unknown`)
- Semantic: 记忆主战技 (`normal_skill`)
- Media evidence range: 7.5-8.5 seconds
- Representative frames: t_007.5.jpg, t_008.0.jpg, t_008.5.jpg
- Frame confidence: `high`
- Known: Remembrance Trailblazer skill is observed in the opening sequence.
- Unknown: Target, Mem interaction state, skill point state, and resulting combat state are not validated.
- Source notes: 记忆主战技。
- Frame notes: Remembrance Trailblazer skill and companion-related animation.

### Step 4: tingyun / skill

- Target: `unknown` (confidence: `unknown`)
- Semantic: 停云战技 (`normal_skill`)
- Media evidence range: 9.0-9.5 seconds
- Representative frames: t_009.0.jpg, t_009.5.jpg
- Frame confidence: `high`
- Known: Tingyun skill is observed before Pela ultimate.
- Unknown: Target, skill point state, buff value, and resulting combat state are not validated.
- Source notes: 停云战技。
- Frame notes: Tingyun skill.

### Step 5: pela / ultimate

- Target: `unknown` (confidence: `unknown`)
- Semantic: 佩拉终结技 (`ultimate_interrupt`)
- Media evidence range: 10.0-12.0 seconds
- Representative frames: t_010.0.jpg, t_011.0.jpg, t_012.0.jpg
- Frame confidence: `high`
- Known: Pela ultimate is observed before Naxia ultimate.
- Unknown: Target scope, energy state, debuff outcome, damage, and toughness effects are not validated.
- Source notes: 佩拉终结技插队。
- Frame notes: Pela ultimate animation.

### Step 6: naxia / ultimate

- Target: `unknown` (confidence: `unknown`)
- Semantic: 那刻夏终结技 (`ultimate_interrupt`)
- Media evidence range: 12.5-14.5 seconds
- Representative frames: t_012.5.jpg, t_013.5.jpg, t_014.5.jpg
- Frame confidence: `high`
- Known: Naxia ultimate is observed before Naxia's composite basic action.
- Unknown: Target, energy state, damage, toughness effects, and follow-up conditions are not validated.
- Source notes: 那刻夏终结技。
- Frame notes: Anaxa ultimate animation.

### Step 7: naxia / basic_plus_extra_skill

- Target: `unknown` (confidence: `unknown`)
- Semantic: 那刻夏普攻 + 额外战技 (`composite_action_placeholder`)
- Media evidence range: 15.0-16.5 seconds
- Representative frames: t_015.0.jpg, t_015.5.jpg, t_016.0.jpg, t_016.5.jpg
- Frame confidence: `medium`
- Known: The trace records this as a composite observed action label.
- Unknown: Executable split, target, resource state, trigger conditions, damage, and toughness effects are not validated.
- Source notes: 那刻夏普攻 + 额外战技。Represent as composite action in trace intake; do not force simulator semantics yet.
- Frame notes: Observed composite sequence; frame boundary between basic and extra skill is approximate.

### Step 8: mem / advance_naxia

- Target: `naxia` (confidence: `high`)
- Semantic: 迷迷拉条那刻夏 (`action_advance_placeholder`)
- Media evidence range: 17.0-17.5 seconds
- Representative frames: t_017.0.jpg, t_017.5.jpg
- Frame confidence: `medium`
- Known: Mem is observed causing Naxia to act sooner in the sequence.
- Unknown: Exact action advance amount, timing semantics, charge conditions, and executable binding are not validated.
- Source notes: 迷迷拉条那刻夏。Exact action advance amount/semantics unknown from this trace.
- Frame notes: Mem animation associated with advancing Anaxa; no action-advance amount is asserted.

### Step 9: naxia / skill_plus_extra_skill

- Target: `unknown` (confidence: `unknown`)
- Semantic: 那刻夏战技 + 额外战技 (`composite_action_placeholder`)
- Media evidence range: 17.5-19.0 seconds
- Representative frames: t_017.5.jpg, t_018.0.jpg, t_018.5.jpg, t_019.0.jpg
- Frame confidence: `medium`
- Known: The trace records this as a composite observed action label after Mem's action.
- Unknown: Executable split, target, resource state, trigger conditions, damage, and toughness effects are not validated.
- Source notes: 那刻夏战技 + 额外战技。Represent as composite action in trace intake; do not force simulator semantics yet.
- Frame notes: Observed composite sequence after Mem; internal split is approximate.

