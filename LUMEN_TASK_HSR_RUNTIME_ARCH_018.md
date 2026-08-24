# HSR-RUNTIME-ARCH-018 — Reviewed Static End-to-End Golden Fixture Regression Integration

## Current confirmed state

- `HSR-RUNTIME-ARCH-017 — PASS` is merged to `main` at `2acd5c3423aacc196cf4d81840082b9c232d66ff`.
- Complete pytest: `1037 / 1037 passed`.
- Legacy locked regression: `20 / 20 passed`.
- Trace evidence: `2 / 2 passed`.
- ARCH-017 accepted static expected artifact:
  - `hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json`
  - exact size: `3013` bytes
  - SHA-256: `f672ffaac9ef9296e4982a6fb61f4d0257b5c0506412bcf54eb1768334118c66`
- The existing `hsr_axis_sim/regression/**` implementation and `hsr_axis_sim/data/regression_manifest.json` are protected legacy/current-contract evidence boundaries. They must remain byte-for-byte unchanged.
- ARCH-018 initial CI run #90 proved that importing runtime sidecars into legacy `regression/**` or changing legacy manifest counts violates accepted preservation and pinned research/current-contract evidence. That direct-integration design is rejected.

## Objective

Promote the accepted ARCH-017 non-circular end-to-end fixture into a **separate locked runtime regression lane** that delegates validation to accepted ARCH-016, while preserving the existing legacy `20/20` regression identity and all pinned research evidence unchanged.

## Required implementation

1. Add a new downstream package `hsr_axis_sim.runtime_action_session_regression` outside `hsr_axis_sim/regression/**`.
2. Add a separate strict runtime regression manifest, e.g. `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`.
3. The standalone manifest root must have an explicit schema/version and a non-empty ordered case list. Unknown fields are rejected.
4. Each runtime action-session case must contain exactly the minimal data needed for the accepted ARCH-017 simple production Action session:
   - `id`;
   - canonical repo-relative `expected_path` to the reviewed static expected runtime-trace artifact;
   - exact lowercase `expected_sha256`;
   - `stream_id`;
   - `actor_id`;
   - non-empty ordered `actions`, each containing exactly:
     - `action_id`;
     - `name`;
     - `ends_turn` boolean.
5. Paths must be explicit repo-relative POSIX paths and must remain inside the repository root after resolution. Missing/non-file targets are rejected.
6. Do not create a generic arbitrary target/effect serialization framework. ARCH-018 cases reconstruct only simple `Action` objects with no targets/effects.
7. Standalone runtime regression execution must:
   - preserve declared case/action order;
   - create a fresh empty `BattleState` per case;
   - reconstruct only the explicitly declared simple production `Action` objects;
   - use caller-owned cursor `(0, 0)`;
   - use `UnknownLegacyEventPolicy.REJECT` and `AmbiguousLegacyEventPolicy.REJECT`;
   - create deterministic per-step trace configs from case ID and step order;
   - create one deterministic final stitch config;
   - read the reviewed expected artifact bytes unchanged from the declared path;
   - construct `GoldenReplayValidationConfig` using the pinned digest and compact-only policy;
   - call accepted `run_action_session_validation` (ARCH-016) exactly once per executed case;
   - report PASS only when the accepted end-to-end result matches;
   - on a completed Golden mismatch, return a failed runtime regression check exposing existing first-divergence record index/path when available, without reinterpreting comparator/reporting semantics;
   - on operational/input exception, return a failed check with the exception text;
   - optionally stop after the first failed check only when an explicit `--fail-fast` flag is supplied.
8. Provide deterministic text/JSON reporting and a module CLI. Do not modify the legacy regression CLI.
9. Add one locked standalone manifest case for `arch-017-reviewed-static-action-session`, pointing to the unchanged ARCH-017 fixture and accepted SHA.
10. Extend `.github/workflows/tests.yml` with one separate step that executes the standalone runtime regression lane after the existing legacy regression and trace-evidence steps.
11. Add tests for strict manifest loading, path/digest/action validation, deterministic execution/reporting, controlled mismatch first-divergence provenance, fail-fast behavior, exact ARCH-017 fixture integrity, and production LIFO preservation.
12. Add preservation tests proving:
   - `hsr_axis_sim/regression/manifest.py` is unchanged from `main`;
   - `hsr_axis_sim/regression/runner.py` is unchanged from `main`;
   - `hsr_axis_sim/data/regression_manifest.json` is unchanged from `main`;
   - all 12 legacy replay entries remain unchanged and the legacy runner still reports `20/20`;
   - ARCH-017 expected bytes/SHA remain unchanged;
   - no simulator or accepted runtime implementation package is modified;
   - no research/reference artifact is modified;
   - production LIFO compatibility behavior remains unchanged.
13. Update `docs/DECISION_LOG.md`, `docs/HSR_AXIS_SIM_MASTER_BIBLE.md`, and `hsr_axis_sim/LUMEN_RESULT.md` after real validation.

## Acceptance criteria

- Complete pytest passes.
- Existing legacy locked regression remains **exactly `20/20`**, with the same category counts:
  - 12/12 legacy golden replays;
  - 2/2 manual checks;
  - 2/2 search scenarios;
  - 2/2 action-sequence trace checks;
  - 2/2 trace-evidence checks.
- Existing trace-evidence-only lane remains exactly `2/2`.
- New standalone locked runtime action-session lane passes exactly `1/1`.
- CI visibly runs all three validation lanes: legacy regression, trace evidence, standalone runtime action-session regression.
- ARCH-017 expected artifact remains byte-for-byte unchanged at 3013 bytes and the accepted SHA-256.
- Legacy `regression/**`, legacy regression manifest, research/reference artifacts, simulator behavior, and accepted runtime implementation behavior remain unchanged.

## Required tests

Cover at minimum:

- strict standalone manifest schema/version/root fields;
- duplicate case IDs rejected;
- absolute/noncanonical/traversing/out-of-root/missing expected paths rejected;
- invalid digest rejected;
- empty actions rejected;
- malformed/unknown action fields rejected;
- non-boolean `ends_turn` rejected;
- locked standalone manifest loads exactly one ARCH-017 case;
- declared action order is preserved;
- locked case passes through ARCH-016 against unchanged static expected bytes;
- controlled second-action mismatch reports first divergence at record 2 and `/event/action_id` using accepted ARCH-006 provenance;
- text and JSON output are deterministic and distinct from the legacy regression report;
- fail-fast behavior is explicit;
- legacy regression remains 20/20 and trace evidence remains 2/2;
- ARCH-017 fixture digest/size stays exact;
- production LIFO compatibility remains protected.

## Files / areas that must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/regression/**`;
- `hsr_axis_sim/data/regression_manifest.json`;
- accepted runtime packages other than adding the new downstream `runtime_action_session_regression/**` package;
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_017_reviewed_action_session_expected.json`;
- `hsr_axis_sim/data/golden_replays/**`;
- manual trace/evidence fixtures;
- search scenarios;
- accepted research/reference artifacts.

The only accepted executable behavior changes are the new standalone runtime regression lane and one CI step that invokes it.

## Explicit exclusions

- no direct integration into legacy `regression/**`;
- no legacy regression manifest/count change;
- no research pin/hash refresh just to accommodate ARCH-018;
- no new simulator mechanics;
- no adapter/exporter/loader/comparator/divergence/Golden/ARCH-016 semantic change;
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
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
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
- explicit legacy `20/20`, trace-evidence `2/2`, and runtime-lane `1/1` counts;
- initial failed CI run #90 and the architecture correction it exposed;
- warnings/errors;
- unresolved issues;
- confirmation that exclusions/protected areas were respected;
- suggested next milestone.
