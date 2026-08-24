# LUMEN REVIEW CHECKLIST — HSR-AXIS-001X

Use this checklist after Codex finishes 001X.

## Required validation

Run:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest hsr_axis_sim/tests -q
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
python -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format markdown
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format markdown --include-snapshots
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format json
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/constrained_search_mvp.json --format markdown
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/constrained_search_mvp.json --format json
```

## Pass conditions

- All previous tests and replays still pass.
- Existing `basic_search_mvp.json` scenario still works unchanged.
- A new constrained scenario fixture works.
- Constraints are parsed from scenario JSON and passed into search.
- Constraints filter legal choices; they must not mutate skill specs or battle state.
- Disabled actor/skill/target constraints are tested.
- Allowed actor/skill/target constraints are tested.
- Branching cap, if implemented, is deterministic and tested.
- Reports include enough metadata to identify which constraints were active, or the scenario object clearly stores that metadata.
- Constraint violations fail clearly when config is malformed.

## Specific things to inspect

- Filtering should happen after normal legal action generation, not by bypassing target legality/resource checks.
- Ultimate choices should respect constraints too, where applicable.
- Enemy AI should not be accidentally blocked by player-side constraints unless explicitly designed.
- Search semantics should not change when constraints are absent.
- Scenario CLI overrides should still work.
- JSON output should still be serializable.
- The implementation should not introduce external dependencies.

## Red flags

- Codex rewrites timeline, damage, toughness, enemy AI, or evaluator internals without being asked.
- Constraints are applied by deleting skills from loaded character specs.
- Disabled targets can still appear in `best_axis_steps`.
- Disabled skills can still appear in final candidates.
- `basic_search_mvp.json` results change when no constraints are supplied.
- Constraint config silently ignores unknown actor/skill ids without any test or documented behavior.
- Search returns root node forever when all choices are filtered, without a clear terminal reason such as `no_legal_choices` or `constraints_no_choices`.

## Likely next task after 001X

If 001X passes, next task should likely be:

**HSR-AXIS-001Y: Batch Scenario Regression Runner MVP**

Purpose: run all search scenarios / golden replays / manual traces from one command and produce a compact regression report before we begin larger real-video calibration work.
