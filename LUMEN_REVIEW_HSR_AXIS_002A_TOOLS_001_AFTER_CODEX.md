# LUMEN REVIEW — HSR-AXIS-002A-TOOLS-001 After Codex

## Verdict

**Status: NEEDS FIX BEFORE WE RELY ON IT FOR 002A.**

The implementation is directionally correct and all existing tests pass, but the tool is not yet reliable enough for the intended real `sample1.mov` workflow.

## Local test results

From the uploaded package:

```text
python -m pytest -q
273 passed in 3.40s
```

Regression manifest:

```text
Manifest: HSR_AXIS_REGRESSION_BASELINE_001Z
PASS 12/12 golden replays
PASS 2/2 manual checks
PASS 2/2 search scenarios
```

Short smoke run against the real uploaded `sample1.mov`:

```text
start=0, end=3, interval=1
Generated video trace intake package ... (4 frames)
```

So the code path works for a short segment.

## What was implemented correctly

- Added `hsr_axis_sim/tools/video_trace_assistant.py`.
- Added `hsr_axis_sim/tools/video_trace_models.py`.
- Added `test_video_trace_assistant.py`.
- Generates:
  - `frames/`
  - `frame_index.csv`
  - `trace_annotation_worksheet.md`
  - `draft_trace.json`
  - `README.md`
- Keeps the real trace as `intake_draft` and `replay_ready=false`.
- Does **not** update the locked manifest.
- Does **not** pretend to infer targets, SP, energy, HP, toughness, or RNG.
- Does **not** scrape Bilibili or do OCR.

## Blocking issue

The intended command for the real opening segment is roughly:

```bash
python -m hsr_axis_sim.tools.video_trace_assistant \
  --video /mnt/data/sample1.mov \
  --trace-name real_video_trace_001_botu_dilemma_3_4_floor12_side1_opening \
  --start 0 \
  --end 16 \
  --interval 0.5 \
  --output-dir /mnt/data/hsr_video_trace_tool_run_full \
  --source-platform bilibili \
  --source-url "https://www.bilibili.com/video/BV1CXtVzaEQB" \
  --video-title "【3.4博徒困境】全网首发！0+1风套那刻夏逆属性2金0t砂金！" \
  --uploader unknown \
  --notes "Opening sequence only; intake draft; not replay-ready."
```

In my sandbox, the full 0–16s / 0.5s run did **not** finish within several minutes. It only partially wrote frames before the command timed out. A short 0–3s smoke run did finish.

This means the MVP is structurally correct, but the extraction implementation is too fragile / slow for the actual workflow.

## Likely cause

The current implementation launches one `ffmpeg` process per timestamp. For a 2880×1800, 60fps clip, this is unnecessarily expensive and appears unreliable around longer extraction batches in this environment.

Current risk:

- Full opening extraction may hang or take too long.
- There is no per-frame timeout exposed through CLI.
- There is no faster batch-extraction mode.
- The command does not use a single-pass `fps` extraction path.

## Required fix before resuming 002A

Create **HSR-AXIS-002A-TOOLS-001-FIX**:

- Keep the existing output format stable.
- Add a faster batch extraction mode.
- Keep per-frame extraction as fallback/debug mode.
- Add CLI option for extraction mode.
- Add timeout/error handling.
- Add tests that do not require real video.
- Do not change simulator core.
- Do not update the regression manifest.

## Acceptance criteria

After the fix, this should complete reliably on a local `sample1.mov`:

```bash
python -m hsr_axis_sim.tools.video_trace_assistant \
  --video /path/to/sample1.mov \
  --trace-name real_video_trace_001_botu_dilemma_3_4_floor12_side1_opening \
  --start 0 \
  --end 16 \
  --interval 0.5 \
  --output-dir data/video_trace_intake/sample1_botu_dilemma_opening \
  --source-platform bilibili \
  --source-url "https://www.bilibili.com/video/BV1CXtVzaEQB" \
  --video-title "【3.4博徒困境】全网首发！0+1风套那刻夏逆属性2金0t砂金！" \
  --uploader unknown \
  --notes "Opening sequence only; intake draft; not replay-ready."
```

Expected frame count for 0 to 16 inclusive at 0.5 interval: **33 frames**.
