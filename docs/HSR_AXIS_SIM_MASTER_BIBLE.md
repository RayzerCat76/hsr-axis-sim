# HSR Axis Sim Tool — Master Bible

**Version:** 0.1.0  
**Status:** ACTIVE  
**Canonical design truth:** this file  
**Canonical accepted implementation:** GitHub `main`

## 1. Project Identity
HSR Axis Sim Tool is a deterministic Honkai: Star Rail action-axis and combat-trace simulator. The assistant/reviewer is **Luman**.

## 2. Final Product Goal
The finished tool should:
1. represent HSR combat actions as structured traces;
2. simulate AV, turn order, pulls, advances, delays, extra turns/actions, SP, energy, ownership, summons, memosprites, linked actors, lifecycle, and supported mechanics deterministically;
3. compare expected traces with simulator output;
4. report the first divergence clearly;
5. support deterministic Golden Replay validation;
6. later make manual trace creation from gameplay footage easier.

Do not begin with full automatic video extraction.

## 3. Priority Order
`correctness > determinism > validation > test coverage > trace inspectability > usability > visual polish > automation`

Never invent hidden game values or semantics. **Unknown > Guess.**

## 4. Confirmed Current Baseline
```text
Latest completed milestone:
HSR-AXIS-001B — PASS

Complete pytest:
831 / 831 passed

Locked regression:
20 / 20 passed

Trace evidence:
2 / 2 passed

Current blocker:
None

Next milestone:
HSR-AXIS-001C — File-backed Golden Replay Case Runner — READY / NOT STARTED
```

Current governance milestone:
`HSR-GOV-001 — PASS`.

## 5. Architecture
```text
hsr_axis_sim/sim              active production MVP
runtime_contracts             immutable runtime/event/trace contracts
runtime_adapters              manual legacy Event -> RuntimeEvent bridge
runtime_exports               deterministic trace export
runtime_loaders               strict schema-v1 loading/integrity validation
runtime_comparators           strict expected-vs-actual trace comparison
runtime_divergence            first-divergence selection/text reporting
runtime_golden_replays        digest-pinned deterministic Golden Replay validation
regression                    locked regression runner
search                        existing search/evaluator tools
real_bindings                 reviewed partial real-game bindings
```

Sidecar contracts do not authorize automatic production integration.

## 6. Runtime Milestones
### ARCH-001 — PASS
Universal Runtime Contract Skeleton. Immutable contexts/events/trace vocabulary; no invented numeric action priority; no FIFO/LIFO default.

### ARCH-002 — PASS
Manual one-way legacy Event -> RuntimeEvent adapter. No automatic simulator hook. `unit_defeated` lifecycle remains unresolved.

### ARCH-003 — PASS
RuntimeEvent[] -> RuntimeTraceRecord[] -> RuntimeTraceDocument -> deterministic JSON bytes -> SHA-256 -> optional explicit file write.

### ARCH-004 — PASS
Strict trace loader/integrity validator. Reject invalid/tampered/noncanonical schema-v1 input; do not repair it.

### ARCH-005 — PASS
Strict expected-vs-actual comparator over ordered `RuntimeTraceRecord` streams. Exact positional comparison, deterministic field differences, no repair or heuristic realignment, and no first-divergence reporting.

### ARCH-006 — PASS
Read-only first-divergence reporter over an existing ARCH-005 comparison result. Selects the first existing non-MATCH record and first already-ordered field difference without recomparison, reprioritization, or realignment; exposes immutable structured output and deterministic text.

### HSR-AXIS-001B — PASS
Deterministic Golden Replay Validator. Expected golden canonical bytes are integrity-pinned by SHA-256; actual canonical bytes are strictly loaded without a pre-known digest. Validation composes the accepted loader, comparator, and first-divergence reporter without duplicating their semantics. The first replay test is manually constructed from explicit runtime events.

## 7. Trace Pipeline
```text
legacy simulator Event
-> RuntimeEvent
-> RuntimeTraceDocument / deterministic artifact
-> strict loader + integrity validation
-> ARCH-005 Expected vs Actual Comparator
-> ARCH-006 First Divergence Reporter
-> HSR-AXIS-001B Deterministic Golden Replay Validator
-> [CURRENT FRONTIER]
-> HSR-AXIS-001C File-backed Golden Replay Case Runner
```

## 8. Determinism Rules
Preserve explicit ordering and identifiers. Reject invalid duplicates instead of rewriting them. Use canonical JSON where required. Exact-byte SHA-256 protects trace artifacts. Display rounding must not feed state. Strict invalid ownership/SP/energy transitions are rejected, not silently clamped.

Golden expected artifacts are digest-pinned. Changing accepted golden bytes requires an explicit expected-digest change. Actual validation output is strictly canonical-loaded and its computed SHA-256 is retained as provenance.

## 9. Evidence Classification
- `CONFIRMED`
- `PARTIAL`
- `UNKNOWN`

Separate visible observation, source/game data, inferred semantic rule, and implementation reference. Research is not implementation authorization.

## 10. Locked / Protected Behaviour
Until an explicit accepted milestone changes them:
- production simulator behavior is protected;
- locked regressions are protected;
- existing production LIFO extra-turn behavior is protected;
- actual HSR same-priority FIFO/LIFO semantics are separate from compatibility behavior;
- accepted trace schema v1 is protected;
- accepted research/reference artifacts are protected;
- `unit_defeated` is not silently upgraded to a specific lifecycle state.

## 11. Known Unresolved Semantics
Important unresolved/partial areas include:
- current-frame Extra Turn FIFO/LIFO game evidence;
- Counter eligibility matrix;
- DoT snapshot vs dynamic;
- single-effect cleanse/dispel priority;
- damage/heal/shield/HP exact rounding;
- generic multi-hit continuation;
- Bounce replacement policy;
- true revive AV/status re-entry.

See `docs/runtime/UNRESOLVED_SEMANTICS_V1.json`.

## 12. Development Workflow
```text
Master Bible = design truth
GitHub main = accepted code truth
Decision Log = decision history
feature/fix/chore branch = isolated current work
```

Milestone flow:
`define -> branch -> inspect -> implement -> test -> PR -> CI -> Luman review -> merge only after PASS`.

Codex is optional and used only when it materially helps.

## 13. Milestone Ledger
| Milestone | Status |
|---|---|
| HSR-AXIS-001A MVP | PASS |
| HSR-RUNTIME-ARCH-001 | PASS |
| HSR-RUNTIME-ARCH-002 | PASS |
| HSR-RUNTIME-ARCH-003 | PASS |
| HSR-RUNTIME-ARCH-004 | PASS |
| HSR-GOV-001 | PASS |
| HSR-RUNTIME-ARCH-005 | PASS |
| HSR-RUNTIME-ARCH-006 | PASS |
| HSR-AXIS-001B Deterministic Golden Replay Validator | PASS |
| HSR-AXIS-001C File-backed Golden Replay Case Runner | READY / NOT STARTED |

## 14. Acceptance
A milestone is not accepted because code looks plausible. Review changed files, tests, regression output, warnings/errors, protected files, unresolved issues, and reference integrity where relevant.

Default commands:
```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

Decision is exactly one of:
`PASS — proceed`, `PARTIAL — fixes required`, `BLOCKED — exact blocker`, `FAIL — acceptance criteria not met`.

## 15. Scope Exclusions
Unless explicitly unlocked: full automatic Bilibili/video-to-trace extraction, scraping, unrelated formula expansion, full character DB, AI combat optimization, unrelated UI expansion, or premature runtime migration.

Golden Replay expected traces remain explicitly reviewed artifacts. Automatic video-to-golden generation is not authorized.

## 16. Near-Term Roadmap
`HSR-AXIS-001C File-backed Golden Replay Case Runner -> deterministic batch replay manifest runner`.

Later: incremental universal runtime integration, broader validated semantics, manual trace authoring improvements, then video assistance.

## 17. Governance Rule
After HSR-GOV-001 merges, normal development uses Git branches, PRs, and CI. ZIP/Finder folder replacement is retired as the normal workflow.
