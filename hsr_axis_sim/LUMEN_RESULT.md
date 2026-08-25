# HSR-RUNTIME-ARCH-037 — ChangeSpeed Runtime Observation Contract

## Status

PASS — proceed

## Implementation summary

- Preserved the existing production `ChangeSpeed` finite-positive-speed formula and existing `new_speed <= 0` error.
- For each successfully changed target, production now emits `speed_changed` only after both AV and speed mutations complete.
- Added dedicated `RuntimeEventType.SPEED_CHANGED`.
- Added frozen `RuntimeSpeedChangeObservation` with exact fields:
  - `target_id`;
  - `before_speed`;
  - `after_speed`;
  - `before_av`;
  - `after_av`.
- Typed validation requires non-empty target identity, finite non-boolean numeric values, positive before/after speeds, and exact `after_av == before_av * before_speed / after_speed`.
- No AV floor/clamp was added; negative AV remains proportionally rescaled.
- Added strict legacy adapter binding `speed_changed -> SPEED_CHANGED`, preserving raw `legacy_data` and exposing the validated observation as `payload["speed_change"]`.
- Malformed structured speed observations raise `LegacyEventSchemaError`; they are not downgraded to `CONTENT_DEFINED`.
- Normal trigger dispatch is preserved. A `speed_changed` trigger observes both post-mutation speed and AV.
- ARCH-012 capture proves exact typed order `ACTION_START -> SPEED_CHANGED -> ACTION_END`.
- No generic action-axis abstraction, static ChangeSpeed Golden fixture, regression promotion, production input cleanup, ImmediateAction observation, or GrantExtraTurn observation was added.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_037.md`
- `docs/runtime/CHANGE_SPEED_OBSERVATION_V1.md`
- `hsr_axis_sim/tests/test_runtime_arch_037_change_speed_observation.py`

## Files modified

- `hsr_axis_sim/sim/effects.py`
- `hsr_axis_sim/runtime_contracts/action_axis_observations.py`
- `hsr_axis_sim/runtime_contracts/enums.py`
- `hsr_axis_sim/runtime_contracts/__init__.py`
- `hsr_axis_sim/runtime_adapters/legacy_events.py`
- `hsr_axis_sim/tests/test_runtime_arch_002_preservation.py`
- `hsr_axis_sim/tests/test_runtime_arch_031_advance_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_034_delay_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_contract_enums.py`
- `hsr_axis_sim/tests/test_runtime_legacy_event_mapping.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

## Tests added / updated

Focused coverage proves:

- frozen strict speed observation and exact payload;
- malformed/non-finite/bool payload rejection;
- positive speed requirement;
- exact rescaling formula;
- speed-up `100 / AV 80 -> 200 / AV 40`;
- slow-down `200 / AV 40 -> 100 / AV 80`;
- negative AV remains unclamped;
- nonpositive requested speed preserves the existing production error and emits no `speed_changed`;
- trigger sees both post-mutation values;
- ARCH-012 exact three-record typed capture;
- Advance and Delay observations remain separate and unchanged;
- ImmediateAction and GrantExtraTurn remain unobserved;
- all seven reviewed static fixture byte identities remain unchanged;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- standalone runtime action-session Golden regression remains `7/7`;
- production LIFO remains `third, second, first`.

Historical preservation tests were updated only where ARCH-037 explicitly supersedes the former assumption that ChangeSpeed had no observation. The original ARCH-001 event vocabulary and ARCH-002 nine-entry mapping document remain preserved as historical projections, while current enum/mapping registries now explicitly include `SPEED_CHANGED` / `speed_changed`.

## Exact commands executed by CI

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Real validation results

### Initial PR CI — preservation correction cycle

GitHub Actions `HSR Axis Sim Validation`, PR #42, run #211, job `97684128973`:

- compile: PASS;
- pytest: `6 failed, 1524 passed`;
- downstream regression steps skipped by the pytest gate.

All six failures were stale preservation/current-registry assertions:

1. ARCH-001 projection had not yet excluded new `SPEED_CHANGED`;
2. ARCH-031 still asserted ChangeSpeed had no `emit_event`;
3. ARCH-034 still asserted ChangeSpeed had no `emit_event`;
4. current enum registry omitted `SPEED_CHANGED`;
5. current legacy mapping registry omitted `speed_changed`;
6. bound mapping count remained ten rather than eleven.

No focused ARCH-037 implementation test failed. No formula, event payload, adapter, trigger-order, ARCH-012 capture, fixture, or existing regression defect was found.

### Corrected implementation CI

GitHub Actions PR #42, run #212, job `97685030484`:

- compile: PASS;
- pytest: **1530 passed in 9.13s**;
- legacy locked regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **7/7**.

### Report-content head CI

GitHub Actions PR #42, run #213, job `97685320027`:

- compile: PASS;
- pytest: **1530 passed in 9.36s**;
- legacy locked regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **7/7**.

The accepted existing seventh Delay case remained PASS with expected SHA-256 `9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d`, actual SHA-256 `c47754957a756bd03624aafdcd78e14ecbaed059cce0c99fddb0d116c88bde77`, and record count `3`.

## Locked areas confirmed unchanged

- `hsr_axis_sim/data/regression_manifest.json` unchanged.
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` unchanged at v1.6 / seven cases.
- Every reviewed static Golden fixture remains byte-identical.
- AdvanceAction and DelayAction production semantics remain unchanged.
- ImmediateAction and GrantExtraTurn remain unchanged.
- No loader/exporter/comparator/divergence/Golden implementation changed.
- No trace schema version changed.
- Production LIFO compatibility remains unchanged.

## Warnings / errors

- Accepted corrected/report-content CI has no compile, pytest, legacy-regression, trace-evidence, or standalone-runtime-regression failure.
- Nonblocking GitHub Actions warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node 20 and are forced onto Node 24.
- Upstream action setup also emits Node `punycode` / `url.parse()` deprecation notices; unrelated to simulator correctness.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-037 acceptance.

ChangeSpeed does not yet have an independently reviewed static Golden fixture. ImmediateAction and GrantExtraTurn still lack equivalent runtime observation contracts.

The Master Bible / Decision Log summary sections remain older than these narrow recent runtime milestones; this task intentionally did not broaden scope into governance synchronization.

## Suggested next milestone

`HSR-RUNTIME-ARCH-038 — Reviewed Static ChangeSpeed Golden Fixture`

Manually author and pin one non-circular compact canonical expected runtime trace for a simple positive ChangeSpeed action, validate the real production action through accepted ARCH-016, and prove one controlled structured divergence. Do not promote it into the regression manifest in the same milestone and do not implement ImmediateAction or GrantExtraTurn early.

Recommended execution routing: ChatGPT **GPT-5.6 Sol**; Codex reasoning **High** if Codex is used.
