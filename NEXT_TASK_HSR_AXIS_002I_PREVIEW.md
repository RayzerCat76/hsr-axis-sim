# NEXT TASK PREVIEW — HSR-AXIS-002I

Proceed only after HSR-AXIS-002H passes every gate.

## Candidate task

**HSR-AXIS-002I: Source-Backed Character Fact Normalization MVP**

Convert only verified 002H facts into a normalized, still non-executable character-fact layer suitable for later simulator binding review.

The task should:

- preserve field-level provenance;
- normalize target types, resource fields, duration language, action categories, and trigger terminology;
- retain conflicts and missing fields;
- prohibit executable effects and CharacterSpec/SkillSpec generation;
- produce a binding-readiness matrix for each first-trace action.

Suggested setup:

```text
Codex Reasoning: HIGH
Recommended model: GPT-5.6 Sol
Fallback: GPT-5.6 Terra when all sources agree and the task is purely normalization.
```

A later task—not 002I—should select one simple character action, likely a Pela or Tingyun action, for the first reviewed real simulator binding.
