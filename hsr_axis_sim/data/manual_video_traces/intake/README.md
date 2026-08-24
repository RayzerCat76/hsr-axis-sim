# Manual Trace Intake Drafts

This folder stores real manually recorded video trace drafts before they are replay-ready.

`real_video_trace_001_botu_dilemma_3_4_floor12_side1_opening_v0_3.json` is sequence-confirmed but not locked into the regression manifest. It records the corrected opening action order for:

- Video: `【3.4博徒困境】全网首发！0+1风套那刻夏逆属性2金0t砂金！`
- URL: `https://www.bilibili.com/video/BV1CXtVzaEQB?vd_source=ac236634092c9f9a4f4b0169249ce344`
- Scenario: `3.4 博徒困境 第12层 第一面`
- Team: `那刻夏 / 停云 / 佩拉 / 记忆主`
- Pre-combat opener: `佩拉秘技开怪`

Remaining confirmations before replay validation or manifest inclusion:

- Exact targets for each action
- Skill point values and deltas
- Energy values and deltas
- Enemy HP and toughness deltas
- Forced RNG outcomes such as crits, target selection, hit/resist, and similar events
- Exact interrupt, current-turn, companion/summon, and bonus-action semantics

Do not add intake drafts to `hsr_axis_sim/data/regression_manifest.json` until they pass the replay-ready manual trace protocol.
