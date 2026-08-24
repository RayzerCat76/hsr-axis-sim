# LUMEN REVIEW CHECKLIST — HSR-AXIS-001U

Use this checklist after Codex returns the 001U package.

## Expected scope

001U should implement Axis Output / Search Report MVP.

It should focus on:

- readable search result output
- Markdown report
- JSON-compatible report export
- score breakdown display
- final beam candidate comparison
- report tests

It should not alter combat semantics.

## Must inspect

### Files expected

Look for some or all of:

```text
hsr_axis_sim/search/report.py
hsr_axis_sim/search/report_cli.py          # optional
hsr_axis_sim/tests/test_search_report.py
hsr_axis_sim/search/__init__.py
hsr_axis_sim/LUMEN_RESULT.md
```

### Report contents

Confirm report includes:

- best score
- best node terminal reason
- SearchResult terminated reason
- nodes expanded
- depth reached
- final beam count
- best axis steps
- top-K final beam candidates
- final score breakdown when evaluator is provided

### Axis step contents

Each step should include:

- step number
- actor id
- skill id or action id
- target ids
- global AV before
- global AV after
- SP after
- score after

### Output formats

Confirm all exist and are tested:

- plain text or line-based readable output
- Markdown output
- JSON-compatible dict export

### Backward compatibility

Confirm existing `format_axis(...)` still works or existing tests are updated in a compatible way.

### JSON serializability

If dict export is implemented, verify it can be passed through:

```python
json.dumps(report_dict)
```

### No mechanics changes

Check git diff / file list carefully.

001U should not change:

- `timeline.py`
- `effects.py`
- `damage.py`
- `break_logic.py`
- `break_damage.py`
- `buffs.py`
- `enemy_ai.py`
- `ultimate_windows.py`

Small import/export adjustments are okay. Mechanic behavior changes are not.

## Required commands for Lumen

Run:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
python -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
```

## Pass criteria

001U passes if:

- pytest passes
- golden replays pass
- manual video trace lint/replay passes
- report output is readable
- dict export is JSON serializable
- no combat mechanics are changed

## Likely next task after 001U

**HSR-AXIS-001V: Minimal CLI Scenario Runner / Axis Export MVP**

Possible direction:

- run beam search from a JSON scenario file
- choose evaluator profile from CLI
- export Markdown / JSON report
- keep this CLI local/offline
- still no web UI

Suggested model / reasoning:

```text
Codex Reasoning: Medium
ChatGPT Model 建议: GPT-5.5 就够，不必用 GPT-5.5 Thinking
理由: 001V should be CLI wiring and scenario/report export, not combat-core logic.
```
