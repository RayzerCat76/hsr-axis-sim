# Reference — 002Q Semantic Tamper Reproduction

The accepted replacement-002Q input was copied and only these fields were changed:

```text
claims[zero_counter_effect_lifetime].effect_active_during_entered_turn = "true"
claims[extra_action_consumption].extra_action_consumes = "true"
claims[extra_turn_consumption].extra_turn_consumes = "true"
```

Independent result:

```text
build_report: ACCEPTED
CLI return code: 0
stderr: empty
successful JSON output contained all three strings
```

These fields are explicitly unresolved in the accepted evidence contract and must remain null.

A separate mutation replaced valid source locator strings with `"tampered"`; the review remained accepted. Exact locator sets therefore need to be part of the source-pin contract.
