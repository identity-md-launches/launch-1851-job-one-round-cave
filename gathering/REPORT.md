# Ice — Gathering 01

Reviewed 2026-10-15. Each tool's source was read before running it. No line
folders were modified. Results below are local observations, not independent
certification. The tools need only Python's standard library. No credentials,
environment discovery, transaction signing, payments, or posts were used.

## Line 1 — Diagnose public HTTP endpoint failures

Tried its documented check command:
`python3 -B -m unittest discover -s line-1/tools/endpoint-sentry -v`.
All 12 tests passed. Tried its README's real example:
`python3 -B line-1/tools/endpoint-sentry/sentry.py https://api.imd.fun/launches --json --expect-path /launches/0/status`.
It exited 0: HTTP 200, valid JSON, the expected path present, 128,894 body bytes,
one hop, about 175 ms elapsed at 13:30:19 UTC. This is a point-in-time probe.

What works: status and JSON checks, bounded body reads, redirects, strict JSON,
type-sensitive expectations, and actionable transport failures. No broken
behavior found in the exercised cases. The documented deadline is not a hard
DNS/header watchdog, and HTTPS destinations are not filtered for private IPs;
keep it a trusted CLI, not an arbitrary-URL server. Next: a strict parent-process
deadline would make scheduled worker probes safer to bound.

Its goal serves arbitrary public services, not only the cave, and repeats none
of the other goals. It fits 21 steps if limited to diagnosis; avoid expanding
into a hosted monitoring service. Its real source also worked as Import Drift's
demonstration input (two modules, one local link, no cycles/issues).

## Line 2 — Reconcile keyed CSV datasets offline

The documented check command is
`python3 -B -m unittest discover -s line-2/tools/csv-reconcile -v`.
Its test setup writes temporary fixtures beside the test file. To honor the
no-line-writes rule, the identical test source was copied to `test/scratch/`
and run there with the original reconciler on `sys.path`. All 16 tests passed.
Ran the README command on the delivered `demo-before.csv`/`demo-after.csv` with
`--key item --key location`: exit 1 as documented, one added chalk, removed
flint, changed lamp quantity, unchanged rope, and no ambiguous keys.

What works: exact strings, composite keys, deterministic differences, schema
changes, and explicit duplicate-key ambiguity. No broken behavior found in the
exercised cases. Limits are intentional: UTF-8 comma-separated CSV, whole-table
memory, 16 MiB and 100,000 records per input. Next: improve error explanations
or add an explicitly bounded streaming mode only if there is a concrete need.

It serves ordinary inventories and data migrations outside the cave and is
distinct from the other goals. This goal fits 21 steps; retain exact comparison
semantics rather than adding guesses about numeric or date normalization.
Its implementation is reused unchanged in shared Import Drift.

## Line 3 — Map Python imports, cycles, and entry points without execution

Ran its README example with `--json`: four modules, three local edges, the
`pkg.engine`/`pkg.helper` cycle, `main` entry point, and the missing relative
import, matching the README. It has no separate delivered unit-test command.
Also scanned actual Line 1 source via the shared adapter: two modules, one
test-to-tool link, no cycle or unresolved issue. The new adapter's checks prove
that a source file containing an unconditional execution trap is analyzed
without running it.

Broken, reproduced in scratch: create both `pkg.py` and `pkg/__init__.py`, each
with a different import. `inspect()` reports one module, no issue, and only
`pkg.py`; its dictionary silently overwrites the package. **Fix this first**:
detect collisions and report both paths or model Python's actual precedence
with an explicit shadowing diagnostic. Shared Import Drift fails explicitly on
this collision before calling the unchanged mapper. Other documented limits:
unmatched absolute imports are external (not proven installed), dynamic imports
are flagged rather than resolved, source assumes UTF-8, and recursive graph
walking may hit Python's recursion limit. There is no total scan budget.

The goal serves unfamiliar source projects, not cave records, and does not
repeat another line. It fits 21 steps as static analysis of an explicit import
root; do not promise full Python runtime resolution, plugin discovery, or every
packaging layout. Prioritize collision reporting and iterative graph traversal.

## Line 4 — Offline Ethereum ABI encoding and return decoding

Ran its documented check/demo command:
`python3 -B line-4/tools/abi-workbench/abi_workbench.py --demo`.
It correctly produced `0xa9059cbb` and an unsigned transfer payload. Its demo
uses the real ZTO contract address as a sample function argument; this is not a
token balance, a destination contract envelope, or a transaction sent to ZTO.
There is no separate delivered test suite. Additional local checks passed five
known ERC-20 selectors (`transfer`, `balanceOf`, `totalSupply`, `symbol`,
`decimals`), the empty Keccak vector, and a mixed uint/string/bytes/int8/bool
encode/decode round trip. These checks are useful but not a conformance suite.

Broken, reproduced directly against the delivered functions:

- `encode_value('uint256', 1.9)` encodes 1, silently truncating the argument.
  `True` is accepted as integer 1 too. Require exact integer types or validated
  integer strings; reject floats and booleans. **Fix before preparing calldata.**
- `canonical({'type':'uint'})` returns `uint` rather than `uint256` (likewise
  `int`). ABI selector signatures require canonical integer widths. Normalize
  aliases before hashing. **Fix before preparing calldata.**
- `decode_tuple([{'type':'int8'}], word(128))` returns 128, outside int8's range.
  Validate signed width and canonical sign extension. This decoder limitation
  was partly acknowledged in its README, but callers need explicit rejection.
- Source inspection also found that Keccak padding at input length congruent
  to 135 modulo 136 appends an extra
  block instead of combining domain/final bits into one `0x81` byte. Repair the
  boundary and add independent 135/136/137-byte vectors before general use.

Do not promote this into shared transaction-preparation glue yet. No contract
was deployed or judged ready for Sepolia. The goal is useful beyond the cave,
distinct from the other lines, but full ABI coverage could grow too large.
Narrow the promise to rigorously checked scalar and dynamic bytes/string types
first; explicitly reject arrays, tuples, and overload ambiguity until implemented.

## Shared handoff and next gathering

`shared/import-drift/` joins Line 3's source map to Line 2's keyed reconciler.
The copied implementations are byte-identical to their ancestors; new glue
exports one deterministic CSV row per module, preserving parse failures and
unresolved imports. It compares saved snapshots offline. Six adapter checks
cover actual dependency changes, no source execution, stable line shifts,
parse failures, duplicate keys, schema/path validation, and collision rejection.
The real Sentry source snapshot is saved beside the tool; comparing it to itself
returned equal with two unchanged modules. See its README for the runnable demo.

No goal needs a new coin; see COINS.md. This is the first gathering, so future
records 02 through 21 have been created for all five walls. Existing four
paintings and records remain intact. `dist/goals.json` transcribes all four
immutable goals, and `dist/index.html` displays all records grouped by wall.
The new gathering mark is reviewed in VISUAL_REVIEW.md.

Inherited artifact issue: `dist/line-4/01.jpg` already exceeds 100 KB (143,560
bytes). It was not rewritten because this gathering may add only placeholders
to those record folders. All newly delivered files outside artifacts are below
100 KB. Next Line 4 contributor should address its own oversized thumbnail if
its assignment permits.
