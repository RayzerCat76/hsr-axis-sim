# LUMEN Review Checklist — HSR-AXIS-002K-FIX

## Gate

- [ ] compileall passes
- [ ] complete pytest passes
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] registry audit reports remain deterministic and byte-identical
- [ ] accepted atomic digest remains unchanged

## Strict schema

- [ ] registry root is required to be an object
- [ ] registry version is a non-empty string
- [ ] every entry is an object
- [ ] scalar string fields reject empty/non-string values
- [ ] boolean fields reject 0/1/string/null and require exact bool
- [ ] collection fields require lists of non-empty strings
- [ ] collection-internal duplicates are rejected
- [ ] SHA-256 is exactly 64 lowercase hex characters
- [ ] malformed types cannot reach unsafe `set`, `sorted`, or hashing operations

## Execution boundary

- [ ] supplied registry objects are revalidated before execution
- [ ] manually forged handles cannot bypass path, flag, digest, metadata, or handler checks
- [ ] no dynamic imports from registry JSON
- [ ] unknown binding/handler fails clearly
- [ ] accepted Pela synthetic execution remains exact

## CLI

- [ ] validation failures exit 1
- [ ] unreadable/invalid JSON exits 2
- [ ] malformed nested values never print a traceback

## Scope

- [ ] exactly one registry entry remains
- [ ] no Tingyun Ultimate
- [ ] no complete skill/kit claim
- [ ] no real-trace execution
- [ ] no damage/toughness implementation
- [ ] no simulator/search/manifest changes
