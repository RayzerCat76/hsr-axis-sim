# HSR-RUNTIME-ARCH-019 — Runtime Resource Change Observation Contract

## Status

PASS — proceed

## Implementation summary

- Extended `RuntimeEventType` with `ENERGY_CHANGED` and `SKILL_POINTS_CHANGED`.
- Added stable `RuntimeResourceKind` (`ENERGY`, `SKILL_POINTS`) and `RuntimeResourceScope` (`UNIT`, `TEAM`) vocabulary.
- Added frozen `RuntimeResourceChangeObservation` with exact fields `resource_kind`, `scope`, `before`, `after`, `requested_delta`, `applied_delta`, `cap`, and `unit_id`.
- Enforced finite numeric inputs, bool rejection, and the universal arithmetic invariant `applied_delta == after - before`.
- ENERGY observations require UNIT scope and a non-empty `unit_id`.
- SKILL_POINTS observations require TEAM scope, `unit_id=None`, and integer numeric values.
- Added deterministic plain payload conversion for schema-v1 `RuntimeEvent.payload`.
- Proved both new event types export and strict-load under accepted `hsr_runtime_trace` schema v1.0 while `RuntimeTraceRecord.numeric_values` remains empty.
- Added no simulator emission and no legacy adapter binding in ARCH-019.
- Added D-029: resource observations remain payload-level under schema v1 before production emission.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_019.md`
- `docs/runtime/RUNTIME_RESOURCE_CHANGE_OBSERVATION_V1.md`
- `hsr_axis_sim/runtime_contracts/resource_observations.py`
- `hsr_axis_sim/tests/test_runtime_arch_019_resource_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_019_preservation.py`

## Files modified

- `hsr_axis_sim/runtime_contracts/enums.py`
- `hsr_axis_sim/runtime_contracts/__init__.py`
- `hsr_axis_sim/tests/test_runtime_contract_enums.py`
- `hsr_axis_sim/tests/test_runtime_arch_002_preservation.py`
- `hsr_axis_sim/tests/test_runtime_arch_003_preservation.py`
- `hsr_axis_sim/tests/test_runtime_arch_004_preservation.py`
- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No simulator, legacy adapter, strict loader, exporter behavior, Golden/session implementation, regression implementation/manifest, ARCH-017 fixture, or research/reference artifact was modified.

## Tests added / updated

ARCH-019 focused tests cover:

- exact valid ENERGY payload;
- exact valid clamped SKILL_POINTS payload with distinct requested/applied delta;
- frozen observation behavior and RuntimeEvent payload freezing;
- bool, NaN, +Infinity, and -Infinity rejection across all numeric fields;
- inconsistent `applied_delta` rejection;
- ENERGY scope/unit-id rejection;
- SKILL_POINTS scope/unit-id/non-integer rejection;
- compact exporter -> strict-loader round trip for `ENERGY_CHANGED`;
- compact exporter -> strict-loader round trip for `SKILL_POINTS_CHANGED`;
- schema identity remains `hsr_runtime_trace` v1.0;
- loaded record-level `numeric_values` remains empty.

Preservation tests confirm:

- `sim/**` contains no ARCH-019 resource observation wiring;
- `runtime_adapters/**` contains no new resource mapping yet;
- `runtime_loaders/**` remains generic and does not import the resource observation model;
- ARCH-017 fixture remains exactly 3013 bytes at SHA-256 `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`;
- production LIFO compatibility remains unchanged;
- historical ARCH-002/003/004 research/reference hashes stay unchanged;
- every old upstream source not explicitly authorized by ARCH-019 remains byte-pinned;
- after filtering the two ARCH-019 additions, the original ARCH-001 `RuntimeEventType` vocabulary remains in its exact original order.

## Exact validation commands and real results

### Initial PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #24, run #113, job `validate` (`97485037199`):

- compile PASS;
- pytest: `3 failed, 1072 passed in 7.72s`;
- later validation lanes were skipped after pytest failure.

All three failures were historical preservation tests whose SHA dictionaries still treated `runtime_contracts/enums.py` and `runtime_contracts/__init__.py` as permanently byte-frozen. The new ARCH-019 contract tests themselves passed. No research/reference artifact was changed. The correction preserved all old reference hashes and all untouched source hashes, explicitly exempted only the two files authorized to evolve by ARCH-019, and added a compatibility assertion for the original ARCH-001 event vocabulary/order.

### Validated implementation CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #24, run #116, job `validate` (`97485886493`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1076 passed in 7.90s`.
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
   - PASS `1/1` runtime action-session Golden regression.

## Warnings / errors

- No compile, implementation-test, loader/export, legacy-regression, trace-evidence, or runtime-regression errors remain after the preservation-test correction.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-019 correctness.

## Acceptance review

- Runtime resource observation vocabulary is additive and deterministic.
- Requested versus applied delta is explicit and arithmetic consistency is enforced.
- No hidden game values, resource sign assumptions, or extra cap/range rules were invented.
- Trace schema v1 is preserved: resource numbers live in `RuntimeEvent.payload`, not record-level `numeric_values`.
- Simulator resource mutation behavior is unchanged.
- Legacy adapter mapping is unchanged.
- Historical reference artifacts remain byte-for-byte unchanged.
- Existing legacy regression remains 20/20, trace evidence 2/2, and runtime action-session regression 1/1.
- No AV/speed/advance/delay/immediate-action/extra-turn observation, Golden fixture change, replay/video automation, or FIFO/LIFO semantic change was introduced.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-019 acceptance.

ARCH-019 intentionally stops at interface vocabulary. Production `GainEnergy`, `ConsumeEnergy`, `GainSkillPoint`, and `ConsumeSkillPoint` still mutate state without resource-change legacy events, so current captured traces cannot yet observe those transitions end to end.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-020 — Production Resource Change Event Emission and Legacy Adapter Binding`

ARCH-020 should emit explicit post-success resource-change legacy events from existing energy/SP effects and bind them to the accepted ARCH-019 runtime event types. It should preserve `before`, `after`, `requested_delta`, `applied_delta`, `cap`, and resource scope/unit provenance; emit nothing for failed consume operations; preserve existing state mutation semantics; keep data in `RuntimeEvent.payload`; and leave AV/timeline observations, static resource Golden fixtures, and regression promotion for later separate milestones.
