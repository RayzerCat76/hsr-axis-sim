# LUMEN_REVIEW_CHECKLIST_HSR_AXIS_001T

Use this checklist after Codex returns HSR-AXIS-001T.

## Required local commands

```bash
cd hsr_axis_001a_package
python -m compileall -q hsr_axis_sim
python -m pytest -q
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
python -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
```

## Pass/fail gates

001T passes only if:

- Full pytest suite passes.
- All golden replay CLIs pass.
- Manual video trace lint and replay pass.
- Existing 001S search tests still pass.
- `beam_search(...)` still works with the default evaluator.
- `beam_search(..., evaluator=Evaluator(profile="zero_cycle"))` works.
- `beam_search(..., max_global_av=...)` is exposed and tested.

## Code review checks

### Evaluator API

- `Evaluator.evaluate(state, depth)` still returns a float.
- `Evaluator.evaluate_breakdown(state, depth)` returns a structured breakdown.
- Backward compatibility for existing `ScoreConfig` is preserved or intentionally migrated with tests.

### Score profiles

Required profiles exist:

```text
generic_kill
zero_cycle
damage_race
survival_safe
sp_conservative
```

Each profile must have a test that proves at least one meaningful behavior difference.

### Score breakdown

- Breakdown total equals sum of component values within tolerance.
- Component names are readable.
- No component should silently depend on hidden global state.

### Search integration

- Search still accepts injected evaluator instances.
- Search does not mutate parent states.
- Deterministic tie-breaking is preserved.
- `max_global_av` is available through `beam_search(...)`.

### Scope control

Codex should NOT:

- modify action value semantics,
- modify target legality,
- modify enemy AI behavior,
- modify replay validator semantics,
- add external scraping,
- add UI,
- add real character data beyond test fixtures.

## Likely next task after 001T

If 001T passes, proceed to:

```text
HSR-AXIS-001U: Axis Output / Explainable Search Report MVP
```

Expected goal:
Convert a best SearchNode into a readable report with:

- action timeline,
- SP / energy / HP / toughness snapshots,
- score breakdown,
- terminal reason,
- beam metadata,
- why the chosen axis was preferred.

Suggested next-task setup:

```text
Codex Reasoning: Medium
ChatGPT Model: GPT-5.5 is enough; use GPT-5.5 Thinking only if report generation requires deeper search changes.
```
