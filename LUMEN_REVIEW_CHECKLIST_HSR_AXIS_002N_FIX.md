# LUMEN Review Checklist — HSR-AXIS-002N-FIX

## Exact source capture

- [ ] intake status is `captured_exact_table`
- [ ] Mar-7th/StarRailRes commit and immutable file URL are recorded
- [ ] KQM-git/SRL commit and immutable file URL are recorded
- [ ] exact skill selectors and `params[*][2]` locators are recorded
- [ ] snapshot/version qualification is accurate
- [ ] no claim of byte identity with game version 3.4
- [ ] Gachabase is context-only, not a full-table source

## Raw and normalized data

- [ ] two raw tables are stored independently
- [ ] both raw tables have 15 ordered rows
- [ ] raw ratios are preserved or their ratio-to-percent conversion is explicit
- [ ] normalized levels are exactly 1-15
- [ ] normalized percentages are exactly 20, 23, 26, 29, 32, 35, 38.75, 42.5, 46.25, 50, 53, 56, 59, 62, 65
- [ ] every normalized row references the matching raw row from both exact sources
- [ ] a one-row source conflict is rejected
- [ ] duplicate and malformed input protections remain intact
- [ ] rendering remains deterministic

## Safety and scope

- [ ] `real_video_trace_level` remains null
- [ ] selected ally remains unknown
- [ ] effect order remains unresolved
- [ ] same-current-turn duration remains unresolved
- [ ] readiness remains `blocked_by_both`
- [ ] simulator binding remains false
- [ ] no AddBuff or executable DMG buff
- [ ] Tingyun Energy binding unchanged
- [ ] Pela binding unchanged
- [ ] registry still has exactly two entries
- [ ] no 002O work

## Gates

- [ ] compileall passes
- [ ] complete pytest collection passes
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] Markdown report is byte-identical to regeneration
- [ ] JSON report is byte-identical to regeneration
- [ ] LUMEN_RESULT contains exact sources, rows, unresolved fields, and preservation confirmation
