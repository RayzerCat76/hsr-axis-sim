# HSR-RUNTIME-ARCH-005 — Expected vs Actual Trace Comparator

## Current confirmed state

- HSR-GOV-001: PASS and merged.
- HSR-RUNTIME-ARCH-004: PASS.
- Complete pytest baseline: 792/792 passed.
- Locked regression: 20/20 passed.
- Trace evidence: 2/2 passed.
- Current blocker: none.

## Objective

Add the smallest safe read-only sidecar that deterministically compares the
ordered runtime records of an expected `RuntimeTraceDocument` with an actual
`RuntimeTraceDocument` and returns an immutable complete comparison result.

## Required implementation

1. Add `hsr_axis_sim.runtime_comparators` without changing existing runtime,
   simulator, adapter, exporter, or loader semantics.
2. Compare `RuntimeTraceDocument.records` strictly by tuple position.
3. Compare every record field recursively through the existing canonical-data
   projection, including strict JSON type differences.
4. Return immutable deterministic result, per-position status, and ordered
   field differences.
5. Represent unmatched tail records explicitly as `EXPECTED_ONLY` or
   `ACTUAL_ONLY`.
6. Retain expected/actual trace IDs and record counts as provenance/result
   context, but do not treat trace IDs, metadata, sequence policy, or derived
   document summary fields as independent trace-equality axes.
7. Document the contract and exclusions.
8. Update `hsr_axis_sim/LUMEN_RESULT.md` with real validation results before
   acceptance.

## Acceptance criteria

- Identical record streams compare as a match even when trace provenance differs.
- Any record field/type difference is deterministic and visible.
- Difference paths are stable and deterministic.
- Missing nested values preserve presence information; a missing value is not
  confused with a present JSON null.
- Length differences are explicit.
- No heuristic realignment or repair occurs.
- Result objects and captured difference values are immutable.
- Repeated comparison of identical inputs yields equal ordered results.
- Existing production behavior and accepted trace pipeline remain unchanged.
- Full CI validation passes.

## Required tests

- exact matching record streams;
- differing provenance with identical records;
- event field mismatch;
- nested payload missing-key mismatch and pointer escaping;
- strict `int` vs `float` mismatch;
- actual-only and expected-only records;
- no middle-record realignment;
- deep freezing/result immutability;
- empty trace comparison;
- invalid input rejection;
- deterministic repeated result/difference ordering;
- sidecar import preservation and production LIFO preservation.

## Protected areas

Do not modify production behavior in:

- `hsr_axis_sim/sim/**`
- `hsr_axis_sim/search/**`
- `hsr_axis_sim/regression/**`
- `hsr_axis_sim/adapters/**`
- `hsr_axis_sim/real_bindings/**`
- `hsr_axis_sim/data/**`
- `hsr_axis_sim/runtime_contracts/**`
- `hsr_axis_sim/runtime_adapters/**`
- `hsr_axis_sim/runtime_exports/**`
- `hsr_axis_sim/runtime_loaders/**`
- locked regression fixtures and accepted runtime research/reference files.

## Explicit exclusions

No first-divergence reporter (ARCH-006), fuzzy/tolerance comparison, configurable
ignore rules, edit-distance/event-ID realignment, repair, migration, trace
schema change, file I/O, comparator JSON artifact/CLI, automatic simulator
integration, video extraction, new HSR mechanics, or FIFO/LIFO semantic change.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

## Final report format

Report task ID, implementation summary, files added/modified, tests added, exact
commands executed, real pass/fail results, unresolved issues, confirmation that
exclusions/protected areas were respected, suggested next milestone, and update
`hsr_axis_sim/LUMEN_RESULT.md`.

## Execution routing

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning level if Codex is used: High.
- Codex is optional under current governance; this milestone may be executed
  directly through the governed GitHub branch/PR/CI workflow.
