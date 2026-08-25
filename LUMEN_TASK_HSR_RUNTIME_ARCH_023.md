# HSR-RUNTIME-ARCH-023 — Reviewed Static Skill-Point Observation Golden Fixture

## Current confirmed state

- HSR-RUNTIME-ARCH-022 — PASS and merged to `main` at `a94b520b3908f62bb54f97e2cc3100879784a2f0`.
- Complete pytest: `1153 / 1153 passed`.
- Legacy locked regression: `20 / 20 passed`.
- Trace evidence: `2 / 2 passed`.
- Runtime action-session Golden regression: `2 / 2 passed`.
- Current blocker: none.

## Objective

Add one independently reviewed, manually constructed static schema-v1 Golden expectation for the production clamped `GainSkillPoint` observation path, validating it through accepted ARCH-016 without modifying simulator semantics or promoting it into either regression manifest yet.

## Reviewed fixture contract

- fixture ID: `arch-023-reviewed-static-clamped-skill-point`;
- stream ID: `arch-023-reviewed-resource`;
- trace ID: `arch-023-reviewed-static-expected`;
- actor ID: `sp-actor`;
- action ID/name: `reviewed-clamped-skill-point`;
- initial team skill points: `4`;
- max team skill points: `5`;
- effect: `GainSkillPoint(amount=3)`;
- action `ends_turn=False`;
- expected final skill points: `5`;
- expected event order: `ACTION_START -> SKILL_POINTS_CHANGED -> ACTION_END`;
- expected resource observation:
  - `resource_kind=SKILL_POINTS`;
  - `scope=TEAM`;
  - `before=4`;
  - `after=5`;
  - `requested_delta=3`;
  - `applied_delta=1`;
  - `cap=5`;
  - `unit_id=null`;
  - runtime `target_id=null`.

## Required implementation

1. Add one static compact canonical UTF-8 Runtime Trace artifact under `hsr_axis_sim/data/runtime_golden_fixtures/`.
2. The fixture must be manually specified and reviewed; tests must not generate expected bytes at runtime from the simulator, adapter, exporter, or canonical serializer.
3. Pin exact fixture byte length and SHA-256 in tests.
4. Strict-load the fixture using the accepted schema-v1 loader with `COMPACT_ONLY` and required digest match.
5. Prove exact three-record ordering and all record-level `numeric_values == {}`.
6. Prove the SP resource record has TEAM scope, no unit ID, no runtime target ID, and exact `resource_change` plus defensive `legacy_data` payload.
7. Execute the real production action through accepted ARCH-016:
   - `BattleState([], skill_points=4, max_skill_points=5)`;
   - one `Action` with `GainSkillPoint(amount=3)`;
   - `ends_turn=False`.
8. Require Golden PASS against the static expected bytes.
9. Add a deliberate actual-only change `amount=2` while keeping the same expected artifact. Because both requests still clamp from 4 to 5, `after=5` and `applied_delta=1` must remain equal while `requested_delta` changes from 3 to 2. Require deterministic first divergence at resource record index `1` and the accepted first field path for `requested_delta`.
10. Keep the new fixture absent from both:
    - `hsr_axis_sim/data/regression_manifest.json`;
    - `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`.
11. Preserve ARCH-017 and ARCH-021 static fixture bytes exactly.
12. Preserve standalone runtime regression at 2/2, legacy regression at 20/20, and trace evidence at 2/2.
13. Preserve production LIFO compatibility behavior.
14. Update `hsr_axis_sim/LUMEN_RESULT.md` with real CI evidence before merge.

## Acceptance criteria

- Static expected artifact has one exact reviewed compact byte identity.
- Strict loader accepts it under schema v1.0.
- Production ARCH-016 action validation matches it exactly at the comparison layer.
- Requested versus applied SP clamp semantics are locked independently of final SP only.
- TEAM scope and absence of unit/target identity are explicit.
- Deliberate requested amount change surfaces a deterministic first divergence while final/applied SP stay unchanged.
- No production/runtime schema/adapter/regression-harness implementation changes.
- Full pytest, legacy 20/20, trace evidence 2/2, and runtime regression 2/2 all pass.

## Required tests

- exact static bytes, SHA-256, no trailing newline;
- strict compact loader/digest match;
- trace ID, schema name/version, sequence policy, record count and sequences;
- `ACTION_START -> SKILL_POINTS_CHANGED -> ACTION_END`;
- exact actor/action provenance;
- SP record target ID is null;
- exact `resource_change` and `legacy_data` payloads;
- every record `numeric_values == {}`;
- production ARCH-016 PASS;
- final team SP is 5;
- pending-event order and final capture cursor are exact;
- amount 3 -> 2 produces Golden mismatch at record 1 requested delta;
- mismatch preserves `after=5` and `applied_delta=1`;
- fixture absent from both regression manifests;
- test source contains no runtime expected-artifact generation path;
- ARCH-017/021 fixture identities unchanged;
- standalone runtime regression remains 2/2;
- legacy regression remains 20/20 and trace evidence 2/2;
- LIFO remains `third, second, first`.

## Protected areas / exclusions

Do not change:
- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- runtime trace contracts/schema/load/export/comparator/divergence implementations;
- Golden validator implementation;
- either regression runner/manifest;
- ARCH-017 or ARCH-021 fixture bytes;
- AV/timeline/extra-turn behavior;
- character/research/evidence artifacts;
- FIFO/LIFO semantics.

No Energy fixture change, no SP regression promotion, no generic setup/effect DSL, no automatic fixture generation, and no video automation in ARCH-023.

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

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, implementation summary, files added/modified, tests, exact commands/results, warnings/errors, unresolved issues, confirmation that exclusions were respected, and suggested next milestone.
