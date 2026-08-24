# LUMEN Review — HSR-AXIS-002M-FIX2

## Verdict

**PASS. HSR-AXIS-002M-FIX2 is accepted. The project may proceed to HSR-AXIS-002N.**

## Independent verification

The uploaded package was extracted and reviewed against the prior 002M-FIX package.

### Build and tests

- `python -m compileall -q hsr_axis_sim`: **PASS**
- Complete test collection: **421 tests**
- Complete suite executed in two disjoint shards because the single all-in-one command exceeded the review runner's wall-clock limit:
  - shard 1: **307 passed**
  - shard 2: **114 passed**
  - total: **421 / 421 passed**
- Focused 002M review tests: **12 passed**

No test file was omitted from the two-shard run.

### Regression gates

- Locked regression: **PASS 20/20**
- Trace-evidence-only regression: **PASS 2/2**
- Manifest counts unchanged:
  - replays: 12
  - manual: 1
  - scenarios: 2
  - action-sequence traces: 1
  - trace evidence: 2

### Report determinism

Regenerated Tingyun damage-buff review reports are byte-identical to the committed reports.

- Markdown SHA-256: `427ecca38eb7a8d92f5c8aa4fec19cee0a51b1ac9193b7e9dc1566bf2fb391ea`
- JSON SHA-256: `8cbdbec44c0132a7cc0c0eb4029357fe1f9feaa84f49b23ad79dc5d797eaf696`

### Adversarial validation

An independent 29-case malformed-provenance matrix was executed. It covered:

- duplicate valid source IDs with object locators;
- duplicate valid source IDs with list locators;
- multiple invalid non-string source IDs;
- mixed object, list, number, boolean and null locator values;
- malformed locator and evidence-summary combinations.

Results:

- direct `build_report(...)`: every case raised controlled `ValueError`;
- no `TypeError`, `AttributeError` or `KeyError` escaped;
- malformed CLI input returned exit code `1`;
- CLI output contained no traceback.

## Code review

The fix addresses the actual root cause rather than hiding the failure around `sorted(...)`.

`_validated_provenance(...)` now:

1. validates each raw provenance field into typed local values;
2. records malformed values as validation issues;
3. appends `FactProvenance` only when the complete row is valid;
4. ensures all values reaching provenance sorting are strings;
5. preserves duplicate valid source-ID detection.

The change is narrowly scoped to:

- `hsr_axis_sim/tools/trace_tingyun_ultimate_damage_buff_review.py`;
- focused 002M tests;
- `hsr_axis_sim/LUMEN_RESULT.md`.

## Preservation review

Confirmed unchanged:

- all six atomic fact contracts;
- readiness remains `blocked_by_both`;
- no executable Tingyun damage buff;
- Tingyun Energy binding;
- Pela partial binding;
- reviewed binding registry with exactly two entries;
- simulator, search, evaluator and replay behavior;
- locked manifest;
- duration-engine behavior;
- unknown real-video Tingyun target and trace level;
- unresolved damage-buff magnitude and effect order.

## Non-blocking note

Codex reported `BLOCKED_PENDING_FULL_PYTEST` because pytest was unavailable in its own interpreter. Independent review covered the entire 421-test collection in two disjoint shards, so this environmental limitation does not block acceptance.
