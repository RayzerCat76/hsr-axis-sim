# HSR-RUNTIME-ARCH-033 — Advance Static Golden Regression Promotion

## Current confirmed state

- HSR-RUNTIME-ARCH-032 — PASS — proceed.
- Accepted main merge commit before this task: `d4d5cc0dae12b3803e88a7d657a6501d24269680`.
- Last confirmed validation:
  - `1348 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `5/5`.
- Accepted ARCH-032 static fixture:
  - path `hsr_axis_sim/data/runtime_golden_fixtures/arch_032_reviewed_action_advance_expected.json`;
  - 2818 bytes;
  - SHA-256 `ab73c224d06690b379d398a5bc2c4b38a1ed654dfd86866d564417432c29d3ce`;
  - one non-clamped self advance from AV 80 to 30 at speed 100, percent 0.5.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Promote the accepted ARCH-032 static Advance fixture into the standalone runtime action-session regression lane as the sixth reviewed case through one explicit strict manifest v1.5 schema evolution.

## Required implementation

Preserve historical grammars exactly:

- v1.0: no `setup`;
- v1.1: `EMPTY | ENERGY_GAIN`;
- v1.2: `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN`;
- v1.3: `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN | ENERGY_CONSUME`;
- v1.4: adds only `SKILL_POINT_CONSUME`.

Add v1.5 with only one new setup kind:

- `ACTION_ADVANCE`.

A v1.4 manifest using `ACTION_ADVANCE` must be rejected explicitly as requiring v1.5.

### ACTION_ADVANCE setup

Add a separate frozen typed setup with exact fields:

- `kind="ACTION_ADVANCE"`;
- `target_id`;
- `target_name`;
- `team`;
- `base_speed`;
- `initial_av`;
- `action_index`;
- `percent`.

Validation:

- string identifiers/names/team are non-empty;
- `base_speed`, `initial_av`, and `percent` are finite int/float values with bool rejected;
- `base_speed > 0` because existing `Unit` requires positive speed;
- `action_index` is an exact nonnegative in-range integer; bool rejected;
- do not add a positivity restriction to `percent`;
- do not add release-game/hidden-value assumptions.

Do not merge Advance with resource setups or a generic effect/mode DSL.

### Runner

For `ACTION_ADVANCE` only:

- construct one production `Unit` with the setup target identity/team/base speed and `current_av=initial_av`;
- construct `BattleState([unit])`;
- inject exactly one production `AdvanceAction(target_ids=[target_id], percent=percent)` on `action_index`;
- all other actions remain effect-free.

Existing setup paths must remain behaviorally unchanged.

### Locked manifest

Upgrade `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` to version `1.5` and append exactly one sixth case after ARCH-027:

- id `arch-032-reviewed-static-action-advance`;
- expected path `hsr_axis_sim/data/runtime_golden_fixtures/arch_032_reviewed_action_advance_expected.json`;
- expected SHA-256 `ab73c224d06690b379d398a5bc2c4b38a1ed654dfd86866d564417432c29d3ce`;
- stream `arch-032-reviewed-axis`;
- actor `advance-actor`;
- one action `reviewed-action-advance`, `ends_turn=false`;
- setup:
  - target id `advance-actor`;
  - target name `Advance Actor`;
  - team `ally`;
  - base speed `100`;
  - initial AV `80`;
  - action index `0`;
  - percent `0.5`.

## Acceptance criteria

- Supported versions exactly `1.0,1.1,1.2,1.3,1.4,1.5`.
- v1.0-v1.4 historical grammars remain strict.
- v1.4 rejects `ACTION_ADVANCE` as requiring v1.5.
- v1.5 accepts exactly six closed setup kinds.
- New Advance setup is frozen and exact-field validated.
- Locked case order exactly ARCH-017 -> ARCH-021 -> ARCH-023 -> ARCH-025 -> ARCH-027 -> ARCH-032.
- Standalone runtime lane passes exactly `6/6` with record counts `4,3,3,3,3,3`.
- Controlled sixth-case mutation `percent=0.5 -> 0.4` reports record index 1, first divergence `/event/payload/action_advance/after_av`.
- All six reviewed fixture byte identities remain unchanged.
- Legacy regression `20/20`; trace evidence `2/2`; LIFO unchanged.

## Required tests

Cover:

- exact supported version tuple;
- v1.0-v1.4 historical grammar preservation;
- explicit v1.4 `ACTION_ADVANCE` rejection;
- v1.5 six-kind closed grammar;
- frozen Advance setup;
- missing/unknown fields;
- finite numeric/bool rejection and positive base speed;
- exact action-index validation;
- no positivity restriction on percent;
- locked six-case order;
- runtime `6/6` and record counts;
- controlled Advance mismatch;
- all reviewed fixture identities;
- closed/non-generic harness source;
- legacy/trace/LIFO preservation.

Historical milestone tests that intentionally assert the current lane size/latest version may be updated only at that explicit stage boundary. Historical grammar tests should use their explicit version constants rather than silently inheriting v1.5.

## Must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`;
- runtime adapters or trace contracts;
- loader/exporter/comparator/divergence/Golden validator;
- legacy regression manifest;
- reviewed static fixture bytes;
- Delay/ChangeSpeed/ImmediateAction/GrantExtraTurn behavior;
- AV/timeline/extra-turn mechanics.

## Explicit exclusions

- generic action-axis effect DSL;
- clamped Advance regression case;
- Delay/Speed/ImmediateAction/ExtraTurn observation;
- automatic fixture generation;
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
