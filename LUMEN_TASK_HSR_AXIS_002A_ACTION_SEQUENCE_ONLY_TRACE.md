# HSR-AXIS-002A-SEQ: Action-Sequence-Only Real Video Trace MVP

## Purpose

The current 002A real video trace workflow expects fields that are not reliably visible from a gameplay video, such as exact SP before/after, exact energy values, enemy HP, exact toughness values, and forced RNG. That creates false precision.

This task changes the 002A real-video intake protocol so it can accept a real gameplay clip as an **action-sequence-only trace** when numeric data is not observable.

The goal is not to prove the simulator matches all battle numbers yet. The goal is to safely store and lint a verified real-video opening action sequence, with unknown fields explicitly marked as unknown or skipped.

## Project Context

We are working on a Honkai: Star Rail inspired action-axis simulator and AI axis-search project.

Current status:

- 001A–001Z MVP baseline is locked.
- 002A was blocked because no real trace was available.
- We now have a real video source and manually confirmed opening action sequence.
- The video does not provide enough visible data to reliably fill exact SP, energy, HP, toughness, or RNG values.

## Real Video Source

Video title:

`【3.4博徒困境】全网首发！0+1风套那刻夏逆属性2金0t砂金！`

Bilibili URL:

`https://www.bilibili.com/video/BV1CXtVzaEQB?vd_source=ac236634092c9f9a4f4b0169249ce344`

Scenario:

- Game: Honkai: Star Rail
- Version/context: 3.4 博徒困境
- Stage: 第12层 第一面
- Team: 那刻夏 / 停云 / 佩拉 / 记忆主
- Engage: 佩拉秘技开怪

Confirmed opening sequence:

1. 停云终结技
2. 佩拉战技
3. 记忆主战技
4. 停云战技
5. 佩拉终结技
6. 那刻夏终结技
7. 那刻夏普攻 + 额外战技
8. 迷迷拉条那刻夏
9. 那刻夏战技 + 额外战技

## Required Work

Add support for a manual real-video trace mode with:

```json
{
  "check_mode": "action_sequence_only",
  "unknown_allowed": true,
  "numeric_expectations": "skip"
}
```

In this mode:

- Actor/action order is required.
- Video metadata is required.
- Team and stage metadata are required.
- Numeric expectations may be omitted, set to `unknown`, or set to `skip`.
- The linter should verify the trace is honest about unknowns.
- The engine replay validator should not try to compare numeric state if check mode is action-sequence-only.
- Do not infer SP, energy, HP, toughness, target, or RNG from the video.
- Do not invent unknown data.

## Files to Add or Update

Likely areas, adapt to the actual existing project structure:

```text
hsr_axis_sim/
  manual_video_trace.py or replay/manual_video_trace.py
  data/golden_replays or data/manual_video_traces
  tests/test_manual_video_trace_action_sequence_only.py
```

Add a fixture similar to:

```text
data/manual_video_traces/real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json
```

## Fixture Requirements

The fixture should contain:

- `name`
- `source`
- `scenario`
- `team`
- `prebattle`
- `check_mode`
- `unknown_allowed`
- `numeric_expectations`
- `steps`

Each step should allow:

```json
{
  "step": 1,
  "video_timestamp": "unknown",
  "actor": "tingyun",
  "action": "ultimate",
  "target": "unknown",
  "target_confidence": "unknown",
  "observable": {
    "actor_action_sequence": true,
    "skill_points": "unknown",
    "energy": "unknown",
    "hp": "skip",
    "toughness": "unknown",
    "damage": "skip",
    "forced_rng": "unknown"
  },
  "notes": "停云终结技 after Pela technique engage. Exact target and numeric state not safely observable from clip."
}
```

Use normalized internal IDs for actors where possible:

```text
naxia
 tingyun
 pela
 remembrance_trailblazer
 mem
```

If the existing project uses different naming conventions, follow them consistently.

## Tests

Add tests that verify:

1. The new action-sequence-only fixture passes lint.
2. Unknown numeric fields are accepted only when `unknown_allowed` is true.
3. Numeric expectations are skipped when `numeric_expectations` is `skip`.
4. Required metadata must be present.
5. Required actor/action sequence fields must be present.
6. Existing 001Z manifest regression remains unchanged and still passes.
7. The new intake fixture is not incorrectly added to fully numeric replay validation unless the code explicitly supports that mode.

## Important Restrictions

Do not modify combat core mechanics.

Do not change damage formula, AV logic, buffs, enemies, triggers, or search.

Do not scrape Bilibili.

Do not download videos.

Do not invent targets, SP, energy, HP, toughness, or RNG values.

Do not add this trace to a locked numeric baseline manifest unless it is clearly marked as action-sequence-only and only linted/checked at that level.

## Deliverables

1. Code/schema support for `check_mode: action_sequence_only`.
2. Real-video action-sequence-only fixture for this Bilibili clip.
3. Tests for the new mode.
4. Existing tests still passing.
5. Existing locked 001Z manifest behavior preserved.
6. `LUMEN_RESULT.md` explaining:
   - what was implemented
   - what was intentionally left unknown
   - what tests were run
   - whether the trace was added to lint-only intake or any manifest
   - next recommended step
