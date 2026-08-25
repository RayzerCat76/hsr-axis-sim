# HSR-RUNTIME-ARCH-023 — Reviewed Static Skill-Point Observation Golden Fixture

## Status

PASS — proceed

## Implementation summary

- Added one independently reviewed static schema-v1 Golden expectation for the clamped production `GainSkillPoint` observation path.
- The fixture is manually specified compact canonical UTF-8 JSON at `hsr_axis_sim/data/runtime_golden_fixtures/arch_023_reviewed_clamped_skill_point_expected.json`.
- Exact fixture identity:
  - size: `2744` bytes;
  - SHA-256: `fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9`;
  - no trailing newline;
  - trace ID: `arch-023-reviewed-static-expected`;
  - fixture ID: `arch-023-reviewed-static-clamped-skill-point`.
- Reviewed production scenario:
  - actor `sp-actor`;
  - action `reviewed-clamped-skill-point`;
  - initial team SP `4` with max SP `5`;
  - one `GainSkillPoint(amount=3)` effect;
  - `ends_turn=False`.
- Expected trace is exactly:
  1. `ACTION_START`;
  2. `SKILL_POINTS_CHANGED`;
  3. `ACTION_END`.
- The resource observation locks:
  - `resource_kind=SKILL_POINTS`;
  - `scope=TEAM`;
  - `before=4`;
  - `after=5`;
  - `requested_delta=3`;
  - `applied_delta=1`;
  - `cap=5`;
  - `unit_id=null`;
  - runtime `target_id=null`.
- Production execution is validated through accepted ARCH-016 and matches the static expected artifact at the comparison layer.
- A deliberate actual-only change `GainSkillPoint.amount=3 -> 2` still clamps from SP 4 to 5, so `after=5` and `applied_delta=1` remain equal while `requested_delta` changes. Accepted first-divergence reporting identifies record index `1` and path `/event/payload/legacy_data/requested_delta`, expected `3`, actual `2`.
- The new SP fixture remains absent from both the legacy and standalone runtime regression manifests.
- ARCH-017 and ARCH-021 reviewed static fixtures remain byte-identical.
- Standalone runtime regression remains 2/2.
- No simulator, adapter, trace contract/schema, loader, exporter, comparator, divergence, Golden validator, regression harness/manifest, AV/timeline, or extra-turn implementation was changed.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_023.md`
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_023_reviewed_clamped_skill_point_expected.json`
- `hsr_axis_sim/tests/test_runtime_arch_023_static_skill_point_golden_fixture.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`

## Tests added

ARCH-023 focused tests cover:

- exact static fixture byte size and SHA-256;
- no trailing newline;
- strict compact canonical loader acceptance with required digest match;
- exact schema-v1 identity and contiguous sequence policy;
- exact three-record `ACTION_START -> SKILL_POINTS_CHANGED -> ACTION_END` order;
- exact actor/action provenance;
- TEAM scope with no unit ID and no runtime target ID;
- exact structured `resource_change` and defensive `legacy_data` payloads;
- every schema-v1 record has `numeric_values == {}`;
- accepted ARCH-016 production Golden PASS;
- final team skill points equal 5;
- exact pending-event order and final capture cursor `(3, 3)`;
- deliberate requested-gain change 3 -> 2 produces a Golden mismatch;
- first divergence is record index 1 at `/event/payload/legacy_data/requested_delta`, expected 3, actual 2;
- deliberate mismatch preserves equal `after=5` and `applied_delta=1`;
- fixture remains absent from both regression manifests;
- AST guard prevents simulator/adapter/export/canonical serialization helpers from becoming a runtime expected-artifact generation path;
- ARCH-017 remains 3013 bytes at SHA-256 `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`;
- ARCH-021 remains 2759 bytes at SHA-256 `4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605`;
- standalone runtime regression remains 2/2;
- legacy regression remains 20/20 and trace evidence remains 2/2;
- production LIFO remains `third, second, first`.

## Exact validation commands and real results

### Initial validated PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #28, run #134, job `validate` (`97646094756`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1161 passed in 7.85s`.
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
   - PASS `2/2` runtime action-session Golden regression:
     - ARCH-017: 4 records;
     - ARCH-021: 3 records.

The first ARCH-023 PR CI was green; no implementation correction was required before finalization.

## Warnings / errors

- No compile, fixture-integrity, strict-loader, ARCH-016, comparator/divergence, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-023 correctness.

## Acceptance review

- Expected bytes are static, reviewed, compact, and digest-pinned.
- Expected bytes are not generated at test runtime from the simulator, adapter, exporter, or canonical serializer.
- Production SP observation matches the reviewed static artifact through accepted ARCH-016.
- Requested-versus-applied clamp semantics are explicitly locked.
- TEAM scope and absence of unit/target identity are explicit rather than inferred.
- Deliberate divergence reuses the same static expected artifact and accepted comparison/first-divergence stack.
- Trace schema v1 remains unchanged and record-level `numeric_values` remains empty.
- Both regression manifests are unchanged and standalone runtime regression stays 2/2.
- ARCH-017 and ARCH-021 fixtures remain unchanged.
- No Energy, AV, speed, advance, delay, immediate-action, extra-turn, character, or release-game semantic was added.
- No hidden HSR value was inferred; fixture values are explicit contract-only test inputs.
- Production LIFO compatibility remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-023 acceptance.

The reviewed SP fixture is intentionally not yet part of the standalone runtime regression lane. Promotion requires a separate narrowly reviewed manifest setup extension; the existing v1.1 setup language supports only `EMPTY` and `ENERGY_GAIN` and must not be broadened generically.

AV/speed/advance/delay/immediate-action/extra-turn state changes still lack equivalent runtime observation events and remain separate work.

## Suggested next milestone

`HSR-RUNTIME-ARCH-024 — Skill-Point Static Golden Regression Promotion`

ARCH-024 should promote the accepted ARCH-023 fixture into the standalone runtime action-session regression lane as a third reviewed case. Evolve the strict manifest setup vocabulary only enough to add one `SKILL_POINT_GAIN` setup containing explicit initial/max SP, action index, and amount. Preserve v1.0/v1.1 compatibility, keep `ENERGY_GAIN` unchanged, avoid generic arbitrary-effect schemas, keep legacy regression unchanged, and require the runtime lane to become exactly 3/3.
