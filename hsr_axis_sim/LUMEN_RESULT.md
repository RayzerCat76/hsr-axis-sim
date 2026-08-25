# HSR-RUNTIME-ARCH-037 — ChangeSpeed Runtime Observation Contract

## Status

PASS candidate — final head CI pending after this report update.

## Implementation summary

- Added the first dedicated runtime observation contract for the existing production `ChangeSpeed` effect without changing its finite-positive-speed formula, target resolution, or existing `new_speed <= 0` error.
- Production behavior remains:
  - capture `before_speed = unit.speed` and `before_av = unit.current_av`;
  - compute `unit.current_av = before_av * before_speed / new_speed`;
  - assign `unit.speed = new_speed`;
  - emit the observation only after both assignments complete.
- Added one legacy event per successfully changed target:
  - `speed_changed`.
- The production event contains only:
  - `actor_id`;
  - `action_id`;
  - `target_id`;
  - `before_speed`;
  - `after_speed`;
  - `before_av`;
  - `after_av`.
- Added dedicated `RuntimeEventType.SPEED_CHANGED`; no existing Advance/Delay event type was renamed or generalized.
- Added frozen `RuntimeSpeedChangeObservation` with strict schema-v1-compatible validation:
  - non-empty target ID;
  - finite non-boolean numeric fields;
  - positive before/after speeds;
  - exact `after_av == before_av * before_speed / after_speed`;
  - no AV floor/clamp.
- Added strict adapter binding:
  - `speed_changed -> RuntimeEventType.SPEED_CHANGED`;
  - normalized action/actor/target IDs;
  - raw source event retained under `payload["legacy_data"]`;
  - typed observation under `payload["speed_change"]`;
  - malformed structured observations raise `LegacyEventSchemaError` rather than degrading to `CONTENT_DEFINED`.
- Trigger dispatch remains on the normal `BattleState.emit_event` path. Tests prove a `speed_changed` listener observes both post-mutation speed and post-mutation AV.
- ARCH-012 capture now proves one non-ending ChangeSpeed action produces exactly:
  - `ACTION_START`;
  - `SPEED_CHANGED`;
  - `ACTION_END`.
- No generic action-axis/speed-change abstraction was introduced.
- No new production validation was added for previously unguarded NaN/infinity/bool inputs; this milestone does not silently alter the accepted production input surface. Runtime structured observations remain strict/canonical instead.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_037.md`
- `docs/runtime/CHANGE_SPEED_OBSERVATION_V1.md`
- `hsr_axis_sim/tests/test_runtime_arch_037_change_speed_observation.py`

## Files modified

Production/runtime:

- `hsr_axis_sim/sim/effects.py`
- `hsr_axis_sim/runtime_contracts/action_axis_observations.py`
- `hsr_axis_sim/runtime_contracts/enums.py`
- `hsr_axis_sim/runtime_contracts/__init__.py`
- `hsr_axis_sim/runtime_adapters/legacy_events.py`

Historical/current preservation tests updated only where ARCH-037 explicitly supersedes the old assumption that ChangeSpeed had no runtime observation:

- `hsr_axis_sim/tests/test_runtime_arch_002_preservation.py`
- `hsr_axis_sim/tests/test_runtime_arch_031_advance_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_034_delay_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_contract_enums.py`
- `hsr_axis_sim/tests/test_runtime_legacy_event_mapping.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

## Locked areas confirmed unchanged

- `hsr_axis_sim/data/regression_manifest.json` unchanged.
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` unchanged at accepted v1.6 / seven cases.
- Every reviewed file under `hsr_axis_sim/data/runtime_golden_fixtures/**` remains byte-identical.
- No static ChangeSpeed Golden fixture was created.
- `AdvanceAction` production formula/event remains unchanged.
- `DelayAction` production formula/event remains unchanged.
- `ImmediateAction` remains unchanged and unobserved.
- `GrantExtraTurn` remains unchanged and unobserved.
- No loader/exporter/comparator/divergence/Golden implementation changed.
- No trace schema version changed.
- Production extra-turn LIFO compatibility remains unchanged.

## Tests added / updated

Focused ARCH-037 coverage proves:

1. `RuntimeSpeedChangeObservation` is frozen and serializes the exact five-field payload.
2. Non-empty target identity is required.
3. Speed/AV fields reject bool and non-finite values in the typed runtime contract.
4. Before/after speeds must be positive.
5. Exact AV rescaling formula is validated.
6. Negative AV remains representable and is not clamped.
7. Direct legacy `speed_changed` adaptation yields `RuntimeEventType.SPEED_CHANGED` and exact `speed_change` payload.
8. Missing/inconsistent/non-finite structured speed observations raise `LegacyEventSchemaError`.
9. Production speed-up example remains exact: speed `100`, AV `80`, new speed `200` -> AV `40`.
10. Production slow-down example remains exact: speed `200`, AV `40`, new speed `100` -> AV `80`.
11. Production negative AV is proportionally rescaled without a new floor.
12. Existing `new_speed <= 0` error remains unchanged and no `speed_changed` event is emitted on that failure path.
13. A `speed_changed` trigger sees both post-mutation speed and AV.
14. ARCH-012 captures exactly `ACTION_START -> SPEED_CHANGED -> ACTION_END` with cursor `(3, 3)`.
15. Advance/Delay observation behavior remains present and separately typed.
16. ImmediateAction and GrantExtraTurn remain without observation emission.
17. All seven reviewed static fixture byte identities remain exact.
18. Legacy regression remains `20/20`.
19. Trace evidence remains `2/2`.
20. Standalone runtime action-session Golden regression remains `7/7`.
21. Extra-turn LIFO remains `third, second, first`.

Historical preservation tests were updated additively rather than weakened:

- the original ARCH-001 event vocabulary projection still excludes all later explicitly authorized additions, now including `SPEED_CHANGED`;
- the current enum registry now explicitly locks `SPEED_CHANGED` in order;
- the current legacy mapping registry now explicitly locks `speed_changed` as the eleventh bound mapping plus one unresolved lifecycle mapping;
- the original ARCH-002 mapping document remains exactly nine historical mappings and is not backfilled;
- ARCH-031/ARCH-034 scope tests now recognize ChangeSpeed as a later ARCH-037 authorization while continuing to prove ImmediateAction and GrantExtraTurn remain untouched.

## Exact validation commands and real results

### Initial PR CI — preservation correction cycle

GitHub Actions workflow `HSR Axis Sim Validation`, PR #42, run #211, job `validate` (`97684128973`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - `6 failed, 1524 passed`.
3. The three downstream regression commands were skipped because the workflow gates them on pytest success.

All six failures were reviewed individually. They were stale preservation/current-registry assertions that predated the explicitly authorized ARCH-037 ChangeSpeed observation:

- original ARCH-001 vocabulary projection did not yet exclude `SPEED_CHANGED`;
- ARCH-031 scope guard still required ChangeSpeed to contain no `emit_event`;
- ARCH-034 scope guard still required ChangeSpeed to contain no `emit_event`;
- current enum registry did not include `SPEED_CHANGED`;
- current legacy mapping registry did not include `speed_changed`;
- bound legacy mapping count remained fixed at ten rather than eleven.

No focused ARCH-037 implementation test failed. No production formula, adapter payload, trigger ordering, ARCH-012 capture, fixture identity, or regression behavior defect was found. The six stale assertions were updated only at the explicitly authorized later-milestone boundary.

### Corrected implementation CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #42, run #212, job `validate` (`97685030484`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1530 passed in 9.13s`.
3. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS legacy locked regression `20/20`:
     - 12/12 Golden replays;
     - 2/2 manual checks;
     - 2/2 search scenarios;
     - 2/2 action-sequence trace checks;
     - 2/2 trace-evidence checks.
4. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS `2/2` trace-evidence checks.
5. `python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text`
   - PASS `7/7` runtime action-session Golden checks.
   - Existing accepted seventh Delay case remains PASS with:
     - expected SHA-256 `9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d`;
     - actual SHA-256 `c47754957a756bd03624aafdcd78e14ecbaed059cce0c99fddb0d116c88bde77`;
     - record count `3`.

## Warnings / errors

- Corrected implementation CI has no compile, pytest, legacy-regression, trace-evidence, or standalone-runtime-regression failure.
- Existing nonblocking GitHub Actions warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node 20 and are forced to run on Node 24.
- Upstream action setup also emits Node `punycode` / `url.parse()` deprecation notices; these are unrelated to simulator correctness.

## Acceptance review

- ChangeSpeed finite-positive behavior remains mathematically identical to the pre-ARCH-037 implementation.
- The event is emitted only after both speed and AV mutation, and normal trigger dispatch observes the fully updated target.
- The runtime contract is dedicated rather than generic and contains only deterministic values already available from production state/mutation inputs.
- No new release-game or hidden-value semantic claim was introduced.
- Runtime strictness does not silently rewrite the production ChangeSpeed input surface.
- Historical ARCH-001/002 evidence remains projected/pinned rather than rewritten.
- Existing Advance/Delay/resource regression lanes remain intact.
- Static expected fixture bytes were not regenerated or modified.
- ImmediateAction and GrantExtraTurn were not implemented early.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-037 acceptance, subject only to the final head CI after this report update.

The current Master Bible / Decision Log summary sections remain older than the recent narrow runtime milestones; this task intentionally does not combine a ChangeSpeed observation PR with a broad governance rewrite.

ChangeSpeed does not yet have an independently reviewed static Golden fixture. ImmediateAction and GrantExtraTurn still lack equivalent runtime observation contracts.

## Suggested next milestone

`HSR-RUNTIME-ARCH-038 — Reviewed Static ChangeSpeed Golden Fixture`

ARCH-038 should manually author and pin one non-circular compact canonical expected runtime trace for a simple positive ChangeSpeed action, then validate the real production action through accepted ARCH-016 against those static bytes and prove one controlled structured divergence. Do not promote the fixture into the regression manifest in the same milestone, and do not implement ImmediateAction or GrantExtraTurn early.

Recommended execution routing: ChatGPT **GPT-5.6 Sol**; Codex reasoning **High** if Codex is used.
