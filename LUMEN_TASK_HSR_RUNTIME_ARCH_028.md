# HSR-RUNTIME-ARCH-028 — Skill-Point Consume Static Golden Regression Promotion

## Current confirmed state

- HSR-RUNTIME-ARCH-027 — PASS — proceed.
- Accepted main merge commit before this task: `494fc70be5b3429e77196c8d00de46e077209b8c`.
- Last confirmed validation:
  - `1269 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `4/4`.
- Accepted ARCH-027 static fixture:
  - 2796 bytes;
  - SHA-256 `d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec`;
  - successful `ConsumeSkillPoint(amount=2)` from team SP `4` to `2`;
  - signed `requested_delta=-2`, `applied_delta=-2`.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Promote the accepted ARCH-027 static successful Skill-Point-consume fixture into the standalone runtime action-session regression lane as the fifth reviewed case through one explicit strict manifest v1.4 schema evolution.

## Required implementation

Preserve historical grammars exactly:

- v1.0: no `setup`;
- v1.1: `EMPTY | ENERGY_GAIN`;
- v1.2: `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN`;
- v1.3: `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN | ENERGY_CONSUME`.

Add v1.4 with only one new setup kind:

- `SKILL_POINT_CONSUME`.

A v1.3 manifest using `SKILL_POINT_CONSUME` must be rejected explicitly as requiring v1.4.

### SKILL_POINT_CONSUME setup

Add a separate frozen typed setup with exact fields:

- `kind="SKILL_POINT_CONSUME"`;
- `initial_skill_points`;
- `max_skill_points`;
- `action_index`;
- `amount`.

Validation mirrors the accepted SP gain field rules:

- SP resource values are exact integers; bool rejected;
- action index is an exact nonnegative in-range integer; bool rejected;
- no additional sign/range/release-game assumptions.

Do not merge SP gain and consume into a generic mode/effect setup.

### Runner

For `SKILL_POINT_CONSUME` only:

- construct `BattleState([], skill_points=initial_skill_points, max_skill_points=max_skill_points)`;
- inject exactly one production `ConsumeSkillPoint(amount=amount)` on `action_index`;
- all other actions remain effect-free.

Existing setup paths must remain behaviorally unchanged.

### Locked manifest

Upgrade `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` to version `1.4` and append exactly one fifth case after ARCH-025:

- id `arch-027-reviewed-static-skill-point-consume`;
- expected path `hsr_axis_sim/data/runtime_golden_fixtures/arch_027_reviewed_skill_point_consume_expected.json`;
- expected SHA-256 `d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec`;
- stream `arch-027-reviewed-resource`;
- actor `sp-consume-actor`;
- one action `reviewed-skill-point-consume`, `ends_turn=false`;
- setup: initial SP 4, max SP 5, action index 0, amount 2.

## Acceptance criteria

- Supported versions exactly `1.0,1.1,1.2,1.3,1.4`.
- v1.0-v1.3 historical grammars remain strict.
- v1.3 rejects `SKILL_POINT_CONSUME` as requiring v1.4.
- v1.4 accepts exactly five closed setup kinds.
- New SP consume setup is frozen and exact-field validated.
- Locked case order exactly ARCH-017 -> ARCH-021 -> ARCH-023 -> ARCH-025 -> ARCH-027.
- Standalone runtime lane passes exactly `5/5` with record counts `4,3,3,3,3`.
- Controlled fifth-case mutation `amount=2 -> 1` reports record index 1, first divergence `/event/payload/legacy_data/after`.
- All five reviewed fixture byte identities remain unchanged.
- Legacy regression `20/20`; trace evidence `2/2`; LIFO unchanged.

## Required tests

Cover version compatibility, explicit v1.3 rejection, v1.4 five-kind acceptance, frozen typed setup, exact/missing/unknown fields, exact integer/action-index validation, locked five-case order, runtime 5/5, controlled consume mismatch, all fixture identities, closed/non-generic harness source, legacy/trace/LIFO preservation.

## Must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`;
- runtime adapters or trace schema;
- loader/exporter/comparator/divergence/Golden validator;
- legacy regression manifest;
- reviewed static fixture bytes;
- AV/timeline/extra-turn mechanics.

## Explicit exclusions

- insufficient-SP failure behavior;
- generic effect DSL;
- automatic fixture generation;
- AV/speed/advance/delay/immediate-action observation;
- character/release-game data;
- video automation;
- FIFO/LIFO changes.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, implementation summary, files, tests, exact commands/results, warnings/errors, unresolved issues, exclusions confirmation, and suggested next milestone.
