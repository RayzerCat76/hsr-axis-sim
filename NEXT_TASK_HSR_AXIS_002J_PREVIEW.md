# NEXT TASK PREVIEW — HSR-AXIS-002J

Proceed only after HSR-AXIS-002I passes every gate.

## Candidate task

**HSR-AXIS-002J: First Source-Reviewed Real Action Binding MVP**

Select exactly one simple, source-ready action from the 002I readiness matrix—most likely Pela Skill or Tingyun Ultimate—and implement the smallest reviewed real binding.

The task should:

- bind one action only;
- use only atomic facts marked source-ready in 002I;
- keep all trace-specific unknowns configurable rather than inferred;
- add a synthetic deterministic fixture before attempting the real video trace;
- compare the implementation against existing generic engine primitives;
- prohibit adding the remaining character kits.

Suggested setup:

```text
Codex Reasoning: HIGH
Recommended model: GPT-5.6 Sol
Fallback: GPT-5.6 Terra only if the chosen action maps directly to already-tested generic primitives and no semantic conflict exists.
```
