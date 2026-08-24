# HSR-AXIS-002A-TOOLS-001 — Video Trace Assistant MVP

## Purpose
Build a small offline helper tool that turns a local gameplay video into a human-annotatable trace intake package.

This does **not** complete 002A. It supports 002A by reducing manual work for real video traces.

## Scope
The tool should take a local `.mov` / `.mp4` file and generate:

1. Extracted frames at a fixed interval.
2. A frame index CSV.
3. A Markdown annotation worksheet.
4. A draft manual-video-trace JSON shell.
5. A CLI command that can be reused for future videos.

## Non-goals
Do **not**:

- download from Bilibili;
- scrape Bilibili;
- run OCR;
- auto-classify skills or characters;
- modify simulator core mechanics;
- add the draft trace to the locked regression manifest;
- pretend the generated draft is replay-ready.

The output is only an intake draft for human confirmation.

## Context
We are blocked on 002A because we need a real manual video trace. The first candidate is:

- Game: Honkai: Star Rail
- Version/context: 3.4 博徒困境 第12层 第一面
- Bilibili: BV1CXtVzaEQB
- Team: 那刻夏 / 停云 / 佩拉 / 记忆主
- Pre-battle: 佩拉秘技开怪
- Confirmed opening sequence v0.3:
  1. 停云终结技
  2. 佩拉战技
  3. 记忆主战技
  4. 停云战技
  5. 佩拉终结技
  6. 那刻夏终结技
  7. 那刻夏普攻 + 额外战技
  8. 迷迷拉条那刻夏
  9. 那刻夏战技 + 额外战技

But SP, targets, energy, toughness, damage, and RNG are not yet fully confirmed.

## Recommended implementation
Create:

```text
hsr_axis_sim/
  tools/
    __init__.py
    video_trace_assistant.py
    video_trace_models.py

data/
  video_trace_intake/
    README.md
    sample1_botu_dilemma_opening/
      # generated output should go here, but do not commit large extracted frames unless the existing project convention allows it

tests/
  test_video_trace_assistant.py
```

## CLI examples

```bash
python -m hsr_axis_sim.tools.video_trace_assistant \
  --video data/video_trace_sources/sample1.mov \
  --trace-name real_video_trace_001_botu_dilemma_3_4_floor12_side1_opening \
  --start 0 \
  --end 16 \
  --interval 0.5 \
  --output-dir data/video_trace_intake/sample1_botu_dilemma_opening
```

Optional metadata fields:

```bash
  --source-platform bilibili \
  --source-url "https://www.bilibili.com/video/BV1CXtVzaEQB" \
  --video-title "【3.4博徒困境】全网首发！0+1风套那刻夏逆属性2金0t砂金！" \
  --uploader "unknown" \
  --notes "Opening sequence only; not replay-ready."
```

## Required outputs
For a run, generate:

```text
output-dir/
  frames/
    t_000.0.jpg
    t_000.5.jpg
    ...
  frame_index.csv
  trace_annotation_worksheet.md
  draft_trace.json
  README.md
```

### frame_index.csv columns

```text
frame_id,timestamp_seconds,timestamp_label,frame_path,annotation_status,notes
```

### trace_annotation_worksheet.md should include

- source metadata;
- video range;
- frame list;
- blank action table for humans to fill;
- known opening sequence v0.3 as reference;
- missing fields checklist.

### draft_trace.json should include

- trace name;
- source metadata;
- units/team notes;
- confirmed opening sequence as `declared_sequence` or `notes`, not as validated replay steps unless fields are complete;
- `status: intake_draft`;
- `replay_ready: false`;
- placeholders for targets, SP, energy, toughness, damage, and forced RNG.

## Video extraction backend
Use `ffmpeg` through `subprocess` if available.

Rules:

- If `ffmpeg` is missing, fail clearly with a helpful message.
- Do not silently skip frame extraction.
- Keep tests independent of real videos by mocking subprocess or testing pure output writers.
- Do not add heavy dependencies unless already present.

## Tests required
Add tests for:

1. CLI argument parsing / config model.
2. Timestamp generation for start/end/interval.
3. CSV writer output.
4. Worksheet writer includes known sequence and missing fields.
5. Draft JSON has `status=intake_draft` and `replay_ready=false`.
6. ffmpeg missing error is clear.
7. No changes to existing regression manifest.

## LUMEN_RESULT.md
Codex must update or create `LUMEN_RESULT.md` with:

1. files changed;
2. commands run;
3. test results;
4. what the tool can do now;
5. what it intentionally does not do;
6. how to run it on `sample1.mov`;
7. next recommended step.

## Acceptance criteria
This task passes if:

- all existing tests still pass;
- new tests pass;
- a local video can be processed into frames + CSV + worksheet + draft JSON;
- the draft trace is clearly marked as not replay-ready;
- no simulator core mechanics were changed;
- no fake trace is added to the locked manifest.
