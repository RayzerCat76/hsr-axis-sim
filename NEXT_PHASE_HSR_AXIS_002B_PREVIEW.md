# HSR-AXIS-002B Preview — Real Trace Mismatch Diagnosis or Second Real Trace

After 002A, choose the next branch based on the result.

## If 002A passes cleanly

Proceed to:

**HSR-AXIS-002B — Second Real Manual Video Trace Fixture**

Goal: add a second low-randomness trace, preferably with a slightly different mechanic profile.

Suggested reasoning/model:

```text
Codex Reasoning: Medium
ChatGPT Model: GPT-5.5
```

## If 002A replay mismatches

Proceed to:

**HSR-AXIS-002B-FIX — Real Trace Mismatch Diagnosis**

Goal: determine whether the mismatch is caused by transcription error, build/stat approximation, missing forced RNG, enemy behavior, or simulator mechanism inaccuracy.

Suggested reasoning/model:

```text
Codex Reasoning: High
ChatGPT Model: GPT-5.5 Thinking
```

Do not change core mechanics until the mismatch source is identified.
