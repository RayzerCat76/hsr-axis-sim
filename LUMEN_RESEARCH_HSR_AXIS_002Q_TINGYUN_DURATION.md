# Lumen Research — HSR-AXIS-002Q Tingyun Ultimate Duration Boundary

## Research question

When Tingyun applies the Ultimate DMG buff, what event consumes its two-turn duration, especially when the buff is applied during the target's already-active turn?

## Result classification

### Confirmed from fixed structured sources

- The Ultimate targets one ally.
- It restores Energy.
- Its DMG increase lasts **2 turns**.
- The complete Lv.1–15 magnitude table is already captured by HSR-AXIS-002N-FIX.

These sources do **not** expose the runtime countdown boundary.

### Accepted project-domain correction

Ray corrected the project assumption:

> Tingyun Ultimate duration settles when the target **enters a turn**, not when that turn ends.

For audit purposes this is recorded as:

`accepted_project_domain_correction_pending_independent_frame_verification`

It replaces the obsolete 002Q premise. It must not be silently upgraded to `independently_video_verified`.

### Bilibili research

Candidate located:

- BV: `BV1yz4y1t79s`
- Title: `【崩坏星穹铁道】景元深度测评：光锥伤害对比+停云布洛妮娅对景元的提升幅度计算+配队思路+体力规划思路`
- URL: `https://www.bilibili.com/video/BV1yz4y1t79s`

The title and BV were recovered from a fixed Bilibili trend archive. The Bilibili page/transcript/frame sequence was not retrievable in the research environment, so no timestamp or frame-level claim is fabricated.

Status:

`candidate_identified_page_or_frames_not_retrieved`

### Independent implementation cross-check

A separate community battle simulator implements Tingyun's Ultimate as a two-turn temporary damage bonus. Its generic temporary-power layer marks a buff as `justApplied` when it is received during the owner's own turn and skips one end-turn decrement. This is useful evidence that a naive end-turn countdown needs a same-turn application guard.

It is **not** proof that the release client internally settles at turn end or at turn entry. It may merely be a different encoding with similar visible lifetime.

## Current HSR Axis Simulator gap

The current engine:

1. emits `turn_started` when a normal or extra turn begins;
2. does not tick `target_normal_turns` at normal-turn entry;
3. ticks the holder's `target_normal_turns` statuses inside `Timeline.end_turn` after a normal turn;
4. has no application-turn marker or deferred-first-tick field on `Buff`;
5. refreshes `remaining_turns` directly.

Therefore the current runtime contract cannot be described as the accepted turn-entry rule.

## Still unresolved

Even after accepting `target_normal_turn_entry` as the settlement boundary, these details remain unverified:

- When the counter transitions `1 → 0` at entry, is the buff removed before the actor can act, or is it still effective for that entered turn?
- Does a granted extra turn count as a duration-consuming turn entry?
- Does a non-turn extra action count? It should not be inferred merely from the phrase “enter turn.”
- How does same-ID refresh behave when performed during the holder's active turn?
- Which event ordering is required relative to `turn_started` triggers?

## Safe next action

HSR-AXIS-002Q must be replaced with a **non-executable evidence normalization and engine-gap audit**. It may formalize the accepted turn-entry correction and demonstrate the current engine mismatch, but it must not modify production duration logic or add executable Tingyun DMG buff behavior.
