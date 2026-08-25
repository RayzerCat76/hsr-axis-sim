# HSR-RUNTIME-ARCH-034 — Delay Action Runtime Observation Contract

## Status

PASS — proceed

## Implementation summary

- Added the smallest dedicated runtime observation path for the existing production `DelayAction` AV mutation.
- Preserved the production formula exactly:
  - `requested_delta_av = base_av * percent`;
  - `after_av = before_av + requested_delta_av`;
  - `applied_delta_av = after_av - before_av`.
- `DelayAction` now emits one legacy `action_delayed` event after each target Unit's `current_av` is updated.
- The emitted event contains exact actor/action/target provenance plus `before_av`, `after_av`, `base_av`, `requested_percent`, `requested_delta_av`, and `applied_delta_av`.
- Added dedicated `RuntimeEventType.ACTION_VALUE_DELAYED`; Delay does not reuse `ACTION_VALUE_ADVANCED` or `CONTENT_DEFINED`.
- Added frozen `RuntimeActionDelayObservation` with strict schema-v1-compatible validation:
  - non-empty target ID;
  - finite non-boolean numeric values;
  - positive `base_av`;
  - exact requested-delta equation;
  - exact after-AV equation;
  - exact applied-delta equation.
- Did not add an AV zero floor, clamp flag, positive-percent restriction, or nonnegative-AV restriction. Existing signed `DelayAction` behavior remains representable, including `percent=-0.5` producing a negative AV result.
- Bound legacy `action_delayed` through the accepted one-way adapter to `ACTION_VALUE_DELAYED`.
- Preserved raw legacy data under `payload["legacy_data"]` and added the validated typed structure under `payload["action_delay"]`.
- Malformed Delay observations raise `LegacyEventSchemaError`; they are not silently degraded.
- Confirmed standard trigger dispatch: an `action_delayed` listener sees the post-mutation target AV because the event is emitted after state mutation through `BattleState.emit_event`.
- Confirmed ARCH-012 capture produces exactly `ACTION_START -> ACTION_VALUE_DELAYED -> ACTION_END` for one non-ending Delay action.
- Kept Advance semantics and payload unchanged.
- Kept ChangeSpeed, ImmediateAction, and GrantExtraTurn eventless in this milestone.
- Kept both regression manifests unchanged; runtime action-session manifest remains schema/version `1.5` and `6/6`.
- Kept all six reviewed static Golden fixtures byte-identical.
- Kept production extra-turn LIFO unchanged.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_034.md`
- `docs/runtime/ACTION_DELAY_OBSERVATION_V1.md`
- `hsr_axis_sim/tests/test_runtime_arch_034_delay_action_observation.py`

## Files modified

- `hsr_axis_sim/sim/effects.py`
- `hsr_axis_sim/runtime_contracts/action_axis_observations.py`
- `hsr_axis_sim/runtime_contracts/enums.py`
- `hsr_axis_sim/runtime_contracts/__init__.py`
- `hsr_axis_sim/runtime_adapters/legacy_events.py`
- `hsr_axis_sim/tests/test_runtime_arch_002_preservation.py`
- `hsr_axis_sim/tests/test_runtime_arch_031_advance_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_contract_enums.py`
- `hsr_axis_sim/tests/test_runtime_legacy_event_mapping.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

No reviewed static Golden fixture, regression manifest, runtime action-session regression grammar/version, trace schema, loader/exporter/comparator/divergence/Golden implementation, Advance production behavior, ChangeSpeed behavior, ImmediateAction behavior, GrantExtraTurn behavior, or extra-turn/LIFO implementation was modified.

## Tests added / updated

ARCH-034 coverage proves:

- `RuntimeActionDelayObservation` is frozen and serializes the exact seven-field typed payload;
- empty target IDs, booleans, non-finite values, non-positive base AV, and inconsistent delta/after equations are rejected;
- signed negative `requested_percent` is valid when mathematically consistent;
- speed/base AV `100`, before AV `30`, percent `0.25` produces after AV `55`;
- percent `-0.5` from before AV `30` produces after AV `-20` with no clamp field;
- `action_delayed` maps exactly to `ACTION_VALUE_DELAYED` with action/actor/target normalization;
- malformed legacy Delay observations raise `LegacyEventSchemaError`;
- production event order is `action_started`, `action_delayed`, `action_finished`;
- trigger dispatch occurs after the AV mutation and the listener sees `55.0` in the positive fixture;
- ARCH-012 typed trace order is exactly `ACTION_START`, `ACTION_VALUE_DELAYED`, `ACTION_END`;
- Delay typed runtime event has the target Unit ID and empty schema-v1 `numeric_values`;
- ARCH-031 Advance observation, clamp field, production event type, and formula remain unchanged;
- ChangeSpeed, ImmediateAction, and GrantExtraTurn do not gain Delay/Advance observation emission;
- historical ARCH-001/002 vocabulary evidence remains pinned while explicitly excluding later authorized additive runtime types;
- current enum registry includes `ACTION_VALUE_DELAYED` in exact order;
- legacy mapping registry now contains 11 mappings total: 10 bound plus the existing unresolved `unit_defeated` lifecycle mapping;
- the historical ARCH-002 mapping document remains exactly nine entries and is not backfilled with ARCH-031/034 additions;
- all six previously reviewed static fixture byte lengths and SHA-256 digests remain exact;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- standalone runtime action-session Golden regression remains `6/6` and version `1.5`;
- production extra-turn LIFO remains `third, second, first`.

## Exact validation commands and real results

### First PR CI — closed registry / historical scope pins exposed

GitHub Actions workflow `HSR Axis Sim Validation`, PR #39, run #183, job `validate` (`97674520437`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - `1428 passed, 5 failed in 9.14s`.
   - All five failures were stale registry/scope expectations:
     - ARCH-001 vocabulary preservation did not exclude the newly authorized `ACTION_VALUE_DELAYED` addition;
     - ARCH-031's milestone-local scope guard still treated `DelayAction` as permanently eventless;
     - the exact current RuntimeEventType list did not yet include `ACTION_VALUE_DELAYED`;
     - the exact legacy mapping registry did not yet include `action_delayed`;
     - the bound mapping count was still `9` rather than `10`.
   - No new Delay contract validation, production formula, adapter payload, trigger ordering, ARCH-012 capture, static-fixture digest, or Advance-preservation test failed.
3. Later regression workflow steps were skipped only because the full pytest step failed.

The five failures were corrected by updating closed registries and historical scope boundaries. Production code was not changed in response.

### Second PR CI — one preservation-hash test constant typo

GitHub Actions workflow `HSR Axis Sim Validation`, PR #39, run #187, job `validate` (`97675071805`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - `1432 passed, 1 failed in 8.75s`.
   - The only failure was `test_runtime_arch_002_preservation.py` because the expected SHA-256 string for unchanged `serialization.py` was mistyped while updating the historical preservation test.
   - CI showed the actual unchanged accepted digest as `626a885857b5e7fd90ae5f56ec0ee712bbdca2f28b4f28ea33bbf8be12c0937d`.
3. Later regression workflow steps were skipped only because the full pytest step failed.

The SHA test constant was corrected exactly; no runtime or simulator code changed.

### Corrected green PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #39, run #188, job `validate` (`97675392026`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1433 passed in 8.87s`.
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
   - PASS `6/6` runtime action-session Golden checks.
   - Existing record counts remain `4,3,3,3,3,3`.

## Warnings / errors

- First CI exposed five stale closed-registry / prior-milestone scope assertions; none represented a Delay behavior failure.
- Second CI exposed one mistyped preservation-test SHA string; the protected production file itself was unchanged.
- No remaining compile, Delay formula, typed observation, adapter mapping, trigger dispatch, ARCH-012 capture, Advance preservation, static-fixture integrity, legacy-regression, trace-evidence, or runtime-regression error is known.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-034 correctness.

## Acceptance review

- The only production semantic addition is observation: `DelayAction` still computes the same AV result from the same inputs.
- The event is emitted after mutation and uses the accepted legacy event/trigger path rather than a side channel.
- Delay has its own dedicated runtime event and typed payload; Advance is not overloaded and no generic action-axis DSL was introduced.
- Signed negative Delay behavior remains representable rather than being silently clamped or rejected.
- Malformed observation data fails closed at the adapter boundary.
- Existing schema-v1 trace behavior remains valid; no trace schema bump occurred.
- Both regression manifests remain unchanged.
- All six reviewed static fixtures remain byte-identical.
- Runtime Golden regression remains exactly `6/6`, so ARCH-034 observation is not prematurely promoted into that lane.
- No hidden HSR values or release-game semantics were inferred; numeric examples are deterministic contract fixtures only.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-034 acceptance.

Delay now has production emission, typed runtime adaptation, strict malformed-data rejection, trigger-order coverage, and ARCH-012 capture coverage. It intentionally does not yet have an independently reviewed static Golden fixture or a locked runtime regression case.

ChangeSpeed, ImmediateAction, and GrantExtraTurn remain unobserved deterministic action-axis mechanics and must be handled in separate milestones.

The Master Bible's top-level current-baseline section is historically stale and should be synchronized in a separate governance-focused change rather than mixed into this Delay observation milestone.

## Suggested next milestone

`HSR-RUNTIME-ARCH-035 — Reviewed Static Delay Action Golden Fixture`

ARCH-035 should manually author and review one static canonical expected runtime trace for a deterministic non-clamped positive Delay action, pin its exact byte length and SHA-256, validate production output through the accepted ARCH-016 path, and prove one controlled percent mutation reports the earliest typed `action_delay` divergence. It should not yet promote the fixture into the runtime regression manifest.

Recommended execution routing: ChatGPT **GPT-5.6 Sol**; Codex reasoning **High** if Codex is used, because the reviewed fixture will lock deterministic action-axis observation semantics.
