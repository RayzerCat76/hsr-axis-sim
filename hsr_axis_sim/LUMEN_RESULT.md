# HSR-RUNTIME-ARCH-041 — Reviewed Static ImmediateAction Golden Fixture

## Status

PASS — proceed

## Task ID

`HSR-RUNTIME-ARCH-041`

## Current confirmed base

- Accepted `main` before this task: `27dbbd988f5e46066ad7b2ba7cd2425e7ecace7c`.
- Baseline validation before this task:
  - pytest: **1627 passed in 9.77s**;
  - legacy regression: **20/20**;
  - trace evidence: **2/2**;
  - standalone runtime action-session Golden regression: **8/8**.

## Implementation summary

- Added one independently reviewed, static, non-circular Golden expectation for the accepted production `ImmediateAction` behavior.
- The expected artifact was manually specified from the already accepted schema and ARCH-040 runtime observation contract. It is not synthesized at test runtime from the simulator, adapter, trace builder, exporter, stitcher, or Golden pipeline under test.
- Reviewed deterministic scenario:
  - fixture ID: `arch-041-reviewed-static-immediate-action`;
  - trace ID: `arch-041-reviewed-static-expected`;
  - stream ID: `arch-041-reviewed-axis`;
  - actor/target ID: `immediate-actor`;
  - Unit name: `Immediate Actor`;
  - team: `ally`;
  - base speed: `100`;
  - initial AV: `80`;
  - action ID/name: `reviewed-immediate-action`;
  - effect: `ImmediateAction()`;
  - `ends_turn=False`;
  - final AV: `0`.
- Static expected event order is exactly:
  - `ACTION_START`;
  - `ACTION_VALUE_IMMEDIATE`;
  - `ACTION_END`.
- The middle record preserves exact typed `payload["immediate_action"]`:
  - `target_id = "immediate-actor"`;
  - `before_av = 80`;
  - `after_av = 0`.
- Raw legacy data is preserved separately under `payload["legacy_data"]`.
- Every schema-v1 record retains `numeric_values={}`.
- The committed fixture is compact canonical JSON with no trailing newline.
- Exact fixture identity is locked at:
  - **2620 bytes**;
  - SHA-256 **`7fd1594362b5bf9a95eec6f6472b2f17afa9dcfe10196d81ec6c970eab86eea1`**.
- A real production ARCH-016 ImmediateAction session matches the static expected artifact and finishes at AV `0` with cursor `(3,3)`.
- A controlled production-only initial-AV change from `80` to `60` still ends at AV `0` but returns the accepted first divergence at:
  - record index `1`;
  - path `/event/payload/immediate_action/before_av`;
  - expected `80`;
  - actual `60`.
- The raw `legacy_data.before_av` difference is also preserved as `80` versus `60`.
- The new fixture remains outside both regression manifests in this milestone.
- All eight prior reviewed static fixture byte identities remain unchanged.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_041.md`
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_041_reviewed_immediate_action_expected.json`
- `hsr_axis_sim/tests/test_runtime_arch_041_static_immediate_action_golden_fixture.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`

## Tests added / updated

Focused ARCH-041 coverage verifies:

- exact static byte length, SHA-256, compact form, and no trailing newline;
- strict loader acceptance with the pinned digest;
- exact schema name/version and contiguous sequences `0,1,2`;
- exact trace ID and reviewed metadata;
- exact event order `ACTION_START`, `ACTION_VALUE_IMMEDIATE`, `ACTION_END`;
- exact legacy event IDs `legacy:arch-041-reviewed-axis:0`, `:1`, `:2`;
- exact action/actor/target provenance;
- exact typed `immediate_action` payload and exact raw `legacy_data`;
- empty record-level `numeric_values` for all three records;
- real ARCH-016 production ImmediateAction session matches the static fixture;
- production final AV is exactly `0` and final cursor is `(3,3)`;
- controlled initial AV `60` mismatch reports record `1`, `/event/payload/immediate_action/before_av`, expected `80`, actual `60`;
- the compared typed and raw payloads both preserve the controlled before-AV difference;
- no runtime expected-generation path exists in the focused test source;
- the new ARCH-041 fixture is absent from both regression manifests;
- all eight prior reviewed static fixture identities remain exact;
- current runtime action-session regression remains exactly `8/8` with the accepted case order;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- production extra-turn LIFO remains `third, second, first`.

## Exact commands executed by CI

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Real validation results

GitHub Actions `HSR Axis Sim Validation`, PR #46, run **#243** (`32919762189`), job **`98030858582`**, on branch head `2d98188271d05c41be03370964429939e8a88546`:

- compile: **PASS**;
- pytest: **1635 passed in 11.19s**;
- legacy locked regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **8/8**.

The complete focused ARCH-041 test set passed in that full suite. Therefore the committed fixture's strict digest/size checks, production match, controlled first-divergence proof, non-circularity guard, prior fixture identities, manifest absence, all existing regression lanes, and LIFO preservation all passed together.

## Fixture identity

- File: `hsr_axis_sim/data/runtime_golden_fixtures/arch_041_reviewed_immediate_action_expected.json`
- Exact byte length: **2620**
- SHA-256: **`7fd1594362b5bf9a95eec6f6472b2f17afa9dcfe10196d81ec6c970eab86eea1`**
- Encoding/form: compact canonical UTF-8 JSON, no trailing newline
- Construction: `manual-reviewed`

## First-divergence result

Controlled mismatch: same accepted production action/session and same static expected fixture, with only production initial AV changed from `80` to `60`.

Accepted first divergence:

- record index: **1**;
- path: **`/event/payload/immediate_action/before_av`**;
- expected: **80**;
- actual: **60**.

This follows the accepted comparator's recursive sorted mapping-key order. No comparator or divergence behavior was changed for this milestone.

## Locked areas confirmed unchanged

- `hsr_axis_sim/sim/**` unchanged.
- `hsr_axis_sim/runtime_contracts/**` unchanged.
- `hsr_axis_sim/runtime_adapters/**` unchanged.
- `hsr_axis_sim/runtime_action_session_regression/**` unchanged.
- `hsr_axis_sim/data/regression_manifest.json` unchanged.
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` unchanged.
- all eight prior reviewed static Golden fixture bytes unchanged.
- loaders/exporters/comparators/divergence/Golden implementation unchanged.
- production ImmediateAction behavior unchanged.
- GrantExtraTurn and Timeline semantics unchanged.
- trace schema/version unchanged.
- production extra-turn LIFO unchanged.

## Warnings / errors

- No compile, pytest, legacy-regression, trace-evidence, or runtime-action-session-regression failure remains in run #243.
- Nonblocking GitHub Actions warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node 20 and are forced onto Node 24.
- Upstream action setup continues to emit Node `punycode` and `url.parse()` deprecation notices. These warnings predate ARCH-041 and are unrelated to simulator correctness.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-041 acceptance.

The ARCH-041 ImmediateAction Golden is deliberately not yet part of the standalone runtime action-session regression manifest. Promotion is a separate milestone so manifest grammar/harness changes can be reviewed independently.

`GrantExtraTurn` remains outside this milestone. No release-game scheduling interpretation is inferred from the ImmediateAction Golden.

## Exclusions confirmation

Respected: no production simulator changes, no runtime contract/adapter changes, no regression manifest or harness changes, no runtime regression promotion, no GrantExtraTurn work, no Timeline/tie-breaking changes, no priority/action-family/interrupt/extra-turn inference, no trace schema change, no Golden/comparator/divergence implementation changes, no video parsing/scraping, no character database work, no AI optimization, and no unrelated UI/refactor work.

## Suggested next milestone

`HSR-RUNTIME-ARCH-042 — ImmediateAction Static Golden Regression Promotion`

Promote the accepted ARCH-041 reviewed static ImmediateAction Golden into the standalone runtime action-session regression lane as the ninth locked reviewed case. Extend the closed manifest grammar/harness only with one explicit ImmediateAction setup and preserve all previous case ordering, fixtures, production semantics, and legacy regression boundaries.

Recommended execution routing: ChatGPT **GPT-5.6 Terra**; Codex reasoning **High** for the deterministic manifest/harness extension and preservation-heavy regression work.
