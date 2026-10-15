# CSV Reconcile

Compare two CSV datasets by one or more stable key columns. Get a deterministic JSON explanation of added rows, removed rows, changed fields, schema changes, and duplicate keys that cannot be safely paired. This helps a worker check an inventory export, migration, catalog, or other tabular handoff without depending on row order or a spreadsheet application.

Python 3.9+; standard library only. No installation, network, account, coin, wallet, or environment-variable access. Inputs must resolve inside the current working directory, including through symlinks. The program only reads the two specified CSV files and prints its report; it does not modify them. Run from the workspace root.

## One command to see it working

```sh
python3 -B line-2/tools/csv-reconcile/reconcile.py line-2/tools/csv-reconcile/demo-before.csv line-2/tools/csv-reconcile/demo-after.csv --key item --key location
```

The bundled fixtures are explicitly synthetic inventory examples. When tried, this reported one addition (`chalk`), one removal (`flint`), one changed quantity (`lamp`, `1` → `2`), one unchanged row (`rope`), and no ambiguous keys. Exit status **1 is expected**, because those datasets differ.

For your own files, replace the two paths and key names. Repeat `--key` for a composite key, or `--ignore` for a non-key column such as an export timestamp. To save a report, redirect stdout to a file inside your permitted workspace.

Exit statuses: **0** = equal; **1** = differences or ambiguity; **2** = invalid input or I/O failure (JSON error on stderr). A parser usage error also exits 2, with argparse usage text. Duplicate keys make `complete` false, even when all duplicate rows look identical; the tool never guesses a pairing. `equal` is false whenever ambiguity exists.

## Comparison contract and limits

- UTF-8 (optional BOM), comma delimiter, standard double-quote escaping, with a required unique, nonempty header. Embedded commas, newlines, and Unicode are supported. Record numbers count logical CSV records, including the header as record 1; they are not physical line numbers.
- Values are exact strings: no whitespace trimming, numeric conversion, timestamp normalization, or Unicode normalization. An empty key is a literal empty string, and duplicates of it are ambiguous too. Composite keys are tuples, so concatenation collisions cannot occur.
- Row and column ordering do not affect equality. Key groups and field differences have deterministic Unicode string order. Source record numbers still reflect source ordering.
- Added/removed columns appear in `schema`. `changed` compares common, nonignored, non-key columns only. A schema change prevents equality even if every common value matches. `unchanged_on_common_columns` explicitly counts matches only on that common projection.
- Rows under any key duplicated on either side are excluded from added/removed/changed/unchanged classification. `ambiguous` contains every occurrence from both sides, with original values and record numbers, to support manual resolution. These raw ambiguity entries also retain ignored columns; `--ignore` is a comparison option, not a redaction feature.
- At most 16 MiB and 100,000 data records per input. Both inputs are held in memory, and large reports can also be large. Malformed quoting, empty records, ragged rows, invalid encoding, missing keys, duplicate headers, and unknown ignore columns fail explicitly. No delimiter inference or automatic repair.
- No chain or swarm data was needed or fetched for this offline tool. Its fixtures demonstrate behavior, not real holdings or transactions.

## Checks performed

```sh
python3 -B -m unittest discover -s line-2/tools/csv-reconcile -v
```

All 16 tests passed on this assignment. They cover reordered rows/columns, additions/removals/changes, exact numeric-looking strings, duplicate keys on either side, composite-key collisions, multiline quoting, BOM/Unicode, schema differences, ignored fields, empty tables, empty keys, malformed input, invalid options, resource bounds, encoding, workspace path containment, and CLI exit statuses. Tests create and remove temporary fixture folders beside the test file. They use no external packages or network.
