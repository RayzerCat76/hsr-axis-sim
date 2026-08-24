# HSR-AXIS-001G — Manifest-backed Golden Replay Batch Runner

Baseline: HSR-AXIS-001F PASS; pytest 892/892; regression 20/20; trace evidence 2/2.

Objective: compose the accepted manifest-file boundary with the accepted deterministic batch runner under one explicit common base directory.

Required contract:
- new downstream `hsr_axis_sim.runtime_golden_manifest_runs` package only;
- input is an accepted `GoldenReplayManifestFileSpec` plus explicit base directory;
- first load exactly one reviewed manifest through HSR-AXIS-001F;
- execute exactly the reconstructed HSR-AXIS-001D batch plan under the same resolved base directory;
- immutable result preserves complete 001F manifest-file provenance and complete 001D batch result;
- returned result must prove plan identity and base-directory alignment between load and execution;
- replay mismatches remain completed batch results; operational failures propagate exactly as accepted downstream contracts define;
- deterministic text wraps the accepted 001F provenance text and accepted 001D batch text without reimplementing either semantic layer.

Protected: all existing executable packages including `runtime_golden_manifest_files` and `runtime_golden_batches`; existing data/fixtures/regression behavior.

Excluded: manifest discovery/scanning, simulator auto-generation, retries, parallelism, partial-error aggregation, CLI/UI, video extraction, repair/migration/defaults, fuzzy comparison, new HSR mechanics, FIFO/LIFO changes.

Validation uses the standard compile, full pytest, locked regression, and trace-evidence commands. Update `hsr_axis_sim/LUMEN_RESULT.md` after real CI.
