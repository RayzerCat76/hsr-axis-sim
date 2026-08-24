# LUMEN REVIEW CHECKLIST — HSR-AXIS-001B

Use this when reviewing Codex's 001B output.

## Must pass

- Existing 001A-FIX tests still pass.
- New replay validator tests pass.
- Sample golden replay loads from JSON.
- Replay runner calls `Timeline.next_turn()` before executing a step action.
- Replay runner passes the active `TurnContext` into `Action.execute()`.
- Wrong actor mismatch is detected.
- Numeric mismatch is detected with tolerance.
- Unknown action / unit / effect errors are clear.
- Result object contains all mismatches where practical.

## Must not happen

- No Huroka scraping.
- No Bilibili scraping.
- No real character kit implementation.
- No full damage formula implementation.
- No AI/beam search implementation.
- No breaking changes to core timeline semantics.

## Special things to inspect

- Does JSON effect deserialization preserve `target_ids`?
- Does step-level target override work?
- Are float comparisons tolerant but not too loose?
- Is the sample replay simple enough to audit by hand?
- Does the validator produce useful failure messages for debugging golden replays?
