# HSR-AXIS-001D — Deterministic Golden Replay Batch Runner

Baseline: HSR-AXIS-001C PASS; pytest 843/843; regression 20/20; trace evidence 2/2.

Objective: execute an explicit immutable ordered tuple of accepted `GoldenReplayFileCase` values under one supplied base directory.

Required contract:
- new downstream `hsr_axis_sim.runtime_golden_batches` package only;
- immutable non-empty batch plan with `batch_id` and ordered case tuple;
- replay IDs must be unique inside a batch;
- execute cases exactly once in declared tuple order through `run_golden_replay_file_case`;
- replay mismatches are ordinary results and do not stop later cases;
- file/config/load exceptions propagate immediately at the exact failing case; no partial batch result is returned;
- immutable complete batch result, deterministic counts and first mismatching case index;
- deterministic text in declared order wrapping accepted 001C case reports.

Protected: all existing executable packages including `runtime_golden_replays` and `runtime_golden_cases`; existing data/fixtures/regression behavior.

Excluded: JSON/file manifest loading, directory discovery, parallel execution, retry, error swallowing/aggregation, simulator auto-run, CLI/UI, video extraction, fuzzy comparison, repair/realignment, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
