# LUMEN Review Checklist — HSR-AXIS-002L-FIX

## Core gates

- [ ] compileall passes
- [ ] complete pytest passes
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] registry and Tingyun committed reports remain deterministic

## Validator safety

- [ ] Tingyun source fact IDs reject non-string members with ValueError
- [ ] Tingyun unresolved fact IDs reject non-string members with ValueError
- [ ] Tingyun unresolved fields reject non-string members with ValueError
- [ ] Pela source fact IDs reject non-string members with ValueError
- [ ] Pela unresolved fact IDs reject non-string members with ValueError
- [ ] atomic_facts rejects non-object items
- [ ] atomic_fact_id rejects non-string/empty values
- [ ] duplicate atomic fact IDs are rejected
- [ ] duplicate binding fact IDs are rejected
- [ ] no set/dict construction occurs before member type validation

## CLI behavior

- [ ] malformed package-contained Tingyun binding returns controlled nonzero exit
- [ ] malformed package-contained Pela binding returns controlled nonzero exit
- [ ] malformed binding stderr contains no Traceback
- [ ] validators themselves raise ValueError, not TypeError/AttributeError

## Behavior preservation

- [ ] Tingyun interrupt/resource fixture remains exact
- [ ] insufficient Tingyun Energy still fails before target mutation
- [ ] target Energy clamp remains exact
- [ ] no SP/AV/HP/toughness/buff mutation is introduced
- [ ] Pela reviewed execution remains exact
- [ ] registry still contains exactly two partial bindings
- [ ] static handler dispatch and pinned digests remain intact
- [ ] historical v0.1/Pela artifacts remain byte-identical

## Scope

- [ ] no Tingyun damage buff
- [ ] no new source research or fact normalization
- [ ] no real-video target inference
- [ ] no complete skill/kit registration
- [ ] no 002M work
