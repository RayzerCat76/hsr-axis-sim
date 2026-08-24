# NEXT TASK PREVIEW — HSR-AXIS-002O

Do not begin this task until 002N-FIX passes independent review.

Likely next gate:

**Tingyun Ultimate DMG-Buff Binding Semantics Review / Executable Readiness**

Even after the 15-level magnitude table is captured, executable binding remains blocked by:

- unresolved order between target Energy restoration and DMG-buff application;
- unverified same-current-turn duration behavior;
- unknown trace level and selected ally in the accepted video.

002O should first resolve or explicitly model these semantic boundaries before adding an executable AddBuff. It must not simply select Lv. 10 or infer the video's target.

Recommended starting configuration after 002N-FIX:

- Codex Reasoning: High
- Model: GPT-5.6 Sol
- Use Terra only if the semantics have already been resolved by exact evidence and the task has become routine implementation.
