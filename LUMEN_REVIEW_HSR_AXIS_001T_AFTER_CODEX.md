# LUMEN REVIEW — HSR-AXIS-001T After Codex

## Verdict

**Status: PASS.**

HSR-AXIS-001T implemented evaluator / scoring profile MVP correctly enough to proceed to 001U.

## Local verification by Lumen

Tested package: `hsr_axis_001a_package(20).zip`

Commands run in a pytest-enabled environment:

```bash
cd /mnt/data/hsr_review_work/hsr_axis_001a_package
python -m pytest -q
```

Result:

```text
210 passed in 8.80s
```

Golden replay CLI checks:

```text
PASS break_damage_elemental_mvp: checked 1 step(s).
PASS bronya_seele_multistep_mvp: checked 3 step(s).
PASS bronya_seele_timeline_mvp: checked 1 step(s).
PASS buff_duration_mvp: checked 2 step(s).
PASS character_kit_001_mvp: checked 3 step(s).
PASS damage_formula_v1_mvp: checked 1 step(s).
PASS damage_rng_mvp: checked 1 step(s).
PASS data_loaded_bronya_seele_mvp: checked 3 step(s).
PASS enemy_ai_mvp: checked 2 step(s).
PASS toughness_break_mvp: checked 2 step(s).
PASS trigger_on_kill_extra_turn_mvp: checked 2 step(s).
PASS ultimate_interrupt_mvp: checked 3 step(s).
```

Manual video trace checks:

```text
PASS manual_video_trace_sample_mvp: manual video trace lint passed.
PASS manual_video_trace_sample_mvp: checked 3 step(s).
```

## What 001T added

001T added the first useful scoring layer on top of the beam search engine:

- `ScoreProfile`
- `ScoreBreakdown`
- built-in profiles:
  - `generic_kill`
  - `zero_cycle`
  - `damage_race`
  - `survival_safe`
  - `sp_conservative`
- `Evaluator.evaluate_breakdown(...)`
- `format_score_breakdown(...)`
- backward compatibility for the old float-returning `Evaluator.evaluate(...)`
- `ScoreConfig` compatibility
- beam search integration with custom evaluators
- `max_global_av` search cap support

## Review notes

### 1. Backward compatibility is preserved

`Evaluator().evaluate(state, depth)` still returns a float. Existing search code does not need to be rewritten.

### 2. Score explainability improved

The new `ScoreBreakdown` is important because future AI axis output must explain why one route was selected. The components are simple but useful for MVP-level debugging.

### 3. Built-in profiles are acceptable as heuristics

The current profile weights are not final endgame scoring. That is okay. They provide different enough behavior to test the search system:

- `zero_cycle` penalizes AV more heavily.
- `damage_race` rewards HP missing more strongly.
- `survival_safe` rewards ally survival more strongly.
- `sp_conservative` rewards remaining SP more strongly.

### 4. No core mechanics were broken

The replay suite still passes. This is the most important point for 001T, because evaluator work should not mutate combat semantics.

## Known limitations

These are acceptable for 001T and should not block progress:

1. The score profiles are heuristic and not yet mode-accurate for MoC / PF / AS.
2. `format_axis(...)` is still too minimal for real player use.
3. The final report does not yet include a full beam comparison, score component table, or terminal reason summary.
4. `max_global_av` currently works as a terminal condition after branch expansion. A stricter future version may prevent executing a normal action if selecting the next actor would cross the AV cap. Do not change this in 001U unless it is necessary for formatting tests.
5. No UI or visualization yet.

## Recommended next task

Proceed to **HSR-AXIS-001U: Axis Output / Search Report MVP**.

001U should not change combat mechanics. It should make the search output usable by a human player / researcher:

- readable axis text
- Markdown report
- JSON export
- final score breakdown
- terminal reason
- beam candidate comparison
- optional CLI to run a small search and print/export the report

## Suggested model / reasoning for 001U

```text
Codex Reasoning: Medium
ChatGPT Model 建议: GPT-5.5 就够，不必用 GPT-5.5 Thinking
理由: 001U 主要是格式化、report、export、CLI 和测试；不应该改战斗核心机制。
```
