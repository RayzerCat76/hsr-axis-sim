# LUMEN Review — HSR-AXIS-002M-FIX After Codex

## Verdict

**NOT YET ACCEPTED — one narrow hardening fix is still required.**

The requested 002M-FIX behavior is correct for all normal and individually malformed cases covered by the committed tests. The full suite and all locked regressions pass, the readiness status is now correctly `blocked_by_both`, and the committed Markdown/JSON reports are deterministic.

However, an additional combined malformed-input case can still escape the validator as a raw Python `TypeError`. Because this validator is explicitly the evidence-to-binding safety boundary, the task gate remains blocked until every malformed JSON-compatible provenance row fails through controlled `ValueError`.

## Independent verification

```text
python -m compileall -q hsr_axis_sim
PASS

python -m pytest -q
419 passed in 47.74s

Locked regression
PASS 12/12 golden replays
PASS 2/2 manual checks
PASS 2/2 search scenarios
PASS 2/2 action-sequence trace checks
PASS 2/2 trace evidence checks

Trace-evidence-only regression
PASS 2/2

Committed Markdown report vs regeneration
BYTE-IDENTICAL

Committed JSON report vs regeneration
BYTE-IDENTICAL
```

## What is correct

- `declared_readiness_status` is now `blocked_by_both`.
- The report distinguishes source gaps from the unverified same-current-turn duration boundary.
- Target scope is locked to `selected_single_ally`.
- Duration is locked to integer `2`; boolean values are rejected.
- Magnitude remains `null` / `missing`.
- Application order remains `null` / `unresolved`.
- Release scope is locked to the accepted v0.1 qualifier.
- Real-video trace level remains `null` / `missing`.
- Individually malformed enum-like values, source fields, provenance IDs/statuses, and declared readiness are rejected.
- Existing Tingyun Energy and Pela reviewed bindings are unchanged.
- No executable damage buff or HSR-AXIS-002N implementation was added.

## Blocking issue: provenance is sorted before malformed rows are made sort-safe

`_validated_provenance(...)` records validation issues, but still constructs `FactProvenance` values containing the original malformed `locator` value. `_validated_facts(...)` then sorts those rows before `build_report(...)` reaches its aggregated `ValueError` gate.

A single malformed locator often appears harmless because different `source_id` values decide the sort order first. But when malformed input also creates duplicate/equivalent source IDs, Python compares the second tuple element and leaks a raw `TypeError`.

### Reproduction 1

```python
p = copy.deepcopy(review["facts"][0]["provenance"][0])
p["locator"] = {"bad": 1}
review["facts"][0]["provenance"][1] = p
build_report(sources, review)
```

Actual result:

```text
TypeError: '<' not supported between instances of 'dict' and 'str'
```

### Reproduction 2

Two invalid non-string source IDs are normalized to the same empty fallback while their locator types differ.

Actual result:

```text
TypeError: '<' not supported between instances of 'str' and 'dict'
```

Both cases are JSON-compatible malformed documents and must raise controlled `ValueError`, with CLI exit `1` and no traceback.

## Required correction

Make malformed provenance rows sort-safe before any sorting, set conversion, report construction, or comparison. Preferred approaches:

1. Validate each row into local typed variables and only append `FactProvenance` when the row is fully valid; or
2. Use deterministic typed fallback strings for every dataclass field while retaining collected issues.

Do not merely catch `TypeError` around `sorted(...)`. The safety contract is that invalid data is validated before unsafe operations.

Add tests that combine multiple malformed fields in the same provenance list, including:

- duplicate valid source ID + object locator;
- two invalid source IDs + mixed locator types;
- duplicate source ID + list locator;
- direct `build_report(...)` must raise `ValueError` only;
- CLI must exit `1` with no `Traceback`.

## Scope decision

Do not start 002N. This should be a narrow **HSR-AXIS-002M-FIX2** hardening pass only.
