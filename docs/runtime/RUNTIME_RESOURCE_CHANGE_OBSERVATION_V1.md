# Runtime Resource Change Observation v1

## Scope

HSR-RUNTIME-ARCH-019 defines observation vocabulary for existing skill-point and energy state changes without changing production simulator behavior.

This is an interface contract only. ARCH-019 does not emit new legacy events, does not add legacy adapter mappings, and does not change the behavior of `GainEnergy`, `ConsumeEnergy`, `GainSkillPoint`, or `ConsumeSkillPoint`.

## Runtime event vocabulary

Two schema-v1-compatible `RuntimeEventType` values are added:

- `ENERGY_CHANGED`
- `SKILL_POINTS_CHANGED`

They are observation names only in ARCH-019. No simulator code produces them yet.

## Resource vocabulary

`RuntimeResourceKind`:

- `ENERGY`
- `SKILL_POINTS`

`RuntimeResourceScope`:

- `UNIT`
- `TEAM`

The immutable `RuntimeResourceChangeObservation` has exactly these fields:

```text
resource_kind
scope
before
after
requested_delta
applied_delta
cap
unit_id
```

## Invariants

All numeric values are finite `int`/`float` values and booleans are rejected.

The only universal arithmetic invariant is:

```text
applied_delta == after - before
```

`ENERGY` requires `UNIT` scope and a non-empty `unit_id`.

`SKILL_POINTS` requires `TEAM` scope, `unit_id=None`, and integer numeric values.

ARCH-019 intentionally does not impose additional sign, lower-bound, initial-value, or cap-consistency assumptions that are not already guaranteed by the production state constructors. The observation records what happened; it does not invent a broader game rule.

## Requested versus applied delta

`requested_delta` and `applied_delta` are separate because the existing production gain effects can clamp at a cap. For example, a skill-point gain may request `+3` from `4/5` while the applied transition is only `+1` to `5/5`.

This distinction describes existing production behavior. It does not define new clamp semantics.

## Schema-v1 compatibility

Runtime trace schema `hsr_runtime_trace` version `1.0` requires `RuntimeTraceRecord.numeric_values` to remain empty. ARCH-019 does not change that schema.

Resource observation values therefore live inside `RuntimeEvent.payload`:

```json
{
  "resource_kind": "ENERGY",
  "scope": "UNIT",
  "before": 70.0,
  "after": 100.0,
  "requested_delta": 50.0,
  "applied_delta": 30.0,
  "cap": 100.0,
  "unit_id": "unit-a"
}
```

The accepted exporter and strict loader can round-trip the new event types under schema v1 without populating record-level numeric values.

Moving resource numbers into `RuntimeTraceRecord.numeric_values` would require separately reviewed trace-schema work and is explicitly not part of ARCH-019.

## Integration boundary

ARCH-019 stops before production integration.

A later milestone may explicitly:

1. emit legacy resource-change observations only after successful production mutations;
2. preserve requested versus applied delta and cap values;
3. add reviewed legacy-event mappings to `ENERGY_CHANGED` and `SKILL_POINTS_CHANGED`;
4. prove action-session trace capture observes those events end to end.

That later milestone must preserve current failure semantics: insufficient consume operations must not fabricate a successful resource-change observation.

## Exclusions

ARCH-019 does not add:

- production event emission;
- legacy adapter mappings;
- SP/energy mutation changes;
- AV, speed, advance, delay, immediate-action, or extra-turn observations;
- trace schema v2;
- record-level numeric values;
- Golden fixture changes;
- replay/video automation;
- FIFO/LIFO changes.
