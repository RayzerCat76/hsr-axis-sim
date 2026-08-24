# LUMEN REVIEW CHECKLIST — HSR-AXIS-002D

## Required gates

- [ ] Full pytest passes.
- [ ] Existing locked regression runner passes unchanged.
- [ ] Existing action-sequence trace and semantic map still validate.
- [ ] No combat core mechanics changed.
- [ ] No SP, energy, HP, toughness, damage, targets, RNG, AV, speed, or action-advance percentage was invented.

## Frame-anchor fixture

- [ ] A separate frame-anchor JSON exists.
- [ ] It is explicitly non-executable.
- [ ] Timestamp basis is media seconds from sample1.mov start.
- [ ] Every prebattle item has exactly one anchor.
- [ ] Every one of the nine steps has exactly one anchor.
- [ ] Actor/action/step keys match the accepted source trace.
- [ ] Approximate boundaries retain confidence metadata.
- [ ] Mem's anchor does not claim an exact pull percentage.
- [ ] Composite actions do not claim exact internal split timing.

## Validator / CLI

- [ ] Source mismatch fails.
- [ ] Missing mapping fails.
- [ ] Actor/action mismatch fails.
- [ ] Reversed interval fails.
- [ ] Decreasing step order fails.
- [ ] Invalid frame reference fails.
- [ ] Invalid confidence fails.
- [ ] Forbidden combat fields fail.
- [ ] Valid CLI returns 0 and invalid CLI returns nonzero.
- [ ] Output is deterministic.

## Decision rule

Accept 002D only if timestamps remain evidence metadata and cannot be mistaken for simulator AV or executable combat state.
