# LUMEN REVIEW — HSR-AXIS-002N After Codex

## Verdict

**HSR-AXIS-002N is NOT accepted yet. A source-capture FIX is required.**

The implementation quality is good: the evidence-intake validator is narrow, deterministic, non-executable, and preserves the existing simulator and reviewed bindings. All 430 collected tests passed when executed in four disjoint shards, locked regression remained 20/20, trace-evidence-only regression remained 2/2, and committed Markdown/JSON reports were byte-identical to regeneration.

However, the central deliverable of 002N was to capture the Tingyun Ultimate DMG-increase level table when adequate exact evidence was available. The submitted artifact instead reports `blocked_source_unavailable`. Independent review found two inspectable, commit-pinned structured tables with identical 15-row values, plus a current release page confirming the Lv. 10 row. Therefore the blocked result is no longer accurate and the task cannot pass in its current form.

## Independent source findings

### Exact structured source A — Mar-7th/StarRailRes

- Repository: `Mar-7th/StarRailRes`
- Commit: `7b349e39ee0f6f3bf814567995829b99c95e7a93`
- Commit message: `Update to version 4.3`
- Path: `index_new/en/character_skills.json`
- Exact object: skill ID `120203`, `Amidst the Rejoicing Clouds`
- Exact field locator: `content["120203"].params[*][2]`
- Supporting structural fields:
  - `max_level = 15`
  - description maps `#3[i]` to target DMG increase
  - 15 ordered parameter rows

### Exact structured source B — KQM-git/SRL

- Repository: `KQM-git/SRL`
- Commit: `de0e5c09c8dbba9577367ad86e991fe91c4f0e36`
- Path: `src/data/characters/Tingyun.json`
- Exact object: `skills[]` entry whose name is `Amidst the Rejoicing Clouds`
- Exact field locator: `skills[name="Amidst the Rejoicing Clouds"].params[*][2]`
- The same 15 ordered rows are present.

These are separately maintained repositories. Their ultimate parameter rows match exactly. The review must not claim they are independent extractions from unrelated upstream game data; they are suitable as row-by-row corroboration at the repository snapshot level.

### Context-only current release check — Gachabase

The current release page identifies itself as v4.3.0 and shows Ultimate Lv. 10 as 50% DMG for 2 turns with 50 Energy restoration. This supports the Lv. 10 row and current release context, but it is not a complete 15-row table and must not be represented as an exact-table source.

## Exact table recovered

| Trace level | DMG increase |
|---:|---:|
| 1 | 20% |
| 2 | 23% |
| 3 | 26% |
| 4 | 29% |
| 5 | 32% |
| 6 | 35% |
| 7 | 38.75% |
| 8 | 42.5% |
| 9 | 46.25% |
| 10 | 50% |
| 11 | 53% |
| 12 | 56% |
| 13 | 59% |
| 14 | 62% |
| 15 | 65% |

The raw values are decimal ratios in both structured sources (`0.2`, `0.23`, ..., `0.65`) and should normalize to percentage values (`20`, `23`, ..., `65`) with the raw rows preserved.

## What Codex did correctly

- Added a narrowly scoped evidence-only artifact and CLI.
- Kept `simulator_binding_allowed: false`.
- Preserved `real_video_trace_level: null`.
- Preserved unresolved target, effect order, and same-current-turn duration semantics.
- Did not implement an executable Tingyun DMG buff.
- Did not alter the Tingyun Energy binding, Pela binding, registry count, simulator, search, evaluator, replay, or manifest.
- Strictly rejects booleans, null, objects, lists, NaN, infinity, duplicate levels, duplicate source IDs, dangling raw references, and executable-schema keys in the tested paths.
- Controlled CLI error paths work without traceback.

## Blocking issue

The committed artifact says no exact table or field locator was available. That statement is contradicted by inspectable commit-pinned structured files. Because source acquisition is the purpose of 002N, passing tests alone is not sufficient.

## Required fix

1. Replace the blocked intake with `captured_exact_table`.
2. Record both exact structured sources with immutable commit URLs and exact field locators.
3. Preserve each source's 15 raw rows independently.
4. Normalize levels 1–15 to percentages while retaining raw ratios and raw-level references.
5. Keep the Gachabase v4.3.0 page as context-only evidence, not as a full-table source.
6. Keep readiness `blocked_by_both` because effect order and same-current-turn duration semantics remain unresolved.
7. Keep the accepted video's Tingyun trace level and selected ally unknown.
8. Do not implement the buff and do not begin 002O.
9. Update tests so the committed captured artifact is validated and reports are deterministic.
10. Re-run all gates.

## Gate after fix

002N may pass only when:

- the exact 15-row table is committed with the source snapshots above;
- source provenance and raw-to-normalized mapping validate;
- all tests and regressions pass;
- reports regenerate byte-identically;
- no executable buff is added.
