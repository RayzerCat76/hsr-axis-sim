# End-to-End Action Session Validation v1

## Scope

HSR-RUNTIME-ARCH-016 adds one explicit caller-controlled composition boundary over accepted ARCH-013, ARCH-014, and ARCH-015.

It provides a single call from caller-declared production actions to an accepted Golden Replay result without adding new simulator, capture, stitch, or Golden semantics.

## Inputs

`run_action_session_validation` accepts:

- caller-owned `BattleState`;
- non-empty tuple of accepted `ExplicitActionCaptureStep` values;
- accepted `MultiActionCaptureSessionConfig`;
- accepted `CapturedTraceStitchConfig`;
- caller-supplied expected Golden payload bytes;
- accepted `GoldenReplayValidationConfig`.

The caller remains responsible for action order, optional turn contexts, initial cursor, adapter configuration, per-action segment trace configs, final stitched trace config, and Golden expectation/configuration.

## Preflight rule

Before ARCH-013 starts state-mutating action execution, ARCH-016 rejects directly checkable invalid input shape/type, including:

- invalid state type;
- empty or invalid step tuple;
- invalid session config;
- segment-config count different from step count;
- invalid stitch config;
- non-bytes expected payload;
- invalid Golden config.

ARCH-016 does not independently parse or integrity-check expected Golden bytes. Those semantics remain exclusively in the accepted Golden path, so digest/content failures may still occur after actions have completed.

## Exact stage order

On valid input, the only execution order is:

```text
ARCH-013 run_multi_action_capture_session
-> ARCH-014 stitch_successful_action_session
-> ARCH-015 validate_successful_session_against_golden
```

Each accepted stage is called exactly once.

The exact returned object from each stage is passed unchanged to the next stage. ARCH-016 does not reconstruct session, stitch, trace, or Golden objects.

## Result

`EndToEndActionSessionValidationResult` is frozen and preserves the exact:

- ARCH-013 `MultiActionCaptureSessionResult`;
- ARCH-014 `SuccessfulSessionTraceStitchResult`;
- ARCH-015 `SuccessfulSessionGoldenValidationResult`.

Construction requires object identity across the stage chain:

```text
session_stitch_result.session_result is session_result
validation_result.session_stitch_result is session_stitch_result
```

This prevents equal-looking reconstructed provenance from being substituted for the accepted stage outputs.

## Failure semantics

ARCH-016 is not transactional.

### ARCH-013 failure

The accepted `MultiActionCaptureSessionFailure` propagates unchanged. ARCH-014 and ARCH-015 are not called. Any mutations/events created before or during the failed action remain exactly as ARCH-013/ARCH-012 define.

### ARCH-014 failure

All ARCH-013 actions have already completed. The ARCH-014 exception propagates unchanged. ARCH-015 is not called. No action rollback occurs.

### ARCH-015 failure

All actions and stitching have already completed. The ARCH-015 exception propagates unchanged. No rollback or synthetic result is created.

### Golden mismatch

A Golden mismatch is not an operational exception. It returns a complete ARCH-016 result whose nested accepted Golden result contains the existing comparator and first-divergence provenance.

## Full explicit successful path

```text
caller-declared action steps/configs
-> ARCH-013 deterministic action capture session
-> ARCH-014 exact session capture-object stitch handoff
-> accepted ARCH-010 deterministic stitched actual artifact
-> ARCH-015 exact stitch-object handoff
-> accepted ARCH-011 exact-byte Golden handoff
-> accepted Golden PASS / first divergence
```

## Exclusions

ARCH-016 does not authorize:

- `Timeline.next_turn` or automatic turn selection;
- automatic action generation/selection;
- replay execution;
- simulator hooks;
- rollback or retry;
- queue draining/clearing;
- file I/O;
- direct ARCH-012 capture orchestration;
- direct ARCH-010 stitching;
- direct ARCH-011 or lower Golden validation calls;
- trace/event reconstruction;
- schema/event-map changes;
- new HSR mechanics;
- FIFO/LIFO changes.
