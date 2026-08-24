# Stitched Actual Golden Validation Handoff V1

## Status

HSR-RUNTIME-ARCH-011 contract.

## Purpose

Close the explicit provenance chain from an ARCH-010 stitched actual runtime trace artifact into the accepted HSR-AXIS-001B Golden Replay validator.

ARCH-011 adds no trace loading, comparison, divergence, or Golden semantics of its own.

## Inputs

`validate_stitched_actual_against_golden` requires:

- one completed `CapturedTraceStitchResult`;
- caller-supplied expected golden runtime trace bytes;
- one accepted `GoldenReplayValidationConfig`.

All inputs are explicit. No files, simulator state, capture queues, or replay execution are consulted.

## Exact actual-byte handoff

The accepted Golden validator is invoked exactly as:

```text
validate_golden_replay_bytes(
    expected_payload_bytes,
    stitch_result.artifact.payload_bytes,
    config=config,
)
```

The actual payload is not reserialized, rebuilt, normalized, encoded, decoded, copied through a trace builder, or written/read through a file boundary before validation.

The stitch artifact's exact canonical/pretty byte identity and SHA-256 therefore remain the actual-trace provenance entering HSR-AXIS-001B.

## Result

`StitchedActualGoldenValidationResult` is immutable and preserves:

- the complete ARCH-010 stitch result;
- the complete accepted `GoldenReplayValidationResult`.

Construction requires the Golden validator's loaded actual artifact to have:

- payload bytes exactly equal to the stitched artifact bytes;
- SHA-256 exactly equal to the stitched artifact SHA-256;
- document equal to the stitched artifact document.

This result does not alter Golden PASS/FAIL semantics. `matches` is the accepted Golden comparison result.

## Deterministic text

`render_stitched_actual_golden_validation_text` emits only stitch provenance before the complete accepted Golden validation text:

- stitched trace ID;
- stitched actual SHA-256;
- segment count;
- accepted Golden Replay report including first divergence.

It does not reformat or reinterpret comparison semantics.

## Failure semantics

- invalid ARCH-011 wrapper input types fail at the wrapper boundary;
- expected digest, size, canonicality, schema, comparison, and divergence-related behavior remains owned by accepted HSR-AXIS-001B and its lower layers;
- those accepted errors propagate rather than being swallowed or converted to a fake mismatch result.

## Explicit non-goals

ARCH-011 does not:

- reserialize or rebuild actual trace bytes;
- call runtime loaders/comparators/divergence directly;
- inspect or mutate simulator state;
- capture or stitch new events;
- execute actions or replay steps;
- add file I/O;
- change Golden Replay semantics;
- change trace schema/event mappings;
- add gameplay mechanics;
- change FIFO/LIFO behavior.
