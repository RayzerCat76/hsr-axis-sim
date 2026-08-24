# HSR-AXIS-002A Opening Sequence Correction v0.3

Source video:
- Title: 【3.4博徒困境】全网首发！0+1风套那刻夏逆属性2金0t砂金！
- URL: https://www.bilibili.com/video/BV1CXtVzaEQB?vd_source=ac236634092c9f9a4f4b0169249ce344
- Scenario: 3.4 博徒困境 第 12 层 第一面
- Team order confirmed by Ray: 那刻夏 / 停云 / 佩拉 / 记忆主
- Combat opener confirmed by Ray: 佩拉秘技开怪

## Correct opening sequence confirmed by Ray

Pre-combat:
0. 佩拉秘技开怪

Opening action sequence:
1. 停云终结技
2. 佩拉战技
3. 记忆主战技
4. 停云战技
5. 佩拉终结技
6. 那刻夏终结技
7. 那刻夏普攻 + 额外战技
8. 迷迷拉条那刻夏
9. 那刻夏战技 + 额外战技

## Important modeling notes

- This supersedes the earlier incorrect draft that placed 那刻夏战技 before 佩拉终结技.
- Step 5 should be treated as an ultimate interrupt window before or during the opening of 那刻夏's action opportunity, depending on exact replay timing.
- `那刻夏普攻 + 额外战技` and `那刻夏战技 + 额外战技` should be recorded as trace-level observed actions first. Do not force the simulator to model these as ordinary turns until the character-specific kit logic is mapped.
- `迷迷拉条那刻夏` should be recorded as a semantic action/event from 记忆主's summon/companion. The exact internal trigger can be implemented later.

## Still needed before replay-ready validation

For each step, confirm if possible:
- exact target
- SP before -> after
- energy before -> after
- enemy HP / toughness before -> after
- whether any hit crits
- whether debuffs land or are resisted
- whether the action occurs inside an interrupt window / current-turn continuation / extra turn

This v0.3 trace is for intake and sequence correction, not a locked manifest baseline yet.
