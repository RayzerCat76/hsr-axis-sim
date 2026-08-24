# HSR-RUNTIME-ARCH-017 — Reviewed Static End-to-End Golden Action Session Fixture

## Status

PASS — proceed

## Implementation summary

- Added the first reviewed static non-circular expected runtime-trace artifact for the production `Action` -> ARCH-016 -> Golden path.
- The expected artifact was manually derived from accepted `Action.execute`, legacy-event adapter, runtime trace projection, and canonical serialization contracts rather than generated from the simulator under test.
- Added exact fixture identity checks: compact canonical JSON, no trailing newline, 3013 bytes, SHA-256 `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`.
- Added a matching two-action production session that executes only through accepted ARCH-016 and must match the static fixture.
- Added a controlled divergence case that changes only the second production action ID while preserving the same static expected bytes; accepted first divergence is record index 2 at `/event/action_id`.
- Added source-level guards preventing the ARCH-017 test from generating expected bytes through runtime trace builders, canonical JSON helpers, adapter helpers, or lower ARCH-013/014/015 orchestration at test runtime.
- Kept the new fixture outside the locked regression manifest in this milestone.
- Added decision D-027: end-to-end Golden expectations are reviewed static artifacts, not simulator-generated test oracles.

## Manual fixture derivation

Reviewed scenario:

- actor: `reviewed-actor`;
- action 1: `reviewed-action-a`, no effects, `ends_turn=False`;
- action 2: `reviewed-action-b`, no effects, `ends_turn=False`;
- legacy adapter stream: `arch-017-reviewed-static`.

Accepted `Action.execute` behavior emits `action_started` then `action_finished` for each no-effect action. With `ends_turn=False`, no turn-end event is introduced by these actions.

Accepted legacy mappings produce:

1. sequence 0 — `ACTION_START` — `reviewed-action-a`;
2. sequence 1 — `ACTION_END` — `reviewed-action-a`;
3. sequence 2 — `ACTION_START` — `reviewed-action-b`;
4. sequence 3 — `ACTION_END` — `reviewed-action-b`.

All four mappings are `BOUND`, contain no semantic gaps, and normalize only the reviewed action/actor IDs. ARCH-003 projects each event to a record with no inferred action/attack/hit context, empty numeric values, and empty notes.

Expected document identity:

- trace id: `arch-017-reviewed-static-expected`;
- record count: 4;
- first/last sequence: 0 / 3;
- sequence policy: `CONTIGUOUS`;
- event counts: `ACTION_START=2`, `ACTION_END=2`;
- semantic gaps: none;
- metadata: `construction=manual-reviewed`, fixture id, purpose `end-to-end-golden`.

## Static fixture identity

File:
`hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json`

Exact identity:

- size: `3013` bytes;
- canonical form: compact runtime trace v1 JSON;
- trailing newline: none;
- SHA-256: `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`.

The digest was calculated directly over the manually written UTF-8 JSON bytes. No simulator, legacy adapter, runtime exporter, or trace builder was used to produce the expected artifact.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_017.md`
- `docs/runtime/REVIEWED_STATIC_END_TO_END_GOLDEN_FIXTURE_V1.md`
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json`
- `hsr_axis_sim/tests/test_runtime_arch_017_static_end_to_end_golden_fixture.py`
- `hsr_axis_sim/tests/test_runtime_arch_017_preservation.py`

## Files modified

- `docs/DECISION_LOG.md`
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`
- `hsr_axis_sim/LUMEN_RESULT.md`

No existing simulator, runtime, Golden, regression, search, binding, fixture, reference, or manifest executable behavior was modified. `hsr_axis_sim/data/regression_manifest.json` remains unchanged.

## Tests added

ARCH-017 tests cover:

- exact static fixture byte count and SHA-256;
- exact compact canonical runtime-trace v1 loading with required digest match;
- reviewed record sequences, event types, and action IDs;
- matching production Action session through accepted ARCH-016 -> Golden PASS;
- deliberately changed second production action -> completed Golden mismatch;
- accepted first divergence at record index `2`, path `/event/action_id`, expected `reviewed-action-b`, actual `reviewed-action-c`;
- AST guard proving the test contains no runtime expected-artifact generation path;
- explicit proof that the fixture is not referenced by the locked regression manifest;
- production LIFO compatibility behavior remains unchanged.

## Exact validation commands and real results

GitHub Actions workflow: `HSR Axis Sim Validation`, PR #21, run #84, job `validate` (`97465300925`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1037 passed in 7.16s`.
3. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS 20/20 total checks:
     - 12/12 golden replays;
     - 2/2 manual checks;
     - 2/2 search scenarios;
     - 2/2 action-sequence trace checks;
     - 2/2 trace-evidence checks.
4. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS 2/2 trace-evidence checks.

## Warnings / errors

- No compile, test, strict-loader, Golden comparison, or regression errors.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-017 correctness.

## Acceptance review

- The expected artifact is independent of the simulator under test at test runtime.
- Exact bytes and SHA are pinned and strict-loaded before use.
- Production Actions genuinely traverse accepted ARCH-016 and match the static record stream.
- A production action-ID change is detected against the same unchanged fixture with accepted first-divergence provenance.
- No runtime helper was added to regenerate or repair the expected artifact.
- No existing runtime executable or Golden semantics were changed.
- The locked regression manifest remains unchanged, preserving the existing 20/20 baseline.
- No automatic turn/action/replay selection, video extraction, new HSR mechanic, or FIFO/LIFO change was introduced.
- Existing production LIFO behavior remains unchanged.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-017 acceptance.

ARCH-017 intentionally proves the reviewed non-circular fixture independently of the locked regression runner. It does not yet promote or register the fixture as a locked regression check.

Existing unresolved HSR game semantics remain tracked separately and were not changed.

## Suggested next milestone

`HSR-RUNTIME-ARCH-018 — Reviewed Static End-to-End Golden Fixture Regression Integration`

ARCH-018 should first inspect the accepted regression runner and manifest schema, then add the smallest safe mechanism that executes the proven ARCH-017 static fixture as a locked repeatable regression check. The fixture bytes and pinned digest must remain unchanged; existing legacy regression behavior must remain preserved. Do not assume the current legacy replay category can represent an ARCH-016 production Action session without inspection.
