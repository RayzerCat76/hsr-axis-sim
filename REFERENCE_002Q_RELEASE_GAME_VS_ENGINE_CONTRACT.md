# Reference — HSR-AXIS-002Q accepted claim vs current engine

## Accepted project-domain claim

`settlement_boundary = target_normal_turn_entry`

Evidence status:

`accepted_project_domain_correction_pending_independent_frame_verification`

## Current engine

### Normal-turn entry

`Timeline.next_turn` selects the actor and emits `turn_started`; it performs no target-normal-turn status tick.

Pinned file:

- `hsr_axis_sim/sim/timeline.py`
- SHA-256: `511d7bebab2542cce45cec6a1ddbf1833c1664770bca5f76267f0561db6e0aa8`
- locator: lines 10–35

### Normal-turn end

`Timeline.end_turn` calls `actor.tick_target_normal_turn_statuses()` for a normal turn.

- same file and digest
- locator: lines 38–63, especially line 45

### Status representation

`Buff` contains duration type and remaining turns but no application-boundary marker.

- `hsr_axis_sim/sim/buffs.py`
- SHA-256: `7095d592ee4466396bcd2224d740aa780271e7f539cd9751949ee41c1f5837b5`
- locator: lines 7–18

### Application and refresh

`AddBuff` stores a `target_normal_turns` status. `_add_status` directly sets or refreshes `remaining_turns` and has no turn-entry lifecycle metadata.

- `hsr_axis_sim/sim/effects.py`
- SHA-256: `3adb44ababa1725933c82a105706b388239d895a98f159db5c4691a12dfa9618`
- locators: lines 134–161 and 416–464

## Proven gap

The accepted project-domain boundary and the current engine boundary are structurally different.

## Not yet proven

This package does not decide:

- whether removal occurs before or after action eligibility when the counter reaches zero;
- whether an extra turn counts;
- event order relative to `turn_started` triggers;
- a safe migration policy for all existing statuses.

Therefore no production change is authorized in 002Q.
