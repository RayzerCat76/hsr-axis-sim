# Golden Replay Validator V1

`HSR-AXIS-001B` composes the accepted runtime trace sidecars into one deterministic Golden Replay validation boundary.

## Input

`validate_golden_replay_bytes(expected_payload_bytes, actual_payload_bytes, *, config)` accepts two exact byte artifacts plus `GoldenReplayValidationConfig`.

The config contains:
- `replay_id`;
- pinned `expected_sha256`;
- one explicit `TraceCanonicalFormPolicy` used for both artifacts;
- one positive `max_bytes` limit used for both artifacts.

## Ordered validation

1. Load the expected golden artifact with the existing strict loader.
2. Require its SHA-256 to exactly match the pinned digest.
3. Load the actual artifact with the same canonical-form and size policy, but with no claimed pre-known digest.
4. Compare the reconstructed documents through ARCH-005.
5. Build the first-divergence report through ARCH-006.
6. Return one immutable `GoldenReplayValidationResult`.

Errors from the strict runtime loader propagate unchanged. The validator does not normalize, repair, migrate, realign, or coerce either trace.

## Golden integrity rule

A Golden Replay is not defined only by a filename or trace ID. Its expected artifact bytes are integrity-pinned by SHA-256. Changing those bytes requires an explicit new expected digest and therefore an explicit reviewable change.

The actual artifact is intentionally not digest-pinned before execution. Its SHA-256 is still calculated and retained in the result as provenance.

## Comparison rule

The validator adds no comparison semantics. It delegates record comparison to `compare_runtime_trace_documents` and first-divergence selection to `build_first_divergence_report`.

Therefore all accepted ARCH-005/006 rules remain unchanged, including positional comparison, strict JSON types, deterministic field ordering, no heuristic realignment, and no semantic reprioritization.

## Text report

`render_golden_replay_validation_text` emits deterministic replay-level provenance, then embeds the existing ARCH-006 text report. It does not recompute divergence.

## First replay requirement

The first test replay is manually constructed from explicit `RuntimeEvent` values solely to validate the pipeline contract. It is not extracted from video and does not encode inferred hidden HSR values.

## Out of scope

V1 does not add simulator auto-wiring, a CLI/UI, batch manifests, automatic file discovery, video extraction, tolerance rules, repair, record realignment, new HSR mechanics, or FIFO/LIFO changes.
