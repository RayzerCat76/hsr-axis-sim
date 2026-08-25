# HSR-RUNTIME-ARCH-021 — Reviewed Static Resource Observation Golden Fixture

## Current confirmed state

- HSR-RUNTIME-ARCH-020 — PASS and merged to `main` at `97d2199c2f5a38d8b2d8475c5f5897a7698c3abe`.
- Complete pytest: `1090 / 1090 passed`.
- Legacy locked regression: `20 / 20 passed`.
- Trace evidence: `2 / 2 passed`.
- Runtime action-session Golden regression: `1 / 1 passed`.
- Current blocker: none.

## Objective

Add one independently reviewed static schema-v1 Golden expectation for the production ARCH-020 clamped-energy observation path, proving the full Action -> production event -> legacy adapter -> capture/stitch -> ARCH-016 Golden chain without using the simulator/exporter under test to generate expected bytes.

## Required implementation

1. Add one compact canonical static expected trace under `hsr_axis_sim/data/runtime_golden_fixtures/`.
2. The expected semantic scenario is fixed and contract-only:
   - actor ID `resource-actor`;
   - target ID `resource-target`;
   - action ID `reviewed-clamped-energy`;
   - target starts at Energy `90`, max Energy `100`;
   - one `GainEnergy(target_ids=["resource-target"], amount=25)` effect;
   - action `ends_turn=False`.
3. The static expected records are exactly:
   - sequence 0 `ACTION_START`;
   - sequence 1 `ENERGY_CHANGED`;
   - sequence 2 `ACTION_END`.
4. The resource observation must explicitly contain:
   - `before=90`;
   - `after=100`;
   - `requested_delta=25`;
   - `applied_delta=10`;
   - `cap=100`;
   - `resource_kind=ENERGY`;
   - `scope=UNIT`;
   - `unit_id=resource-target`.
5. Expected bytes must be manually specified/reviewed, compact canonical UTF-8 JSON, no trailing newline, and pinned by exact byte size + SHA-256.
6. Tests may strict-load and compare the static expected bytes but must not generate authoritative expected bytes at test runtime through simulator execution, legacy adaptation, runtime trace builders/exporters, or canonical serialization helpers.
7. Execute the real production scenario through accepted ARCH-016 and prove it matches the static expected artifact.
8. Add one deliberate production-input divergence that changes the resource observation while preserving the same expected artifact, and assert the accepted first-divergence path identifies the first changed resource field deterministically.
9. Keep the fixture outside both regression manifests. No regression promotion in ARCH-021.

## Acceptance criteria

- Static fixture is exact compact canonical schema v1 and digest-pinned.
- Fixture is demonstrably independent from the runtime path under test.
- ARCH-016 production `GainEnergy` scenario matches it.
- Expected resource record preserves requested/applied clamp distinction.
- A deliberate resource-input change returns a normal Golden mismatch with accepted first-divergence provenance.
- No simulator/adapter/schema/Golden-validator implementation change.
- No regression manifest change.
- Full validation suite passes.

## Required tests

- exact fixture byte size/SHA and no trailing newline;
- strict loader digest/canonical-form PASS;
- exact 3-record order and resource payload fields;
- schema-v1 record `numeric_values == {}`;
- ARCH-016 production scenario PASS;
- actual target reaches Energy 100;
- deliberate changed resource input reports first resource divergence;
- fixture absent from legacy and runtime regression manifests;
- AST/source guard forbids expected-artifact generation in ARCH-021 test source;
- ARCH-017 fixture digest unchanged;
- production LIFO unchanged.

## Protected areas / exclusions

Do not change:
- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- runtime contracts/export/load/compare/divergence/Golden implementation;
- existing Golden fixtures;
- legacy/runtime regression manifests;
- Tingyun evidence/report artifacts;
- AV/timeline semantics;
- FIFO/LIFO semantics.

No SP Golden case, trigger Golden case, regression promotion, schema v2, automatic fixture generation, or video/replay automation in ARCH-021.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Execution routing

- ChatGPT model: GPT-5.6 Sol
- Codex reasoning: High if used; Codex is optional.

## Final report

Update `hsr_axis_sim/LUMEN_RESULT.md` with exact fixture identity, implementation/tests, exact validation results, warnings/errors, exclusion confirmation, unresolved issues, and suggested next milestone.
