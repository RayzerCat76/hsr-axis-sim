# NEXT TASK PREVIEW — HSR-AXIS-002F

Proceed only after HSR-AXIS-002E-FIX passes all gates.

## Candidate task

**HSR-AXIS-002F: Human-Readable Trace Evidence Report MVP**

Generate deterministic Markdown and JSON review reports that combine:

- accepted observable action sequence;
- semantic placeholder labels;
- approximate media timestamp ranges;
- representative frame references;
- confidence labels;
- explicitly unknown fields.

The report must remain evidence-only and non-executable. It should help a human reviewer compare the source clip against the recorded trace without manually opening three separate JSON files.

Suggested setup:

```text
Codex Reasoning: MEDIUM
Recommended model: GPT-5.6 Terra
```

Do not implement combat mechanics, real character kits, video-derived numeric assumptions, OCR, or automatic action recognition in 002F.
