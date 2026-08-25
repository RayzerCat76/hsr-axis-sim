# HSR-RUNTIME-ARCH-038 — Reviewed Static ChangeSpeed Golden Fixture

## Status

PASS — proceed

## Implementation summary

- Added one independently reviewed compact static Golden expectation for a deterministic positive production `ChangeSpeed` action.
- The reviewed fixture uses explicit test inputs only:
  - actor/target `speed-actor`;
  - initial speed `100`;
  - initial AV `80`;
  - `ChangeSpeed(new_speed=200)`;
  - final speed `200`;
  - final AV `40.0`.
- The expected trace is manually authored from the accepted schema/runtime observation contracts and committed as static bytes. It is not generated from the simulator, adapter, exporter, stitcher, or Golden pipeline at test runtime.
- The fixture contains exactly three contiguous records: `ACTION_START -> SPEED_CHANGED -> ACTION_END`.
- The speed observation locks both raw `legacy_data` and typed `payload["speed_change"]` with exact before/after speed and AV values.
- Production validation runs one real production `Action` through accepted ARCH-016 `run_action_session_validation` against the static expected bytes.
- A controlled `new_speed=160` run proves deterministic mismatch behavior with final speed `160` and AV `50.0`.
- Existing comparator semantics are preserved. Because mapping keys are compared in sorted order and `legacy_data` precedes `speed_change`, the accepted first divergence is record `1`, path `/event/payload/legacy_data/after_av`, expected `40.0`, actual `50.0`. The focused test separately verifies the corresponding typed `speed_change` differences.
- No regression promotion is included in this milestone.
- No production code, runtime contract, adapter, loader/exporter/comparator/divergence/Golden implementation, schema, or manifest is changed.

## Static fixture identity

- File: `hsr_axis_sim/data/runtime_golden_fixtures/arch_038_reviewed_change_speed_expected.json`
- Size: **2604 bytes**
- SHA-256: **`c23b34e0afffdfe4bee53d028e5ff21d946623300b169ba57e5ddfb69478df2a`**
- Canonical form: compact UTF-8 JSON
- Trailing newline: none
- Trace ID: `arch-038-reviewed-static-expected`
- Fixture ID: `arch-038-reviewed-static-change-speed`
- Construction metadata: `manual-reviewed`

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_038.md`
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_038_reviewed_change_speed_expected.json`
- `hsr_axis_sim/tests/test_runtime_arch_038_static_change_speed_golden_fixture.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`

## Tests added

Focused ARCH-038 coverage proves:

- exact 2604-byte fixture identity and pinned SHA-256;
- no trailing newline and compact canonical form;
- strict digest-matching loader acceptance;
- unchanged schema name/version and contiguous `0,1,2` sequence;
- exact event order `ACTION_START -> SPEED_CHANGED -> ACTION_END`;
- exact action/actor/target/event-ID provenance;
- exact raw `legacy_data` and typed `speed_change` payload;
- empty schema-v1 `numeric_values` for all three records;
- real ARCH-016 production ChangeSpeed matches the reviewed static fixture;
- final production state is speed `200`, AV `40.0`, cursor `(3,3)`;
- controlled `new_speed=160` produces speed `160`, AV `50.0` and the exact accepted first-divergence path/value;
- compared typed `speed_change` payloads retain exact before values and deterministic changed after values;
- test source contains no runtime expected-generation path;
- ARCH-038 fixture is absent from both regression manifests;
- all seven prior reviewed static fixture byte identities remain exact;
- runtime action-session regression remains `7/7`;
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

GitHub Actions `HSR Axis Sim Validation`, PR #43, run #216, job `97700323840`:

- compile: **PASS**;
- pytest: **1538 passed in 9.46s**;
- legacy locked regression: **20/20**;
- trace evidence: **2/2**;
- standalone runtime action-session Golden regression: **7/7**.

The seven already-promoted runtime Golden cases remained unchanged and PASS. The new ARCH-038 fixture is intentionally not part of that manifest yet.

## Locked areas confirmed unchanged

- `hsr_axis_sim/sim/**` unchanged.
- `hsr_axis_sim/runtime_contracts/**` unchanged.
- `hsr_axis_sim/runtime_adapters/**` unchanged.
- loaders/exporters/comparators/divergence/Golden implementation unchanged.
- `hsr_axis_sim/data/regression_manifest.json` unchanged.
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` unchanged at seven cases.
- All seven prior reviewed static Golden fixtures remain byte-identical.
- AdvanceAction, DelayAction, and ChangeSpeed production semantics remain unchanged.
- ImmediateAction and GrantExtraTurn remain unchanged.
- Trace schema version remains `1.0`.
- Production LIFO compatibility remains unchanged.

## Warnings / errors

- No compile, pytest, legacy-regression, trace-evidence, or runtime-action-session-regression failure occurred.
- Nonblocking GitHub Actions warning remains: `actions/checkout@v4` and `actions/setup-python@v5` target Node 20 and are forced onto Node 24.
- Upstream action setup emits Node `punycode` / `url.parse()` deprecation notices; these are unrelated to simulator correctness and were already present before ARCH-038.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-038 acceptance.

The new ChangeSpeed fixture is intentionally not yet promoted into the standalone runtime action-session regression manifest. ImmediateAction and GrantExtraTurn still lack equivalent runtime observation contracts.

The Master Bible summary remains historically stale relative to the current narrow runtime frontier; this milestone intentionally did not broaden scope into governance synchronization.

## Exclusions confirmation

Respected: no regression promotion, no production ChangeSpeed change, no non-positive-speed Golden case, no ImmediateAction observation, no GrantExtraTurn observation, no generic action-axis abstraction, no new production input validation, no video parsing, no scraping, no character database expansion, no AI optimization, and no unrelated UI/refactor work.

## Suggested next milestone

`HSR-RUNTIME-ARCH-039 — ChangeSpeed Golden Regression Promotion`

Promote only the accepted ARCH-038 reviewed static ChangeSpeed fixture into the existing standalone `runtime_action_session_regression` lane, mirroring the accepted Advance/Delay promotion pattern. Preserve the legacy regression manifest, production semantics, fixture bytes, trace schema, comparator semantics, and LIFO behavior.

Recommended execution routing: ChatGPT **GPT-5.6 Terra**; Codex reasoning **Medium** if Codex is used.
