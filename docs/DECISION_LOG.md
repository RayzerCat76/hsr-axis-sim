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

## D-010 — First divergence consumes comparator order without reprioritization
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** ARCH-006 selects the first non-`MATCH` record and, for a `MISMATCH`, the first already-ordered ARCH-005 field difference.  
**Reason:** A reporter must expose comparator truth rather than introduce a second hidden ordering or semantic priority.  
**Consequences:** First-divergence reporting does not recompare, re-sort, realign, or guess which difference is more important.  
**Supersedes:** None.  
**Superseded By:** None.

## D-011 — Golden expected artifacts are digest-pinned
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** A Golden Replay expected trace is identified by explicit replay metadata plus an exact SHA-256 of its canonical expected artifact bytes; actual output is strictly loaded but is not pre-pinned to a digest.  
**Reason:** Golden expectations must not drift silently, while actual output must remain free to vary and then be compared deterministically.  
**Consequences:** Changing golden bytes requires an explicit digest change; actual artifact SHA-256 is retained as provenance after loading.  
**Supersedes:** Filename- or trace-ID-only golden identity.  
**Superseded By:** None.

## D-012 — Golden file cases are base-directory bounded
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** File-backed Golden Replay cases use canonical relative POSIX paths under one explicit base directory, and resolved targets must remain inside that base after symlink resolution.  
**Reason:** Reviewed file identity must be portable and must not depend on implicit working-directory traversal or path escape.  
**Consequences:** Absolute paths, parent traversal, noncanonical relative spellings, and symlink escape are rejected before validation.  
**Supersedes:** Unbounded or ambient-path Golden Replay file lookup.  
**Superseded By:** None.

## D-013 — Golden batches preserve declared case order and fail fast on operational errors
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** A Golden Replay batch executes unique replay IDs exactly once in declared tuple order. Replay mismatches remain completed results and do not stop later cases; any exception that prevents a case result propagates immediately and no partial batch result is returned.  
**Reason:** Comparison failure and inability to perform validation are different states and must not be conflated.  
**Consequences:** Batch output is always complete when returned, preserves declared order, and does not hide file/config/loader failures behind partial summaries.  
**Supersedes:** Implicit sorting, silent partial batch success, or swallowed operational errors.  
**Superseded By:** None.

## D-014 — Golden manifests use exact compact canonical JSON bytes
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Golden Replay manifest v1 has a fixed minimal schema and one accepted byte form: compact canonical UTF-8 JSON. Equivalent but differently formatted JSON, duplicate keys, unknown fields, missing fields, and implicit defaults are rejected.  
**Reason:** A reviewed manifest must have stable byte identity and cannot safely drift through parser normalization or extension fields.  
**Consequences:** Manifest SHA-256 identifies exact reviewed bytes; case order is preserved; any schema evolution requires an explicit versioned milestone rather than permissive parsing.  
**Supersedes:** Permissive or formatting-insensitive Golden Replay manifest parsing.  
**Superseded By:** None.

## D-015 — Golden manifest files are explicit and base-directory bounded
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** A Golden Replay manifest file is addressed by one canonical relative POSIX path under an explicit base directory; the resolved target must remain inside that base after symlink resolution before any bytes are loaded.  
**Reason:** Manifest artifact identity and filesystem location are separate contracts, and reviewed manifests must not depend on ambient working-directory lookup or permit path escape.  
**Consequences:** Absolute/noncanonical paths, traversal, symlink escape, non-files, and missing targets are rejected at the file boundary; exact manifest bytes remain governed only by HSR-AXIS-001E.  
**Supersedes:** Ambient or unbounded Golden Replay manifest file lookup.  
**Superseded By:** None.

## D-016 — Manifest-backed batches share one resolved base directory
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Manifest-backed Golden Replay execution first loads one reviewed manifest through HSR-AXIS-001F, then executes exactly its reconstructed HSR-AXIS-001D plan using the same resolved base directory returned by the manifest-file load.  
**Reason:** Manifest location and replay-file location need one explicit portable root; recomputing or changing the base between load and execution would make reviewed paths ambiguous.  
**Consequences:** The composition result must preserve the complete manifest load and batch result, and must reject any plan or base-directory misalignment; no lower-level semantics are duplicated.  
**Supersedes:** Multi-root or implicitly recomputed manifest-backed batch execution.  
**Superseded By:** None.

## D-017 — Legacy-event trace bridging is explicit and source-owned
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** The first runtime integration bridge accepts a caller-supplied legacy `Event` iterable and composes the accepted legacy adapter with the accepted runtime trace exporter; it does not inspect, drain, clear, or hook simulator event queues/state.  
**Reason:** Event adaptation/export semantics are already validated, but the lifecycle and retention semantics of simulator event queues are a separate integration decision that must not be guessed.  
**Consequences:** ARCH-007 can produce deterministic runtime trace artifacts from explicit observations while leaving simulator capture lifecycle untouched for a later milestone.  
**Supersedes:** Implicit simulator-event capture as part of the first trace bridge.  
**Superseded By:** None.

## D-018 — BattleState pending-event capture uses explicit non-mutating slices
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Runtime capture from `BattleState.pending_events` requires an explicit `[start_index:end_index)` slice of the list as it exists at capture time; the slice is snapshotted and delegated to ARCH-007 without draining, clearing, reordering, or automatically advancing a stored cursor.  
**Reason:** The current simulator appends dispatched events to `pending_events`, but its name and existing contract do not justify silently treating it as a permanent complete history or assigning automatic retention/cursor semantics.  
**Consequences:** ARCH-008 can safely capture exact current slices and return `next_index=end_index`, while persistent cursor/session and history-retention semantics remain separate reviewed work.  
**Supersedes:** Implicit full-list capture, queue draining, or permanent-history assumptions.  
**Superseded By:** None.

## D-019 — Pending-event capture cursors are caller-owned coordinate checkpoints
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Sequential pending-event capture uses an immutable caller-owned cursor containing only the next list index and next runtime sequence. Every capture still requires a caller-supplied explicit end index and a bridge config whose start sequence matches the cursor.  
**Reason:** Sequential trace slices need deterministic index/sequence continuity without moving lifecycle state into the simulator or assuming the pending-event list is permanent history.  
**Consequences:** Successful captures return a new cursor advanced by exactly the captured count; a cursor beyond current list length is rejected as stale, but arbitrary truncate/refill history cannot be inferred when current length still satisfies the cursor.  
**Supersedes:** Hidden current-end capture, simulator-owned cursor persistence, or inferred queue-history identity.  
**Superseded By:** None.

## D-020 — Captured trace stitching preserves adapted event identity and source stream
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Stitching completed ARCH-009 capture segments requires declared segment order, exact cursor-chain/runtime-sequence continuity, and one common ARCH-002 `LegacyEventAdapterConfig`; the stitcher reuses the existing adapted `RuntimeEvent` objects and never re-adapts or renumbers them.  
**Reason:** A final actual trace should preserve the observation stream and runtime event identities already established by accepted capture layers, while allowing segment-local trace artifact metadata to remain local.  
**Consequences:** Final trace identity/metadata come from one explicit final `TraceExportConfig`; mixed legacy stream IDs/policies, broken segment chains, sorting, realignment, renumbering, or source legacy-event rereads are rejected or excluded.  
**Supersedes:** Re-adapting captured segments or silently merging different legacy observation streams into one actual trace.  
**Superseded By:** None.

## D-021 — Stitched actual Golden validation passes exact artifact bytes unchanged
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** Golden validation of an ARCH-010 stitched actual trace passes the exact `stitch_result.artifact.payload_bytes` directly to the accepted HSR-AXIS-001B validator and preserves the complete stitch and Golden validation results together.  
**Reason:** The stitched artifact's byte identity/SHA is already the accepted actual-trace provenance; rebuilding or reserializing it at the validation handoff would create an unnecessary second identity boundary.  
**Consequences:** ARCH-011 adds no loader/comparator/divergence semantics; expected Golden validation errors propagate, and any returned wrapper must prove the Golden actual bytes/SHA/document match the stitched artifact exactly.  
**Supersedes:** Reserializing or reconstructing stitched actual traces before Golden validation.  
**Superseded By:** None.

## D-022 — Single-action capture is explicit and non-transactional
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** ARCH-012 executes exactly one caller-supplied production `Action` only when the caller-owned pending-event cursor is aligned to the current list end, then captures exactly the newly appended event window through accepted ARCH-009 semantics. No rollback, retry, queue cleanup, or synthetic result is attempted on failure.  
**Reason:** `Action.execute` mutates simulator state and may emit events before raising; pretending this boundary is transactional would hide real partial state and create false deterministic provenance.  
**Consequences:** Action or post-action capture exceptions propagate unchanged, all mutations remain as production execution left them, the caller-owned cursor is not mutated in place, and successful results prove the exact pre/post event-window boundaries.  
**Supersedes:** Implicit rollback, auto-retry, or silently capturing pre-existing events around one action.  
**Superseded By:** None.

## D-023 — Multi-action sessions stop at first failure and preserve only confirmed capture boundaries
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** ARCH-013 executes caller-supplied action steps strictly in declared order through accepted ARCH-012, advances only from completed result cursors, and stops at the first failed action/capture step. The controlled session failure preserves prior completed results and the last successful cursor while chaining the original exception.  
**Reason:** Repeated state-mutating action capture needs inspectable partial-session provenance without pretending failed steps are transactional or recoverable.  
**Consequences:** Later actions are never executed after failure; no rollback/retry/cursor repair occurs; `last_successful_cursor` is a confirmed historical boundary only and is not automatically safe for resume because the failed step may already have mutated state or appended uncaptured events.  
**Supersedes:** Implicit continuation after failed action capture, silent partial-session success, or treating the last completed cursor as guaranteed recovery state.  
**Superseded By:** None.

## D-024 — Successful-session stitch handoff preserves exact accepted capture objects
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** ARCH-014 accepts only a completed successful ARCH-013 result, extracts each completed ARCH-012 result's accepted ARCH-009 `capture_result` in exact session order, and delegates that exact tuple once to accepted ARCH-010 stitching.  
**Reason:** A successful session already contains reviewed capture provenance; rebuilding, re-adapting, reordering, or replacing those segments would introduce an unnecessary second trace-source identity boundary.  
**Consequences:** The ARCH-014 wrapper preserves the complete session and stitch results and requires every stitched segment to be the exact same Python object as the corresponding session capture result. Failed/partial session objects are not valid inputs, and ARCH-010 errors propagate unchanged.  
**Supersedes:** Reconstructing session segments or implicitly stitching partial-session provenance.  
**Superseded By:** None.

## D-025 — Successful-session Golden handoff preserves exact accepted stitch provenance
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** ARCH-015 accepts only a completed ARCH-014 result and passes `session_stitch_result.stitch_result` unchanged to accepted ARCH-011 exactly once.  
**Reason:** ARCH-014 already defines the authoritative stitched actual-trace provenance; restitching, rebuilding, or reserializing it before Golden validation would create duplicate identity and semantic boundaries.  
**Consequences:** ARCH-015 preserves the complete ARCH-014 and ARCH-011 results, requires exact stitch-object identity across the handoff, leaves Golden mismatches as completed validation results, and propagates ARCH-011 input/operational errors unchanged without direct lower-layer validation logic.  
**Supersedes:** Rebuilding, restitching, or independently revalidating the actual trace between successful session stitching and accepted ARCH-011.  
**Superseded By:** None.

## D-026 — End-to-end action-session validation composes accepted stages without transaction semantics
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** ARCH-016 preflights directly checkable caller input, then composes accepted ARCH-013 -> ARCH-014 -> ARCH-015 exactly once each and passes each exact returned stage object unchanged to the next stage.  
**Reason:** A single explicit validation entry point is useful only if it preserves the already-reviewed state-mutation, capture, stitch, and Golden boundaries rather than creating new hidden semantics.  
**Consequences:** ARCH-013 failures stop later stages and propagate unchanged; ARCH-014/015 failures after completed actions also propagate unchanged with no rollback; Golden mismatch remains a completed result; ARCH-016 does not catch/retry lower failures or call ARCH-012/010/011/lower layers directly.  
**Supersedes:** Ad hoc end-to-end composition that could defer obvious input errors until after state mutation or bypass accepted stage boundaries.  
**Superseded By:** None.

## D-027 — End-to-end Golden expectations are reviewed static artifacts, not simulator-generated test oracles
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** ARCH-017's first end-to-end Golden expectation is a manually constructed compact canonical runtime-trace file, stored separately under `data/runtime_golden_fixtures`, with exact byte size and SHA-256 pinned in tests and documentation.  
**Reason:** Generating expected bytes with the same simulator/adapter/export pipeline under test would make an end-to-end PASS circular and unable to detect shared output drift.  
**Consequences:** Tests may strictly load and compare the static expected bytes but may not generate them at runtime; any fixture-byte change requires explicit review and digest update. ARCH-017 does not promote the fixture into the locked regression manifest; that remains a separate milestone.  
**Supersedes:** Runtime-generated expected artifacts as the authority for end-to-end action-session validation tests.  
**Superseded By:** None.

## D-028 — Reviewed runtime action-session Golden checks use a separate locked regression lane
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** ARCH-018 promotes reviewed production-action-session Golden validation through a dedicated downstream `runtime_action_session_regression` package and separate strict manifest/CI step. The legacy `hsr_axis_sim.regression` runner, its manifest, category meanings, and 20/20 baseline remain unchanged.  
**Reason:** Directly importing runtime sidecars into the legacy regression package violated accepted sidecar-preservation boundaries and invalidated research/reference pins over the legacy runner/manifest bytes and counts. Those failures exposed an architecture boundary rather than a test suite to weaken.  
**Consequences:** Locked validation now reports two distinct baselines: legacy regression `20/20` and runtime action-session Golden regression `1/1`. Future runtime cases may extend the dedicated lane only under explicit reviewed contracts; they must not be silently folded into the legacy replay categories or broaden the minimal action schema into arbitrary targets/effects.  
**Supersedes:** Direct runtime-sidecar integration into the legacy regression runner or treating the accepted baseline as one combined `21/21` count.  
**Superseded By:** None.

## D-029 — Resource observations stay payload-level under trace schema v1 before production emission
**Status:** CONFIRMED  
**Date:** 2026-08-24  
**Decision:** ARCH-019 adds `ENERGY_CHANGED` and `SKILL_POINTS_CHANGED` plus an immutable resource-change payload contract, while schema-v1 `RuntimeTraceRecord.numeric_values` remains empty and no simulator or legacy-adapter emission is introduced yet.  
**Reason:** The accepted v1 loader explicitly requires empty record-level numeric values, but `RuntimeEvent.payload` is already the schema-compatible extensibility point. Separating vocabulary from production emission keeps contract evolution reviewable and prevents a resource-observation milestone from becoming an implicit trace-schema migration.  
**Consequences:** Resource observations distinguish `requested_delta` from `applied_delta`, require `applied_delta == after - before`, and encode ENERGY as unit-scoped and SKILL_POINTS as team-scoped. Historical ARCH-002/003/004 reference artifacts remain byte-pinned; their preservation tests continue pinning every untouched source while explicitly allowing the additive `runtime_contracts/enums.py` and `__init__.py` evolution authorized by ARCH-019. Production emission and legacy adapter binding require a separate milestone.  
**Supersedes:** Treating resource values as record-level numeric data under schema v1 or silently wiring production emission into the vocabulary milestone.  
**Superseded By:** None.
