# HSR-RUNTIME-ARCH-012 — Explicit Single-Action Event Capture Orchestrator

## Current confirmed state

- HSR-RUNTIME-ARCH-011 — PASS.
- Accepted baseline: 975/975 pytest, 20/20 locked regression, 2/2 trace evidence.
- No blocker.

## Objective

Add one explicit sidecar orchestration boundary that executes exactly one caller-supplied production `Action` against one caller-supplied `BattleState`, then captures exactly the newly appended `pending_events` window through accepted ARCH-009/ARCH-008 semantics.

## Required implementation

- New downstream package `hsr_axis_sim.runtime_action_captures`.
- Immutable request containing one caller-owned `PendingEventCaptureCursor` and one accepted `LegacyEventTraceBridgeConfig`.
- Preflight requires the cursor pending-event index to equal the current `len(state.pending_events)` so no pre-existing events can be silently included.
- Call `Action.execute(state, turn_context)` exactly once using the supplied production objects.
- After successful action execution, set the capture end to the current pending-event list length and delegate capture to `capture_battle_state_pending_events_from_cursor`.
- Return a frozen result preserving request, action identity, pre/post event counts, returned `TurnContext`, and complete accepted ARCH-009 capture result.
- No rollback or transactional claim. If action execution or subsequent capture fails, propagate the failure and leave all simulator mutations exactly as they occurred.

## Acceptance criteria

- Successful execution captures exactly `[pre_action_pending_event_count:post_action_pending_event_count)`.
- Existing events before the cursor are excluded.
- Cursor must be aligned to the pre-action list end before the action is executed.
- ARCH-009 next-index and runtime-sequence behavior is preserved exactly.
- Production exceptions are not converted into fake capture results.
- Partial failure is explicitly documented as non-transactional.
- `sim/**` remains unchanged.

## Required tests

- Successful single action capture with exact new events, indices, sequences, action IDs, and cursor advancement.
- Pre-existing pending events remain untouched and excluded.
- Misaligned/stale cursor rejected before `Action.execute` is called.
- Caller-supplied `TurnContext` is passed to the production action and returned by identity.
- Action failure after emitting/mutating preserves partial state/events, propagates the original exception, and does not run capture.
- Post-action capture failure propagates and does not roll back the successful action.
- Frozen/strict request and result models.
- Preservation tests: no `sim/**` modification; no replay/Golden/comparator/stitch calls; production LIFO unchanged.

## Protected areas

Do not modify existing `sim`, runtime contracts/adapters/exporters/bridges/captures/cursors/stitching/loaders/comparators/divergence/Golden packages, regression/search/bindings/data/fixtures.

## Explicit exclusions

No automatic action selection, `Timeline.next_turn` orchestration, replay execution, simulator hooks, queue draining/clearing, rollback, retry, batching, file I/O, Golden validation, trace stitching, new event mappings, new HSR mechanics, or FIFO/LIFO changes.

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
