# Action Advance Runtime Observation V1

## Status

HSR-RUNTIME-ARCH-031 contract.

This document defines the smallest deterministic runtime observation for the existing production `AdvanceAction` mutation.

It does not define Delay, speed changes, immediate action, extra-turn behavior, or real-game hidden values.

## Existing production formula

The accepted simulator behavior remains:

```text
after_av = max(0, before_av - base_av * percent)
```

where `base_av` is the target Unit's existing `Unit.base_av` value.

ARCH-031 does not add a positivity restriction to `AdvanceAction.percent`. The observation layer describes the existing accepted input surface; it does not narrow it.

## Legacy production event

After each target Unit's AV assignment succeeds, `AdvanceAction` emits exactly one normal simulator event:

```text
action_advanced
```

The event data contains:

- `actor_id`;
- `action_id`;
- `target_id`;
- `before_av`;
- `after_av`;
- `base_av`;
- `requested_percent`;
- `requested_delta_av`;
- `applied_delta_av`;
- `clamped_to_zero`.

The signed delta convention is:

```text
requested_delta_av = -(base_av * requested_percent)
applied_delta_av = after_av - before_av
```

`clamped_to_zero` is true only when the requested unclamped result would be below zero. Reaching exactly zero without crossing below zero is not a clamp.

## Dispatch ordering

The production AV mutation happens before `state.emit_event(...)`.

Therefore normal legacy dispatch order is:

1. assign the target Unit's new `current_av`;
2. append `action_advanced` to `BattleState.pending_events`;
3. run matching standard legacy triggers in deterministic trigger-ID order.

A trigger listening to `action_advanced` therefore observes post-mutation AV. This is intentional. ARCH-031 does not bypass the standard trigger system with a side channel.

For a non-ending one-effect action, the observable legacy order is:

```text
action_started
-> action_advanced
-> action_finished
```

## Typed runtime contract

`action_advanced` binds to:

```text
RuntimeEventType.ACTION_VALUE_ADVANCED
```

The runtime event normalizes:

- `action_id`;
- `actor_id`;
- `target_id`.

The raw event remains preserved under:

```text
payload["legacy_data"]
```

The validated structured observation is exposed under:

```text
payload["action_advance"]
```

using frozen `RuntimeActionAdvanceObservation`.

## Structured observation

`RuntimeActionAdvanceObservation` contains:

- `target_id`;
- `before_av`;
- `after_av`;
- `base_av`;
- `requested_percent`;
- `requested_delta_av`;
- `applied_delta_av`;
- `clamped_to_zero`.

Validation requires:

- non-empty `target_id`;
- finite non-boolean numeric fields;
- positive `base_av`;
- `requested_delta_av == -(base_av * requested_percent)`;
- `applied_delta_av == after_av - before_av`;
- `after_av == max(0, before_av + requested_delta_av)`;
- exact clamp flag consistency with an unclamped result below zero.

Malformed bound `action_advanced` observations raise `LegacyEventSchemaError`. They are not silently downgraded to `CONTENT_DEFINED`.

## Trace schema

ARCH-031 is additive inside existing schema v1. There is no trace schema version bump.

The action-advance values remain inside `RuntimeEvent.payload`. Record-level `numeric_values` remains unchanged and empty for this observation.

A captured one-effect non-ending advance action becomes:

```text
ACTION_START
-> ACTION_VALUE_ADVANCED
-> ACTION_END
```

## Scope exclusions

ARCH-031 does not add observation semantics for:

- `DelayAction`;
- `ChangeSpeed`;
- `ImmediateAction`;
- `GrantExtraTurn`;
- static Advance Golden fixtures;
- runtime regression manifest promotion;
- character or release-game data;
- video extraction.

Production LIFO compatibility remains unchanged.
