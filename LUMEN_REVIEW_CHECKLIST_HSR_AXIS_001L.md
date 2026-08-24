# LUMEN REVIEW CHECKLIST — HSR-AXIS-001L Ultimate / Interrupt Window MVP

Use this checklist after Codex returns 001L.

## Required test commands

Run from the project root:

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
```

## Pass criteria

001L passes only if all of these are true:

1. Full pytest suite passes.
2. All old golden replays still pass unchanged.
3. New `ultimate_interrupt_mvp.json` golden replay passes.
4. Ultimate choice enumeration is deterministic.
5. Ultimate choice generation does not mutate battle state.
6. Dead ultimate users are excluded.
7. Insufficient energy excludes ultimates.
8. Dead targets are excluded.
9. Target legality still uses 001J target validation.
10. Interrupt execution does not call `Timeline.next_turn`.
11. Interrupt execution does not advance `global_av`.
12. Interrupt execution does not reset actor `current_av`.
13. Interrupt execution does not tick target-normal-turn buff/debuff durations.
14. Interrupt execution does not expire current-turn statuses.
15. Interrupt action with `ends_turn=True` fails clearly.
16. Replay validator supports interrupt steps without breaking normal steps.
17. The implementation does not add Beam Search, scoring, enemy AI, Huroka import, or full damage formula.

## Things to inspect manually

- `TurnContext`: if `is_interrupt` was added, confirm it is not confused with `is_extra_turn`.
- `Action.execute`: confirm interrupt actions cannot accidentally end/reset a normal turn.
- `ReplayValidator.validate`: confirm normal steps still call `Timeline.next_turn`, interrupt steps do not.
- `legal_ultimate_choices`: confirm it filters strictly by `skill_type == "ultimate"`.
- `LUMEN_RESULT.md`: confirm it lists real command outputs, not vague claims.

## Likely next task after 001L

If 001L passes, next task should probably be:

**HSR-AXIS-001M: Enemy AI / Enemy Action Pattern MVP**

Reason: after normal actions and off-turn ultimates are both enumerable, the simulator needs enemy actions to reproduce real videos and prepare for search.
