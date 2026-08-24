# HSR-AXIS-001B — Deterministic Golden Replay Validator

Baseline: ARCH-006 PASS; pytest 819/819; regression 20/20; trace evidence 2/2.

Objective: compose the accepted strict loader, ARCH-005 comparator, and ARCH-006 first-divergence reporter into one read-only Golden Replay validation sidecar.

Required contract:
- expected trace bytes require a pinned SHA-256 match;
- actual trace bytes require strict canonical loading but no pre-known digest;
- comparison is delegated to `compare_runtime_trace_documents`;
- first divergence is delegated to `build_first_divergence_report`;
- immutable config/result models and deterministic text output;
- first test replay is manually constructed from explicit runtime events and contains no hidden game values.

Protected: simulator, runtime contracts/adapters/exports/loaders/comparators/divergence, regression, search, bindings, existing fixtures.

Excluded: simulator auto-wiring, CLI/UI, batch manifest runner, video extraction, fuzzy/tolerance comparison, realignment/repair, new HSR mechanics, FIFO/LIFO changes.

Validation:
`python -m compileall -q hsr_axis_sim`
`python -m pytest -q`
`python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
`python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`

Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI results.
