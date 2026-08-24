# LUMEN Review — HSR-AXIS-002O

## Verdict

**REQUIRES FIX. HSR-AXIS-002O is not accepted yet. Do not begin HSR-AXIS-002P.**

The semantic-readiness architecture and the committed evidence conclusions are largely correct, but the required malformed-input gate fails inside the new 002O validator itself.

## Independent verification

- `python -m compileall -q hsr_axis_sim`: **PASS**
- Complete pytest collection: **456 passed, 2 failed, 458 total**
  - group 1: 121 passed
  - group 2: 175 passed
  - group 3: 85 passed, 2 failed
  - group 4: 75 passed
- Focused 002O tests: **26 passed, 2 failed**
- Locked regression: **PASS 20/20**
- Trace-evidence-only regression: **PASS 2/2**
- Regenerated Markdown report: **byte-identical**
- Regenerated JSON report: **byte-identical**
- Historical 002M/002N artifacts and existing simulator/binding files: unchanged against the accepted 002N-FIX package

A single full-suite invocation exceeded the review sandbox time limit after exposing the two failures. All 45 test files were then run in four non-overlapping groups, covering the complete 458-test collection.

## What is correct

The committed 002O result correctly keeps both unresolved semantic questions open:

- Energy restoration versus DMG-buff application order remains unresolved.
- The same-current-turn duration edge remains unresolved against release-game evidence.

The readiness axes are separated correctly:

- generic binding: `blocked_by_both_semantics`
- accepted-video binding: `blocked_by_unknown_target_and_trace_level`
- accepted-video semantic readiness: `blocked_by_both_semantics`
- simulator binding allowed: `false`

The exact 15-level magnitude table is validated and consumed without selecting a level:

`20, 23, 26, 29, 32, 35, 38.75, 42.5, 46.25, 50, 53, 56, 59, 62, 65`

The two controlled-interaction protocols remain evidence metadata only with `result_status: not_run` and `observed_result: null`.

Confirmed absent:

- executable Tingyun DMG buff
- real-video target inference
- real-video trace-level inference
- reviewed-registry changes
- Tingyun Energy-binding changes
- Pela-binding changes
- simulator/search/evaluator/replay/manifest changes
- HSR-AXIS-002P implementation

## Blocking defect

The new validator validates `semantic_claims[*].status` as a string, but then performs set membership before stopping on the failed type check:

```python
if item.get("status") not in STATUSES or item.get("status") != status:
```

For JSON-compatible object or list values, this raises a native exception instead of the required controlled `ValueError`:

```text
status = {"bad": "value"}
TypeError: unhashable type: 'dict'

status = ["bad"]
TypeError: unhashable type: 'list'
```

These are not hypothetical hidden cases: two tests committed with 002O fail on exactly this defect.

The CLI also classifies the malformed but readable review incorrectly:

```text
malformed semantic_claims[*].status object
exit code: 2
stderr: ERROR ... unhashable type: 'dict'
traceback: none
```

The task contract requires malformed readable input to return **exit 1**, without traceback. Exit 2 is reserved for missing/unreadable/input-loading failures.

## Independent malformed-input audit

A 220-case JSON-compatible scalar mutation matrix was run across top-level fields, input artifacts, semantic claims, provenance, engine assessment, protocols, and blocker lists.

Results:

- controlled `ValueError`: 214
- native exception leaks: 2
- no-op mutations equal to the original valid value: 4

The only native leaks found were:

- `semantic_claims[*].status` as object
- `semantic_claims[*].status` as list

This makes the required fix narrow and well-defined.

## Required disposition

Create **HSR-AXIS-002O-FIX**. Add a type guard before membership/comparison, expand the adversarial tests so every scalar semantic field is exercised, and verify malformed status input reaches the normal validation-failure path with CLI exit 1.

Do not change the semantic conclusions or begin 002P while fixing this validator defect.
