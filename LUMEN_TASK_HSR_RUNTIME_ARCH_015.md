# HSR-RUNTIME-ARCH-015 — Explicit Successful Session Golden Validation Handoff

## Current confirmed state

- HSR-RUNTIME-ARCH-014 — PASS and merged to `main`.
- Confirmed baseline: 1007/1007 pytest, 20/20 locked regression, 2/2 trace evidence.
- Current blocker: none.

## Objective

Add the smallest read-only typed composition from one completed successful ARCH-014 session-stitch result into the accepted ARCH-011 stitched-actual Golden validation handoff.

## Required implementation

1. Add one downstream package `hsr_axis_sim.runtime_session_golden_validation`.
2. Public entry point accepts exactly:
   - one `SuccessfulSessionTraceStitchResult`;
   - caller-supplied expected Golden payload bytes;
   - one accepted `GoldenReplayValidationConfig`.
3. Pass exactly `session_stitch_result.stitch_result` to accepted ARCH-011 `validate_stitched_actual_against_golden` exactly once.
4. Do not rebuild, restitch, reserialize, reload, or otherwise recreate actual trace bytes.
5. Return one frozen wrapper preserving:
   - the complete ARCH-014 session-stitch result;
   - the complete accepted ARCH-011 stitched-Golden validation result.
6. Wrapper construction must prove the ARCH-011 result contains the exact same Python stitch-result object as ARCH-014.
7. Golden mismatch remains a completed validation result; ARCH-011/input/operational errors propagate unchanged.

## Acceptance criteria

- Exact ARCH-014 stitch object enters ARCH-011 unchanged.
- No action/session execution or BattleState access.
- No direct Golden Replay validator, loader, comparator, divergence, exporter, stitcher, or file-I/O implementation.
- No trace/event reconstruction, sorting, realignment, renumbering, or repair.
- Frozen wrapper preserves full provenance and rejects stitch-object substitution.
- Existing production/runtime/Golden behavior remains unchanged.
- Complete CI suite passes.

## Required tests

- matching successful session-stitch -> Golden PASS through ARCH-011;
- Golden mismatch remains completed result with accepted first-divergence provenance;
- exact ARCH-014 stitch Python object is passed once to ARCH-011;
- invalid input types are rejected before ARCH-011 invocation;
- underlying ARCH-011 operational/input failure propagates unchanged;
- frozen wrapper rejects equal-looking/different stitch provenance;
- preservation test proves accepted upstream packages do not import the new package and production LIFO remains unchanged.

## Files/areas that must remain unchanged

Do not modify executable behavior in `sim/**`, `search/**`, `regression/**`, `adapters/**`, `real_bindings/**`, `data/**`, accepted runtime packages, accepted Golden packages, fixtures, or reference artifacts.

## Explicit exclusions

No action/session execution, `BattleState`, `Timeline.next_turn`, replay/action selection, retry/rollback, file I/O, trace stitching, actual-trace reserialization, direct Golden validator/comparator/divergence calls, event-map/schema changes, new HSR mechanics, or FIFO/LIFO changes.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

## Final report format

Report task ID, implementation summary, files added/modified, tests added, exact commands/results, warnings/errors, unresolved issues, exclusion confirmation, suggested next milestone, and update `hsr_axis_sim/LUMEN_RESULT.md`.

## Execution routing

ChatGPT: GPT-5.6 Sol.  
Codex: High if used; Codex is optional for this milestone.
