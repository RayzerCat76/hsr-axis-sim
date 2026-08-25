# Runtime Action-Session Regression Manifest v1.3

## Status

Accepted by HSR-RUNTIME-ARCH-026 when its full validation passes.

## Purpose

Version 1.3 adds one narrowly reviewed successful Energy-consume setup to the standalone runtime action-session Golden regression lane. It does not create a generic combat script or arbitrary-effect language.

## Version compatibility

The parser keeps each historical grammar explicit:

- **v1.0** — original case fields only; `setup` is not allowed.
- **v1.1** — `setup` is required and `kind` is limited to `EMPTY` or `ENERGY_GAIN`.
- **v1.2** — `setup` is required and `kind` is limited to `EMPTY`, `ENERGY_GAIN`, or `SKILL_POINT_GAIN`.
- **v1.3** — `setup` is required and adds `ENERGY_CONSUME` to those three kinds.

A v1.2 manifest containing `ENERGY_CONSUME` is rejected. New syntax is never silently interpreted under an older version.

## ENERGY_CONSUME setup

Exact fields:

```json
{
  "kind": "ENERGY_CONSUME",
  "target_id": "consume-target",
  "target_name": "consume-target",
  "team": "ally",
  "base_speed": 100,
  "initial_energy": 80,
  "max_energy": 100,
  "action_index": 0,
  "amount": 30
}
```

Rules:

- unknown and missing fields are rejected;
- `target_id`, `target_name`, and `team` are non-empty strings;
- `base_speed`, `initial_energy`, `max_energy`, and `amount` are finite numbers and booleans are rejected;
- `base_speed` must be greater than zero, matching the existing Unit constructor requirement;
- `action_index` is an exact nonnegative integer, booleans are rejected, and it must address a declared action;
- no extra Energy sign/range or release-game assumption is added by the regression manifest.

`ENERGY_CONSUME` has its own frozen typed model. It is not represented as an `ENERGY_GAIN` mode flag or a generic resource-effect type.

## Runner construction

For an `ENERGY_CONSUME` case the standalone runner:

1. constructs exactly one Unit from the declared setup;
2. constructs the declared Actions;
3. injects exactly one production `ConsumeEnergy(target_ids=[target_id], amount=amount)` on `action_index`;
4. leaves all other actions effect-free;
5. executes the existing accepted action-session capture/stitch/Golden validation pipeline.

Existing `EMPTY`, `ENERGY_GAIN`, and `SKILL_POINT_GAIN` construction paths remain unchanged.

## Locked v1.3 manifest

`HSR_RUNTIME_ACTION_SESSION_REGRESSION_001` contains exactly four reviewed cases in order:

1. `arch-017-reviewed-static-action-session` — effect-free multi-action capture;
2. `arch-021-reviewed-static-clamped-energy` — clamped Energy gain;
3. `arch-023-reviewed-static-clamped-skill-point` — clamped Skill-Point gain;
4. `arch-025-reviewed-static-energy-consume` — successful Energy consumption.

Expected record counts are `4, 3, 3, 3`.

## Explicit non-goals

Version 1.3 does not add:

- arbitrary effect lists or class names;
- reflection/import paths;
- effect kwargs;
- scripts, eval, or exec;
- insufficient-Energy failure semantics;
- `ConsumeSkillPoint`;
- AV/speed/advance/delay/immediate-action setup;
- character or skill databases;
- automatic fixture generation;
- changes to the legacy regression manifest;
- changes to trace schema v1;
- changes to simulator mechanics or LIFO compatibility behavior.
