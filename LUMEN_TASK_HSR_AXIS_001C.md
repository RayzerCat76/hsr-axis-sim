# HSR-AXIS-001C — File-backed Golden Replay Case Runner

Baseline: HSR-AXIS-001B PASS; pytest 831/831; regression 20/20; trace evidence 2/2.

Objective: add a downstream file-case boundary around the accepted in-memory Golden Replay validator.

Required contract:
- new `hsr_axis_sim.runtime_golden_cases` package only;
- immutable case definition with an accepted `GoldenReplayValidationConfig` plus canonical relative expected/actual paths;
- explicit base directory supplied at run time;
- both resolved files must remain inside that base directory, including after symlink resolution;
- bounded binary reads, then delegation to `validate_golden_replay_bytes`;
- immutable run result with resolved path provenance;
- deterministic text wrapping the accepted 001B report.

Protected: all existing executable packages including `runtime_golden_replays`; existing data/fixtures/regression behavior.

Excluded: directory scanning, batch manifest, simulator auto-run, CLI/UI, video extraction, fuzzy comparison, repair/realignment, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
