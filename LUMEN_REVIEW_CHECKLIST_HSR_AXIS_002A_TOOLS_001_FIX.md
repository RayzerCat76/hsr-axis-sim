# LUMEN Review Checklist — HSR-AXIS-002A-TOOLS-001-FIX

## Must pass

- [ ] `python -m pytest -q` passes.
- [ ] Regression manifest passes.
- [ ] Locked manifest is unchanged.
- [ ] No simulator core mechanics changed.
- [ ] No OCR / Bilibili scraping / action auto-classification added.

## Video tool checks

- [ ] CLI supports `--extraction-mode batch`.
- [ ] CLI supports `--extraction-mode per_frame`.
- [ ] Default extraction mode is batch.
- [ ] CLI supports `--ffmpeg-timeout-seconds`.
- [ ] Batch mode uses one ffmpeg process for a range, not one process per timestamp.
- [ ] Per-frame mode uses `-nostdin`, `-hide_banner`, `-loglevel error`, and `-update 1`.
- [ ] `generate_timestamps(0, 16, 0.5)` produces 33 timestamps.
- [ ] Output frame names remain `frames/t_000.0.jpg`, `frames/t_000.5.jpg`, etc.
- [ ] `frame_index.csv` still matches the actual frame files.
- [ ] `draft_trace.json` remains `status=intake_draft` and `replay_ready=false`.

## Real sample smoke check, if `sample1.mov` is available

- [ ] Run 0–16s / 0.5s interval.
- [ ] It completes in reasonable time.
- [ ] It produces 33 frames.
- [ ] It writes worksheet and draft JSON.

## Blockers

- [ ] Any failure to complete the sample1 opening extraction is a blocker for resuming 002A.
