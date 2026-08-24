# HSR-RUNTIME-ARCH-018 — Reviewed Static End-to-End Golden Fixture Regression Integration

## Current confirmed state

- `HSR-RUNTIME-ARCH-017 — PASS` is merged to `main` at `2acd5c3423aacc196cf4d81840082b9c232d66ff`.
- Complete pytest: `1037 / 1037 passed`.
- Locked regression: `20 / 20 passed`.
- Trace evidence: `2 / 2 passed`.
- ARCH-017 accepted static expected artifact:
  - `hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json`
  - exact size: `3013` bytes
  - SHA-256: `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`
- The existing regression `replays` group uses the legacy `sim.replay.ReplayValidator` format and must not be repurposed for runtime-trace Golden validation.

## Objective

Promote the accepted ARCH-017 non-circular end-to-end fixture into the locked regression baseline as a distinct runtime action-session check, while preserving every existing legacy regression check unchanged and delegating runtime validation to accepted ARCH-016.

## Required implementation

1. Add a new regression manifest/report group named `runtime_action_sessions`.
2. Extend the regression manifest parser with a strict group-specific entry contract sufficient to describe the accepted simple ARCH-017 production Action session:
   - `id`;
   - `path` to the reviewed static expected runtime-trace artifact;
   - exact `expected_sha256`;
   - `stream_id`;
   - `actor_id`;
   - non-empty ordered `actions`, each containing exactly:
     - `action_id`;
     - `name`;
     - `ends_turn` boolean.
3. Keep the new group separate from legacy `replays`; do not send runtime traces through `ReplayValidator`.
4. Add one locked manifest entry for `arch-017-reviewed-static-action-session` pointing to the exact already accepted ARCH-017 fixture and pinned SHA.
5. Regression execution for this group must:
   - create a fresh empty `BattleState`;
   - reconstruct only the explicitly declared simple production `Action` objects, with no targets/effects;
   - use caller-owned cursor `(0, 0)`;
   - use `UnknownLegacyEventPolicy.REJECT` and `AmbiguousLegacyEventPolicy.REJECT`;
   - create deterministic per-step trace configs from the manifest entry/order;
   - create one deterministic final stitch config;
   - read the reviewed expected artifact bytes unchanged from the declared path;
   - call accepted `run_action_session_validation` (ARCH-016) exactly once;
   - report PASS only when the accepted end-to-end result matches;
   - on a completed Golden mismatch, return one failed regression result with first-divergence details rather than reinterpret the mismatch;
   - on operational/input exception, return one failed regression result with the exception text, consistent with existing regression-runner behavior.
6. Add `--only runtime_action_sessions` support and stable text/markdown/JSON report rendering.
7. Preserve declared manifest order.
8. Update tests for manifest parsing, runner execution/reporting, total locked check count, and backward compatibility of manifests that omit the new group.
9. Add preservation tests proving:
   - the 12 legacy `replays` remain exactly the same entries and still use `ReplayValidator`;
   - ARCH-017 expected bytes and SHA are unchanged;
   - no simulator, runtime adapter/exporter/loader/comparator/divergence/Golden/ARCH-016 implementation file is modified;
   - production LIFO compatibility behavior remains unchanged.
10. Update `docs/DECISION_LOG.md`, `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`, and `hsr_axis_sim/LUMEN_RESULT.md` after real validation.

## Acceptance criteria

- Complete pytest passes.
- Existing legacy regression checks remain unchanged and passing:
  - 12/12 legacy golden replays;
  - 2/2 manual checks;
  - 2/2 search scenarios;
  - 2/2 action-sequence trace checks;
  - 2/2 trace-evidence checks.
- New locked runtime action-session group passes `1/1`.
- Total locked regression becomes exactly `21/21`, where the additional check is visibly reported under `runtime_action_sessions` rather than folded into legacy `replays`.
- `--only trace_evidence` remains exactly `2/2`.
- `--only runtime_action_sessions` returns exactly `1/1`.
- ARCH-017 expected artifact remains byte-for-byte unchanged at 3013 bytes and the accepted SHA-256.
- No protected production/runtime behavior is changed.

## Required tests

Cover at minimum:

- default manifest count includes `runtime_action_sessions: 1`;
- old manifests omitting the new group remain valid and yield count 0;
- malformed runtime action-session entries are rejected: missing/invalid digest, empty actions, malformed action objects, invalid booleans, missing expected path;
- locked entry reconstructs the declared ordered actions and passes through ARCH-016 against the fixed expected bytes;
- `--only runtime_action_sessions` runs only the new check;
- text/markdown/JSON reports include the new group distinctly;
- full locked regression total is 21 and all pass;
- first-divergence information is surfaced for a controlled test mismatch without redefining comparator/reporting semantics;
- ARCH-017 expected artifact digest/size stays exact;
- production LIFO compatibility remains protected.

## Files / areas that must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`;
- accepted `runtime_*` packages outside `hsr_axis_sim/regression/**`;
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json`;
- any existing file under `hsr_axis_sim/data/golden_replays/**`;
- manual trace/evidence fixtures;
- search scenarios;
- accepted research/reference artifacts.

The only accepted behavior changes are regression manifest/schema/runner/report integration and its tests/docs.

## Explicit exclusions

- no new runtime wrapper;
- no new simulator mechanics;
- no adapter/exporter/loader/comparator/divergence/Golden semantics;
- no automatic expected generation;
- no video parsing/extraction;
- no turn/action selection or optimization;
- no generic arbitrary effect/target serialization framework;
- no replacement of legacy replay validation;
- no FIFO/LIFO semantic change.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only runtime_action_sessions --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

## Execution routing

- ChatGPT model: `GPT-5.6 Sol`
- Codex reasoning: `High` if Codex is used; Codex is optional.

## Final report format

`hsr_axis_sim/LUMEN_RESULT.md` must include:

- task ID;
- implementation summary;
- files added/modified;
- tests added;
- exact commands executed;
- exact pass/fail results;
- locked regression category counts;
- warnings/errors;
- unresolved issues;
- confirmation that exclusions/protected areas were respected;
- suggested next milestone.
