# HSR-RUNTIME-ARCH-026 — Energy Consume Static Golden Regression Promotion

## Current confirmed state

- HSR-RUNTIME-ARCH-025 — PASS — proceed.
- Accepted main merge commit before this task: `2bf730b36cf5f54109f408bf15a3d8fda3f20cbf`.
- Last confirmed final-head validation:
  - `1203 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `3/3`.
- ARCH-025 reviewed static successful Energy-consume fixture:
  - 2750 bytes;
  - SHA-256 `7d61528687a5a2f499249e0f914f6f2f50975c7c153165eddd5e116f3ed19a75`;
  - production `ConsumeEnergy(30)` from Energy `80` to `50`;
  - signed `requested_delta=-30`, `applied_delta=-30`.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Promote the accepted ARCH-025 static successful Energy-consume fixture into the standalone runtime action-session regression lane as the fourth reviewed case through one explicit strict manifest v1.3 schema evolution.

## Required implementation

### Manifest versions

Preserve exact historical grammars:

- v1.0: original six case fields, no `setup`;
- v1.1: required setup, `EMPTY | ENERGY_GAIN` only;
- v1.2: required setup, `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN` only.

Add v1.3 with required setup vocabulary:

- `EMPTY`;
- `ENERGY_GAIN`;
- `SKILL_POINT_GAIN`;
- `ENERGY_CONSUME`.

A v1.2 manifest using `ENERGY_CONSUME` must be rejected explicitly rather than interpreted under v1.3 semantics.

### ENERGY_CONSUME setup

Add one frozen typed setup with exact fields:

- `kind="ENERGY_CONSUME"`;
- `target_id`;
- `target_name`;
- `team`;
- `base_speed`;
- `initial_energy`;
- `max_energy`;
- `action_index`;
- `amount`.

Validation must mirror the already accepted Energy-unit setup rules:

- string fields non-empty;
- numeric fields finite and boolean rejected;
- `base_speed > 0`;
- `action_index` exact nonnegative integer, boolean rejected, and must reference a declared action;
- no additional sign/range/game-rule assumptions.

Do not collapse gain and consume into a generic mode/effect model.

### Runner

For `ENERGY_CONSUME` only:

- construct exactly one Unit using the declared setup fields;
- inject exactly one production `ConsumeEnergy(target_ids=[target_id], amount=amount)` on the selected action;
- all other actions remain effect-free.

Do not alter existing `EMPTY`, `ENERGY_GAIN`, or `SKILL_POINT_GAIN` behavior.

### Locked manifest

Upgrade `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` to version `1.3` and append exactly one fourth case after the existing three:

- id: `arch-025-reviewed-static-energy-consume`;
- expected path: `hsr_axis_sim/data/runtime_golden_fixtures/arch_025_reviewed_energy_consume_expected.json`;
- expected SHA-256: `7d61528687a5a2f499249e0f914f6f2f50975c7c153165eddd5e116f3ed19a75`;
- stream ID: `arch-025-reviewed-resource`;
- actor ID: `consume-actor`;
- one action `reviewed-energy-consume`, `ends_turn=false`;
- setup: target `consume-target`, ally, speed 100, Energy 80/100, action index 0, amount 30.

## Acceptance criteria

- Supported versions are exactly `1.0`, `1.1`, `1.2`, `1.3`.
- v1.0/v1.1/v1.2 historical grammars remain strict and accepted.
- v1.2 rejects `ENERGY_CONSUME` as requiring v1.3.
- v1.3 accepts exactly the four closed setup kinds.
- `ENERGY_CONSUME` has a frozen typed setup and exact-field validation.
- Locked manifest order is exactly ARCH-017 -> ARCH-021 -> ARCH-023 -> ARCH-025.
- Standalone runtime Golden lane passes exactly `4/4` with record counts `4,3,3,3`.
- Controlled ARCH-025 setup mutation `amount=30 -> 25` reports a normal Golden mismatch on resource record index 1, with first divergence `/event/payload/legacy_data/after`, expected 50, actual 55.
- All four reviewed static fixture byte identities remain unchanged.
- Legacy regression remains `20/20`; trace evidence remains `2/2`.
- Production LIFO remains `third, second, first`.

## Required tests

Cover:

- explicit version constants/order;
- v1.0 no-setup compatibility;
- v1.1 accepted setup vocabulary unchanged;
- v1.2 accepted setup vocabulary unchanged and explicit `ENERGY_CONSUME` rejection;
- v1.3 required setup and all four allowed kinds;
- `ENERGY_CONSUME` exact/missing/unknown fields;
- finite numeric validation, positive base speed, exact action index, non-empty strings;
- locked four-case manifest identity/order;
- standalone runtime `4/4`;
- controlled consume mismatch;
- all fixture byte identities;
- closed/non-generic harness source;
- legacy regression, trace evidence, LIFO preservation.

## Files / areas that must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`;
- runtime adapters;
- runtime trace schema/contract;
- loader/exporter/comparator/divergence/Golden-validator implementation;
- legacy `hsr_axis_sim/data/regression_manifest.json`;
- reviewed static fixture bytes;
- AV/timeline/extra-turn mechanics.

## Explicit exclusions

- insufficient-Energy failure behavior;
- `ConsumeSkillPoint`;
- generic effect DSL or effect registry;
- automatic fixture generation;
- AV/speed/advance/delay/immediate-action observation;
- character database/release-game values;
- damage expansion;
- video parsing/scraping/automation;
- FIFO/LIFO changes.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, implementation summary, changed files, tests, exact commands/results, warnings/errors, unresolved issues, exclusions confirmation, and suggested next milestone.
