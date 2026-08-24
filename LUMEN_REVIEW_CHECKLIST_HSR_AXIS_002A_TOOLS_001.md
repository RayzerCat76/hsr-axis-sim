# Lumen Review Checklist — HSR-AXIS-002A-TOOLS-001

Use this after Codex finishes.

## Hard pass/fail

- [ ] Existing tests still pass.
- [ ] New tests pass.
- [ ] No simulator core mechanics were changed.
- [ ] Locked regression manifest was not changed.
- [ ] No fake completed real trace was added.
- [ ] Draft trace is marked `status: intake_draft`.
- [ ] Draft trace has `replay_ready: false`.

## CLI / output

- [ ] CLI accepts local video path, start, end, interval, trace-name, output-dir, and metadata.
- [ ] Output directory contains `frames/`, `frame_index.csv`, `trace_annotation_worksheet.md`, `draft_trace.json`, and `README.md`.
- [ ] `frame_index.csv` has required columns.
- [ ] Worksheet has a human-fillable action table.
- [ ] Worksheet includes confirmed v0.3 sequence.
- [ ] Missing fields checklist is explicit.

## Video handling

- [ ] Uses ffmpeg or a clearly documented backend.
- [ ] Missing ffmpeg error is clear and actionable.
- [ ] Tests do not require real video files.
- [ ] Does not silently skip extraction failures.

## Trace quality

- [ ] The known opening sequence is stored as declared/intake notes, not as validated replay steps unless fields are complete.
- [ ] Targets/SP/energy/toughness/RNG are placeholders if not confirmed.
- [ ] There is no claim that this completes 002A.

## Result file

- [ ] `LUMEN_RESULT.md` lists files changed.
- [ ] `LUMEN_RESULT.md` lists commands run.
- [ ] `LUMEN_RESULT.md` explains how to run on `sample1.mov`.
- [ ] `LUMEN_RESULT.md` states limitations and next step.
