# HSR-RUNTIME-ARCH-024 — Skill-Point Static Golden Regression Promotion

## Current confirmed state

- HSR-RUNTIME-ARCH-023 — PASS and merged to `main` at `f22dcd62dc3e5dff74059e63b8915344aeac40d1`.
- Complete pytest: `1161 / 1161 passed`.
- Legacy locked regression: `20 / 20 passed`.
- Trace evidence: `2 / 2 passed`.
- Runtime action-session Golden regression: `2 / 2 passed`.
- ARCH-023 fixture: `hsr_axis_sim/data/runtime_golden_fixtures/arch_023_reviewed_clamped_skill_point_expected.json`, 2744 bytes, SHA-256 `fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9`.
- Current blocker: none.

## Objective

Promote the accepted ARCH-023 static clamped-Skill-Point fixture into the standalone runtime action-session regression lane as the third reviewed case using one new narrow versioned setup kind, without broadening the manifest into a generic effect DSL.

## Required implementation

1. Keep the existing standalone runtime regression package and command.
2. Evolve the locked runtime regression manifest to version `1.2`.
3. Preserve exact historical version contracts:
   - v1.0 case objects have the original six fields and no `setup`;
   - v1.1 case objects require `setup` and accept only `EMPTY` or `ENERGY_GAIN`;
   - v1.1 must reject `SKILL_POINT_GAIN`;
   - v1.2 case objects require `setup` and accept `EMPTY`, `ENERGY_GAIN`, or new `SKILL_POINT_GAIN`.
4. `EMPTY` and `ENERGY_GAIN` validation/runner behavior must remain unchanged from ARCH-022.
5. Add one frozen `RuntimeActionSessionRegressionSkillPointGainSetup` with exact fields:
   - `initial_skill_points`;
   - `max_skill_points`;
   - `action_index`;
   - `amount`.
6. `SKILL_POINT_GAIN` manifest setup has exact fields `kind` plus those four fields.
7. Validation:
   - `initial_skill_points`, `max_skill_points`, and `amount` must be exact integers with bool rejected, matching the production SP resource contract;
   - `action_index` must be an exact nonnegative integer, bool rejected, and address a declared action;
   - do not invent extra sign/range rules beyond existing `BattleState` / `GainSkillPoint` behavior.
8. Runner construction for `SKILL_POINT_GAIN`:
   - construct `BattleState([], skill_points=initial_skill_points, max_skill_points=max_skill_points)`;
   - inject exactly one `GainSkillPoint(amount=amount)` on the selected action;
   - all other actions remain effect-free.
9. Do not add generic effect names/lists, reflection/import paths, free-form kwargs, target DSL, character/skill identifiers, scripts, or expression evaluation.
10. Locked v1.2 manifest must contain exactly three cases in declared order:
   1. ARCH-017 `EMPTY`, unchanged reviewed identity;
   2. ARCH-021 `ENERGY_GAIN`, unchanged reviewed identity/setup;
   3. ARCH-023 `SKILL_POINT_GAIN` with:
      - fixture ID `arch-023-reviewed-static-clamped-skill-point`;
      - expected path `hsr_axis_sim/data/runtime_golden_fixtures/arch_023_reviewed_clamped_skill_point_expected.json`;
      - expected SHA `fc359b367c2922ed39e059f89ad16845ba215508292cfa43ca2ab6031c4c9ba9`;
      - stream `arch-023-reviewed-resource`;
      - actor `sp-actor`;
      - one action `reviewed-clamped-skill-point`, `ends_turn=false`;
      - initial SP 4, max SP 5, action index 0, amount 3.
11. Standalone runtime regression command must report PASS `3/3`, with record counts 4, 3, 3 respectively.
12. Preserve all three reviewed static fixture files byte-for-byte.
13. Keep legacy `regression_manifest.json` unchanged at 20/20.
14. Keep trace schema v1, adapter/resource emission, simulator formulas, AV/timeline, and LIFO behavior unchanged.
15. Update ARCH-023 stage-boundary test only to reflect explicit standalone runtime promotion; it must still forbid legacy-manifest promotion.
16. Update `hsr_axis_sim/LUMEN_RESULT.md` with real CI evidence before merge.

## Acceptance criteria

- Manifest latest version is 1.2 with explicit v1.0/v1.1 compatibility.
- v1.1 cannot silently accept v1.2 `SKILL_POINT_GAIN`.
- Locked standalone lane passes exactly 3/3 in declared order.
- ARCH-017/021 behavior and fixture identity remain unchanged.
- ARCH-023 fixture identity remains unchanged.
- New setup vocabulary is narrow and non-generic.
- Full pytest, legacy 20/20, trace evidence 2/2, runtime regression 3/3 all pass.

## Required tests

- v1.0 compatibility unchanged;
- v1.1 EMPTY and ENERGY_GAIN still accepted;
- v1.1 rejects SKILL_POINT_GAIN;
- v1.2 requires setup and accepts all three allowed kinds;
- SKILL_POINT_GAIN exact fields only;
- SP setup bool/non-int rejection;
- action index exact/range rejection;
- locked manifest exact three-case order;
- locked lane 3/3 with record counts 4/3/3;
- controlled amount 3 -> 2 mismatch surfaces record 1 requested delta;
- all three fixture byte/SHA identities exact;
- no generic effect DSL in manifest/runner source;
- legacy 20/20, trace 2/2, LIFO unchanged.

## Protected areas / exclusions

Do not change:
- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- runtime trace schema/load/export/comparator/divergence implementations;
- Golden validator implementation;
- all three static expected fixture bytes;
- `hsr_axis_sim/data/regression_manifest.json`;
- AV/timeline/extra-turn behavior;
- character/research/evidence artifacts;
- FIFO/LIFO semantics.

No consume-SP case, no generic effect DSL, no automatic fixture generation, and no video automation in ARCH-024.

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

Update `hsr_axis_sim/LUMEN_RESULT.md` with implementation summary, files/tests, exact validation results, warnings/errors, unresolved issues, exclusions confirmation, and suggested next milestone.
