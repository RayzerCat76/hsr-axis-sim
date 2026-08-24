# HSR-RUNTIME-ARCH-019 — Runtime Resource Change Observation Contract

## Current confirmed state

- HSR-RUNTIME-ARCH-018 — PASS and merged to `main` at `f28afde90bbfeb9c87550d6739e988e6148cce86`.
- Complete pytest: `1052 / 1052 passed`.
- Legacy locked regression: `20 / 20 passed`.
- Trace evidence: `2 / 2 passed`.
- Runtime action-session Golden regression: `1 / 1 passed`.
- Current blocker: none.

## Objective

Define the smallest schema-v1-compatible runtime observation vocabulary for existing production energy and skill-point state changes without yet changing simulator emission, legacy-event adaptation, trace schema, or Golden fixtures.

## Required implementation

1. Extend `RuntimeEventType` with exactly:
   - `ENERGY_CHANGED`;
   - `SKILL_POINTS_CHANGED`.
2. Add immutable resource observation vocabulary under `runtime_contracts`:
   - `RuntimeResourceKind`: `ENERGY`, `SKILL_POINTS`;
   - `RuntimeResourceScope`: `UNIT`, `TEAM`;
   - frozen `RuntimeResourceChangeObservation`.
3. Observation fields are exactly:
   - `resource_kind`;
   - `scope`;
   - `before`;
   - `after`;
   - `requested_delta`;
   - `applied_delta`;
   - `cap`;
   - `unit_id`.
4. Contract invariants:
   - all numeric fields are finite `int`/`float`, never bool;
   - `applied_delta == after - before`;
   - `ENERGY` requires `UNIT` scope and a non-empty `unit_id`;
   - `SKILL_POINTS` requires `TEAM` scope and `unit_id is None`;
   - `SKILL_POINTS` numeric values are integers;
   - no additional sign/range/clamp/game-value assumptions are introduced.
5. Provide deterministic payload conversion using plain canonicalizable data only.
6. Prove schema v1 can export and strict-load the new event types while `record.numeric_values` remains empty.
7. Document that resource values live in `RuntimeEvent.payload` in v1; moving them into `RuntimeTraceRecord.numeric_values` would require separate schema work.
8. Do not add legacy-event mappings or simulator emissions in ARCH-019.

## Acceptance criteria

- New resource observations are immutable and deterministic.
- Invalid scope/unit/type/delta consistency is rejected.
- Both event types round-trip through accepted exporter + strict loader under schema v1.
- Existing runtime trace schema identity remains `hsr_runtime_trace` v1.0.
- Existing simulator and adapter behavior remain unchanged.
- All existing validation lanes remain green.

## Required tests

- valid energy observation payload;
- valid skill-point observation payload;
- frozen dataclass behavior and payload immutability once wrapped by `RuntimeEvent`;
- boolean/NaN/Infinity invalid numeric rejection;
- inconsistent `applied_delta` rejection;
- ENERGY scope/unit-id rejection cases;
- SKILL_POINTS scope/unit-id/non-integer rejection cases;
- compact export -> strict load round trip for `ENERGY_CHANGED`;
- compact export -> strict load round trip for `SKILL_POINTS_CHANGED`;
- loaded v1 records still have empty `numeric_values`;
- preservation tests: no simulator/adapter imports of the new resource contract, locked fixture SHA unchanged, production LIFO unchanged.

## Protected areas

Do not modify executable behavior in:
- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- `hsr_axis_sim/runtime_loaders/**`;
- accepted exporter/comparator/divergence/Golden/session/regression packages;
- legacy or runtime regression manifests;
- ARCH-017 fixture;
- research/reference artifacts.

## Explicit exclusions

No production event emission, no legacy mapping, no SP/energy effect semantic change, no AV/speed/advance/delay observation, no trace schema v2, no record-level numeric values, no file I/O, no Golden fixture update, no replay/video work, no FIFO/LIFO change.

## Commands to run

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

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, implementation/files/tests, exact commands/results, warnings/errors, unresolved issues, protected/exclusion confirmation, and suggested next milestone.
