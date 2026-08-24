# HSR-RUNTIME-ARCH-014 — Explicit Successful Session Trace Stitch Handoff

## Current confirmed state

- HSR-RUNTIME-ARCH-013 — PASS.
- Accepted baseline: 998/998 pytest, 20/20 locked regression, 2/2 trace evidence.
- No blocker.

## Objective

Add one read-only typed handoff from a completed successful ARCH-013 multi-action capture session to the accepted ARCH-010 deterministic trace stitcher without executing actions or adding Golden validation.

## Required implementation

- New downstream package `hsr_axis_sim.runtime_session_stitching`.
- Accept only one completed `MultiActionCaptureSessionResult` plus one accepted `CapturedTraceStitchConfig`.
- Extract exactly one ARCH-009 `PendingEventCursorCaptureResult` from each completed ARCH-012 result using `action_result.capture_result`, preserving exact session order and object identity.
- Delegate that tuple exactly once to accepted `stitch_captured_trace_segments`.
- Return a frozen wrapper preserving the complete ARCH-013 session result and complete ARCH-010 stitch result.
- Wrapper invariants require stitch segment count/order/object identity to exactly match the session's completed capture results.

## Acceptance criteria

- Successful session capture segments enter ARCH-010 unchanged and in exact session order.
- Final trace identity/metadata/serialization remain controlled only by caller-supplied `CapturedTraceStitchConfig` and accepted ARCH-010 semantics.
- No action execution, state inspection, event adaptation, export reconstruction, sorting, renumbering, or Golden validation is added.
- ARCH-010 errors propagate unchanged.
- `sim/**` remains unchanged.

## Required tests

- Successful multi-action session -> stitched trace with exact segment identity/order, contiguous runtime event identity/order, final trace ID/metadata/SHA, and record count.
- Monkeypatch handoff to prove accepted ARCH-010 stitcher receives the exact segment objects and exact config exactly once.
- Wrong session/config input types rejected before stitch invocation.
- Underlying stitch failure propagates unchanged.
- Frozen wrapper and rejection of session/stitch provenance mismatch.
- Preservation tests: accepted upstream packages do not import this layer; no action execution/state access/Golden/direct adaptation/export logic; production LIFO unchanged.

## Protected areas

Do not modify existing `sim`, runtime contracts/adapters/exporters/bridges/state-captures/cursors/stitching/stitched-Golden/action-captures/action-sessions/loaders/comparators/divergence/Golden packages, regression/search/bindings/data/fixtures.

## Explicit exclusions

No action execution, `BattleState` access, `Timeline.next_turn`, replay execution, simulator hooks, retry/rollback, file I/O, Golden validation, direct event adaptation/export, sorting/realignment/renumbering, new schema/event mappings, new HSR mechanics, or FIFO/LIFO changes.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

## Final report

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, implementation summary, files added/modified, tests added, exact commands/results, warnings/errors, unresolved issues, exclusions confirmation, and suggested next milestone.

Execution routing: ChatGPT GPT-5.6 Sol. Codex reasoning: High if Codex is used; Codex is optional.
