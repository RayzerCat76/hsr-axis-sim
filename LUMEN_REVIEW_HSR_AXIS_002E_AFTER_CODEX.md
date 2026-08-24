# LUMEN REVIEW — HSR-AXIS-002E AFTER CODEX

## Decision

**NEEDS FIX — do not accept 002E or start 002F yet.**

The production implementation and locked regression runner are largely correct, but the required full-test gate is not green.

## Independent verification

Commands run from the submitted package root:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner \
  --manifest hsr_axis_sim/data/regression_manifest.json \
  --format text
python -m hsr_axis_sim.regression.runner \
  --manifest hsr_axis_sim/data/regression_manifest.json \
  --only trace_evidence \
  --format text
```

Results:

- Compileall: **PASS**
- Full pytest: **FAIL — 322 passed, 1 failed**
- Locked manifest regression: **PASS — 20/20 checks**
- Trace-evidence-only regression: **PASS — 2/2 checks**

## Blocking failure

Failing test:

```text
hsr_axis_sim/tests/test_manual_video_trace_action_sequence_only.py
::test_existing_regression_manifest_includes_real_trace_as_action_sequence_only
```

The test still expects the pre-002E exact group-count dictionary:

```python
{
    "replays": 12,
    "manual": 1,
    "scenarios": 2,
    "action_sequence_traces": 1,
}
```

After 002E, `counts_by_group()` correctly also returns:

```python
"trace_evidence": 2
```

Therefore the test is stale, not the manifest implementation.

## What appears correct

- `trace_evidence` is supported and ordered in the manifest and runner.
- The locked manifest contains exactly one semantic-map check and one frame-anchor check.
- Evidence entries retain explicit `source_trace_path` values.
- `--only trace_evidence` executes exactly two checks.
- Both accepted evidence artifacts pass.
- Invalid evidence is converted to failed regression results rather than crashing the runner.
- Frame-anchor `status`, `timestamp_basis`, `frame_anchor_id`, and `version` validation was hardened.
- Evidence remains non-executable and separate from combat simulation.
- No video-derived SP, energy, HP, toughness, damage, RNG, AV, speed, or action-advance values were added.

## Required fix

Make a narrow test-maintenance change. Do not alter the production manifest or runner to hide the new group.

Preferred repair:

- Change `test_existing_regression_manifest_includes_real_trace_as_action_sequence_only` so it tests its actual responsibility: the real trace is still present as one `action_sequence_traces` entry with both required checks.
- Keep a dedicated 002E test that locks `trace_evidence == 2` and validates the new evidence entries.
- Avoid asserting the entire group-count dictionary inside a test whose purpose is only the action-sequence group; otherwise every future independent regression group will break this unrelated test.

After the repair, rerun the complete suite and all regression commands.

## Acceptance gate after fix

Accept 002E only when all of the following are true:

- Full pytest passes with zero failures.
- Compileall passes.
- Locked regression remains 20/20.
- Trace-evidence-only regression remains 2/2.
- No combat-core code is changed.
- No evidence artifact becomes executable.
- `LUMEN_RESULT.md` reports the real final verification outcome and does not claim completion while a known full-suite failure remains.
