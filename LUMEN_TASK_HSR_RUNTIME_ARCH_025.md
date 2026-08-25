# HSR-RUNTIME-ARCH-025 — Reviewed Static Energy Consume Observation Golden Fixture

## Current confirmed state

- HSR-RUNTIME-ARCH-024 — PASS — proceed.
- Accepted main merge commit before this task: `63fae900717af9a5d4d3c423eaba02b6d8718805`.
- Last confirmed final-head validation:
  - `1195 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `3/3`.
- Accepted reviewed runtime fixtures already cover:
  - effect-free multi-action capture (ARCH-017);
  - clamped `GainEnergy` (ARCH-021, promoted by ARCH-022);
  - clamped `GainSkillPoint` (ARCH-023, promoted by ARCH-024).

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Add one independently reviewed static schema-v1 Golden expectation for a successful production `ConsumeEnergy` action, validate it end-to-end through the accepted ARCH-016 action-session validation stack, and lock signed Energy-consumption observation semantics without changing simulator/runtime implementation or promoting the new fixture into a regression manifest yet.

## Required implementation

Add one static compact canonical UTF-8 JSON expected artifact under `hsr_axis_sim/data/runtime_golden_fixtures/` for this exact contract-only scenario:

- actor ID: `consume-actor`;
- target Unit ID/name: `consume-target`;
- target team: `ally`;
- target base speed: `100`;
- target initial Energy: `80`;
- target max Energy: `100`;
- action ID/name: `reviewed-energy-consume`;
- action has exactly one `ConsumeEnergy(target_ids=["consume-target"], amount=30)` effect;
- `ends_turn=False`.

The reviewed static trace must contain exactly three records in order:

1. `ACTION_START`;
2. `ENERGY_CHANGED`;
3. `ACTION_END`.

The `ENERGY_CHANGED` record must lock the exact resource observation:

- `resource_kind="ENERGY"`;
- `scope="UNIT"`;
- `before=80`;
- `after=50`;
- `requested_delta=-30`;
- `applied_delta=-30`;
- `cap=100`;
- `unit_id="consume-target"`;
- runtime `target_id="consume-target"`.

Expected artifact requirements:

- schema name `hsr_runtime_trace`;
- schema version `1.0`;
- contiguous sequence policy;
- compact canonical UTF-8 JSON;
- no trailing newline;
- static/manual-reviewed metadata;
- exact bytes are authoritative and must not be generated from simulator/runtime code during tests.

## Acceptance criteria

- Static fixture has a fixed reviewed byte length and SHA-256 asserted by tests.
- Strict runtime loader accepts the fixture with compact-only canonical policy and required digest match.
- Every schema-v1 record has `numeric_values == {}`.
- Accepted ARCH-016 production execution of the exact `ConsumeEnergy(30)` scenario matches the static expected artifact.
- Final target Energy is exactly `50`.
- Pending-event order is exactly `action_started`, `energy_changed`, `action_finished`.
- Final capture cursor is exactly `(3, 3)`.
- A deliberate actual-only `ConsumeEnergy.amount=30 -> 25` change must produce a normal Golden mismatch using the same expected artifact.
- The mismatch must occur on the resource record and tests must prove actual signed values are `requested_delta=-25`, `applied_delta=-25`, with final Energy `55`, while expected remains `-30`, `-30`, Energy `50`.
- The new fixture must remain absent from both legacy and standalone runtime regression manifests in ARCH-025.
- Existing ARCH-017, ARCH-021, and ARCH-023 fixture byte identities remain unchanged.
- Standalone runtime action-session regression remains exactly `3/3`.
- Legacy regression remains `20/20` and trace evidence remains `2/2`.
- Production LIFO compatibility remains `third, second, first`.

## Required tests

Add focused tests covering:

- exact static bytes/digest/no trailing newline;
- strict compact loader acceptance;
- exact trace identity, record order, actor/action/target provenance;
- exact structured `resource_change` and defensive `legacy_data` signed consume payloads;
- ARCH-016 production PASS;
- final state, pending-event order, and cursor;
- controlled `30 -> 25` mismatch and resource-record divergence;
- expected vs actual signed resource values;
- fixture remains outside both regression manifests;
- AST/source guard preventing simulator/adapter/export/canonical serialization helpers from becoming an expected-artifact generation path;
- prior fixture identities unchanged;
- runtime regression remains `3/3`;
- legacy regression `20/20`, trace evidence `2/2`, LIFO unchanged.

## Files / areas that must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`;
- runtime adapter mappings;
- runtime trace contract/schema;
- loader/exporter/comparator/divergence/Golden-validator implementation;
- `hsr_axis_sim/data/regression_manifest.json`;
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`;
- existing reviewed static fixture bytes;
- AV/timeline/extra-turn mechanics.

## Explicit exclusions

Out of scope:

- insufficient-Energy/failure behavior;
- `ConsumeSkillPoint`;
- regression promotion/schema extension;
- generic effect DSL;
- simulator/resource formula changes;
- AV, speed, advance, delay, immediate-action observation;
- character database/release-game values;
- damage expansion;
- video parsing/scraping/automation;
- FIFO/LIFO behavior changes.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report format

Update `hsr_axis_sim/LUMEN_RESULT.md` with:

- task ID;
- implementation summary;
- files added/modified;
- tests added;
- exact commands executed;
- exact pass/fail results;
- warnings/errors;
- unresolved issues;
- confirmation exclusions were respected;
- suggested next milestone.
