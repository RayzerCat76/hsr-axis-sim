# Action Delay Observation V1

## Status

ARCH-034 contract for observing the existing production `DelayAction` mutation in runtime traces.

This document describes simulator/runtime behavior only. It does not claim that the numeric inputs below are hidden or authoritative Honkai: Star Rail values.

## Production formula

The accepted production mutation remains:

```text
after_av = before_av + base_av * percent
```

ARCH-034 does not change that formula, add a zero floor, or restrict the sign of `percent`.

For one target Unit, production now emits `action_delayed` only after `current_av` has been assigned the resulting value.

The raw event contains exactly:

- `actor_id`
- `action_id`
- `target_id`
- `before_av`
- `after_av`
- `base_av`
- `requested_percent`
- `requested_delta_av`
- `applied_delta_av`

where:

```text
requested_delta_av = base_av * requested_percent
after_av = before_av + requested_delta_av
applied_delta_av = after_av - before_av
```

A normal positive delay therefore has a positive signed AV delta. Negative percentages remain representable because the pre-existing `DelayAction` and `Unit.current_av` contracts do not impose a nonnegative AV floor.

## Runtime contract

`action_delayed` maps to the dedicated runtime type:

```text
RuntimeEventType.ACTION_VALUE_DELAYED
```

The typed structured payload is stored under:

```text
payload["action_delay"]
```

using frozen `RuntimeActionDelayObservation` fields:

- `target_id`
- `before_av`
- `after_av`
- `base_av`
- `requested_percent`
- `requested_delta_av`
- `applied_delta_av`

The observation requires a non-empty target ID, finite non-boolean numeric fields, positive `base_av`, and exact consistency with the three equations above. It deliberately does not require nonnegative percentages or AV values.

The raw legacy event remains available unchanged under:

```text
payload["legacy_data"]
```

Malformed `action_delayed` observations are rejected with `LegacyEventSchemaError`; they are not degraded to `CONTENT_DEFINED`.

## Dispatch ordering

The event is emitted through normal `BattleState.emit_event` only after the target AV mutation. A trigger listening for `action_delayed` therefore observes the post-mutation AV and participates in the standard legacy trigger path.

For a single non-ending Delay action, the expected legacy order is:

```text
action_started
action_delayed
action_finished
```

The corresponding ARCH-012 typed runtime trace order is:

```text
ACTION_START
ACTION_VALUE_DELAYED
ACTION_END
```

## Explicit non-goals

ARCH-034 does not add or change:

- Advance semantics or its clamp observation;
- ChangeSpeed observation;
- ImmediateAction observation;
- GrantExtraTurn observation;
- a generic action-axis event abstraction;
- trace schema version;
- static Delay Golden fixtures;
- runtime regression manifest grammar/version or promotion;
- legacy regression cases;
- LIFO extra-turn behavior.
