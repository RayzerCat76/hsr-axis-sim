# LUMEN REVIEW — HSR-AXIS-002K After Codex

## Decision

**NEEDS FIX before 002L.**

The reviewed-binding registry architecture is directionally correct and all existing project tests pass, but independent malformed-input testing found a real validation boundary defect. Because 002K is intended to be the reusable safety contract for every future real character binding, this should be fixed before adding Tingyun Ultimate.

## Independent results

- `python -m compileall -q hsr_axis_sim`: PASS
- Full pytest suite: **367 passed in 36.83s**
- Locked manifest regression: PASS
  - replays: 12/12
  - manual checks: 2/2
  - search scenarios: 2/2
  - action-sequence checks: 2/2
  - trace-evidence checks: 2/2
- Trace-evidence-only regression: PASS 2/2
- Registry focused tests: PASS 8/8
- Registry Markdown report: byte-identical to committed report
- Registry JSON report: byte-identical to committed report
- Validation mismatch CLI: exit 1
- Missing input CLI: exit 2, no traceback
- Accepted atomic-fact SHA-256 remains:
  `b17a5f295cb8902883d6e8ddaa70c626bdbddf60572db8ce28da6eb3c555491f`

## What is correct

- Registry execution uses a binding ID rather than accepting a raw binding dictionary.
- Handles are frozen dataclasses and list metadata is normalized to tuples.
- Handler dispatch uses a static allow-list and does not import arbitrary JSON module paths.
- The accepted Pela fixture still reproduces the 002J result exactly.
- Paths are resolved under the package root during normal registry loading.
- Duplicate binding IDs, unknown handlers, unsupported types, missing files, metadata mismatches, digest mismatches, partial-to-complete claims, real-trace execution, and damage/toughness implementation claims are rejected for ordinary validly typed JSON.
- No second binding, full kit, real-trace execution, manifest change, or simulator/search change was added.

## Blocking defect found independently

The registry does not strictly validate JSON field types before duplicate checks, tuple conversion, comparisons, and set operations.

Reproduced examples:

1. A dictionary used as `registry_entry_id` is accepted and the CLI exits 0.
2. Integer `0` used as `complete_game_skill` is accepted because Python treats `0 == False`.
3. A dictionary inside `source_atomic_fact_ids` reaches `set(...)`, raises `TypeError: unhashable type: 'dict'`, and prints a traceback instead of returning a controlled validation error.

This means the current object is only safe for well-shaped input. It is not yet a hardened registry boundary for future externally produced or manually edited registry files.

## Required correction

Add strict schema/type validation before any hashing, sorting, duplicate detection, set conversion, path resolution, or handle construction.

At minimum:

- registry root must be a JSON object;
- `registry_version` must be a non-empty string;
- every entry must be a JSON object;
- all ID/category/path/status/digest fields must be non-empty strings;
- boolean fields must use exact JSON booleans (`type(value) is bool`), not `0`/`1`;
- fact-ID and unresolved-field collections must be arrays of non-empty strings;
- reject duplicate strings inside each collection;
- accepted SHA-256 must be exactly 64 lowercase hexadecimal characters;
- malformed but readable input must return CLI exit 1 without traceback;
- supplied registry/handle objects used by `execute_reviewed_binding` must be revalidated or otherwise prevented from bypassing the reviewed loader contract.

## Scope gate

Do not start Tingyun Ultimate in this fix. Preserve the single accepted Pela partial shell, all committed reports, manifest counts, atomic digest, and 002J execution behavior.
