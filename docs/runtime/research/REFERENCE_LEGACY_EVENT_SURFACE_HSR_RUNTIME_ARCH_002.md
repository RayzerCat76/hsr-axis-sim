# Reference — Legacy Event Surface for HSR-RUNTIME-ARCH-002

## Inspection boundary

Repository package inspected:

```text
hsr_axis_001a_package(1).zip
```

Inspection date:

```text
2026-07-12
```

This reference records the complete event-construction surface currently found
under `hsr_axis_sim/sim/**`. It is an adapter specification, not permission to
change the existing simulator.

## Existing event mechanism

```python
@dataclass
class Event:
    type: str
    data: dict[str, Any]
```

Events are appended to:

```text
BattleState.pending_events
```

`dispatch_event()` also runs existing triggers synchronously. ARCH-002 must not
modify, wrap, intercept, or replace that path.

## Exact legacy event types

| Legacy type | Source | Payload | Runtime envelope |
|---|---|---|---|
| `action_started` | `sim/action.py` | `actor_id`, `action_id` | `ACTION_START` |
| `action_finished` | `sim/action.py` | `actor_id`, `action_id` | `ACTION_END` |
| `turn_started` | `sim/timeline.py` | `actor_id`, `is_extra_turn` | `TURN_START` |
| `turn_ended` | `sim/timeline.py` | `actor_id`, `is_extra_turn` | `TURN_END` |
| `damage_dealt` | `sim/effects.py` | `source_id`, `target_id`, `amount`, `damage_type`, `element`, `is_crit`, `formula_parts`; optional `is_break_damage` | `DAMAGE_RESOLVED` |
| `weakness_break` | `sim/effects.py` | `source_id`, `target_id`, `element`, `break_damage_amount`, `elemental_break_effect_id`, `formula_parts` | `WEAKNESS_BROKEN` |
| `unit_defeated` | `sim/effects.py` | `killer_id`, `target_id` | `CONTENT_DEFINED` only |

## Lifecycle ambiguity

The MVP's `unit_defeated` event occurs after:

```text
target.hp = 0
target.is_alive = False
```

It does not distinguish:

```text
DOWNED
KNOCKED_DOWN
DEATH
PENDING_REVIVE
lethal interception
```

Therefore:

```text
legacy unit_defeated
!= safe RuntimeEventType.DEATH
!= safe RuntimeEventType.KNOCKED_DOWN
```

Use semantic gap:

```text
LEGACY_EVENT.UNIT_DEFEATED_LIFECYCLE
```

Do not alias `killer_id` to `RuntimeEvent.source_id`; preserve it only in the
raw legacy payload.

## Unknown event types exist

Project fixtures include event types not produced by the active simulator,
including:

```text
preexisting_event
```

Unknown event behavior must never silently default. The caller must explicitly
choose:

```text
PRESERVE_AS_CONTENT_DEFINED
or
REJECT
```

The same explicit choice is required for known-but-ambiguous mappings.

## No hierarchy inference

The legacy event surface does not expose:

```text
event_id
sequence
attack_id
hit_id
ActionContext
AttackContext
HitContext
ActionFamily
PriorityClass
SamePriorityPolicy
```

ARCH-002 must not manufacture those semantics.

A caller-supplied stream ID and sequence may be used only to create a
deterministic envelope identity.

## Adapter direction

Allowed:

```text
legacy Event / iterable[Event]
→ immutable RuntimeEvent envelope(s)
```

Forbidden:

```text
automatic hook into BattleState.emit_event
RuntimeEvent dispatch back into sim
legacy trigger migration
formula or queue changes
Action/Attack/Hit reconstruction
```
