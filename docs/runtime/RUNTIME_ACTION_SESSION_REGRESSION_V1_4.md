# Runtime Action-Session Regression Manifest v1.4

## Purpose

Manifest v1.4 adds one narrow regression setup for the already reviewed successful `ConsumeSkillPoint` Golden fixture. It does not broaden the harness into a generic effect language.

The standalone runtime regression lane remains a deterministic hand-authored replay check over accepted production action execution, capture, adaptation, stitching, and Golden validation.

## Version compatibility

The manifest parser keeps every historical grammar explicit:

- v1.0: no `setup` field;
- v1.1: `EMPTY | ENERGY_GAIN`;
- v1.2: `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN`;
- v1.3: `EMPTY | ENERGY_GAIN | SKILL_POINT_GAIN | ENERGY_CONSUME`;
- v1.4: adds only `SKILL_POINT_CONSUME`.

A v1.3 manifest containing `SKILL_POINT_CONSUME` is invalid and is rejected as requiring v1.4. v1.4 does not retroactively widen v1.0-v1.3.

## `SKILL_POINT_CONSUME`

The setup is a dedicated frozen typed model with exactly these fields:

```text
kind = "SKILL_POINT_CONSUME"
initial_skill_points: int
max_skill_points: int
action_index: int
amount: int
```

Validation intentionally matches the existing Skill-Point gain field surface:

- `initial_skill_points`, `max_skill_points`, and `amount` must be exact integers;
- booleans are rejected even though Python treats `bool` as an `int` subtype;
- `action_index` must be an exact nonnegative integer and must reference one declared action;
- unknown or missing fields are rejected;
- no hidden HSR limits, release-game values, or sign assumptions are added by the regression schema.

The gain and consume setup types remain separate. There is no generic `mode`, effect-class name, dynamic import, kwargs bag, reflection, or executable manifest content.

## Runner behavior

For a `SKILL_POINT_CONSUME` case, the runner:

1. constructs `BattleState([], skill_points=initial_skill_points, max_skill_points=max_skill_points)`;
2. creates the declared actions in manifest order;
3. injects exactly one production `ConsumeSkillPoint(amount=amount)` on `action_index`;
4. leaves all other declared actions effect-free;
5. executes the accepted ARCH-016 action-session validation pipeline against the referenced static Golden bytes.

The runner does not implement Skill-Point arithmetic itself. Production `ConsumeSkillPoint` remains the source of the actual state transition and emitted event.

## Locked fifth reviewed case

v1.4 appends:

- case id: `arch-027-reviewed-static-skill-point-consume`;
- fixture: `hsr_axis_sim/data/runtime_golden_fixtures/arch_027_reviewed_skill_point_consume_expected.json`;
- SHA-256: `d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec`;
- stream: `arch-027-reviewed-resource`;
- actor: `sp-consume-actor`;
- action: `reviewed-skill-point-consume`;
- initial team SP: `4`;
- max team SP: `5`;
- consume amount: `2`;
- expected record count: `3`.

The locked manifest order is:

1. ARCH-017 effect-free action session;
2. ARCH-021 clamped Energy gain;
3. ARCH-023 clamped Skill-Point gain;
4. ARCH-025 successful Energy consume;
5. ARCH-027 successful Skill-Point consume.

The standalone runtime lane therefore targets exactly `5/5` reviewed Golden checks with record counts `4,3,3,3,3`.

## Deliberate mismatch contract

Changing only the fifth case consume amount from `2` to `1`, while keeping the reviewed expected artifact unchanged, must fail normally through the accepted Golden comparator. The expected first divergence is resource record index `1` at:

```text
/event/payload/legacy_data/after
```

This mismatch is diagnostic coverage only; it does not alter production behavior or expected bytes.

## Explicit exclusions

v1.4 does not add or change:

- insufficient-Skill-Point failure handling;
- simulator resource formulas;
- runtime event adapters or trace schema;
- Golden loader/export/comparison/divergence semantics;
- generic effect DSL support;
- automatic fixture generation;
- AV, speed, advance, delay, immediate-action, or extra-turn observations;
- legacy regression manifest contents;
- production LIFO behavior;
- character or release-game data;
- video extraction or automation.
