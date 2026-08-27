# HSR-RUNTIME-ARCH-043 — GrantExtraTurn Runtime Observation Contract

## Status

PASS — proceed

## Task ID

`HSR-RUNTIME-ARCH-043`

## Current confirmed base

- Accepted `main` before this task: `23be13799facfe63152d727459f345f03e87fac6`.
- Baseline post-merge validation before this task, GitHub Actions run #257:
  - pytest: **1687 passed in 10.16s**;
  - legacy regression: **20/20**;
  - trace evidence: **2/2**;
  - standalone runtime action-session Golden regression: **9/9**.

## Objective completed

Made the already-existing production `GrantExtraTurn` extra-turn-stack append observable through the runtime trace pipeline without changing target resolution, append order, LIFO resolution, Timeline selection, action-value behavior, or the nine accepted reviewed Golden fixtures.

This task observes the simulator's deterministic queue mutation only. It does **not** claim or infer real Honkai: Star Rail priority values, interrupt windows, ultimate priority, extra-action/follow-up behavior, or any undocumented scheduling rule.

## Accepted simulator semantics preserved

For each target resolved by the existing `UnitEffect.target_units()` path, `GrantExtraTurn.apply()` now records the queue depth around the existing append while preserving the append itself:

```python
stack_depth_before = len(state.extra_turn_stack)
state.extra_turn_stack.append(unit.id)
stack_depth_after = len(state.extra_turn_stack)
```

It then emits one post-mutation legacy event:

`extra_turn_queued`

with exactly:

- `actor_id`;
- `action_id`;
- `target_id`;
- `stack_depth_before`;
- `stack_depth_after`.

The event is emitted after the append, so triggers observe the already-mutated stack. Target order is unchanged. `Timeline.next_turn()` remains unchanged and still resolves the accepted simulator stack by `pop()` from the end, so targets appended `[first, second]` resolve as `second`, then `first`.

Extra-turn selection still does not advance global AV or mutate the normal timeline AV snapshot merely by selecting the queued turn.

## Runtime contract added

Added frozen `RuntimeExtraTurnQueuedObservation` in:

`hsr_axis_sim/runtime_contracts/turn_order_observations.py`

Exact fields:

- `target_id: str`;
- `stack_depth_before: int`;
- `stack_depth_after: int`.

Validation requires:

- non-empty string target ID;
- exact integers for both depth fields, rejecting booleans and floats;
- nonnegative depths;
- `stack_depth_after == stack_depth_before + 1`.

`to_payload()` returns exactly those three fields. The contract is exported from `hsr_axis_sim/runtime_contracts/__init__.py`.

## Runtime adapter binding

The existing runtime vocabulary value `RuntimeEventType.EXTRA_TURN_QUEUED` is reused; `runtime_contracts/enums.py` is unchanged.

Added deterministic legacy mapping:

`extra_turn_queued -> EXTRA_TURN_QUEUED`

Normalized IDs:

- `action_id <- action_id`;
- `actor_id <- actor_id`;
- `target_id <- target_id`.

For valid events the adapter preserves:

- exact raw input in `payload["legacy_data"]`;
- validated structured queue observation in `payload["extra_turn_queue"]`;
- existing adapter provenance.

Malformed structured queue events raise `LegacyEventSchemaError`; they do not degrade to `CONTENT_DEFINED` and are not silently repaired.

The current mapping registry is 14 entries with 13 bound mappings and the pre-existing unresolved `unit_defeated` lifecycle mapping. The historical ARCH-002 mapping document remains its exact nine-entry historical projection and does not backfill `extra_turn_queued`.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_043.md`
- `hsr_axis_sim/runtime_contracts/turn_order_observations.py`
- `hsr_axis_sim/tests/test_runtime_arch_043_extra_turn_observation.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`
- `hsr_axis_sim/runtime_contracts/__init__.py`
- `hsr_axis_sim/runtime_adapters/legacy_events.py`
- `hsr_axis_sim/sim/effects.py`
- `hsr_axis_sim/tests/test_runtime_legacy_event_mapping.py`
- `hsr_axis_sim/tests/test_runtime_arch_031_advance_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_034_delay_action_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_037_change_speed_observation.py`
- `hsr_axis_sim/tests/test_runtime_arch_040_immediate_action_observation.py`

## Focused tests added / updated

ARCH-043 coverage proves:

1. `RuntimeExtraTurnQueuedObservation` is frozen and serializes the exact three-field payload;
2. empty/non-string target IDs are rejected;
3. bool/float/string/negative queue-depth values are rejected;
4. depth transitions other than exact `before + 1` are rejected;
5. `extra_turn_queued` maps to `RuntimeEventType.EXTRA_TURN_QUEUED`;
6. normalized action/actor/target IDs are exact;
7. raw `legacy_data` is preserved exactly;
8. typed `extra_turn_queue` payload is exact;
9. malformed structured legacy events raise `LegacyEventSchemaError`;
10. one-target production event order is exactly `action_started -> extra_turn_queued -> action_finished`;
11. the event data contains exactly the five specified legacy fields;
12. an `extra_turn_queued` trigger sees the already-appended target and post-append depth;
13. self-target actor/target identity and depth are exact;
14. multi-target events preserve declared append order;
15. multi-target depth transitions are `0 -> 1` then `1 -> 2`;
16. subsequent `Timeline.next_turn()` calls resolve the accepted stack LIFO in reverse append order;
17. extra-turn selection leaves global AV and normal unit AV snapshots unchanged;
18. ARCH-012 capture produces exactly `ACTION_START -> EXTRA_TURN_QUEUED -> ACTION_END`;
19. `GrantExtraTurn` remains distinct from Advance/Delay/ChangeSpeed/ImmediateAction observation families;
20. all nine reviewed Golden fixture byte identities remain exact;
21. legacy regression remains `20/20`;
22. trace evidence remains `2/2`;
23. standalone runtime action-session Golden regression remains `9/9`;
24. pre-existing production LIFO compatibility remains explicit and passing.

Historical ARCH-031/034/037/040 source guards were updated narrowly to permit the later-authorized `extra_turn_queued` observation while continuing to assert that `GrantExtraTurn` does not emit their action-axis event types.

## Exact commands executed by CI

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Real validation results

Authoritative green PR validation before this completion-report update:

GitHub Actions `HSR Axis Sim Validation`, PR #48, run **#262** (`33027644428`), job **`98372622604`**, branch head `4851c6e551313082dc38c2b3ae8a763357e8624d`:

- compile: **PASS**;
- pytest: **1713 passed in 9.85s**;
- legacy locked regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **9/9**.

The nine runtime action-session reviewed cases and their accepted record counts remain:

1. `arch-017-reviewed-static-action-session` — 4;
2. `arch-021-reviewed-static-clamped-energy` — 3;
3. `arch-023-reviewed-static-clamped-skill-point` — 3;
4. `arch-025-reviewed-static-energy-consume` — 3;
5. `arch-027-reviewed-static-skill-point-consume` — 3;
6. `arch-032-reviewed-static-action-advance` — 3;
7. `arch-035-reviewed-static-action-delay` — 3;
8. `arch-038-reviewed-static-change-speed` — 3;
9. `arch-041-reviewed-static-immediate-action` — 3.

No tenth runtime regression case was added.

## Validation history / resolved failures

Initial PR validation run **#258** (`33027318210`), job **`98371603615`**, branch head `bd44f11ee3b34502aac525fd94748e867a83fba7`:

- compile: **PASS**;
- pytest: **4 failed, 1709 passed in 10.76s**;
- downstream regression lanes were skipped because the pytest gate failed.

All four failures were stale historical source guards that still required `GrantExtraTurn` to emit no event at all:

1. ARCH-031 action-advance observation scope guard;
2. ARCH-034 action-delay observation scope guard;
3. ARCH-037 speed-change observation scope guard;
4. ARCH-040 ImmediateAction observation scope guard.

No new ARCH-043 contract, adapter, production queue mutation, trigger, capture, self-target, multi-target, LIFO, or regression-identity test failed in that run.

The four historical guards were then updated narrowly so they continue to reject cross-mechanic action-axis events but explicitly allow the newly authorized `extra_turn_queued` observation. Run #262 then passed the complete workflow.

## Locked areas confirmed unchanged

- `hsr_axis_sim/runtime_contracts/enums.py` unchanged; the pre-existing `EXTRA_TURN_QUEUED` value is reused.
- `hsr_axis_sim/sim/timeline.py` unchanged.
- `hsr_axis_sim/sim/action.py` unchanged.
- `hsr_axis_sim/sim/state.py` unchanged.
- `hsr_axis_sim/sim/unit.py` unchanged.
- runtime resource and action-axis observation semantics unchanged.
- runtime action-session regression manifest, grammar, and runner unchanged.
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` unchanged at v1.8 / 9 cases.
- `hsr_axis_sim/data/regression_manifest.json` unchanged.
- every reviewed Golden fixture under `hsr_axis_sim/data/runtime_golden_fixtures/` unchanged.
- Golden validator/comparator/first-divergence implementation unchanged.
- trace schema/version unchanged.
- ownership/SP/energy semantics unchanged.
- Advance/Delay/ChangeSpeed/ImmediateAction production semantics unchanged.

The only production simulator modification is observation emission around the pre-existing append inside `GrantExtraTurn.apply()`.

## Warnings / errors

- No compile, pytest, legacy-regression, trace-evidence, or runtime-action-session-regression failure remains in run #262.
- Existing nonblocking GitHub Actions warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node 20 and are forced onto Node 24.
- Existing upstream Node `punycode` and `url.parse()` deprecation notices remain unrelated to simulator correctness.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-043 acceptance.

Real HSR extra-turn scheduling/priority semantics remain intentionally unresolved. This task only exposes the already accepted simulator LIFO stack mutation and must not be used as evidence that the game implements the same hidden scheduler.

## Exclusions confirmation

Respected: no real-HSR priority inference, no interrupt windows, no ultimate-priority rules, no extra-action/follow-up semantics, no FIFO alternative, no generalized scheduler/priority queue, no Timeline change, no queue deduplication/replacement, no automatic action selection, no static GrantExtraTurn Golden, no runtime regression promotion, no manifest v1.9, no generic effect DSL, no enum change, no trace schema bump, no comparator/divergence change, no video parsing/scraping, no character database expansion, no damage formula work, no AI optimization, and no unrelated UI/refactor work.

## Suggested next milestone

Do not begin a new milestone until ARCH-043 is accepted on canonical `main` with post-merge CI.

After acceptance, the smallest safe continuation is expected to be **HSR-RUNTIME-ARCH-044 — Reviewed Static GrantExtraTurn Golden Fixture**: manually construct and review one deterministic static Golden for the accepted queue observation and existing LIFO simulator behavior, prove production match and controlled first divergence, and do **not** promote it into the runtime regression lane in the same task.

Recommended routing for ARCH-044 after ARCH-043 acceptance:

- ChatGPT: **GPT-5.6 Terra**;
- Codex reasoning: **High**.

The production semantics are already locked; ARCH-044 is deterministic fixture construction and validation rather than a new scheduler-semantic change.
