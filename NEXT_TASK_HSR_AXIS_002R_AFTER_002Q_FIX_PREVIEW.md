# Next Task Preview — HSR-AXIS-002R

Do not start until HSR-AXIS-002Q-FIX passes independent review.

## Proposed scope

**Global `target_normal_turns` Consumer Inventory and Turn-Entry Migration Impact Audit**

This should remain non-runtime work.

The audit should inventory every production, fixture, replay, imported sample, character-kit sample, binding, tool, and test that creates or relies on `target_normal_turns`.

For each consumer, classify:

- current creation boundary;
- current end-turn decrement expectation;
- whether application can occur during the holder's active turn;
- whether extra turns or non-ending actions are involved;
- whether moving the global tick to normal-turn entry changes observable behavior;
- whether a per-status policy or application marker would be safer than a global migration;
- which locked replay/test would need a deliberately reviewed update.

## Still-blocking release-game evidence

002R must not invent answers for:

- effect lifetime when the counter reaches zero;
- decrement/removal order relative to `turn_started`;
- extra-turn consumption;
- extra-action consumption;
- same-ID refresh during an already-active turn.

The Bilibili candidate remains candidate-only until exact frames or another direct mechanism test are retrieved.

## Output

Produce a deterministic migration-risk matrix and recommended architecture options, but do not change Timeline, Unit, Buff, effects, bindings, or regression expectations.

Likely recommendation when this task is issued:

- Codex Reasoning: High
- Model: GPT-5.6 Sol
- Fallback: GPT-5.6 Terra after the inventory schema and classifications are fixed
