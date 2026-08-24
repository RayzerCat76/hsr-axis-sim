# HSR Axis Sim Tool — Decision Log

Statuses: `CONFIRMED`, `PROVISIONAL`, `SUPERSEDED`. Never delete superseded history.

## D-001 — GitHub main is canonical implementation truth
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** GitHub `main` is the canonical accepted implementation.  
**Reason:** ZIP handoffs obscured preservation, version identity, and Git metadata.  
**Consequences:** Feature work is not accepted until reviewed and merged.  
**Supersedes:** ZIP package as canonical development transport.  
**Superseded By:** None.

## D-002 — Master Bible is canonical design truth
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** `docs/HSR_AXIS_SIM_MASTER_BIBLE.md` is the active design source of truth.  
**Reason:** Architecture, scope, unresolved mechanics, and milestones need one durable authority.  
**Consequences:** Tasks must not silently contradict it.  
**Supersedes:** Conversation/scattered-preview-only design memory.  
**Superseded By:** None.

## D-003 — One milestone per branch / PR
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Isolate each milestone in one feature/fix/chore branch and PR.  
**Reason:** Small, reviewable, reversible changes reduce semantic drift.  
**Consequences:** No unrelated future work in milestone PRs.  
**Supersedes:** Mixed handoff packages.  
**Superseded By:** None.

## D-004 — Unknown HSR mechanics are never guessed
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Unsupported values/semantics remain UNKNOWN, PARTIAL, optional, unresolved, or explicit extension points.  
**Reason:** Deterministic output must represent uncertainty honestly.  
**Consequences:** Never invent hidden values to make a scenario pass.  
**Supersedes:** None.  
**Superseded By:** None.

## D-005 — Runtime migration is incremental and sidecar-first
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** New universal runtime contracts remain sidecar-first until an explicit integration milestone.  
**Reason:** Protect the existing working simulator while semantics mature.  
**Consequences:** A contract does not authorize production wiring.  
**Supersedes:** None.  
**Superseded By:** None.

## D-006 — Production LIFO remains locked compatibility behavior
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Existing production LIFO extra-turn behavior remains protected until separately evidenced and authorized.  
**Reason:** Regression compatibility and actual HSR same-priority ordering are different questions.  
**Consequences:** Production LIFO is not automatically game truth.  
**Supersedes:** None.  
**Superseded By:** None.

## D-007 — Trace pipeline precedes Golden Replay comparison work
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Trace contracts/export/integrity/comparison/first-divergence precede expanded Golden Replay automation.  
**Reason:** Replay validation depends on trustworthy trace artifacts.  
**Consequences:** `ARCH-002 -> ARCH-003 -> ARCH-004 -> ARCH-005 -> ARCH-006 -> Golden Replay`.  
**Supersedes:** Jumping directly to full replay/video automation.  
**Superseded By:** None.

## D-008 — ZIP/Finder replacement workflow is retired
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Normal development uses Git branches, PRs, and CI.  
**Reason:** Finder replacement previously caused accepted docs to disappear.  
**Consequences:** ZIPs are archival/export only, not canonical development transport.  
**Supersedes:** Finder folder replacement workflow.  
**Superseded By:** None.

## D-009 — Codex is optional
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Default workflow is Luman + GitHub + GitHub Actions; Codex is optional.  
**Reason:** Many milestones do not need a separate executor/handoff layer.  
**Consequences:** `PASTE_THIS_IN_CODEX_*` is not required for future milestones.  
**Supersedes:** Codex-as-default workflow.  
**Superseded By:** None.
