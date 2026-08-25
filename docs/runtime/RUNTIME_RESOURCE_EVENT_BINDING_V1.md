# Runtime Resource Event Binding v1

## Milestone

`HSR-RUNTIME-ARCH-020 — Production Resource Change Event Emission and Legacy Adapter Binding`

## Scope

ARCH-020 binds the accepted ARCH-019 observation vocabulary to exactly four
existing production effects:

- `GainEnergy`
- `ConsumeEnergy`
- `GainSkillPoint`
- `ConsumeSkillPoint`

It does not change their existing mutation formulas, caps, insufficient-resource
checks, AV/timeline behavior, trace schema v1, Golden fixtures, or LIFO
extra-turn compatibility behavior.

## Production event contract

After each successful resource mutation, the effect emits exactly one normal
legacy event through `BattleState.emit_event`.

Energy uses `energy_changed` per successfully mutated unit. Skill points use
`skill_points_changed` per successful team mutation.

Each event contains:

- `actor_id`
- `action_id`
- `resource_kind`
- `scope`
- `before`
- `after`
- `requested_delta`
- `applied_delta`
- `cap`
- `unit_id`

Energy uses `resource_kind=ENERGY`, `scope=UNIT`, and the affected unit ID.
Skill points use `resource_kind=SKILL_POINTS`, `scope=TEAM`, and `unit_id=null`.

Gain effects record `requested_delta=+amount`; consume effects record
`requested_delta=-amount`. `applied_delta` is always the actual `after-before`,
so a capped gain can intentionally have a smaller applied delta than requested.
ARCH-020 does not add new validation for negative legacy effect amounts.

## Failure and dispatch semantics

Existing insufficient-resource checks remain before mutation. A consume that
fails at that check does not mutate the failing resource and emits no resource
change event for that failed mutation.

Emission occurs after mutation and uses ordinary trigger-visible event dispatch.
If dispatch or a triggered effect raises after the resource mutation, ARCH-020
does not roll back state. This preserves the simulator's accepted
non-transactional action semantics.

## Legacy adapter binding

The accepted legacy adapter now binds:

- `energy_changed -> RuntimeEventType.ENERGY_CHANGED`
- `skill_points_changed -> RuntimeEventType.SKILL_POINTS_CHANGED`

Both normalize `action_id` and `actor_id`. Energy additionally normalizes
`target_id` from legacy `unit_id`; skill points have no normalized target ID.

Before a resource event becomes a `RuntimeEvent`, its observation fields are
validated by constructing the accepted ARCH-019
`RuntimeResourceChangeObservation`. The exact `to_payload()` result is stored at
`payload.resource_change`; existing `payload.adapter` and defensive
`payload.legacy_data` provenance remain present.

Malformed resource observations are rejected as `LegacyEventSchemaError` and
are never repaired or normalized into a different semantic meaning.

## Trace schema boundary

ARCH-020 does not create trace schema v2 and does not use record-level numeric
projection. Resource numbers remain in `RuntimeEvent.payload`; schema-v1
`RuntimeTraceRecord.numeric_values` remains empty.

## Explicit exclusions

No AV/speed/advance/delay/immediate-action observation, extra-turn ordering
change, static resource Golden fixture, regression-manifest expansion, damage
formula work, video extraction, or automatic gameplay-to-trace inference is
authorized by ARCH-020.
