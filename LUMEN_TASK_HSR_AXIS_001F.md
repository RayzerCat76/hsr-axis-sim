# HSR-AXIS-001F — Base-bounded Golden Replay Manifest File Loader

Baseline: HSR-AXIS-001E PASS; pytest 866/866; regression 20/20; trace evidence 2/2.

Objective: add one explicit filesystem boundary for a reviewed Golden Replay manifest without executing its batch plan.

Required contract:
- new downstream `hsr_axis_sim.runtime_golden_manifest_files` package only;
- immutable file spec with canonical relative POSIX manifest path, positive max bytes, and optional pinned manifest SHA-256;
- explicit base directory at load time;
- resolved manifest must remain inside base after symlink resolution and must be a regular file;
- bounded binary read, then delegate exact bytes to accepted 001E `load_golden_replay_manifest_bytes`;
- immutable result with resolved path provenance and complete manifest artifact;
- deterministic text summary only; no batch execution.

Protected: all existing executable packages including `runtime_golden_manifests`; existing data/fixtures/regression behavior.

Excluded: batch execution, directory scanning/discovery, manifest repair/migration/defaults, simulator auto-run, CLI/UI, video extraction, fuzzy comparison, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
