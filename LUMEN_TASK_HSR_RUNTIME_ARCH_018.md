# HSR-RUNTIME-ARCH-018 — Reviewed Static End-to-End Golden Fixture Regression Integration

## Current confirmed state

- HSR-RUNTIME-ARCH-017 — PASS and merged to `main`.
- Confirmed baseline: 1037/1037 pytest, 20/20 locked regression, 2/2 trace evidence.
- ARCH-017 reviewed fixture is fixed at 3013 bytes with SHA-256 `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`.
- Current blocker: none.

## Objective

Promote the proven ARCH-017 non-circular static Golden fixture into the locked regression runner using one explicit regression category that executes production `Action` objects only through accepted ARCH-016.

## Required implementation

1. Add regression manifest group `runtime_action_sessions` without reusing legacy `replays` semantics.
2. Add one v1 manifest entry mode: `no_effect_action_session_golden`.
3. Each runtime-action-session entry must explicitly provide:
   - `id`;
   - `path` to the static expected runtime trace;
   - `check` = `no_effect_action_session_golden`;
   - lowercase 64-hex `expected_sha256`;
   - non-empty `adapter_stream_id`;
   - non-empty `actor_id`;
   - non-empty ordered list of unique non-empty `action_ids`.
4. Extend `RegressionManifestEntry` only with the fields needed by this group.
5. Manifest loading must validate the v1 fields and preserve all existing group behavior.
6. Add runner support for `runtime_action_sessions`:
   - construct a fresh `BattleState([])`;
   - construct exactly the declared no-effect `Action` values with `ends_turn=False` in declared order;
   - use deterministic explicit ARCH-013/014/015 configuration derived from the entry;
   - read exact expected bytes from the reviewed fixture path;
   - validate only through `run_action_session_validation` (ARCH-016);
   - return one `RegressionCheckResult` per entry.
7. On Golden mismatch, expose accepted first-divergence provenance from the returned ARCH-016 result; do not recompute comparison/divergence.
8. Add the ARCH-017 fixture as exactly one `runtime_action_sessions` manifest entry.
9. Existing five regression groups must preserve their previous 20/20 checks; the new group adds 1/1 for a total expected locked regression of 21/21.
10. `--only runtime_action_sessions` must work.
11. Default in-process regression discovery must include the locked runtime-action-session entry.

## Acceptance criteria

- ARCH-017 fixture bytes and SHA remain unchanged.
- Legacy `replays` remains owned by old `ReplayValidator`; runtime Action sessions are not routed through it.
- Runner calls ARCH-016 and does not directly invoke ARCH-013/014/015/011 or lower Golden/comparator/divergence functions.
- New manifest schema rejects malformed digest, missing required fields, duplicate/empty action IDs, and unsupported check mode.
- Text/Markdown/JSON reports include the new group deterministically.
- Existing five groups remain 20/20; new group is 1/1; total locked regression is 21/21.
- Trace-evidence-only remains 2/2.
- Complete pytest suite passes.

## Required tests

- default manifest counts include `runtime_action_sessions: 1` while existing counts remain unchanged;
- default manifest regression total is 21 and passes;
- `--only runtime_action_sessions` returns exactly one passing check;
- CLI JSON/text/Markdown reporting exposes the new group;
- old-manifest backward compatibility gives runtime-action-session count 0;
- malformed runtime-action-session entries are rejected;
- synthetic runtime-action-session mismatch using the same ARCH-017 fixture reports first divergence record 2 at `/event/action_id`;
- fixture SHA remains exactly pinned;
- runner source delegates only to ARCH-016 for the new check;
- production LIFO remains unchanged.

## Editable files / areas

Authorized executable/data changes:
- `hsr_axis_sim/regression/manifest.py`
- `hsr_axis_sim/regression/runner.py`
- `hsr_axis_sim/data/regression_manifest.json`
- regression / ARCH-018 tests
- task/docs/governance result files

## Protected files / areas

Do not modify:
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json`;
- `sim/**`;
- accepted runtime packages including ARCH-016;
- accepted Golden packages;
- existing legacy replay/manual/search/trace fixture files;
- reference/research artifacts.

## Explicit exclusions

No new simulator mechanics, no generic action DSL, no effects/targets/turn-context schema, no automatic action selection, no replay/video extraction, no expected regeneration, no Golden/comparator/divergence reimplementation, no file writing, and no FIFO/LIFO change.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only runtime_action_sessions --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

## Final report format

Report task ID, implementation summary, changed files, tests, exact commands/results, old-five-group preservation, new-group result, fixture SHA preservation, warnings/errors, unresolved issues, exclusions, suggested next milestone, and update `hsr_axis_sim/LUMEN_RESULT.md`.

## Execution routing

ChatGPT: GPT-5.6 Sol.  
Codex: High if used; Codex is optional for this milestone.
