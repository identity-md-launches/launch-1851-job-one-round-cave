# Import Map

Import Map reads Python source with the standard library AST parser. It reports local import links, strongly connected import cycles, `if __name__ == "__main__"` entry points, unresolved local or relative imports, parse errors, and calls to `__import__` or `importlib.import_module`. It never imports or executes the inspected project.

Run the included example from the repository root:

```sh
python3 line-3/tools/import-map/import_map.py line-3/tools/import-map/examples
```

When tried locally, it found four modules, three local edges, the `pkg.engine`/`pkg.helper` cycle, `main` as an entry point, and the absent `pkg.missing` import. `--json` emits a deterministic machine-readable report; `--strict` exits 1 when a cycle or issue is found.

I also ran it on the existing `line-1/tools/endpoint-sentry` and `line-2/tools/csv-reconcile` source trees. Each scan found two modules and the test module's local import of its tool, with no cycles or unresolved imports. These scans read source only and did not run either tool.

The root is an import root, so a `src/` project should be scanned from `src/`. Absolute imports without a matching local top-level name are labeled external rather than missing, since source inspection cannot prove whether a third-party module is installed. `from module import name` may name an attribute rather than a submodule; the tool conservatively links to the known module. Dynamic import targets are flagged but not inferred.
