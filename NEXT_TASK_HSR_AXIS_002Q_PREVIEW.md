# NEXT TASK PREVIEW — HSR-AXIS-002Q

Do not begin until HSR-AXIS-002P passes independent review.

## Likely task

**Same-current-turn duration ambiguity isolation and dual-policy conformance harness**

If 002P proves effect order irrelevant under the current simulator contract, the only generic semantic blocker should be whether an ally's already-active normal turn consumes the first count of Tingyun's two-turn DMG buff.

002Q should not guess the release-game behavior. It should formalize and compare both candidate policies:

1. the already-active target normal turn counts when it ends;
2. counting begins only from the target's next normal turn after application.

The task should produce deterministic synthetic timelines for both policies, identify the exact first divergent boundary, and generate a minimal versioned release-game evidence-intake protocol. No policy should become the default and no reviewed Tingyun DMG-buff binding should be added without accepted evidence or an explicitly separate caller-selected simulation policy.

## Safety boundaries

- no real Tingyun DMG-buff registry entry
- no accepted-video target or trace-level inference
- no release-game duration claim without evidence
- no silent change to the existing global buff-duration behavior
- do not rewrite 002O or 002P evidence in place

## Suggested configuration

- Codex Reasoning: High
- Recommended model: GPT-5.6 Sol
- Fallback: GPT-5.6 Terra only after the two policy contracts and expected timelines are fully specified
