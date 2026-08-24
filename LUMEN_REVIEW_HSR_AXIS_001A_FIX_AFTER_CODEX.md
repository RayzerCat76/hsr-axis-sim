# LUMEN REVIEW — HSR-AXIS-001A-FIX

## Verdict

**Accepted. HSR-AXIS-001A-FIX passes and is safe to move into HSR-AXIS-001B.**

I inspected the uploaded package and ran the test suite locally.

```text
26 passed in 0.14s
```

## What improved since 001A

The requested safety fixes were implemented:

1. `Action.execute()` now rejects an action whose `actor_id` does not match the active `TurnContext.actor_id`.
2. `ConsumeSkillPoint` now raises `ValueError` when SP is insufficient instead of silently clamping.
3. `ConsumeEnergy` now raises `ValueError` when energy is insufficient instead of silently clamping.
4. Extra turn ordering is explicitly tested as **LIFO** for the MVP.
5. Self `ImmediateAction` and self `AdvanceAction` during a normal turn are covered by tests.
6. The test suite grew from 20 tests to 26 tests.

## Current implementation status

The following mechanics are acceptable for the current MVP:

- base AV: `10000 / speed`
- current AV
- normal actor selection by lowest current AV
- global AV advancement
- normal turn reset
- action advance
- action delay
- speed change AV recalculation
- immediate action
- extra turn stack
- does-not-end-turn behavior
- strict SP/energy consumption
- placeholder damage

## Important assumptions to preserve

These are not necessarily final HSR-accurate forever, but they are now explicit MVP rules:

1. Extra turns resolve in **LIFO** order.
2. Extra turns do not advance global AV.
3. Extra turns do not alter the unit's original normal timeline current AV.
4. Self immediate/advance during the actor's normal turn does not create a second immediate normal action; after the turn ends, the actor receives a normal reset.
5. Resource gains clamp to max; resource consumption is strict.

## Watchlist for 001B and later

Do not fix these inside 001A-FIX unless they block replay validation. They should be handled deliberately later:

1. `Action.execute(state)` without a `TurnContext` can still execute a normal-ending action outside `Timeline.next_turn()`. For 001B, replay playback should always call `Timeline.next_turn()` first and pass the returned context.
2. Actions are not transactional. If a later effect fails, earlier effects may already have modified state. In search mode, the engine should eventually simulate on cloned states or prevalidate legal actions.
3. Buff/debuff duration tracking is not implemented yet.
4. Enemy AI is not implemented yet.
5. Damage formula is a placeholder.
6. Character data and real HSR mechanics are not implemented yet.

## Recommendation

Proceed to **HSR-AXIS-001B: Replay Validator MVP**.

001B should not add real character logic or Huroka importing. It should only add the ability to load a manually written golden replay JSON, run simulator steps, compare expected values, and report mismatches clearly.
