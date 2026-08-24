# NEXT TASK PREVIEW — HSR-AXIS-002P

Do not begin until HSR-AXIS-002O-FIX passes independent review.

## Likely task

**Current-contract effect-order irrelevance proof for Tingyun Ultimate**

HSR-AXIS-002O correctly leaves two generic semantic blockers:

1. Energy restoration versus DMG-buff application order
2. same-current-turn duration behavior

The smallest next step that Codex can complete without external gameplay evidence is to determine whether effect order is provably irrelevant to every **current simulator event and trigger contract**.

The task should audit and pin the relevant implementation boundaries, including:

- action execution order
- `GainEnergy`
- `AddBuff`
- emitted event boundaries
- trigger event types and conditions
- action/turn snapshots and deterministic reports

A test-only synthetic comparison may execute the two candidate orders:

- Energy then buff
- buff then Energy

It must compare all currently observable state and event/trigger outputs under the complete current contract. It must not create a real reviewed binding or infer release-game order.

## Possible outcomes

### Proven irrelevant under current contracts

Create a new non-executable evidence artifact stating that release-game order remains unknown but is semantically irrelevant to the current simulator contract. Generic readiness would then remain blocked only by same-current-turn duration semantics.

### Not proven irrelevant

Keep the effect-order blocker and produce the exact smallest missing evidence requirement.

## Safety boundaries

- no executable Tingyun DMG-buff binding
- no registry entry
- no real-video target or trace-level inference
- no duration-policy assumption
- do not rewrite the historical 002O artifact in place

## Suggested configuration

- Codex Reasoning: High
- Recommended model: GPT-5.6 Sol
- Fallback: GPT-5.6 Terra only if the event/trigger contract inventory is already explicit and the work is purely mechanical
