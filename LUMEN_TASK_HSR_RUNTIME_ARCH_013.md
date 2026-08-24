# HSR-RUNTIME-ARCH-013 — Explicit Multi-Action Capture Session

## Current confirmed state

- HSR-RUNTIME-ARCH-012 — PASS.
- Accepted baseline: 986/986 pytest, 20/20 locked regression, 2/2 trace evidence.
- No blocker.

## Objective

Compose an explicit caller-supplied ordered sequence of production actions through repeated accepted ARCH-012 single-action capture calls while preserving caller-owned cursor continuity and explicit non-transactional failure provenance.

## Required implementation

- New downstream package `hsr_axis_sim.runtime_action_sessions`.
- Frozen `ExplicitActionCaptureStep` containing one production `Action` and optional production `TurnContext`.
- Frozen `MultiActionCaptureSessionConfig` containing:
  - initial caller-owned `PendingEventCaptureCursor`;
  - one accepted `LegacyEventAdapterConfig` shared by the session;
  - one explicit tuple of per-step `TraceExportConfig` values;
  - one explicit `pretty` flag for segment artifacts.
- Session runner accepts a non-empty tuple of explicit steps and requires the number of per-step export configs to match exactly before executing anything.
- For each step in declared tuple order:
  - construct `LegacyEventTraceBridgeConfig` using the common adapter config, current cursor runtime sequence, that step's explicit export config, and session pretty flag;
  - construct `SingleActionEventCaptureRequest` from the current cursor;
  - invoke accepted ARCH-012 `execute_action_and_capture_pending_events` exactly once;
  - append the completed result and advance only from its accepted `next_cursor`.
- Successful frozen result preserves config, exact step tuple, exact completed ARCH-012 result tuple, and final cursor.
- Add controlled `MultiActionCaptureSessionFailure` for any step failure. It must preserve failed index/action ID, tuple of completed results before failure, and last successful cursor; the original exception must be chained as `__cause__`.

## Failure semantics

- Stop immediately at the first failed step.
- Do not execute later actions.
- Do not return a successful session result.
- Do not rollback, retry, clear queues, or synthesize capture results/cursor advancement.
- Failed action or failed post-action capture may already have mutated simulator state and appended uncaptured events.
- `last_successful_cursor` means only the last confirmed completed capture boundary. It must NOT be documented or treated as automatically safe to resume/retry from after a failed action.

## Acceptance criteria

- Declared action order is authoritative and preserved.
- Every step uses exactly the current accepted cursor from the previous completed step.
- Per-step trace config identity/order is explicit and preserved.
- Session uses one common accepted legacy adapter config and one explicit pretty flag.
- No automatic turn selection, action selection, sorting, replay logic, stitching, or Golden validation.
- Failure provenance is inspectable and original exception remains chained.
- `sim/**` remains unchanged.

## Required tests

- Successful 2–3 action session: exact order, action IDs, cursor index/sequence chain, per-step trace IDs/metadata, final cursor.
- Reuse of the same caller-supplied `TurnContext` object across two non-ending actions; production `actions_taken` accumulates and identity is preserved.
- Failure on second action: first result retained in failure provenance, exact failed index/action ID, third action not executed, partial mutation/events remain, original exception is `__cause__`.
- Post-action capture/adaptation failure on second action: same stop/provenance semantics, successful action mutation remains.
- Empty steps and export-config count mismatch rejected before any action executes.
- Strict/frozen step/config/result models and exact result alignment checks.
- Preservation tests: accepted upstream packages do not import session layer; session runner calls only ARCH-012 execution boundary; no direct Timeline/replay/Golden/stitch/capture/export implementation; production LIFO unchanged.

## Protected areas

Do not modify existing `sim`, runtime contracts/adapters/exporters/bridges/state-captures/cursors/stitching/stitched-Golden/action-captures/loaders/comparators/divergence/Golden packages, regression/search/bindings/data/fixtures.

## Explicit exclusions

No `Timeline.next_turn`, automatic action generation/selection, replay execution, simulator hooks, queue draining/clearing, rollback, retry, file I/O, trace stitching, Golden validation, new event mappings, new schema, new HSR mechanics, or FIFO/LIFO changes.

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
