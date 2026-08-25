# HSR-RUNTIME-ARCH-022 — Clamped Resource Static Golden Regression Promotion

## Current confirmed state

- HSR-RUNTIME-ARCH-021 — PASS and merged to `main` at `7b4d11260a4ed616a34b55fb88e78d398e78d21e`.
- Complete pytest: `1096 / 1096 passed`.
- Legacy locked regression: `20 / 20 passed`.
- Trace evidence: `2 / 2 passed`.
- Runtime action-session Golden regression: `1 / 1 passed`.
- ARCH-021 static fixture: `hsr_axis_sim/data/runtime_golden_fixtures/arch_021_reviewed_clamped_energy_expected.json`, 2759 bytes, SHA-256 `4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605`.
- Current blocker: none.

## Objective

Promote the accepted ARCH-021 static clamped-Energy Golden fixture into the standalone runtime action-session regression lane as the second reviewed case, using the smallest explicit manifest/runner extension required to reconstruct exactly that production action.

## Required implementation

1. Keep the existing standalone runtime regression package and lane. Do not create a second competing runner.
2. Evolve the locked runtime regression manifest from version `1.0` to version `1.1`.
3. Preserve exact parsing compatibility for legacy manifest version `1.0`:
   - v1.0 root/case/action exact fields remain unchanged;
   - v1.0 must reject the new `setup` field rather than silently accepting it.
4. Version `1.1` case objects contain the existing six case fields plus one required `setup` field.
5. `setup` is a strict discriminated union with only two accepted kinds:
   - `EMPTY`: exact object `{ "kind": "EMPTY" }`; reproduces ARCH-017 behavior;
   - `ENERGY_GAIN`: exact fields `kind`, `target_id`, `target_name`, `team`, `base_speed`, `initial_energy`, `max_energy`, `action_index`, `amount`.
6. `ENERGY_GAIN` validation:
   - string fields are non-empty strings;
   - `base_speed`, `initial_energy`, `max_energy`, and `amount` are finite numbers with bool rejected;
   - `base_speed > 0` because `Unit` requires positive speed;
   - `action_index` is an exact nonnegative integer, bool rejected, and must address one declared action;
   - do not add extra sign/range assumptions for Energy or amount beyond existing production constructors/effects.
7. The runner must construct only the explicitly described narrow setup:
   - `EMPTY` -> `BattleState([])` and unchanged no-effect actions;
   - `ENERGY_GAIN` -> one `Unit` with exactly the setup values; the selected action receives exactly one `GainEnergy(target_ids=[target_id], amount=amount)` effect; all other actions remain effect-free.
8. Do not add generic effect names, arbitrary effect lists, reflection/import paths, free-form kwargs, character IDs, skill IDs, or script execution to the manifest.
9. Update the locked v1.1 manifest to contain exactly two cases in declared order:
   1. `arch-017-reviewed-static-action-session` with `setup.kind=EMPTY` and otherwise unchanged reviewed identity;
   2. `arch-021-reviewed-static-clamped-energy` with the exact ARCH-021 inputs:
      - expected fixture SHA `4fe2c8b3c9c22821a49ff380c9635828e36f3c4a3bbbc13d2cc077dd4d97e605`;
      - stream `arch-021-reviewed-resource`;
      - actor `resource-actor`;
      - one action `reviewed-clamped-energy`, `ends_turn=false`;
      - target `resource-target`, name `resource-target`, team `ally`, base speed 100, initial Energy 90, max Energy 100;
      - `action_index=0`, `amount=25`.
10. The standalone runtime regression command must report PASS `2/2` with the ARCH-017 case still producing 4 records and the ARCH-021 case producing 3 records.
11. Preserve both reviewed static fixture files byte-for-byte.
12. Keep the legacy `regression_manifest.json` unchanged at 20/20; do not add either runtime fixture to it.
13. Keep trace schema v1, adapter/resource emission, AV/timeline, Golden validation implementation, production resource formulas, and LIFO behavior unchanged.
14. Update `hsr_axis_sim/LUMEN_RESULT.md` with real CI evidence before merge.

## Acceptance criteria

- Locked runtime regression lane passes exactly 2/2 in declared order.
- ARCH-017 expected fixture identity and behavior remain unchanged.
- ARCH-021 expected fixture identity and clamped requested/applied observation remain unchanged.
- Manifest v1.0 remains strictly parseable with its old exact schema.
- Manifest v1.1 requires strict typed setup and rejects malformed/unknown setup data.
- No generic effect DSL or arbitrary simulator construction path is introduced.
- Full pytest, legacy 20/20, trace evidence 2/2, and runtime regression 2/2 all pass.

## Required tests

- v1.0 compatibility: accepted original-style case with no setup;
- v1.0 rejects setup;
- v1.1 requires setup;
- v1.1 EMPTY exact fields only;
- v1.1 ENERGY_GAIN exact field contract;
- bool/NaN/+Infinity/-Infinity rejection for numeric setup fields;
- nonpositive base speed rejection;
- invalid/non-integer/out-of-range action index rejection;
- unknown setup kind/field rejection;
- locked manifest loads exactly two cases in declared order;
- locked runtime lane passes exactly 2/2;
- result details prove ARCH-017 record_count=4 and ARCH-021 record_count=3;
- ARCH-021 case reaches production `GainEnergy` and its exact reviewed fixture without runtime expected generation;
- both fixture byte size/SHA identities remain exact;
- legacy regression remains 20/20 and trace evidence 2/2;
- production LIFO remains `third, second, first`.

## Protected areas / exclusions

Do not change:
- `hsr_axis_sim/sim/effects.py`;
- `hsr_axis_sim/runtime_adapters/**`;
- runtime trace schema/load/export/comparator/divergence implementations;
- ARCH-017 or ARCH-021 static expected fixture bytes;
- `hsr_axis_sim/data/regression_manifest.json`;
- AV/speed/advance/delay/immediate-action/extra-turn behavior;
- character/research/evidence artifacts;
- FIFO/LIFO semantics.

No SP regression case, no arbitrary effects DSL, no automatic fixture generation, and no video automation in ARCH-022.

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
