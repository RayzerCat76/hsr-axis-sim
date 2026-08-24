# LUMEN_TASK_HSR_AXIS_001A

## Project
HSR Axis Simulator

## Task ID
HSR-AXIS-001A

## Reasoning level
High

## Task type
Core engine foundation

## Goal
Build a clean, deterministic action-value timeline simulator core for a Honkai: Star Rail inspired axis-search project.

This task is **not** about AI search yet. It is only about making the action-axis engine accurate, testable, and extensible.

---

## Scope

### Implement in this task
- Unit speed
- Base action value: `base_av = 10000 / current_speed`
- Current action value
- Selecting the next actor by lowest `current_av`
- Advancing global AV time
- Subtracting elapsed AV from all normal timeline units
- Resetting a normal actor after their turn by adding `base_av`
- Action advance / pull forward
- Action delay / push back
- Speed buffs and debuffs
- Immediate action
- Extra turn stack
- Action that does not end the current turn
- Basic skill point changes
- Basic energy gain
- Unit tests for all mechanics

### Do not implement in this task
- Full damage formula
- Full character database
- Huroka/Yatta/HoneyHunter importers
- Web scraping
- Real Bronya/Seele/Sparkle/etc. character logic
- Enemy AI
- Beam search
- AI axis finder
- UI
- Bilibili replay validation

---

## Required project structure

Create this structure:

```text
hsr_axis_sim/
  sim/
    __init__.py
    unit.py
    state.py
    timeline.py
    effects.py
    action.py
    turn_context.py
  tests/
    test_action_value.py
    test_speed_change.py
    test_action_advance.py
    test_immediate_action.py
    test_extra_turn.py
  LUMEN_RESULT.md
```

---

## Required classes

Use dataclasses or Pydantic. Keep the code readable and testable.

### Unit
Suggested fields:

```python
id: str
name: str
team: str  # ally or enemy
base_speed: float
speed: float
current_av: float
energy: float = 0
max_energy: float = 100
hp: float = 1
max_hp: float = 1
is_alive: bool = True
```

Required computed property or method:

```python
base_av = 10000 / speed
```

### BattleState
Suggested fields:

```python
global_av: float
units: list[Unit]
skill_points: int
max_skill_points: int
extra_turn_stack: list[str]
logs: list[str]
```

### TurnContext
Suggested fields:

```python
actor_id: str
is_extra_turn: bool
should_end_turn: bool
actions_taken: list[str]
```

### Action
Suggested fields:

```python
id: str
name: str
actor_id: str
target_ids: list[str]
effects: list[Effect]
ends_turn: bool = True
```

### Effect
Implement generic effect primitives. Do not hard-code real character logic.

Required effect types:

```text
GainEnergy
ConsumeEnergy
GainSkillPoint
ConsumeSkillPoint
AdvanceAction
DelayAction
ChangeSpeed
ImmediateAction
GrantExtraTurn
DoesNotEndTurn
```

Optional placeholder effect:

```text
DealDamage
```

Damage can be simple placeholder damage in this task.

---

## Timeline rules

### Normal timeline actor selection
The next normal actor is the alive unit with the lowest `current_av`.

When selecting a normal actor:

```python
elapsed = min(unit.current_av for unit in alive_units)
state.global_av += elapsed
for unit in alive_units:
    unit.current_av -= elapsed
actor.current_av = 0
```

### Normal turn ending
After a normal turn ends:

```python
actor.current_av += actor.base_av
```

### Extra turns
Extra turns must be resolved before the normal timeline.

If `extra_turn_stack` is not empty, pop the next extra-turn actor and create a TurnContext with `is_extra_turn=True`.

Extra turns must not modify the unit's original normal timeline position.

### Immediate action
Immediate action sets:

```python
unit.current_av = 0
```

### Action advance
Action advance uses:

```python
unit.current_av = max(0, unit.current_av - unit.base_av * percent)
```

### Action delay
Action delay uses:

```python
unit.current_av = unit.current_av + unit.base_av * percent
```

### Speed change
When speed changes while the unit already has remaining current AV:

```python
new_current_av = old_current_av * old_speed / new_speed
unit.speed = new_speed
```

The new base AV becomes:

```python
base_av = 10000 / new_speed
```

### Does not end current turn
An action with `DoesNotEndTurn` should set:

```python
turn_context.should_end_turn = False
```

It should not create an extra turn.
It should not reset the actor's AV yet.
It means the current turn context remains open.

---

## Required tests

Use pytest.

### test_action_value.py
Test that:
- speed 100 gives base AV 100
- speed 134 gives base AV about 74.6269
- the lowest current AV actor acts first
- global AV advances correctly
- all units' current AV values are reduced by elapsed AV
- actor current AV is reset after turn end

### test_speed_change.py
Test that:
- speed increase reduces remaining current AV using `old_current_av * old_speed / new_speed`
- speed decrease increases remaining current AV using the same formula
- base AV updates after speed changes

### test_action_advance.py
Test that:
- 50% advance subtracts `base_av * 0.5`
- 100% advance does not go below 0
- action delay adds `base_av * percent`

### test_immediate_action.py
Test that:
- immediate action sets current AV to 0
- immediate action is not the same as 100% advance if current AV is greater than base AV

### test_extra_turn.py
Test that:
- extra turns are taken before normal timeline actors
- extra turns do not advance global AV
- extra turns do not alter the unit's original normal timeline current AV
- normal turn reset still works after extra turn stack is empty

---

## Floating point tolerance
Use explicit tolerance in tests, for example:

```python
assert actual == pytest.approx(expected, abs=1e-6)
```

---

## Coding style requirements

- Keep state mutations explicit.
- Avoid hidden global variables.
- Avoid real character names in core mechanics.
- Use generic sample units in tests, such as `ally_fast`, `ally_slow`, `enemy`.
- Make logs readable, but do not overbuild logging in this task.
- Keep the package importable.

---

## Deliverable

Codex must produce a working Python package with passing pytest tests.

It must also create `LUMEN_RESULT.md` with:

```text
# LUMEN_RESULT_HSR_AXIS_001A

## Implemented files

## Tests run

## Passing tests

## Known inaccuracies / assumptions

## Intentionally not implemented

## Blockers

## Recommended next task
```

---

## Gate condition

Do not move to HSR-AXIS-001B until:
- all 001A tests pass
- the timeline engine is readable
- extra turns are correctly separated from normal timeline movement
- immediate action and 100% action advance are not confused
- speed-change AV recalculation is implemented correctly
