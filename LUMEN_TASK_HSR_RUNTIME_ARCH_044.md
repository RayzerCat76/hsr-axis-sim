# HSR-RUNTIME-ARCH-044 — Reviewed Static GrantExtraTurn Golden Fixture

## Execution routing
- ChatGPT model: **GPT-5.6 Terra**
- Codex reasoning: **High**

## Current confirmed state
- Canonical accepted `main`: `b3e9f7385f08dd13e53caa00a2b921dd1b500471`.
- HSR-RUNTIME-ARCH-043 is accepted.
- Post-merge main CI run #264 passed:
  - pytest: `1713 passed in 10.07s`
  - legacy regression: `20/20`
  - trace evidence: `2/2`
  - runtime action-session Golden regression: `9/9`
- Accepted `GrantExtraTurn` simulator behavior appends target IDs to `extra_turn_stack`, emits one post-append `extra_turn_queued` event per resolved target, and preserves existing LIFO resolution.
- `RuntimeExtraTurnQueuedObservation` and the legacy adapter mapping are already accepted.
- Real HSR hidden extra-turn scheduling priority/FIFO/LIFO remains outside this task and unresolved.

## Objective
Add one independently authored, manually reviewed, compact canonical runtime Golden expectation for a deterministic one-target `GrantExtraTurn` production action and prove accepted ARCH-016 end-to-end validation matches it.

This task adds evidence only. It must not change simulator semantics or promote the new fixture into the runtime regression manifest.

## Required implementation
1. Add exactly one static fixture:
   - `hsr_axis_sim/data/runtime_golden_fixtures/arch_044_reviewed_grant_extra_turn_expected.json`
   - compact canonical UTF-8 JSON
   - no trailing newline
   - metadata:
     - `construction: manual-reviewed`
     - `fixture_id: arch-044-reviewed-static-grant-extra-turn`
     - `purpose: grant-extra-turn-end-to-end-golden`
   - trace ID: `arch-044-reviewed-static-expected`
   - exactly three records, sequence `0,1,2`:
     1. `ACTION_START`
     2. `EXTRA_TURN_QUEUED`
     3. `ACTION_END`
   - adapter stream ID: `arch-044-reviewed-axis`
   - action ID: `reviewed-grant-extra-turn`
   - actor ID: `extra-turn-actor`
   - target ID: `extra-turn-target`
   - queued observation must be exactly:
     - `target_id: extra-turn-target`
     - `stack_depth_before: 0`
     - `stack_depth_after: 1`
   - record-level `numeric_values` remains empty.
2. Add one focused test module:
   - `hsr_axis_sim/tests/test_runtime_arch_044_static_grant_extra_turn_golden_fixture.py`
3. Build production actual only through the accepted ARCH-016 action-session path using one production `Action` with `GrantExtraTurn(target_ids=["extra-turn-target"])`, `ends_turn=False`.
4. Pin the static fixture's exact byte length and SHA-256 in the focused test after the file is finalized.
5. Prove the exact static fixture schema/event IDs/actor/action/target/payloads and adapter binding.
6. Prove production validation matches the static fixture and leaves the queued target on `extra_turn_stack` without changing target AV.
7. Add one controlled mismatch by preloading one valid queued unit ID in `BattleState.extra_turn_stack` before the same action. The accepted comparator sorts mapping keys, so the exact first divergence must be:
   - record index: `1`
   - path: `/event/payload/extra_turn_queue/stack_depth_after`
   - expected: `1`
   - actual: `2`
   Also prove the corresponding `stack_depth_before` values are expected `0`, actual `1`.
8. Add an AST/source guard proving this ARCH-044 test contains no runtime expected-generation or fixture-write path. The static expectation must remain independently authored.
9. Prove the ARCH-044 fixture is absent from both the legacy regression manifest and the runtime action-session regression manifest.
10. Pin all nine previously accepted static fixture identities exactly and prove the existing runtime regression lane remains exactly `9/9` in its accepted case order.
11. Prove legacy regression remains `20/20`, trace evidence remains `2/2`, and production extra-turn LIFO compatibility is unchanged.
12. Update `hsr_axis_sim/LUMEN_RESULT.md` only after real CI results exist. Report actual commands and actual results only.

## Acceptance criteria
- New fixture is independent static reviewed bytes, not generated from simulator/runtime export code.
- Static fixture has exactly 3 records with `ACTION_START -> EXTRA_TURN_QUEUED -> ACTION_END`.
- `EXTRA_TURN_QUEUED` contains exact typed `extra_turn_queue` and exact preserved `legacy_data`.
- ARCH-016 production action-session validation matches the static fixture.
- Controlled preloaded-stack mismatch reports the exact first structured divergence at `/event/payload/extra_turn_queue/stack_depth_after`, record 1, expected 1 vs actual 2.
- Existing production LIFO behavior remains unchanged.
- Existing nine reviewed fixture byte identities remain unchanged.
- New fixture is not promoted into either regression manifest.
- Full pytest passes.
- Legacy regression remains 20/20.
- Trace evidence remains 2/2.
- Runtime action-session Golden regression remains exactly 9/9.
- No locked/unauthorized files are modified.
- `LUMEN_RESULT.md` contains the final evidence and exclusions.

## Required tests
At minimum, the focused test must cover:
- exact fixture byte count and SHA-256;
- no trailing newline;
- strict compact loader + required digest match;
- exact metadata/schema/sequence/event types/event IDs/action/actor/target;
- exact `extra_turn_queue` payload;
- exact raw `legacy_data` payload;
- exact adapter legacy event type/mechanic/mapping status;
- production ARCH-016 match;
- state postcondition: stack gains target and AV is unchanged;
- controlled preloaded-stack mismatch and exact first-divergence path/value;
- no expected-generation/write path in focused test source;
- fixture absent from both manifests;
- all nine prior fixture identities exact;
- runtime lane exactly 9/9 in existing order;
- legacy 20/20 and trace 2/2;
- LIFO compatibility unchanged.

## Files/areas that must remain unchanged
Do not modify:
- `hsr_axis_sim/sim/**`
- `hsr_axis_sim/runtime_contracts/**`
- `hsr_axis_sim/runtime_adapters/**`
- `hsr_axis_sim/runtime_comparators/**`
- `hsr_axis_sim/runtime_divergence/**`
- `hsr_axis_sim/runtime_loaders/**`
- `hsr_axis_sim/runtime_exports/**`
- `hsr_axis_sim/runtime_action_sessions/**`
- `hsr_axis_sim/runtime_action_session_validation/**`
- `hsr_axis_sim/runtime_action_session_regression/**`
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`
- `hsr_axis_sim/data/regression_manifest.json`
- every pre-ARCH-044 Golden fixture
- trace schemas and research/reference artifacts.

Only these task files are expected before the final report update:
- `LUMEN_TASK_HSR_RUNTIME_ARCH_044.md`
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_044_reviewed_grant_extra_turn_expected.json`
- `hsr_axis_sim/tests/test_runtime_arch_044_static_grant_extra_turn_golden_fixture.py`

Then update only:
- `hsr_axis_sim/LUMEN_RESULT.md`

## Explicit exclusions
- No production behavior changes.
- No Timeline changes.
- No extra-turn ordering changes.
- No new event types or adapter mappings.
- No schema/comparator/divergence changes.
- No regression-manifest version bump or fixture promotion.
- No claim about real HSR FIFO/LIFO, priority, interrupts, or hidden scheduling values.
- No damage/character database/video extraction/UI work.
- No unrelated refactors or documentation cleanup.

## Commands to run
```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report format
Update `hsr_axis_sim/LUMEN_RESULT.md` with:
- task ID;
- implementation summary;
- files added/modified;
- tests added;
- exact commands executed;
- exact pass/fail results;
- exact fixture byte size + SHA-256;
- controlled mismatch first-divergence evidence;
- unresolved issues;
- confirmation that exclusions and locked areas were respected;
- suggested next smallest milestone.

Do not report PASS from code inspection alone. Real GitHub Actions evidence is required before merge, then post-merge `main` CI must pass before the task is accepted.