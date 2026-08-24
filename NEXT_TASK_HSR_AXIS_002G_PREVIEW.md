# NEXT TASK PREVIEW — HSR-AXIS-002G

Proceed only after HSR-AXIS-002F passes all gates.

## Candidate task

**HSR-AXIS-002G: First-Trace Simulator Binding Gap Inventory MVP**

Use the accepted evidence report to produce a deterministic, non-executable inventory of what is still required before the first real trace can become an executable simulator replay.

The inventory should separate:

- already supported generic engine primitives;
- missing verified character-kit semantics;
- missing target information;
- missing resource/energy initialization;
- unresolved composite-action behavior;
- unresolved Mem action-advance semantics;
- evidence that cannot be recovered from this video alone.

It must not implement real character kits or invent values. Its purpose is to define the smallest verified-data and engine work needed for a future executable trace.

Suggested setup:

```text
Codex Reasoning: MEDIUM
Recommended model: GPT-5.6 Terra
Escalate to GPT-5.6 Sol only if a genuine cross-engine architectural conflict is found
```
