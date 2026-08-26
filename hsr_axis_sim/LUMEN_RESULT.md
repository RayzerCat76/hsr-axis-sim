# HSR-RUNTIME-ARCH-040 — ImmediateAction Runtime Observation Contract

## Status

PASS — proceed

## Task ID

`HSR-RUNTIME-ARCH-040`

## Current confirmed base

- Accepted `main` before this task: `cde75d15e71a75d7158a5229d07da47dbeab6753`.
- Baseline validation before this task:
  - pytest: **1601 passed**;
  - legacy regression: **20/20**;
  - trace evidence: **2/2**;
  - standalone runtime action-session Golden regression: **8/8**.

## Implementation summary

- Added the smallest typed runtime observation for the already-existing production `ImmediateAction` mutation.
- Preserved the production mutation exactly: each resolved target still receives `unit.current_av = 0`.
- Added one post-mutation legacy event per resolved target:
  - event type: `action_immediate`;
  - fields: `actor_id`, `action_id`, `target_id`, `before_av`, `after_av`.
- Added dedicated runtime event vocabulary:
  - `RuntimeEventType.ACTION_VALUE_IMMEDIATE`.
- Added frozen `RuntimeImmediateActionObservation` with exact payload fields:
  - `target_id`;
  - `before_av`;
  - `after_av`.
- The typed observation requires:
  - non-empty target ID;
  - finite non-boolean numeric AV values;
  - exact `after_av == 0`.
- The observation intentionally does **not** add percent, base AV, requested/applied deltas, clamp flags, priority, turn kind, interrupt semantics, or extra-turn semantics.
- Bound legacy `action_immediate` to `RuntimeEventType.ACTION_VALUE_IMMEDIATE` in the manual one-way legacy adapter.
- Normalized `action_id`, `actor_id`, and `target_id` only.
- Preserved raw event fields under `payload["legacy_data"]` and exposed the validated structured observation under `payload["immediate_action"]`.
- Malformed structured ImmediateAction observations raise `LegacyEventSchemaError`; they are not silently degraded to `CONTENT_DEFINED`.
- Preserved the existing deterministic legacy mapping registry ordering by placing `action_immediate` in lexical order between `action_finished` and `action_started`.
- Added dedicated self-target coverage. A self-target ImmediateAction records its existing AV and then observes the same actor at AV `0`; no new timeline/turn-order interpretation is introduced.
- Preserved `GrantExtraTurn` completely unchanged and unobserved.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_040.md`
- `hsr_axis_sim/tests/test_runtime_arch_040_immediate_action_observation.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`
- `hsr_axis_sim/runtime_contracts/__init__.py`
- `hsr_axis_sim/runtime_contracts/action_axis_observations.py`
- `hsr_axis_sim/runtime_contracts/enums.py`
- `hsr_axis_sim/runtime_adapters/legacy_events.py`
- `hsr_axis_sim/sim/effects.py`
- `hsr_axis_sim/tests/test_runtime_arch_002_preservation.py`
- `hsr_axis_sim/tests/test_runtime_arch_031_advance_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_034_delay_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_037_change_speed_observation.py`
- `hsr_axis_sim/tests/test_runtime_contract_enums.py`
- `hsr_axis_sim/tests/test_runtime_legacy_event_mapping.py`

## Tests added / updated

Focused ARCH-040 coverage verifies:

- `RuntimeImmediateActionObservation` is frozen;
- exact payload shape is only `target_id`, `before_av`, `after_av`;
- empty target IDs are rejected;
- bool/non-numeric/non-finite AV values are rejected by the typed observation;
- `after_av` must equal exactly zero;
- positive, zero, and negative finite `before_av` values remain representable;
- direct legacy `action_immediate` adaptation produces `ACTION_VALUE_IMMEDIATE`;
- raw legacy data is preserved under `legacy_data`;
- validated structured data is exposed under `immediate_action`;
- malformed or missing ImmediateAction fields raise `LegacyEventSchemaError`;
- production self-target ImmediateAction preserves the existing AV-to-zero mutation;
- production zero-AV input remains zero and is still observable;
- production negative AV is set to zero without adding a new precondition or alternate formula;
- one event is emitted per resolved target in declared target order;
- trigger dispatch observes target AV only after the mutation has completed;
- a normal non-ending action produces legacy order `action_started`, `action_immediate`, `action_finished`;
- ARCH-012 capture produces typed order `ACTION_START`, `ACTION_VALUE_IMMEDIATE`, `ACTION_END`;
- record-level `numeric_values` remains empty;
- AdvanceAction, DelayAction, and ChangeSpeed observations remain separately typed and unchanged;
- `GrantExtraTurn` still has no ImmediateAction event emission or observation contract;
- no static ImmediateAction Golden fixture or runtime regression promotion is introduced;
- all eight already accepted reviewed runtime Golden fixtures remain usable and the runtime lane remains `8/8`;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- production extra-turn stack remains LIFO.

Historical preservation/scope tests were updated only where they previously treated ImmediateAction's then-unobserved state or the current enum/mapping registry as a permanent ceiling. Their original historical semantics remain explicitly protected, while later authorized additive observation contracts are no longer incorrectly forbidden.

## Exact commands executed by CI

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Real validation results

GitHub Actions `HSR Axis Sim Validation`, PR #45, run **#240** (`32819183184`), job **`97713545633`**, on branch head `b3aec3506611db6611d4f95eeb256dd12b4f3470`:

- compile: **PASS**;
- pytest: **1627 passed in 10.14s**;
- legacy locked regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **8/8**.

The accepted eight runtime Golden cases all remained PASS with record counts:

1. `arch-017-reviewed-static-action-session` — 4 records;
2. `arch-021-reviewed-static-clamped-energy` — 3 records;
3. `arch-023-reviewed-static-clamped-skill-point` — 3 records;
4. `arch-025-reviewed-static-energy-consume` — 3 records;
5. `arch-027-reviewed-static-skill-point-consume` — 3 records;
6. `arch-032-reviewed-static-action-advance` — 3 records;
7. `arch-035-reviewed-static-action-delay` — 3 records;
8. `arch-038-reviewed-static-change-speed` — 3 records.

No reviewed Golden fixture was added or modified by ARCH-040.

## Validation history / resolved failures

Two earlier PR validation passes were intentionally used to narrow stale historical assertions:

- run **#233**: `7 failed, 1620 passed in 9.95s`;
  - failures were old enum/mapping registry snapshots and ARCH-031/034/037 scope tests that still required `ImmediateAction` to emit no event forever;
  - no focused ARCH-040 behavior test failed.
- run **#239**: `1 failed, 1626 passed in 7.43s`;
  - the only remaining failure was deterministic legacy mapping registry order because `action_immediate` had initially been inserted before `action_finished`;
  - production semantics and focused ImmediateAction tests passed.

The mapping was moved to its accepted deterministic lexical position without weakening the registry-order test. Run #240 then passed the complete workflow including all three regression lanes.

## Locked areas confirmed unchanged

- Existing `ImmediateAction` state mutation remains `current_av = 0` for every resolved target.
- `GrantExtraTurn` implementation and extra-turn stack behavior are unchanged.
- Production extra-turn LIFO behavior is unchanged.
- `AdvanceAction`, `DelayAction`, and `ChangeSpeed` formulas/events are unchanged.
- Timeline selection/reset/tie-breaking behavior is unchanged.
- Action family, turn kind, priority, interrupt, and extra-turn semantics are not inferred from ImmediateAction.
- `hsr_axis_sim/data/regression_manifest.json` is unchanged.
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` is unchanged.
- `hsr_axis_sim/runtime_action_session_regression/**` is unchanged.
- all files under `hsr_axis_sim/data/runtime_golden_fixtures/**` are unchanged.
- Golden validator/comparator/divergence implementation is unchanged.
- trace loader/exporter/stitching implementation is unchanged.
- trace schema/version is unchanged.

## Warnings / errors

- No compile, pytest, legacy-regression, trace-evidence, or runtime-action-session-regression failure remains in run #240.
- Nonblocking GitHub Actions warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node 20 and are forced onto Node 24.
- Upstream action setup continues to emit Node `punycode` and `url.parse()` deprecation notices. These warnings predate ARCH-040 and are unrelated to simulator correctness.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-040 acceptance.

`ImmediateAction` now has a dedicated runtime observation contract, but it does not yet have a reviewed static Golden fixture or standalone runtime regression case. Those are intentionally separate milestones.

`GrantExtraTurn` remains intentionally unobserved and out of scope. Actual HSR scheduling interpretation remains separate from the simulator's accepted deterministic production behavior.

The Master Bible current-baseline summary is historically stale relative to the accepted runtime frontier; ARCH-040 does not broaden scope into governance synchronization.

## Exclusions confirmation

Respected: no `GrantExtraTurn` changes or observation, no static ImmediateAction Golden fixture, no runtime regression promotion, no generic action-axis DSL, no Timeline/tie-breaking changes, no priority/action-family/interrupt/extra-turn inference, no release-game hidden values, no trace schema version bump, no Golden/comparator/divergence changes, no legacy regression-manifest change, no video parsing/scraping, no character database work, no AI optimization, and no unrelated UI/refactor work.

## Suggested next milestone

`HSR-RUNTIME-ARCH-041 — Reviewed Static ImmediateAction Golden Fixture`

Construct and independently review one minimal deterministic static Golden expectation for a production non-ending `ImmediateAction` action session using the accepted ARCH-040 event contract. Pin exact canonical bytes and SHA-256, prove one matching session passes and one controlled mismatch reports the accepted first divergence, and keep the fixture outside the runtime regression manifest until a later explicit promotion milestone.

Recommended execution routing: ChatGPT **GPT-5.6 Terra**; Codex reasoning **High** for exact-byte deterministic fixture construction/review while preserving the now-accepted ImmediateAction semantics.
