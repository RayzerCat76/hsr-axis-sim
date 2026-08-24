# LUMEN REVIEW — HSR-AXIS-002A Action-Sequence-Only Real Trace

## Verdict

**PASS.** 002A action-sequence-only real trace support is accepted.

This version correctly adapts the first real Bilibili trace into a conservative, honest intake format: it locks the observable action order while explicitly marking unobservable numeric fields as `unknown` or `skip`.

## Test results I ran

```text
pytest -q
288 passed in 4.66s
```

Action-sequence trace lint:

```text
python -m hsr_axis_sim.sim.replay_lint \
  hsr_axis_sim/data/manual_video_traces/intake/real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json

PASS real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only: action-sequence-only manual video trace lint passed.
```

Action-sequence replay check:

```text
python -m hsr_axis_sim.sim.replay \
  hsr_axis_sim/data/manual_video_traces/intake/real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json

PASS real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only: checked 9 step(s).
```

Regression manifest:

```text
python -m hsr_axis_sim.regression.runner \
  --manifest hsr_axis_sim/data/regression_manifest.json \
  --format text

PASS 12/12 golden replays
PASS 2/2 manual checks
PASS 2/2 search scenarios
```

## What is correct

1. The trace now uses `check_mode: action_sequence_only`.
2. `unknown_allowed: true` and `numeric_expectations: skip` are explicit, which avoids fake precision.
3. The first real video trace records the confirmed sequence:
   - Pela technique engage
   - Tingyun ultimate
   - Pela skill
   - Remembrance Trailblazer skill
   - Tingyun skill
   - Pela ultimate
   - Naxia ultimate
   - Naxia basic + extra skill
   - Mem advances Naxia
   - Naxia skill + extra skill
4. The validator checks actor/action sequence shape only and does not try to create a fake combat state.
5. The existing locked numeric replay baseline remains unchanged.
6. The implementation does not invent SP, energy, HP, toughness, damage, target, or RNG values.

## Important limitation

The real trace is currently stored as an intake fixture and tested by pytest, but it is **not yet part of the locked regression manifest**. That means the formal regression runner still reports only:

```text
replays=12 manual=1 scenarios=2
```

This is acceptable for 002A, but the next step should lock this real action-sequence trace into a separate manifest group so it cannot be silently deleted, renamed, or broken.

## Recommended next task

**HSR-AXIS-002B: Action-Sequence Trace Regression Manifest Group**

Purpose: add a dedicated manifest group for action-sequence-only real traces. This should run lint + sequence validation for real video traces without pretending they are numeric combat replays.

Suggested Codex setup:

```text
Codex Reasoning: Medium
ChatGPT Model: GPT-5.5
Reason: this is manifest/runner/report/test plumbing, not combat-semantics work. It should not require GPT-5.5 Thinking unless a regression architecture issue appears.
```
