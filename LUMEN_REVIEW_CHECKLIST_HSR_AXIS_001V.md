# LUMEN REVIEW CHECKLIST — HSR-AXIS-001V

Use this checklist after Codex returns the 001V package.

## Expected scope

001V should implement a Minimal CLI Scenario Runner / Axis Export MVP.

It should focus on:

- loading a search scenario JSON
- resolving relative paths
- building BattleState from existing sample data
- running existing beam search
- selecting an evaluator profile
- rendering text / Markdown / JSON reports
- optional output file writing
- tests for the above

It should not change combat mechanics.

## Expected files

Look for some or all of:

```text
hsr_axis_sim/search/scenario.py
hsr_axis_sim/data/search_scenarios/basic_search_mvp.json
hsr_axis_sim/tests/test_search_scenario_runner.py
hsr_axis_sim/search/__init__.py
hsr_axis_sim/LUMEN_RESULT.md
```

## Must inspect

### Scenario schema

Confirm scenario supports:

- id
- name
- description
- characters_dir
- team_path
- search.max_depth
- search.beam_width
- search.profile
- search.include_ultimates
- search.max_global_av
- search.max_nodes_expanded
- report.format
- report.top_k

### Path handling

Confirm:

- relative paths resolve relative to scenario file parent
- missing paths produce helpful errors
- tests cover relative paths

### Runner behavior

Confirm:

- uses existing `build_battle_state_from_files(...)`
- uses existing `Evaluator(...)`
- uses existing `beam_search(...)`
- uses existing `build_search_report(...)`
- does not reimplement search or report logic

### Output formats

Confirm all are supported and tested:

- text
- markdown
- json

JSON must be valid `json.loads(...)` output and contain search report fields such as `best_axis_steps`.

### CLI behavior

Confirm examples work:

```bash
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format markdown
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format text
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format json
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format markdown --output /tmp/axis_report.md
```

### Error handling

Confirm tests cover:

- unknown report format
- unknown evaluator profile
- missing scenario file or missing required scenario fields

### No mechanics changes

Check file changes carefully.

001V should not modify:

```text
hsr_axis_sim/sim/timeline.py
hsr_axis_sim/sim/effects.py
hsr_axis_sim/sim/damage.py
hsr_axis_sim/sim/break_logic.py
hsr_axis_sim/sim/break_damage.py
hsr_axis_sim/sim/buffs.py
hsr_axis_sim/sim/enemy_ai.py
hsr_axis_sim/sim/ultimate_windows.py
hsr_axis_sim/sim/targeting.py
```

Small import/export changes are okay. Combat behavior changes are not.

## Required commands for Lumen

Run:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
python -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format markdown
python -m hsr_axis_sim.search.scenario hsr_axis_sim/data/search_scenarios/basic_search_mvp.json --format json
```

## Pass criteria

001V passes if:

- compileall passes
- pytest passes
- all golden replays pass
- manual trace lint/replay passes
- scenario CLI prints Markdown/text/JSON successfully
- output file writing works
- no combat mechanics changed

## Likely next task after 001V

**HSR-AXIS-001W: Static Timeline Visualization / Export MVP**

Possible direction:

- convert `SearchReport` into a simple timeline table
- export CSV or Mermaid sequence/timeline markup
- maybe generate a static Markdown timeline section
- no interactive web UI yet

Suggested model / reasoning:

```text
Codex Reasoning: Medium
ChatGPT Model 建议: GPT-5.5 就够，不必用 GPT-5.5 Thinking
理由: 001W should be report visualization/export wiring, not combat-core logic.
```
