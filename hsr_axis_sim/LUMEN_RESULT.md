# HSR-RUNTIME-ARCH-020 — Production Resource Change Event Emission and Legacy Adapter Binding

## Status

PASS — proceed

## Implementation summary

- Bound the accepted ARCH-019 energy and skill-point observation contract to exactly four existing production effects: `GainEnergy`, `ConsumeEnergy`, `GainSkillPoint`, and `ConsumeSkillPoint`.
- Preserved the existing mutation formulas, gain clamps, and insufficient-resource checks.
- Added post-success normal production events through `BattleState.emit_event`:
  - `energy_changed` once per successfully mutated energy target;
  - `skill_points_changed` once per successful team skill-point mutation.
- Resource events preserve `actor_id`, `action_id`, `resource_kind`, `scope`, `before`, `after`, `requested_delta`, `applied_delta`, `cap`, and `unit_id`.
- Gain records the requested positive amount while `applied_delta` records the actual clamped change. Consume records the requested negative amount.
- Failed consume checks still raise before mutation and emit no resource-change event for the failed mutation.
- Resource events use ordinary trigger-visible production dispatch. No rollback was added after a post-mutation dispatch/trigger failure; accepted non-transactional action semantics remain authoritative.
- Extended the accepted legacy adapter with:
  - `energy_changed -> RuntimeEventType.ENERGY_CHANGED`;
  - `skill_points_changed -> RuntimeEventType.SKILL_POINTS_CHANGED`.
- Energy normalizes `action_id`, `actor_id`, and runtime `target_id <- unit_id`; skill points normalize `action_id` and `actor_id` with no runtime target ID.
- The adapter validates resource data by constructing the accepted ARCH-019 `RuntimeResourceChangeObservation`. Its exact `to_payload()` projection is stored at `payload.resource_change` while existing `payload.adapter` and defensive `payload.legacy_data` provenance remain intact.
- Malformed resource observations are rejected as `LegacyEventSchemaError`; no repair or semantic normalization is attempted.
- Trace schema v1 is unchanged. Resource numbers remain event payload data and captured `RuntimeTraceRecord.numeric_values` remains empty.
- Added an executable current-engine counterexample proving that resource-event trigger visibility creates a real observation point between ordered effects: a trigger on `energy_changed` can make `GainEnergy -> AddBuff` and `AddBuff -> GainEnergy` produce different final same-ID buff state.
- This executable counterexample invalidates the premises of the older Tingyun 002P current-contract effect-order proof, which explicitly pinned `GainEnergy` as emitting no event and stated that future engine changes were outside its proof. The historical 002P and dependent 002Q evidence/report artifacts were not edited or regenerated. Their current-contract validators now correctly reject the stale source pins, and tests treat the committed artifacts as historical evidence rather than silently rewriting them.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_020.md`
- `docs/runtime/RUNTIME_RESOURCE_EVENT_BINDING_V1.md`
- `hsr_axis_sim/tests/test_runtime_arch_020_resource_event_binding.py`
- `hsr_axis_sim/tests/test_runtime_arch_020_effect_order_supersession.py`

## Files modified

- `hsr_axis_sim/sim/effects.py`
- `hsr_axis_sim/runtime_adapters/legacy_events.py`
- `docs/runtime/LEGACY_EVENT_MAPPING_V1.json`
- `docs/runtime/LEGACY_EVENT_ADAPTER_V1.md`
- `hsr_axis_sim/tests/test_runtime_legacy_event_mapping.py`
- `hsr_axis_sim/tests/test_runtime_arch_003_preservation.py`
- `hsr_axis_sim/tests/test_runtime_arch_004_preservation.py`
- `hsr_axis_sim/tests/test_runtime_arch_019_preservation.py`
- `hsr_axis_sim/tests/test_tingyun_ultimate_effect_order_irrelevance.py`
- `hsr_axis_sim/tests/test_tingyun_ultimate_turn_entry_duration_gap.py`
- `hsr_axis_sim/LUMEN_RESULT.md`

No Golden fixture, Golden manifest, regression manifest, trace schema, timeline implementation, extra-turn implementation, runtime loader/export/comparator/divergence implementation, character binding, or research/evidence/report artifact was modified.

## Tests added / updated

ARCH-020 focused tests cover:

- exact unclamped `GainEnergy` event fields;
- clamped `GainEnergy` with distinct requested/applied deltas;
- successful `ConsumeEnergy` signed deltas;
- insufficient-energy failure with unchanged energy and no resource event;
- exact unclamped and clamped `GainSkillPoint` observations;
- successful and insufficient `ConsumeSkillPoint` behavior;
- deterministic multi-target energy event order matching declared target order;
- resource events traversing the existing trigger-visible dispatch path;
- exact ENERGY adapter mapping, normalized IDs, BOUND status, defensive raw snapshot, and structured `resource_change` payload;
- exact SKILL_POINTS adapter mapping with no target ID;
- malformed/missing/mismatched resource legacy observations rejected without repair;
- ARCH-012 action capture order `ACTION_START -> ENERGY_CHANGED -> ACTION_END`;
- captured schema-v1 record-level `numeric_values == {}`;
- executable proof that an `energy_changed` trigger can make two previously assumed-equivalent effect orders observably different;
- production simulator remains free of runtime-sidecar imports;
- ARCH-017 static fixture identity remains unchanged;
- production LIFO remains `third, second, first`;
- historical research/reference artifacts remain unchanged.

The existing Tingyun validator suites retain their malformed-input, safety-boundary, unknown-value, source-locator, and CLI controlled-error coverage. Only the assertions that required the archived 002P/002Q artifacts to remain valid against the changed current engine were revised: those artifacts are now required to remain readable historical evidence while their current-contract validation fails on stale source pins.

## Exact validation commands and real results

### Initial PR CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #25, run #121, job `validate` (`97639605110`):

- compile PASS;
- pytest: `11 failed, 1077 passed in 7.40s`;
- later validation lanes were skipped after pytest failure.

All 11 failures came from the existing Tingyun 002P effect-order and 002Q turn-entry current-contract audit suites. The new ARCH-020 focused tests passed. The failures were not treated as stale-hash noise: ARCH-020 made `GainEnergy` emit a trigger-visible intermediate event, directly invalidating an explicit 002P proof premise (`GainEnergy` emitted no event; no intermediate primitive event existed). A dedicated executable counterexample was added before the historical tests were revised. No Tingyun evidence/report artifact was changed.

### Validated implementation CI

GitHub Actions workflow `HSR Axis Sim Validation`, PR #25, run #124, job `validate` (`97641064492`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1090 passed in 7.75s`.
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

- No compile, focused-test, adapter, legacy-regression, trace-evidence, or runtime-Golden errors remain after the explicit historical-proof supersession handling.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-020 correctness.
- The default historical Tingyun 002P/002Q current-contract audit CLIs now intentionally exit with controlled validation failure because their source pins describe a pre-ARCH-020 engine. They do not emit tracebacks and their archived reports remain unchanged.

## Acceptance review

- Existing resource mutation behavior is preserved apart from the newly authorized observation events.
- Clamped gains expose requested versus applied change explicitly.
- Failed consumes emit no false resource-change event.
- Resource events are real trigger-visible production events.
- Adapter binding is strict and typed through the accepted ARCH-019 observation contract.
- Raw adapter provenance remains available alongside structured resource data.
- No record-level numeric projection or trace-schema migration was introduced.
- No hidden HSR value or release-game resource/ordering semantic was invented.
- ARCH-017 Golden fixture and both regression manifests remain unchanged.
- Legacy regression remains 20/20, trace evidence 2/2, runtime action-session Golden regression 1/1.
- Production LIFO compatibility remains unchanged.
- No AV/speed/advance/delay/immediate-action/extra-turn observation was introduced.
- Historical Tingyun artifacts were preserved rather than rewritten to match the new engine.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-020 acceptance.

The archived Tingyun 002P/002Q reports are no longer valid descriptions of the current engine because their source pins predate trigger-visible resource events. This does not establish any new release-game Tingyun effect-order or duration semantic; those game semantics remain unresolved and must not be inferred from the ARCH-020 engine counterexample.

AV/speed/advance/delay/immediate-action/extra-turn state changes still lack equivalent runtime observation events.

## Suggested next milestone

`HSR-RUNTIME-ARCH-021 — Reviewed Static Resource Observation Golden Fixture`

ARCH-021 should add one independently reviewed, manually constructed static expected runtime-trace artifact for a simple production action containing a clamped `GainEnergy` effect. The Golden expectation should lock the exact `ACTION_START -> ENERGY_CHANGED -> ACTION_END` record order and the structured payload distinction between requested and applied delta. It should validate through accepted ARCH-016 without adding a new regression-manifest case yet. No simulator semantics, adapter mapping, trace schema, AV/timeline observation, or automatic fixture generation should be added in ARCH-021.
