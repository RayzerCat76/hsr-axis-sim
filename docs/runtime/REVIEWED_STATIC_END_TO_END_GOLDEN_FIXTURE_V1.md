# Reviewed Static End-to-End Golden Action Session Fixture v1

## Purpose

HSR-RUNTIME-ARCH-017 adds the first non-circular static expected runtime trace for the explicit production-Action -> ARCH-016 -> Golden validation path.

The expected bytes are stored as a reviewed repository artifact. Tests read those bytes; they do not generate the expected trace from the simulator, adapter, exporter, or any accepted runtime builder at test runtime.

## Fixture identity

- fixture id: `arch-017-reviewed-static-action-session`
- file: `hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json`
- schema: `hsr_runtime_trace` v1.0
- canonical form: compact canonical UTF-8 JSON
- trailing newline: none
- byte size: `3013`
- SHA-256: `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`

## Manual construction basis

The expected record stream is derived directly from already accepted contracts, not from a captured simulator run.

### Explicit production actions

The reviewed test scenario contains exactly two caller-declared actions:

```text
Action id: reviewed-action-a
Actor id: reviewed-actor
Effects: none
ends_turn: false

Action id: reviewed-action-b
Actor id: reviewed-actor
Effects: none
ends_turn: false
```

`Action.execute` emits `action_started` before effects and `action_finished` after effects. Because these actions contain no effects and do not end the turn, no other action-owned or turn-end event is expected from this scenario.

### Accepted legacy adapter mapping

The accepted adapter contract maps:

```text
action_started  -> ACTION_START
action_finished -> ACTION_END
```

For both event types the normalized fields are exactly:

```text
action_id
actor_id
```

The adapter source stream is fixed as:

```text
arch-017-reviewed-static
```

Therefore event IDs are manually assigned by the accepted adapter rule:

```text
legacy:arch-017-reviewed-static:0
legacy:arch-017-reviewed-static:1
legacy:arch-017-reviewed-static:2
legacy:arch-017-reviewed-static:3
```

No accepted mapping in this scenario is ambiguous or unresolved, so every adapter payload uses:

```text
binding_status = BOUND
mapping_status = BOUND
semantic_gap_ids = []
```

## Reviewed record stream

| Sequence | Runtime event | Action | Actor |
|---:|---|---|---|
| 0 | `ACTION_START` | `reviewed-action-a` | `reviewed-actor` |
| 1 | `ACTION_END` | `reviewed-action-a` | `reviewed-actor` |
| 2 | `ACTION_START` | `reviewed-action-b` | `reviewed-actor` |
| 3 | `ACTION_END` | `reviewed-action-b` | `reviewed-actor` |

Every record has empty action/attack/hit contexts, empty numeric values, and empty notes because ARCH-003's accepted event-to-record projection does not infer additional contexts or numeric values.

The expected document therefore has:

```text
record_count = 4
first_sequence = 0
last_sequence = 3
sequence_policy = CONTIGUOUS
event_type_counts = {ACTION_END: 2, ACTION_START: 2}
semantic_gap_ids = []
```

## Expected artifact metadata

Expected wrapper metadata is intentionally review provenance rather than runtime provenance:

```json
{"construction":"manual-reviewed","fixture_id":"arch-017-reviewed-static-action-session","purpose":"end-to-end-golden"}
```

The expected trace id is:

```text
arch-017-reviewed-static-expected
```

ARCH-005 comparison is record-stream based, so the production actual trace may use a different trace id and metadata while still matching the reviewed expected records exactly.

## Digest derivation

After the JSON fields were manually written according to the accepted schema and canonical key ordering, SHA-256 was calculated directly over the exact 3013 UTF-8 bytes:

```text
f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66
```

No simulator, adapter, runtime exporter, or runtime trace builder was invoked to produce those expected bytes.

## Validation tests

ARCH-017 tests perform three independent checks:

1. strict ARCH-004 loading confirms the repository file is exact compact canonical schema-v1 input and matches the pinned digest;
2. matching production `Action` objects execute only through accepted ARCH-016 and must produce a Golden PASS against the static bytes;
3. changing only the second production action id to `reviewed-action-c` must return a completed Golden mismatch whose accepted first divergence is record index `2`, path `/event/action_id`.

The divergence test uses the same unchanged static expected file.

## Regression status

This fixture is intentionally **not** added to `hsr_axis_sim/data/regression_manifest.json` in ARCH-017.

ARCH-017 proves the non-circular end-to-end fixture first. Promotion into the locked regression baseline, if desired, is a separate reviewed milestone.

## Exclusions

ARCH-017 adds no new runtime wrapper or production behavior. It does not modify simulator mechanics, adapter/exporter/loader/comparator/divergence/Golden semantics, replay or action selection, file-writing runtime APIs, video extraction, or FIFO/LIFO behavior.
