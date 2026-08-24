# LUMEN REVIEW CHECKLIST — HSR-AXIS-001R

## Task expected

**HSR-AXIS-001R: Manual Video Golden Replay Protocol MVP**

This task should create a no-network, manual transcription protocol for video-style golden replays. It should add metadata/linting/templates/samples, not actual Bilibili scraping or AI search.

## Must pass locally

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q hsr_axis_sim/tests
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
python -m hsr_axis_sim.sim.replay_lint hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
python -m hsr_axis_sim.sim.replay hsr_axis_sim/data/manual_video_traces/samples/manual_video_trace_sample_mvp.json
```

## Required checks

### Scope control

- [ ] No Bilibili scraping.
- [ ] No video download.
- [ ] No OCR.
- [ ] No network requests.
- [ ] No AI search or beam search.
- [ ] No combat-engine rewrite.
- [ ] Existing golden replays still pass.

### Manual video trace structure

- [ ] `hsr_axis_sim/data/manual_video_traces/README.md` exists.
- [ ] `templates/manual_video_trace_template.json` exists.
- [ ] `samples/manual_video_trace_sample_mvp.json` exists.
- [ ] Sample has `trace_type: manual_video_trace`.
- [ ] Sample has `source`, `assumptions`, `builds`, `transcription`, and `steps`.
- [ ] Sample is still compatible with existing `ReplayValidator`.

### Linter behavior

- [ ] `hsr_axis_sim/sim/replay_lint.py` exists.
- [ ] Linter catches missing source metadata.
- [ ] Linter catches missing expected actor on normal steps unless explicitly allowed.
- [ ] Linter catches invalid `forced_rng` type.
- [ ] Linter does not fail existing non-manual replay files just because they lack video metadata.
- [ ] CLI returns 0 for valid manual trace and nonzero for invalid manual trace.

### Replay behavior

- [ ] Manual video trace sample passes lint.
- [ ] Manual video trace sample passes existing replay validation.
- [ ] Existing golden replay CLI checks still pass.

## Expected verdict logic

Pass 001R only if:

- full tests pass,
- existing golden replays pass,
- manual video trace sample passes both lint and replay validation,
- no web/video/OCR/live parsing was added,
- combat core was not changed beyond harmless metadata handling.

If Codex tries to fetch or parse a real video in this task, mark it as scope failure and request a fix.
