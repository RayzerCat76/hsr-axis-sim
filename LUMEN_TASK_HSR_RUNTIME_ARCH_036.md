# HSR-RUNTIME-ARCH-036 — Delay Static Golden Regression Promotion

## Current confirmed state

- HSR-RUNTIME-ARCH-035 — PASS — proceed.
- Accepted main merge commit before this task: `ceaa3fd02ee18d08ac983b733f6acbc85d8d373c`.
- Last confirmed validation:
  - `1441 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `6/6`.
- Accepted ARCH-035 static fixture:
  - path `hsr_axis_sim/data/runtime_golden_fixtures/arch_035_reviewed_action_delay_expected.json`;
  - 2728 bytes;
  - SHA-256 `9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d`;
  - one positive self delay from AV 30 to 55 at speed 100, percent 0.25.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Promote the accepted ARCH-035 static Delay fixture into the standalone runtime action-session regression lane as the seventh reviewed case through one explicit strict manifest v1.6 schema evolution.

## Required implementation

Preserve historical grammars exactly:

- v1.0: no `setup`;
- v1.1: `EMPTY | ENERGY_GAIN`;
- v1.2: adds only `SKILL_POINT_GAIN`;
- v1.3: adds only `ENERGY_CONSUME`;
- v1.4: adds only `SKILL_POINT_CONSUME`;
- v1.5: adds only `ACTION_ADVANCE`.

Add v1.6 with only one new setup kind:

- `ACTION_DELAY`.

A v1.5 manifest using `ACTION_DELAY` must be rejected explicitly as requiring v1.6. `ACTION_ADVANCE` must remain valid in v1.5 and v1.6.

### ACTION_DELAY setup

Add a separate frozen typed setup with exact fields:

- `kind="ACTION_DELAY"`;
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
- do not add an AV floor or clamp rule;
- do not add release-game/hidden-value assumptions.

Do not merge Delay with Advance/resource setup into a generic effect or action-axis DSL.

### Runner

For `ACTION_DELAY` only:

- construct one production `Unit` with setup target identity/team/base speed and `current_av=initial_av`;
- construct `BattleState([unit])`;
- inject exactly one production `DelayAction(target_ids=[target_id], percent=percent)` on `action_index`;
- all other actions remain effect-free.

Existing setup paths must remain behaviorally unchanged.

### Locked manifest

Upgrade `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` to version `1.6` and append exactly one seventh case after ARCH-032:

- id `arch-035-reviewed-static-action-delay`;
- expected path `hsr_axis_sim/data/runtime_golden_fixtures/arch_035_reviewed_action_delay_expected.json`;
- expected SHA-256 `9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d`;
- stream `arch-035-reviewed-axis`;
- actor `delay-actor`;
- one action `reviewed-action-delay`, `ends_turn=false`;
- setup:
  - target id `delay-actor`;
  - target name `Delay Actor`;
  - team `ally`;
  - base speed `100`;
  - initial AV `30`;
  - action index `0`;
  - percent `0.25`.

## Acceptance criteria

- Supported versions exactly `1.0,1.1,1.2,1.3,1.4,1.5,1.6`.
- v1.0-v1.5 historical grammars remain strict.
- v1.5 rejects `ACTION_DELAY` as requiring v1.6.
- v1.5 continues to accept `ACTION_ADVANCE`.
- v1.6 accepts exactly seven closed setup kinds.
- New Delay setup is frozen and exact-field validated.
- Signed finite Delay percent and finite negative initial AV remain representable; no new floor/clamp semantics.
- Locked case order exactly ARCH-017 -> ARCH-021 -> ARCH-023 -> ARCH-025 -> ARCH-027 -> ARCH-032 -> ARCH-035.
- Standalone runtime lane passes exactly `7/7` with record counts `4,3,3,3,3,3,3`.
- Controlled seventh-case mutation `percent=0.25 -> 0.20` reports record index 1, first divergence `/event/payload/action_delay/after_av`.
- All seven reviewed fixture byte identities remain unchanged.
- Legacy regression `20/20`; trace evidence `2/2`; LIFO unchanged.

## Required tests

Cover:

1. exact supported version tuple through v1.6;
2. explicit v1.5 `ACTION_DELAY` rejection;
3. v1.5 `ACTION_ADVANCE` preservation;
4. v1.6 seven-kind closed grammar;
5. frozen Delay setup;
6. missing/unknown fields and unknown generic kind rejection;
7. finite numeric/bool rejection and positive base speed;
8. exact action-index validation;
9. no positivity restriction on percent and no new initial-AV range restriction;
10. locked seven-case order and exact seventh setup;
11. runtime `7/7` and record counts;
12. controlled Delay mismatch;
13. all reviewed fixture identities;
14. closed/non-generic harness source;
15. legacy/trace/LIFO preservation.

Historical milestone tests that intentionally assert the latest lane size, latest version, or unpromoted-fixture absence may be updated only at this explicit stage boundary. Historical grammar tests must use their explicit version constants so v1.0-v1.5 meanings do not silently change.

## Must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`;
- runtime adapters or runtime trace contracts;
- loader/exporter/comparator/divergence/Golden validator;
- legacy regression manifest;
- reviewed static fixture bytes;
- Advance/Delay production semantics;
- ChangeSpeed/ImmediateAction/GrantExtraTurn behavior;
- AV/timeline/extra-turn mechanics.

## Explicit exclusions

- generic action-axis effect DSL;
- a second Delay fixture or negative-Delay Golden case;
- ChangeSpeed observation;
- ImmediateAction observation;
- GrantExtraTurn observation;
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
