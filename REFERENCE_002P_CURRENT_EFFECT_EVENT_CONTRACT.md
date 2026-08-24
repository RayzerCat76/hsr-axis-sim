# Reference — Current Effect/Event Contract for HSR-AXIS-002P

This reference describes the code boundaries that 002P must independently pin and verify. It is not itself proof and must not be copied into a report without source digests and executable checks.

## Current observed architecture

### `Action.execute`

Current action execution is:

1. reset per-action trigger counters;
2. emit `action_started`;
3. apply effects sequentially in list order;
4. append the action ID to `TurnContext.actions_taken`;
5. emit `action_finished`;
6. end the turn only when `should_end_turn` is true.

### `GainEnergy`

Current behavior:

- resolves target units;
- sets `energy = min(max_energy, energy + amount)`;
- emits no event itself;
- does not mutate buffs, AV, HP, SP, logs, or turn context.

### `AddBuff`

Current behavior:

- resolves target units;
- inserts or refreshes a buff through `_add_status`;
- emits no event itself;
- does not mutate Energy, AV, HP, SP, logs, or turn context.

### Trigger visibility

Current triggers execute only when `BattleState.emit_event(...)` is called. Under the current implementation, there is no event boundary between `GainEnergy` and `AddBuff`. Therefore triggers can observe the state before both effects at `action_started`, or after both effects at `action_finished`, but no current trigger contract appears able to observe their intermediate order.

This must be proven by 002P rather than assumed.

## Required proof scope

The proof should compare at minimum:

- all unit dataclass fields;
- all buff/debuff contents and metadata;
- Energy including below-cap, near-cap, and at-cap cases;
- global AV and per-unit AV;
- skill points;
- extra-turn stack;
- logs;
- pending events and their order/data;
- trigger fire counts and dispatch count;
- enemy AI plans/cursors;
- complete `TurnContext`;
- deterministic rendered audit output.

Include valid existing-buff refresh and unrelated-status cases. Include boundary triggers on `action_started` and `action_finished` so the proof does not silently ignore the trigger system.

## Explicit exclusions

A current-contract irrelevance result must not claim:

- the release game's real internal effect order;
- equivalence under invalid effect configuration or mid-action exceptions;
- equivalence after future engine changes;
- same-current-turn duration equivalence;
- authorization to create a real Tingyun DMG-buff binding;
- accepted-video target or trace level.
