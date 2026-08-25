# HSR-RUNTIME-ARCH-020 — Production Resource Change Event Emission and Legacy Adapter Binding

## Current confirmed state

- HSR-RUNTIME-ARCH-019 — PASS and merged to `main` at `ebb823fd473b551a93a5c3deafa586efa4c45e42`.
- Complete pytest: `1076 / 1076 passed`.
- Legacy locked regression: `20 / 20 passed`.
- Trace evidence: `2 / 2 passed`.
- Runtime action-session Golden regression: `1 / 1 passed`.
- Current blocker: none.

## Objective

Bind the accepted ARCH-019 energy/skill-point observation vocabulary to the existing production resource effects and legacy-event adapter without changing resource mutation formulas, trace schema v1, or AV/timeline semantics.

## Required implementation

1. Update only these production effects for resource observation:
   - `GainEnergy`;
   - `ConsumeEnergy`;
   - `GainSkillPoint`;
   - `ConsumeSkillPoint`.
2. After each successful resource mutation, emit exactly one normal production legacy event through `state.emit_event`:
   - `energy_changed` for each successfully mutated target unit;
   - `skill_points_changed` for each successful team SP mutation.
3. Legacy event data must include:
   - `actor_id` and `action_id` provenance;
   - exact ARCH-019 resource observation fields: `resource_kind`, `scope`, `before`, `after`, `requested_delta`, `applied_delta`, `cap`, `unit_id`.
4. Signed deltas:
   - gain effect `requested_delta = +amount`;
   - consume effect `requested_delta = -amount`;
   - `applied_delta = after - before` always.
   Negative legacy effect amounts are not newly forbidden or normalized in this milestone.
5. Existing clamp/insufficient-resource behavior remains authoritative:
   - gain still clamps exactly as before;
   - consume still checks insufficiency exactly as before;
   - failed consume emits no resource-change event and performs no resource mutation.
6. Emission is post-mutation and uses normal event dispatch/trigger semantics. If event dispatch or a triggered effect subsequently raises, no rollback is attempted; existing non-transactional production semantics remain authoritative.
7. Extend accepted legacy adapter mappings:
   - `energy_changed -> RuntimeEventType.ENERGY_CHANGED`;
   - `skill_points_changed -> RuntimeEventType.SKILL_POINTS_CHANGED`.
8. Normalize:
   - both resource events: `action_id`, `actor_id`;
   - energy additionally normalizes `target_id` from legacy `unit_id`;
   - SP has no target/unit runtime ID.
9. For the two resource mappings, add `payload["resource_change"]` equal to the exact validated `RuntimeResourceChangeObservation.to_payload()` result, while preserving existing `payload["adapter"]` and defensive `payload["legacy_data"]` provenance.
10. Malformed resource legacy event data must be rejected as `LegacyEventSchemaError`; do not repair it.
11. Update `LEGACY_EVENT_MAPPING_V1.json` and adapter documentation to the reviewed mapping contract. Historical ARCH-002 research/reference artifacts remain unchanged.
12. Prove ARCH-012 action capture observes resource events in order between action start/end and schema-v1 records still have empty `numeric_values`.

## Acceptance criteria

- Existing resource before/after behavior is unchanged apart from new observation events.
- Clamped gain records requested and applied deltas separately.
- Failed consume creates neither mutation nor resource event.
- Resource events are normal trigger-visible production events.
- Adapter produces bound ARCH-019 runtime event types with exact structured `resource_change` payload.
- Existing adapter payload provenance (`adapter`, `legacy_data`) remains present.
- No trace schema change or record-level numeric values.
- ARCH-017 static fixture remains byte-identical and existing runtime regression remains 1/1.
- Full validation suite passes.

## Required tests

- GainEnergy unclamped and clamped before/after/requested/applied/cap/unit/action provenance;
- ConsumeEnergy success and failure-no-event/no-mutation;
- GainSkillPoint unclamped and clamped;
- ConsumeSkillPoint success and failure-no-event/no-mutation;
- multi-target energy emits one ordered event per target;
- trigger can observe a resource event using existing trigger machinery;
- adapter exact resource mappings, normalized IDs, mapping status BOUND, structured resource payload and defensive legacy snapshot;
- malformed resource legacy data rejected;
- ARCH-012 single-action capture order: ACTION_START -> resource event(s) -> ACTION_END;
- captured schema-v1 record `numeric_values` remains empty;
- preservation: ARCH-017 fixture digest, legacy 20/20, runtime lane 1/1, production LIFO unchanged.

## Protected areas / exclusions

Do not change:
- resource formulas/clamp/insufficient checks beyond observation instrumentation;
- any AV/speed/advance/delay/immediate-action/extra-turn behavior;
- trace schema v1 or loader rules;
- Golden fixtures/manifests;
- legacy/runtime regression manifests;
- research/reference artifacts;
- unrelated simulator effects;
- FIFO/LIFO semantics.

No static resource Golden fixture or regression promotion in ARCH-020; that is separate later work.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Execution routing

- ChatGPT model: GPT-5.6 Sol
- Codex reasoning: High if used; Codex is optional.

## Final report

Update `hsr_axis_sim/LUMEN_RESULT.md` with implementation summary, files/tests, exact validation results, warnings/errors, unresolved issues, protected/exclusion confirmation, and suggested next milestone.
