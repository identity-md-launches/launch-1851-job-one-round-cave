# Endpoint Sentry

Diagnose a public HTTPS endpoint with one anonymous GET. Python 3.9+ and its standard library are the only runtime dependencies. No installation is needed.

From the repository root, see it working on the real swarm:

```sh
python3 -B line-1/tools/endpoint-sentry/sentry.py https://api.imd.fun/launches --json --expect-path /launches/0/status
```

The command prints a JSON report and exits 0 when every requested check passes, 1 for a failed probe, or 2 for invalid command arguments. It records each redirect, HTTP status, header latency, final body length and SHA-256, total elapsed time, explicit limits, and individual check results. It does not print or save response bodies. Timestamps and timings describe observations, not guarantees of future availability.

Require a particular JSON value, including its type:

```sh
python3 -B line-1/tools/endpoint-sentry/sentry.py https://api.imd.fun/launches --expect-path /launches/0/chainId --expect-value 1
```

That example intentionally depends on the newest launch being on Ethereum; a different chain produces a failed value check. Use a stable application-specific expectation for monitoring. JSON pointers follow RFC 6901: `/items/0/name`, `~1` for a slash in a key, `~0` for a tilde, and an empty pointer for the whole document. JSON parsing rejects duplicate keys, non-finite numbers, malformed UTF-8, and malformed documents. Numeric `1` and boolean `true` are different expectations.

## Bounds and transport

Defaults are 10 seconds, 1 MiB, and at most three redirects. Override with `--timeout`, `--max-bytes`, and `--max-redirects`. Redirects must remain HTTPS and cannot introduce credentials. The tool sends its own User-Agent, requests identity encoding, verifies TLS certificates, and refuses compressed responses so the byte limit is unambiguous. A response over the limit fails after reading at most one byte beyond it. Incorrect Content-Length, missing redirect locations, and redirect loops fail explicitly. An HTTP error is still reported, with its status check, rather than disappearing into a generic exception.

The time budget is shared across hops and body reads; socket timeouts use the remaining budget. OS DNS resolution and the HTTP library's header processing may exceed the nominal deadline, so this is not a hard process watchdog. Probing is sequential, with no retries, timer, background process, or writes. Add an external process timeout when your orchestration needs a strict wall-clock limit.

Only use public, non-secret URLs whose GET semantics you trust. HTTPS does not imply that a URL is public; private-network destinations are not filtered. This is a diagnostic CLI, not an SSRF boundary for a server accepting untrusted URLs. It uses direct connections, no environment proxy discovery, no authentication, cookies, wallet, signing, transaction sending, or HTTP mutation methods. URL query strings and redirect URLs appear in reports, so do not pass secret-bearing URLs. It never opens a local input file or writes a report file itself; shell redirection is optional.

## What happened when tried

On 2026-10-15, the real `https://api.imd.fun/launches` returned HTTP 200, valid JSON, and an existing `/launches/0/status`. The probe exited 0. The real API root `https://api.imd.fun` returned HTTP 404 and failed the default HTTP 200 expectation with exit 1. Small, body-free reports are preserved in `live-success.json` and `live-failure.json`; they are historical observations and not offline substitutes for a live request.

Run the offline checks, which need neither internet nor installed packages:

```sh
python3 -B -m unittest discover -s line-1/tools/endpoint-sentry -v
```

All 12 tests passed. Fixtures exercise success, status mismatch, redirects and downgrade refusal, byte limits, truncated/compressed responses, invalid JSON, pointer escaping, missing paths, value types, network failure categories, and CLI validation. Fixtures test response handling; the live run separately exercises DNS, TLS, and the real HTTP service. Future pieces can add retry policies, comparisons across providers, or a strict process watchdog without changing this tool's default single-GET behavior.
