# ChangeSpeed Runtime Observation v1

## Scope

HSR-RUNTIME-ARCH-037 adds a deterministic observation boundary around the already-existing production `ChangeSpeed` effect. It does not change the speed/AV formula, target resolution, or the existing `new_speed <= 0` error.

## Production formula

For one resolved target and a successful finite positive requested speed:

```text
before_speed = unit.speed
before_av = unit.current_av
after_av = before_av * before_speed / new_speed
after_speed = new_speed
```

No AV floor is added. Negative AV remains negative after proportional rescaling.

This milestone does not add new production validation for previously unguarded NaN/infinity/bool inputs. The typed runtime observation is stricter because runtime payloads must be canonical-JSON-compatible.

## Legacy event

After both `current_av` and `speed` are assigned, `ChangeSpeed` emits:

`speed_changed`

with:

- `actor_id`
- `action_id`
- `target_id`
- `before_speed`
- `after_speed`
- `before_av`
- `after_av`

The event uses ordinary `BattleState.emit_event`, so matching triggers run after both mutations and can observe the post-change speed and AV.

## Runtime binding

The legacy adapter binds:

`speed_changed -> RuntimeEventType.SPEED_CHANGED`

The normalized event carries action, actor, and target IDs. Raw legacy data remains under `payload["legacy_data"]`; the strict typed payload is under `payload["speed_change"]`.

`RuntimeSpeedChangeObservation` requires:

- non-empty `target_id`;
- finite non-boolean numeric fields;
- positive before/after speeds;
- exact `after_av == before_av * before_speed / after_speed`.

Malformed structured events raise `LegacyEventSchemaError`; they are not downgraded to `CONTENT_DEFINED`.

## Explicit exclusions

This contract does not add:

- a generic action-axis observation abstraction;
- a static ChangeSpeed Golden fixture;
- runtime regression promotion;
- ImmediateAction observation;
- GrantExtraTurn observation;
- new production input validation;
- release-game hidden values or assumptions.
