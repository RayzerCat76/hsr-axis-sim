# HSR-RUNTIME-ARCH-006 — First Divergence Reporter

## Current confirmed state

- HSR-GOV-001: PASS.
- HSR-RUNTIME-ARCH-005: PASS and merged to `main`.
- Complete pytest baseline: 805/805 passed.
- Locked regression: 20/20 passed.
- Trace evidence: 2/2 passed.
- Current blocker: none.

## Objective

Add the smallest safe read-only sidecar that consumes an existing
`RuntimeTraceComparisonResult`, selects the first divergence using only the
already-determined ARCH-005 ordering, and exposes both an immutable structured
report and a deterministic human-readable text rendering.

## Required implementation

1. Add `hsr_axis_sim.runtime_divergence` without changing simulator,
   contracts, adapters, exporters, loaders, or comparator semantics.
2. Accept only a valid `RuntimeTraceComparisonResult`.
3. Select the first record whose status is not `MATCH`, preserving the exact
   existing tuple order from ARCH-005.
4. For a `MISMATCH` record, select the first existing ordered field difference
   without re-sorting or recomputing differences.
5. For `EXPECTED_ONLY` and `ACTUAL_ONLY`, report the unmatched record directly
   without inventing a field difference.
6. Preserve enough provenance/context to make the divergence understandable:
   trace IDs, record counts, total mismatch count, record index, record status,
   expected/actual record sequence, event ID, event type, first field
   difference when applicable, and count of differences at that record.
7. Provide deterministic text rendering that distinguishes missing values from
   present JSON null values and uses canonical JSON for rendered values.
8. Return a clean match report when no divergence exists.
9. Document the selection/rendering contract and explicit exclusions.
10. Update `hsr_axis_sim/LUMEN_RESULT.md` with real validation results before
    acceptance.

## Acceptance criteria

- A matching comparison produces no first divergence and a stable MATCH text.
- Initial matching records are skipped; the first non-MATCH position is chosen.
- A MISMATCH uses the first ARCH-005 field difference exactly as already ordered.
- EXPECTED_ONLY and ACTUAL_ONLY are reported clearly without fabricated fields.
- Missing and present-null values remain distinguishable in structured and text output.
- Text rendering is deterministic and repeatable for the same report.
- Reporter never calls the comparator, never realigns records, and never changes
  comparator ordering or contents.
- Result models are immutable.
- Existing production/runtime behavior remains unchanged.
- Full CI validation passes.

## Required tests

- fully matching comparison;
- first mismatch after one or more matching records;
- first field-difference selection preserves comparator order;
- later divergences do not replace the first divergence;
- EXPECTED_ONLY first divergence;
- ACTUAL_ONLY first divergence;
- missing-vs-null distinction;
- deterministic canonical value rendering, including strings and nested JSON;
- immutable report models;
- invalid input rejection;
- reporter is read-only and repeatable;
- sidecar import-direction preservation;
- production LIFO preservation.

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
- `hsr_axis_sim/runtime_comparators/**`
- locked regression fixtures and accepted runtime research/reference files.

## Explicit exclusions

No new comparison logic, no comparator modification, no fuzzy/tolerance rules,
no event-ID/sequence/edit-distance realignment, no trace repair, no semantic
priority ranking, no file I/O, no JSON report artifact schema, no CLI, no
Golden Replay orchestration, no simulator auto-wiring, no video extraction, no
new HSR mechanics, and no FIFO/LIFO semantic change.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

## Final report format

Report task ID, implementation summary, files added/modified, tests added, exact
commands executed, real pass/fail results, warnings/errors, unresolved issues,
confirmation that exclusions/protected areas were respected, suggested next
milestone, and update `hsr_axis_sim/LUMEN_RESULT.md`.

## Execution routing

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning level if Codex is used: High.
- Codex is optional under current governance; this milestone may be executed
  directly through the governed GitHub branch/PR/CI workflow.
