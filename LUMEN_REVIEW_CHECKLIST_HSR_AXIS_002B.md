# LUMEN REVIEW CHECKLIST — HSR-AXIS-002B

## Purpose

Verify that Codex added a dedicated regression manifest group for action-sequence-only real traces without changing combat semantics or inventing numeric data.

## Must pass

- `pytest -q`
- `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
- `python -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/intake/real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json`
- `python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/intake/real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json`

## Check implementation

- New manifest group exists for action-sequence-only traces.
- The real Bilibili trace is listed in the manifest.
- Regression runner reports the action-sequence trace group separately.
- Both lint and sequence validation are run.
- Existing replays/manual/scenarios groups still work.
- Backward compatibility is preserved.

## Red flags

- Codex invents SP, energy, HP, toughness, damage, target, or RNG.
- Codex tries to simulate the full Naxia trace as a combat replay.
- Codex changes action value, damage, break, buff, trigger, or enemy AI semantics.
- Codex adds real character kit logic in this task.
- Codex merges action-sequence-only traces into numeric golden replays.

## Expected model guidance for next step

If 002B passes, the next likely task is:

**HSR-AXIS-002C: Real Trace Character Semantics Planning — Naxia / Tingyun / Pela / Remembrance Trailblazer**

Suggested setup for 002C:

```text
Codex Reasoning: High
ChatGPT Model: GPT-5.5 Thinking
Reason: this will touch real character mechanics, composite actions, Mem action advance, and trace-to-simulator mapping.
```
