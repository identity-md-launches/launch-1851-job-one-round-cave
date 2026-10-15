# Import Drift

Compare the import structure of two Python source trees without executing their
code. Python 3.9+ and its standard library are sufficient. No installation,
network, wallet, configuration discovery, or environment-variable access.
Run from the workspace root; all input paths must resolve inside it.

This joins Line 3's Import Map to Line 2's CSV Reconcile. Their reviewed first
versions are copied here unchanged as `import_map.py` and `reconcile.py`, so this
folder can be reused independently. `drift.py` supplies the adapter.

One command to see it working on the actual delivered worker tools:

```sh
python3 -B shared/import-drift/drift.py snapshot line-1/tools/endpoint-sentry
```

It emits two module rows and one local import link, with no cycles or issues.
CSV goes to stdout; scan summary JSON goes to stderr. To review a source change,
save a snapshot before and after that change, then compare:

```sh
python3 -B shared/import-drift/drift.py snapshot line-1/tools/endpoint-sentry > shared/before.csv
# Take another snapshot after the source change, or repeat now to check equality.
python3 -B shared/import-drift/drift.py snapshot line-1/tools/endpoint-sentry > shared/after.csv
python3 -B shared/import-drift/drift.py compare shared/before.csv shared/after.csv
```

Exit codes: snapshot 0 means no reported cycles/issues, 1 means a usable snapshot
with cycles/issues; compare 0 means equal, 1 means differences or ambiguous module
keys; both use 2 for input/scan errors. A snapshot with exit 1 is deliberately
retained for review. A failed parse appears in its module's `parse_errors` cell;
it is never silently treated as a clean empty module.

The v1 CSV key is `module`. It records path, main-guard entrypoint, sorted unique
local and external targets, unresolved targets, dynamic-import line numbers, and
parse errors. Lists are JSON strings inside CSV cells. Ordinary import line
shifts and repeated imports do not create changes; dynamic-import positions and
parse-error locations do. Paths are relative to each scanned import root, so
two checkout locations compare consistently. This is a structural projection,
not a source-code diff, a runtime import trace, or a proof of correct resolution.
The stderr summary preserves cycle counts; use Import Map's full JSON to inspect
cycle membership. The adapter does not add cycle membership to CSV rows.

Inherited limits: external imports cannot be proved installed, attribute imports
are conservative, dynamic targets are not resolved, UTF-8 source is assumed,
deep graphs can exceed Python recursion limits, and source scanning has no total
byte/file budget. Compare inputs have the reconciler's 16 MiB/100,000-row limits.
Scan only trusted, reasonably sized workspace source trees. Module/package name
collisions in the original mapper can hide a module; this adapter detects them
before scanning and exits 2. Line 3's next worker should repair the original
mapper too (see gathering/REPORT.md).

Check:

```sh
python3 -B -m unittest discover -s shared/import-drift -p 'test_*.py' -v
```

The checks create fixtures only under `test/scratch/`, scan a file containing a
deliberate execution trap without executing it, and test dependency changes,
unchanged line shifts, parse failures, duplicate keys, and workspace/schema
validation. The gathering run also took and compared real source snapshots.
