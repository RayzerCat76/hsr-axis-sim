# LUMEN REVIEW CHECKLIST — HSR-AXIS-001Y

Use this checklist after Codex finishes 001Y.

## Required validation

Run:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest hsr_axis_sim/tests -q
python -m hsr_axis_sim.regression.runner --format text
python -m hsr_axis_sim.regression.runner --format markdown
python -m hsr_axis_sim.regression.runner --format json
python -m hsr_axis_sim.regression.runner --only replays
python -m hsr_axis_sim.regression.runner --only manual
python -m hsr_axis_sim.regression.runner --only scenarios
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
python -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format json
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/constrained_search_mvp.json --format json
```

## Pass conditions

- All previous tests still pass.
- Regression runner runs from `python -m hsr_axis_sim.regression.runner`.
- Runner discovers existing golden replays.
- Runner discovers existing manual video trace sample(s).
- Runner discovers existing search scenarios.
- Runner reports group-level counts.
- Runner returns exit code `0` when all selected checks pass.
- Runner returns nonzero for invalid options or failed checks.
- `--only replays`, `--only manual`, and `--only scenarios` work.
- `--format text`, `--format markdown`, and `--format json` work.
- JSON output is stable and parseable.
- `--output` writes the selected report format to a file.
- `--fail-fast` is tested.
- Implementation uses in-process APIs where practical and does not depend on external network access or new dependencies.

## Specific things to inspect

- The runner should not silently swallow failures.
- The runner should include enough error text to diagnose a bad fixture.
- Manual trace lint and replay validation should both be represented.
- Scenario checks should include best score / terminal reason / depth / nodes expanded where practical.
- Paths in JSON output should be stable enough for local debugging.
- The runner should not rewrite scenario files, replay files, character specs, or battle state fixtures.

## Red flags

- Codex changes timeline, damage, toughness, buff duration, target legality, enemy AI, evaluator, or beam-search semantics.
- Runner shells out to many commands when direct APIs already exist, unless clearly justified.
- Runner only prints a string and has no structured testable result object.
- Runner ignores failed checks and still returns exit code `0`.
- Runner requires pytest or optional external dependencies at runtime.
- Runner hardcodes a single fixture instead of scanning the fixture directories.
- JSON format is just a string dump of text output rather than structured data.

## Likely next task after 001Y

If 001Y passes, next task should likely be:

**HSR-AXIS-001Z: Scenario Lint / Config Diagnostics MVP**

Purpose: validate scenario configs more deeply before running search, including unknown actor IDs, unknown skill IDs, unknown target IDs, impossible constraints, and missing data files.
