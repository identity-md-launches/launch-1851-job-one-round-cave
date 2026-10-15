# Gathering 01 reuse

- `import-drift/import_map.py`: byte-for-byte copy of
  `line-3/tools/import-map/import_map.py`, reviewed as source before execution.
- `import-drift/reconcile.py`: byte-for-byte copy of
  `line-2/tools/csv-reconcile/reconcile.py`, reviewed as source before execution.
- `import-drift/drift.py`: new module-keyed CSV adapter and comparison CLI.
- Endpoint Sentry's real source is a snapshot demonstration input.
- ABI Workbench was reviewed and checked, but not copied into a shared payment
  tool because the gathering found correctness bugs listed in REPORT.md.

No line source or record was changed. The gathering adds only future placeholder
records under `dist/line-N/`, as explicitly requested for the first gathering.
