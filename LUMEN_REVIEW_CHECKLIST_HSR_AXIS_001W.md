# LUMEN REVIEW CHECKLIST — HSR-AXIS-001W

Use this checklist after Codex finishes 001W.

## Required validation

Run:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
python -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format markdown
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format markdown --include-snapshots
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format json
```

## Pass conditions

- All pytest tests pass.
- All old golden replays pass.
- Manual video trace lint/replay still passes.
- Existing scenario CLI behavior still works.
- `--include-snapshots` works for Markdown/text output.
- JSON report includes machine-readable unit state snapshots, or if optional, the behavior is clearly documented and tested.
- Snapshot data is compact; it must not serialize full `BattleState` objects.
- Unit ordering in snapshots is deterministic.
- Existing score/search behavior is not changed.
- No combat-core semantics changed.

## Specific things to inspect

- `ActionRecord` or `AxisStepReport` should carry compact snapshot data, not full mutable states.
- Floating point values should stay numeric in JSON.
- Markdown tables should be readable and not huge for the MVP scenario.
- Snapshot fields should match actual `Unit` state; no invented mechanics.
- Snapshot code should not import CLI modules into combat core.
- Scenario CLI should not break old `--format` and `--output` behavior.

## Red flags

- Codex changes timeline, damage, toughness, action generation, enemy AI, or evaluator scoring without being asked.
- Codex stores complete `BattleState` objects inside reports.
- JSON export becomes non-serializable.
- Old reports become too verbose by default.
- Snapshot output depends on dictionary iteration order where deterministic ordering is needed.
- Tests only check for strings and do not verify snapshot data structure.

## Likely next task after 001W

If 001W passes, next task should likely be:

**HSR-AXIS-001X: Scenario Config V1 / Search Constraints MVP**

Purpose: let scenario files configure mode-specific search constraints more clearly, such as max AV, max cycles, fixed RNG seed/options, forced ultimate windows, and disabled/enabled skills, before moving toward larger real-video scenario reproduction.
