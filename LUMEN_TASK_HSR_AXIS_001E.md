# HSR-AXIS-001E — Strict Golden Replay Manifest Artifact

Baseline: HSR-AXIS-001D PASS; pytest 853/853; regression 20/20; trace evidence 2/2.

Objective: define a deterministic canonical JSON artifact that reconstructs an accepted `GoldenReplayBatchPlan` without executing it.

Required contract:
- new downstream `hsr_axis_sim.runtime_golden_manifests` package only;
- fixed schema name `hsr_golden_replay_manifest`, version `1.0`;
- compact canonical UTF-8 JSON exact bytes only;
- top-level exact fields: `schema_name`, `schema_version`, `batch_id`, `cases`;
- each ordered case exact fields: `replay_id`, `expected_sha256`, `expected_relative_path`, `actual_relative_path`, `canonical_form_policy`, `max_bytes`;
- strict duplicate-key rejection and exact field/type validation;
- reconstruct accepted validation config, file case, and batch plan models rather than duplicating their semantic validation;
- deterministic build artifact with SHA-256;
- strict byte loader with explicit max-byte limit and optional expected SHA-256 verification;
- loader rejects noncanonical formatting rather than normalizing it.

Protected: all existing executable packages including `runtime_golden_batches`; existing data/fixtures/regression behavior.

Excluded: manifest file I/O, batch execution, directory discovery, defaults/repair/migration, metadata extensions, simulator auto-run, CLI/UI, video extraction, fuzzy comparison, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
