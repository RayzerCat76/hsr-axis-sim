# LUMEN Review — HSR-AXIS-002M After Codex

## Verdict

**NEEDS FIX — do not begin 002N yet.**

The evidence-only review is directionally correct and all accepted simulator behavior remains untouched. However, the new review validator has two blocking issues:

1. malformed JSON-compatible values can escape as `TypeError` instead of controlled `ValueError` validation failures; and
2. the computed readiness status says `blocked_by_source_gap` even though the report itself states that the same-current-turn duration edge is not verified against game behavior. Under the task's four-state readiness contract, the current result must be `blocked_by_both` until that duration-semantics uncertainty is resolved.

The validator also accepts fact-specific values with incorrect types or meanings, so the evidence report can be silently corrupted without failing validation.

## Independent results

- `python -m compileall -q hsr_axis_sim`: **PASS**
- pytest collection: **416 tests**
- pytest split run A: **303 passed**
- pytest split run B: **113 passed**
- total independently executed: **416/416 passed**
- locked regression: **PASS 20/20**
- trace-evidence-only regression: **PASS 2/2**
- 002M Markdown report regeneration: **byte-identical**
- 002M JSON report regeneration: **byte-identical**

A single all-tests invocation did not complete within the sandbox command window, so the suite was divided into two exhaustive, non-overlapping module groups. Every collected test was executed and passed.

## What is correct

- No executable Tingyun damage buff was added.
- Existing Tingyun Energy behavior, Pela behavior, reviewed registry v0.2, simulator, search, evaluator, replay, trace evidence, and locked manifest remain unchanged.
- The review keeps the real-video target and Tingyun trace level unknown.
- Target scope and two-turn duration are recorded as corroborated evidence.
- Magnitude by trace level remains `missing` rather than guessed.
- Buff-versus-Energy order remains `unresolved` rather than guessed.
- The current engine duration behavior is documented and covered by a focused boundary test.
- Extra turns and non-ending actions do not decrement the reviewed `target_normal_turns` counter.
- CLI Markdown/JSON output is deterministic.
- Committed reports are byte-identical to regeneration.

## Blocking issue 1 — uncontrolled malformed-input paths

Direct calls to `build_report(...)` can raise uncontrolled `TypeError` for JSON-compatible malformed values, including:

```text
facts[0].verification_status = {"bad": 1}
provenance[0].source_id = {"bad": 1}
provenance[0].release_status = {"bad": 1}
provenance[0].corroboration_status = {"bad": 1}
declared_readiness_status = {"bad": 1}
```

These values reach set membership or dictionary lookup before their types are validated.

The CLI catches the generic exception and returns exit 2, but that does not make the validator safe. Schema-invalid evidence must raise a controlled `ValueError` and produce the normal validation-failure exit path without traceback.

## Blocking issue 2 — fact-specific schema is not enforced

The current validator accepts materially invalid evidence values, including:

```text
damage_buff_target_scope = "all_allies"
damage_buff_duration_turns = 999
damage_buff_duration_turns = true
release_and_version_scope = {"bad": 1}
unit = {"bad": 1}
```

It also accepts a nonsensical string as a supposedly corroborated trace-level magnitude table or application-order value if the status/provenance fields are changed consistently.

The versioned 002M evidence file needs strict per-fact validation so its report cannot be silently altered into a different claim.

## Blocking issue 3 — readiness classification is internally inconsistent

The report states:

- `verified_game_equivalence = false`;
- `engine_representation_status = representable_with_source_unverified_same_turn_edge`;
- the same-current-turn duration edge remains unverified;
- that edge is listed among the blockers.

But `_computed_readiness(...)` only treats `not_representable` as a duration gap. Therefore it reports:

```text
blocked_by_source_gap
```

instead of:

```text
blocked_by_both
```

The task explicitly provides `blocked_by_duration_semantics_gap` and `blocked_by_both`. A source-unverified duration boundary is a duration-semantics gap even when the engine can mechanically represent one chosen interpretation.

## Required correction

- Validate types before all set membership, dictionary lookup, sorting, or comparison operations.
- Make malformed schema values raise controlled `ValueError` from `build_report(...)`.
- Make schema validation failures use the CLI validation-failure path, with no traceback.
- Add strict per-fact validation for the six expected atomic facts.
- Validate the required source-catalog fields used by the report.
- Treat unverified game-equivalence at the same-current-turn boundary as a duration-semantics gap.
- Change the current declared/computed readiness to `blocked_by_both`.
- Regenerate the committed Markdown and JSON reports deterministically.
- Preserve all non-executable scope boundaries and all existing accepted simulator behavior.

Do not research new magnitude data, choose an effect order, implement the buff, or begin 002N in this fix.
