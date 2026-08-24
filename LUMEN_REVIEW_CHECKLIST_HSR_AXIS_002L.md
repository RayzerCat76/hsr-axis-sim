# LUMEN Review Checklist — HSR-AXIS-002L

## Gate

- [ ] compileall passes
- [ ] complete pytest passes
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] registry v0.2 reports are deterministic and byte-identical
- [ ] Tingyun binding reports are deterministic and byte-identical
- [ ] accepted atomic artifact digest remains pinned

## Registry architecture

- [ ] static handler specification contains executor, validator, and pinned digest
- [ ] no module/callable is loaded from JSON
- [ ] handler-specific validator runs during load and execution
- [ ] actual digest equals entry digest and handler-spec digest
- [ ] all 002K strict-type and forged-handle protections remain
- [ ] registry v0.2 contains exactly two entries
- [ ] entry order is deterministic
- [ ] historical v0.1 registry and audits remain byte-identical

## Tingyun partial binding

- [ ] actor is `tingyun`
- [ ] action category is `ultimate`
- [ ] target type is `single_ally`
- [ ] action uses Ultimate interrupt semantics
- [ ] Tingyun consumes exactly 130 Energy
- [ ] selected ally gains exactly 50 Energy
- [ ] energy gain clamps at target max Energy
- [ ] insufficient actor Energy fails before target mutation
- [ ] SP does not change
- [ ] global AV does not change
- [ ] unit current AV values do not change
- [ ] no normal turn ends
- [ ] returned context has `is_interrupt=True`
- [ ] returned context has `should_end_turn=False`
- [ ] no buff is added
- [ ] no damage is dealt
- [ ] no toughness is changed

## Evidence boundary

- [ ] only three accepted executable atomic facts are bound
- [ ] damage-buff duration remains unresolved/non-executable
- [ ] damage-buff magnitude remains unresolved
- [ ] buff decrement/expiration semantics remain unresolved
- [ ] real-video target remains unknown
- [ ] synthetic target is not described as trace evidence
- [ ] no real-trace execution is authorized

## Compatibility

- [ ] Pela registry execution remains exact
- [ ] Pela validator still rejects altered binding data
- [ ] unknown handlers remain rejected
- [ ] malformed and forged registry objects remain controlled failures
- [ ] no generic simulator/search/evaluator/manifest change

## Scope

- [ ] no Tingyun Skill
- [ ] no complete Tingyun Ultimate
- [ ] no complete Tingyun kit
- [ ] no playable character-data registration
- [ ] no DMG-increase buff
- [ ] no trace target inference
