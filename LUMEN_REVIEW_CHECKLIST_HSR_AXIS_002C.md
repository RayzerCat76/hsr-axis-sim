# LUMEN REVIEW CHECKLIST — HSR-AXIS-002C

Use this checklist after Codex returns 002C.

## Required gates

- [ ] Full pytest passes.
- [ ] Existing regression runner still passes.
- [ ] The existing action-sequence trace still passes lint and action-sequence checks.
- [ ] No combat core mechanics were changed unnecessarily.
- [ ] No numeric SP / energy / HP / toughness / damage / RNG values were invented.

## Semantic map checks

- [ ] A new semantic map fixture exists for the Botu Dilemma trace.
- [ ] The semantic map has `executable=false` or equivalent.
- [ ] The semantic map explicitly disallows numeric claims.
- [ ] Every prebattle action has a mapping.
- [ ] Every trace step has exactly one mapping.
- [ ] Composite actions remain placeholders, not fake executable skills.
- [ ] `mem advance_naxia` is not falsely converted into a specific 100% advance or immediate action unless proven.
- [ ] Naxia extra-skill behavior is marked as placeholder/unknown, not fully implemented.

## Tooling checks

- [ ] Semantic map lint CLI exists and prints clear PASS/FAIL output.
- [ ] Missing step mapping fails clearly.
- [ ] Source trace mismatch fails clearly.
- [ ] Numeric claims are rejected when the map policy disallows them.
- [ ] The CLI has deterministic output suitable for future regression use.

## Decision rule

Accept 002C only if it strengthens the real-trace workflow without pretending that the simulator can already execute the real Naxia/Tingyun/Pela/Remembrance Trailblazer kit.
