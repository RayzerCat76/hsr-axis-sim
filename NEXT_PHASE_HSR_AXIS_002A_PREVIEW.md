# HSR-AXIS-002A Preview — First Real Manual Video Trace Intake

After 001Z, the project should have a locked regression baseline.

The next phase should begin with a real manually recorded trace from a public gameplay video, but Codex should not browse, download, or scrape videos.

The intended workflow is:

1. Ray chooses a low-randomness video.
2. Ray or Lumen manually records the trace into the existing manual video trace JSON format.
3. Codex adds it as a new fixture only after the data is provided locally.
4. The regression manifest is updated to include the new trace.
5. The simulator attempts to reproduce the trace step by step.

Recommended first real trace properties:

- Low RNG.
- Simple enemy behavior.
- Character builds shown clearly at the end of the video.
- Few follow-ups / summons / random target choices.
- Prefer “no-reset/no-heavy-rng” style gameplay over high-roll showcase gameplay.

Possible 002A task name:

**HSR-AXIS-002A — First Real Manual Video Trace Fixture MVP**

Expected reasoning/model:

```text
Codex Reasoning: Medium initially; High only if simulator mismatches require mechanism debugging.
ChatGPT Model suggestion: GPT-5.5 for fixture wiring; GPT-5.5 Thinking for mismatch diagnosis.
```
