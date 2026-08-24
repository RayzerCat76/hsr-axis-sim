# Next Task Preview — HSR-AXIS-002R

Do not start 002R until replacement 002Q passes Lumen review.

Likely 002R scope:

`Verified turn-entry duration contract or additional evidence acquisition`

Gate before runtime work:

1. obtain frame-level evidence for the `1 → 0` boundary and whether the buff remains effective during that entered turn;
2. classify extra turn versus extra action consumption;
3. determine event ordering relative to `turn_started`;
4. assess migration impact on every existing `target_normal_turns` status and locked replay.

Only after those gates may 002R choose between:

- a global turn-entry duration engine migration;
- a per-status duration-boundary policy;
- an application-boundary marker;
- continued blocking pending evidence.

002R must not be assumed to be an implementation task in advance.
