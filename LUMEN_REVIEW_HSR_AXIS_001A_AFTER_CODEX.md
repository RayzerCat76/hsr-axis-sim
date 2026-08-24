# LUMEN REVIEW — HSR-AXIS-001A After Codex

## Verdict

**HSR-AXIS-001A is basically accepted.**

The Codex output successfully created a clean MVP action-value engine and the local pytest suite passes in this environment:

```bash
20 passed in 0.17s
```

This is good enough to continue the project, but I recommend doing a small cleanup task before starting HSR-AXIS-001B Replay Validator.

---

## What is correct

### 1. Core AV formula

`base_av = 10000 / speed` is implemented as a property on `Unit`, which is good because it automatically updates when speed changes.

### 2. Normal timeline selection

`Timeline.next_turn()` correctly chooses the alive unit with the lowest `current_av`, advances global AV by that amount, and subtracts elapsed AV from all alive units.

### 3. Normal turn reset

A normal actor gets `actor.current_av += actor.base_av` when the turn ends. This matches the intended MVP model.

### 4. Action advance / delay

`AdvanceAction` and `DelayAction` use:

```python
current_av -= base_av * percent
current_av += base_av * percent
```

This is the right MVP model.

### 5. Speed change

`ChangeSpeed` uses:

```python
new_current_av = old_current_av * old_speed / new_speed
```

This is the correct core relationship for changing speed while a unit is already on the timeline.

### 6. Immediate action vs 100% advance

There is a dedicated test proving that immediate action is not the same as 100% action advance when current AV is larger than base AV. This is important and correct.

### 7. Extra turns

Extra turns are handled before the normal timeline and do not advance global AV or change the unit's original normal timeline position. That is the right MVP behavior.

### 8. DoesNotEndTurn

`DoesNotEndTurn` keeps the same `TurnContext` open and does not reset AV. This is the right direction for Qingque / Boothill-style mechanics later.

---

## Issues to fix before HSR-AXIS-001B

### Fix 1 — Add turn ownership validation

Right now `Action.execute()` does not verify that `action.actor_id == turn_context.actor_id`.

That means a replay could accidentally say Bronya is taking a turn but execute Seele's action, and the simulator would not complain.

Add validation:

```python
if self.actor_id != turn_context.actor_id:
    raise ValueError(...)
```

This is especially important before replay validation.

---

### Fix 2 — Split resource legality from resource effects

Right now `ConsumeSkillPoint` and `ConsumeEnergy` clamp at zero.

That is okay for the earliest MVP, but it is dangerous for replay validation and search. A simulated action should not silently spend 1 SP when only 0 SP exists.

For 001A-fix, add a strict mode or basic validation:

```python
if state.skill_points < amount:
    raise ValueError("Not enough skill points")
```

Energy should do the same for ultimates later.

---

### Fix 3 — Add actor/current-turn edge case tests

Current tests cover immediate action on another unit and extra turns well, but they do not cover problematic cases such as:

- A current actor applying ImmediateAction to itself during its own turn.
- Action advance applied to the acting unit before turn end.
- Extra turn granted during an extra turn.
- Multiple extra turns granted in a known order.

For MVP, self-immediate-action can be documented as undefined if we do not want to model it yet. But there should be a test or a clear guard.

---

### Fix 4 — Decide extra-turn ordering policy

Current implementation uses a LIFO stack.

That is acceptable for now, but the project should explicitly document it. Later, if game testing shows HSR behaves like FIFO or has priority rules, we can change it.

For now, add a test named something like:

```python
test_multiple_extra_turns_use_documented_lifo_order()
```

This prevents accidental changes.

---

### Fix 5 — Add package metadata / import cleanup

The current package runs when tested from the parent folder, but before the project grows, add one of these:

- `pyproject.toml`, or
- a simple root-level README with test instructions.

This will make future Codex tasks more stable.

---

## Do not start 001B until these are done

HSR-AXIS-001B will depend heavily on replay validation. Replay validation needs strict actor/action/resource checks. Otherwise it may pass bad replays silently.

Recommended next task:

**HSR-AXIS-001A-FIX — harden the MVP engine before replay validation.**

After that, proceed to:

**HSR-AXIS-001B — Golden Replay Validator.**
