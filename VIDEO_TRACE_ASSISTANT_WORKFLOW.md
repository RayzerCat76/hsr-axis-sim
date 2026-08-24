# Video Trace Assistant Workflow

## Goal
Reduce manual work when turning gameplay videos into replay fixtures.

## Flow

1. Put source video in:

```text
data/video_trace_sources/sample1.mov
```

2. Run the assistant:

```bash
python -m hsr_axis_sim.tools.video_trace_assistant \
  --video data/video_trace_sources/sample1.mov \
  --trace-name real_video_trace_001_botu_dilemma_3_4_floor12_side1_opening \
  --start 0 \
  --end 16 \
  --interval 0.5 \
  --output-dir data/video_trace_intake/sample1_botu_dilemma_opening \
  --source-platform bilibili \
  --source-url "https://www.bilibili.com/video/BV1CXtVzaEQB" \
  --video-title "【3.4博徒困境】全网首发！0+1风套那刻夏逆属性2金0t砂金！" \
  --uploader "unknown" \
  --notes "Opening sequence only; intake draft; not replay-ready."
```

3. Open `trace_annotation_worksheet.md`.

4. Fill human-confirmed action fields:

```text
step, timestamp, actor, action, target, SP before/after, energy before/after, HP, toughness, forced RNG
```

5. Only after those fields are confirmed, resume 002A and convert the intake draft into a real manual video trace fixture.

## Confirmed opening sequence v0.3

```text
Pre: 佩拉秘技开怪
1: 停云终结技
2: 佩拉战技
3: 记忆主战技
4: 停云战技
5: 佩拉终结技
6: 那刻夏终结技
7: 那刻夏普攻 + 额外战技
8: 迷迷拉条那刻夏
9: 那刻夏战技 + 额外战技
```

## Still missing

- targets;
- SP before/after;
- energy before/after;
- enemy HP changes;
- toughness changes;
- forced RNG;
- exact meaning of 迷迷拉条那刻夏 in engine terms.
