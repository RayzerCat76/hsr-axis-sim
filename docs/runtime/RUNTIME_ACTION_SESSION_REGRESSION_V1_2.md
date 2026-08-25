# Runtime Action-Session Regression Manifest v1.2

## Purpose

Version 1.2 promotes the reviewed ARCH-023 clamped Skill-Point fixture into the locked standalone runtime action-session Golden regression lane while preserving the earlier manifest grammars exactly.

## Versioned grammar

The loader accepts three explicit versions:

- `1.0`: original six case fields only; no `setup` field is accepted.
- `1.1`: the six case fields plus required `setup`; accepted kinds are exactly `EMPTY` and `ENERGY_GAIN`.
- `1.2`: the six case fields plus required `setup`; accepted kinds are exactly `EMPTY`, `ENERGY_GAIN`, and `SKILL_POINT_GAIN`.

`SKILL_POINT_GAIN` is not backported to 1.1. A 1.1 manifest using that discriminator is rejected rather than interpreted under newer semantics.

## Existing setup kinds

### `EMPTY`

Exact form:

```json
{"kind":"EMPTY"}
```

The runner constructs `BattleState([])` and all actions remain effect-free.

### `ENERGY_GAIN`

The v1.1 contract is unchanged. The runner constructs one explicit Unit and injects exactly one production `GainEnergy` effect at the declared action index.

## New `SKILL_POINT_GAIN`

Exact fields:

```text
kind
initial_skill_points
max_skill_points
action_index
amount
```

The runner constructs:

```python
BattleState(
    [],
    skill_points=initial_skill_points,
    max_skill_points=max_skill_points,
)
```

and injects exactly one:

```python
GainSkillPoint(amount=amount)
```

on the declared action index. Every other action remains effect-free.

`initial_skill_points`, `max_skill_points`, and `amount` must be exact integers with booleans rejected. `action_index` must be an exact nonnegative integer and address a declared action. The manifest layer does not invent additional SP sign/range rules; existing production constructors/effects remain authoritative.

## Locked cases

Version 1.2 contains exactly three reviewed cases in declared order:

1. `arch-017-reviewed-static-action-session` — `EMPTY`, four records.
2. `arch-021-reviewed-static-clamped-energy` — `ENERGY_GAIN`, three records.
3. `arch-023-reviewed-static-clamped-skill-point` — `SKILL_POINT_GAIN`, three records.

The third fixture locks team-scoped Skill Points changing from 4/5 with requested gain 3 to final 5, distinguishing `requested_delta=3` from `applied_delta=1`.

## Explicit non-goals

Version 1.2 does not add:

- arbitrary effect lists or effect names;
- reflection/import paths;
- free-form constructor kwargs;
- target-selection DSLs;
- character or skill databases;
- script/expression evaluation;
- consume-resource cases;
- AV/timeline cases;
- fixture generation;
- video extraction.

Future setup kinds require separate reviewed versioned schema evolution rather than turning this manifest into a generic combat DSL.
