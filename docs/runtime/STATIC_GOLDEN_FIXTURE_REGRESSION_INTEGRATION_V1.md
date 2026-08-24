# Reviewed Static End-to-End Golden Fixture Regression Integration v1

## Purpose

HSR-RUNTIME-ARCH-018 promotes the proven ARCH-017 static non-circular Golden fixture into the locked regression runner without reusing the legacy replay validator or changing the static fixture bytes.

The existing regression manifest ID remains `HSR_AXIS_REGRESSION_BASELINE_001Z`; this milestone extends that accepted baseline with one explicitly separate runtime-action-session group. The previous five groups remain unchanged and must continue to contribute their prior 20 passing checks.

## Why this is not a legacy replay

`replays` and `manual` use the existing `ReplayValidator` and legacy replay JSON contracts. The ARCH-017 artifact is an `hsr_runtime_trace` v1 Golden expectation validated through ARCH-016.

Routing the ARCH-017 fixture through `replays` would conflate two incompatible contracts. ARCH-018 therefore adds:

```text
runtime_action_sessions
```

This group has independent reporting and dispatch.

## Manifest entry v1

ARCH-018 supports one narrow check mode:

```text
no_effect_action_session_golden
```

Each entry must contain:

```text
id
path
check
expected_sha256
adapter_stream_id
actor_id
action_ids
```

Rules:

- `path` must exist under the existing manifest path-resolution rules;
- `check` must equal `no_effect_action_session_golden`;
- `expected_sha256` must be exactly 64 lowercase hexadecimal characters;
- `adapter_stream_id` must be a non-empty string;
- `actor_id` must be a non-empty string;
- `action_ids` must be a non-empty ordered list of unique non-empty strings;
- generic effects, targets, turn contexts, and action-generation semantics are not part of v1.

## Locked ARCH-017 entry

The first entry is:

```text
id: arch-017-reviewed-static-action-session
path: hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json
check: no_effect_action_session_golden
expected_sha256: f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66
adapter_stream_id: arch-017-reviewed-static
actor_id: reviewed-actor
action_ids:
  - reviewed-action-a
  - reviewed-action-b
```

The expected fixture remains exactly 3013 bytes with no trailing newline. ARCH-018 does not rewrite it.

## Runner contract

For each `runtime_action_sessions` entry, the runner:

1. reads the exact static expected bytes from `entry.path`;
2. creates one fresh `BattleState([])`;
3. creates production `Action` objects in declared `action_ids` order using:
   - `id = action_id`;
   - `name = action_id`;
   - declared `actor_id`;
   - no effects;
   - `ends_turn=False`;
4. creates explicit caller-owned cursor/adapter/per-segment/final-stitch/Golden configs deterministically from the entry;
5. calls accepted `run_action_session_validation` (ARCH-016) exactly as the validation boundary;
6. reports the accepted result.

The runner does not directly call ARCH-013, ARCH-014, ARCH-015, ARCH-011, the Golden byte validator, loader, comparator, or first-divergence builder for this group.

## Mismatch reporting

A Golden mismatch remains a completed ARCH-016 result. The regression checker reads the already-produced accepted provenance and exposes:

```text
mismatch_count
first_divergence_record_index
first_divergence_status
first_divergence_path  # when a field difference exists
```

It does not recompute or reprioritize divergence.

## Discovery and CLI

`runtime_action_sessions` is a first-class accepted regression group:

```bash
python -m hsr_axis_sim.regression.runner \
  --manifest hsr_axis_sim/data/regression_manifest.json \
  --only runtime_action_sessions \
  --format text
```

Default in-process regression discovery loads the runtime-action-session entries from the canonical default regression manifest so the new locked check is not silently omitted outside manifest-driven CI.

## Expected locked baseline after ARCH-018

Existing groups remain:

```text
12/12 golden replays
2/2 manual checks
2/2 search scenarios
2/2 action-sequence trace checks
2/2 trace evidence checks
```

These still total 20/20.

ARCH-018 adds:

```text
1/1 runtime action-session Golden checks
```

Expected locked total:

```text
21/21
```

Trace-evidence-only remains 2/2.

## Exclusions

ARCH-018 does not add a generic Action DSL, effects, targeting, turn selection, replay/video extraction, expected regeneration, new runtime/Golden semantics, simulator changes, or FIFO/LIFO changes.
