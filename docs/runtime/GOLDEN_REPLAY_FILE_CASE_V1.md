# Golden Replay File Case V1

`HSR-AXIS-001C` adds an explicit file boundary downstream of the accepted in-memory Golden Replay validator.

## Case definition

`GoldenReplayFileCase` contains:
- one accepted `GoldenReplayValidationConfig`;
- `expected_relative_path`;
- `actual_relative_path`.

Paths use canonical relative POSIX syntax. Absolute paths, parent traversal, backslashes, and noncanonical spellings such as `./x` or repeated separators are rejected.

## Execution boundary

`run_golden_replay_file_case(case, base_directory=...)` requires one explicit base directory. The runner:
1. resolves the base directory;
2. resolves each reviewed relative case path;
3. rejects any resolved target outside the base directory, including symlink escape;
4. requires regular files;
5. performs bounded binary reads using the accepted validation byte limit;
6. delegates trace loading/comparison/divergence semantics to `validate_golden_replay_bytes`.

The file runner does not parse or validate runtime trace semantics itself.

## Result

`GoldenReplayFileRunResult` is immutable and preserves:
- the file case;
- resolved absolute base directory;
- resolved expected path;
- resolved actual path;
- the complete accepted `GoldenReplayValidationResult`.

`render_golden_replay_file_case_text` emits path provenance and then embeds the deterministic 001B report.

## Scope boundary

V1 performs no directory scanning, automatic discovery, batch manifest execution, simulator auto-run, CLI/UI, video extraction, repair, fuzzy comparison, realignment, new game mechanics, or FIFO/LIFO changes.
