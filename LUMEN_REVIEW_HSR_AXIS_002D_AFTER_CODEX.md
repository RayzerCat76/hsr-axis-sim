# LUMEN REVIEW — HSR-AXIS-002D AFTER CODEX

## Decision

**PASS — HSR-AXIS-002D is accepted.**

The implementation keeps the timestamp/frame layer as non-executable media evidence. It does not reinterpret video seconds as simulator time or claim hidden combat-state values.

## Verification performed by Lumen

### Full test suite

```text
312 passed in 9.58s
```

### Frame-anchor CLI

```text
PASS frame anchor validation passed.
```

### Existing semantic-map CLI

```text
PASS semantic map validation passed.
```

### Locked regression manifest

```text
Manifest: HSR_AXIS_REGRESSION_BASELINE_001Z
Manifest counts: replays=12 manual=1 scenarios=2 action_sequence_traces=1
PASS 12/12 golden replays
PASS 2/2 manual checks
PASS 2/2 search scenarios
PASS 2/2 action-sequence trace checks
```

## What passed review

- A separate frame-anchor fixture exists for the accepted Botu Dilemma real trace.
- The fixture explicitly sets `policy.executable` to `false`.
- The timestamp basis is documented as seconds from the start of local `sample1.mov`.
- The prebattle technique and all nine observed steps each have one matching anchor.
- Actor, action, and step identifiers match the accepted action-sequence trace.
- Approximate boundaries retain confidence metadata.
- Steps 7–9 remain approximate evidence only.
- Mem's action does not claim a precise pull percentage or immediate-action behavior.
- Composite Anaxa actions do not claim exact internal split timing.
- Representative frame files are references only and are not required in the repository.
- The validator rejects missing mappings, mismatched actors/actions, reversed intervals, decreasing start-time order, invalid image references, invalid confidence values, and forbidden combat-state keys.
- Existing replay, search, action-sequence, and semantic-map behavior remains intact.

## Non-blocking hardening item before baseline lock

The validator currently requires top-level `status` and `timestamp_basis` fields to exist, but it does not enforce their exact allowed values. A malformed file could therefore use misleading values while still passing if its policy object remains valid.

Before adding this artifact to the locked regression manifest, 002E should add exact validation and tests for:

```text
status == approximate_media_evidence_only
timestamp_basis == seconds_from_local_clip_start
```

It should also require non-empty string values for `frame_anchor_id` and `version`.

This does not invalidate the current accepted fixture; the fixture itself already uses the intended values.

## Scope still intentionally absent

- No real character kits.
- No executable conversion of the real video trace.
- No SP, energy, HP, toughness, damage, target, RNG, AV, speed, delay, or pull-percentage claims.
- No OCR, video download, scraping, or automatic action recognition.
- No frame-anchor checks in the locked regression manifest yet.

## Next task

Proceed to **HSR-AXIS-002E: Trace Evidence Regression Group MVP**.

The task should lock both the semantic map and frame-anchor artifact into a dedicated `trace_evidence` regression group, separate from numeric replays and action-sequence checks.
