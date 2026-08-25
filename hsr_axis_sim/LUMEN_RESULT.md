# HSR-RUNTIME-ARCH-031 — Advance Action Runtime Observation Contract

## Status

PASS — proceed

## Implementation summary

- Added the first deterministic typed runtime observation for production `AdvanceAction` without changing its accepted AV formula or percent input surface.
- Production mutation remains directly:
  - `after_av = max(0, before_av - base_av * percent)`.
- After each target Unit's AV mutation succeeds, production emits one standard legacy `action_advanced` event through `state.emit_event`.
- The event records exact actor/action/target provenance plus:
  - `before_av`;
  - `after_av`;
  - `base_av`;
  - `requested_percent`;
  - `requested_delta_av = -(base_av * requested_percent)`;
  - `applied_delta_av = after_av - before_av`;
  - `clamped_to_zero`.
- `clamped_to_zero` is true only when the requested unclamped result is below zero; reaching exactly zero is not marked as clamped.
- Added `RuntimeEventType.ACTION_VALUE_ADVANCED`.
- Added frozen `RuntimeActionAdvanceObservation` with strict finite-number, target, arithmetic, formula, and clamp validation.
- Bound legacy `action_advanced` to `ACTION_VALUE_ADVANCED`; normalized `action_id`, `actor_id`, and `target_id`; preserved raw `legacy_data`; exposed validated `payload["action_advance"]`.
- Malformed bound advance observations raise `LegacyEventSchemaError`; they are not downgraded to `CONTENT_DEFINED`.
- Standard trigger dispatch is intentional: AV is assigned first, then `action_advanced` is appended/dispatched, so matching triggers observe the post-mutation AV.
- Schema v1 remains unchanged. Advance observation values remain in `RuntimeEvent.payload`, and record-level `numeric_values` remains empty.
- `DelayAction`, `ChangeSpeed`, `ImmediateAction`, and `GrantExtraTurn` were not given new event semantics.
- Historical `docs/runtime/LEGACY_EVENT_MAPPING_V1.json` remains the exact ARCH-002 nine-entry historical projection; ARCH-031's additive mapping is not backfilled into it.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_031.md`
- `docs/runtime/ACTION_ADVANCE_OBSERVATION_V1.md`
- `hsr_axis_sim/runtime_contracts/action_axis_observations.py`
- `hsr_axis_sim/tests/test_runtime_arch_031_advance_action_observation.py`

## Files modified

- `hsr_axis_sim/runtime_contracts/enums.py`
- `hsr_axis_sim/runtime_contracts/__init__.py`
- `hsr_axis_sim/runtime_adapters/legacy_events.py`
- `hsr_axis_sim/sim/effects.py`
- `hsr_axis_sim/tests/test_runtime_arch_002_preservation.py`
- `hsr_axis_sim/tests/test_runtime_contract_enums.py`
- `hsr_axis_sim/tests/test_runtime_legacy_event_mapping.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

No regression manifest, reviewed static fixture, Golden comparator/divergence implementation, loader/exporter, Delay/ChangeSpeed/ImmediateAction/GrantExtraTurn behavior, or extra-turn/LIFO implementation was changed.

## Tests added / updated

ARCH-031 coverage proves:

- `RuntimeActionAdvanceObservation` is frozen and emits the exact schema-v1 payload;
- target ID and all numeric fields are strict; booleans/nonfinite values are rejected;
- `base_av` must be positive;
- requested/applied delta arithmetic is exact;
- `after_av` must match the accepted clamped advance formula;
- clamp flag is exact, including the distinction between below-zero clamp and exact zero;
- negative `requested_percent` remains representable because ARCH-031 does not narrow production input semantics;
- `action_advanced` maps to `ACTION_VALUE_ADVANCED` with exact actor/action/target normalization;
- malformed bound advance observations raise `LegacyEventSchemaError`;
- non-clamped production example remains speed `100`, AV `80`, percent `0.5` -> AV `30`;
- clamped production example remains speed `100`, AV `40`, percent `1.0` -> AV `0`, requested delta `-100`, applied delta `-40`;
- legacy event order is `action_started -> action_advanced -> action_finished`;
- a normal trigger listening to `action_advanced` observes post-mutation AV;
- ARCH-012 capture is exactly `ACTION_START -> ACTION_VALUE_ADVANCED -> ACTION_END`, with cursor `(3,3)`;
- runtime target provenance and `payload["action_advance"]` are exact;
- record-level `numeric_values` remains empty;
- Delay/ChangeSpeed/ImmediateAction/GrantExtraTurn remain outside this event surface;
- production LIFO remains `third, second, first`.

## Exact validation commands and real results

### First PR CI — preservation pins exposed

GitHub Actions workflow `HSR Axis Sim Validation`, PR #36, run #158, job `validate` (`97660846177`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - `1335 passed, 4 failed in 8.79s`.
   - All four failures were stale historical exact-list/count preservation assertions:
     - ARCH-001 vocabulary preservation had not excluded the newly authorized additive enum;
     - current exact `RuntimeEventType` list lacked `ACTION_VALUE_ADVANCED`;
     - legacy mapping registry still expected nine total mappings;
     - bound mapping count still expected eight.
   - No ARCH-031 focused production, observation, adapter, trigger-order, or capture test failed.
3. Later regression steps were skipped because pytest failed.

The fixes updated only those preservation boundaries to explicitly distinguish historical projections from the current additive vocabulary. Production behavior was not changed to satisfy the failures.

### Validated implementation CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #36, run #162, job `validate` (`97661303978`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1340 passed in 8.92s`.
3. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS legacy locked regression `20/20`:
     - 12/12 golden replays;
     - 2/2 manual checks;
     - 2/2 search scenarios;
     - 2/2 action-sequence trace checks;
     - 2/2 trace-evidence checks.
4. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS `2/2` trace-evidence checks.
5. `python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text`
   - PASS `5/5` runtime action-session Golden checks with record counts `4,3,3,3,3`.

## Warnings / errors

- The first PR run exposed four stale preservation assertions; all were corrected without changing production semantics.
- No remaining compile, advance-formula, structured-observation, adapter, trigger-dispatch, capture, legacy-regression, trace-evidence, or runtime-Golden error is known.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-031 correctness.

## Acceptance review

- Existing `AdvanceAction` AV results are preserved.
- Observation data is derived from, and does not replace, the accepted production formula.
- Advance has a dedicated runtime event instead of being hidden under `CONTENT_DEFINED` or prematurely generalized into a broad action-axis event.
- Normal simulator event dispatch is preserved; post-mutation trigger visibility is explicit and tested.
- Schema v1 is unchanged and historical mapping evidence remains intact.
- No adjacent action-axis mechanics were implemented early.
- Successful runtime resource regressions remain `5/5`; legacy regression remains `20/20`; trace evidence remains `2/2`.
- No hidden HSR values or release-game semantics were inferred. Test values are explicit contract-only inputs.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-031 acceptance.

Advance observation is now traceable, but no independently reviewed static Golden fixture yet locks its exact exported bytes. Delay, speed change, immediate action, and extra-turn observation remain separate future mechanics.

## Suggested next milestone

`HSR-RUNTIME-ARCH-032 — Reviewed Static Advance Action Observation Golden Fixture`

ARCH-032 should add one independently reviewed, non-circular compact schema-v1 expected trace for a controlled non-clamped self-advance action (for example speed `100`, before AV `80`, percent `0.5`, after AV `30`) and prove production ARCH-016 output matches it. Keep regression-manifest promotion as a separate later milestone, preserve the new ARCH-031 production contract unchanged, and do not add Delay/Speed/ImmediateAction/ExtraTurn semantics.
