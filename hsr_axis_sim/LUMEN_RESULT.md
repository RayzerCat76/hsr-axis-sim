# HSR-RUNTIME-ARCH-025 — Reviewed Static Energy Consume Observation Golden Fixture

## Status

PASS — proceed

## Implementation summary

- Added one independently reviewed static schema-v1 Golden expectation for the successful production `ConsumeEnergy` observation path.
- The fixture is manually specified compact canonical UTF-8 JSON at `hsr_axis_sim/data/runtime_golden_fixtures/arch_025_reviewed_energy_consume_expected.json`.
- Exact fixture identity:
  - size: `2750` bytes;
  - SHA-256: `7d61528687a5a2f499249e0f914f6f2f50975c7c153165eddd5e116f3ed19a75`;
  - no trailing newline;
  - trace ID: `arch-025-reviewed-static-expected`;
  - fixture ID: `arch-025-reviewed-static-energy-consume`.
- Reviewed production scenario:
  - actor `consume-actor`;
  - target `consume-target`;
  - target starts at Energy `80` with max Energy `100`;
  - one `ConsumeEnergy(target_ids=["consume-target"], amount=30)` effect;
  - `ends_turn=False`.
- Expected trace is exactly:
  1. `ACTION_START`;
  2. `ENERGY_CHANGED`;
  3. `ACTION_END`.
- The resource observation locks successful signed consumption semantics:
  - `resource_kind=ENERGY`;
  - `scope=UNIT`;
  - `before=80`;
  - `after=50`;
  - `requested_delta=-30`;
  - `applied_delta=-30`;
  - `cap=100`;
  - `unit_id=consume-target`;
  - runtime `target_id=consume-target`.
- Production execution is validated through accepted ARCH-016 and matches the static expected artifact.
- A deliberate actual-only `ConsumeEnergy.amount=30 -> 25` change produces a normal Golden mismatch on resource record index `1`. Accepted first-divergence reporting identifies `/event/payload/legacy_data/after`, expected `50`, actual `55`.
- The same mismatch also proves expected signed values `requested_delta=-30`, `applied_delta=-30` versus actual `-25`, `-25`.
- The new fixture remains absent from both the legacy and standalone runtime regression manifests.
- ARCH-017, ARCH-021, and ARCH-023 reviewed static fixture identities remain unchanged.
- Standalone runtime regression remains exactly `3/3`.
- No simulator, runtime adapter, trace schema, loader, exporter, comparator, divergence, Golden validator, regression harness/manifest, AV/timeline, or extra-turn implementation was changed.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_025.md`
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_025_reviewed_energy_consume_expected.json`
- `hsr_axis_sim/tests/test_runtime_arch_025_static_energy_consume_golden_fixture.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`

## Tests added

ARCH-025 focused tests cover:

- exact static fixture byte size and SHA-256;
- no trailing newline;
- strict compact canonical loader acceptance with required digest match;
- exact schema-v1 identity and contiguous sequence policy;
- exact `ACTION_START -> ENERGY_CHANGED -> ACTION_END` order;
- exact actor/action/target provenance;
- exact structured `resource_change` and defensive `legacy_data` payloads;
- every schema-v1 record has `numeric_values == {}`;
- accepted ARCH-016 production Golden PASS;
- final target Energy equals `50`;
- pending-event order is exactly `action_started`, `energy_changed`, `action_finished`;
- final capture cursor is `(3, 3)`;
- deliberate `ConsumeEnergy.amount=30 -> 25` mismatch;
- first divergence is resource record index `1` at `/event/payload/legacy_data/after`, expected `50`, actual `55`;
- expected signed requested/applied deltas remain `-30/-30`, actual values are `-25/-25`;
- fixture remains absent from both regression manifests;
- AST guard prevents simulator/adapter/export/canonical serialization helpers from becoming a runtime expected-artifact generation path;
- ARCH-017 remains 3013 bytes at SHA-256 `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`;
- ARCH-021 remains 2759 bytes at SHA-256 `4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605`;
- ARCH-023 remains 2744 bytes at SHA-256 `fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9`;
- standalone runtime regression remains `3/3`;
- legacy regression remains `20/20` and trace evidence remains `2/2`;
- production LIFO remains `third, second, first`.

## Exact validation commands and real results

GitHub Actions workflow `HSR Axis Sim Validation`, PR #30, run #140, job `validate` (`97649199225`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1203 passed in 8.31s`.
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
   - PASS `3/3` runtime action-session Golden regression:
     - ARCH-017: 4 records;
     - ARCH-021: 3 records;
     - ARCH-023: 3 records.

The first ARCH-025 PR CI was green; no implementation correction was required.

## Warnings / errors

- No compile, fixture-integrity, strict-loader, ARCH-016, comparator/divergence, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-025 correctness.

## Acceptance review

- Expected bytes are static, manually reviewed, compact, and digest-pinned.
- Expected bytes are not generated at test runtime from simulator, adapter, exporter, or canonical serializer code.
- Production successful Energy consumption matches the reviewed static artifact through accepted ARCH-016.
- Negative requested/applied deltas are explicitly locked rather than inferred from final Energy alone.
- Deliberate mismatch reuses the same reviewed expected artifact and accepted comparator/first-divergence stack.
- Trace schema v1 remains unchanged and record-level `numeric_values` remains empty.
- Both regression manifests remain unchanged and standalone runtime regression stays `3/3`.
- Prior reviewed fixtures remain unchanged.
- Insufficient-Energy behavior was deliberately not combined with successful consume semantics.
- No hidden HSR value or release-game semantic was inferred; all fixture values are explicit contract-only test inputs.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-025 acceptance.

The reviewed Energy-consume fixture is intentionally not yet part of the standalone runtime regression lane. Promotion should remain a separate narrow manifest schema milestone.

Insufficient-Energy failure behavior also remains separate because it is an operational exception/no-resource-event path rather than the successful observation contract locked here.

AV/speed/advance/delay/immediate-action/extra-turn state changes still lack equivalent runtime observation events.

## Suggested next milestone

`HSR-RUNTIME-ARCH-026 — Energy Consume Static Golden Regression Promotion`

ARCH-026 should promote the accepted ARCH-025 fixture into the standalone runtime action-session regression lane as a fourth reviewed case. Evolve the strict manifest setup vocabulary only enough to add one explicit `ENERGY_CONSUME` setup using the same Unit fields as `ENERGY_GAIN`, plus action index and amount. Preserve v1.0/v1.1/v1.2 grammars, avoid a generic arbitrary-effect DSL, keep insufficient-Energy failure behavior separate, keep legacy regression unchanged, and require the runtime lane to become exactly `4/4`.
