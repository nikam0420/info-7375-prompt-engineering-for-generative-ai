# Real board retrieval

One live fetch was made during implementation, by Claude Code running
`python3 -m watcher fetch --board stripe`. It did not touch watcher state.

| | |
|---|---|
| Board | `stripe` |
| URL | `https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true` |
| HTTP status | 200 (no redirect) |
| Response finished (UTC) | 2026-10-18T16:06:35.967132Z |
| Raw bytes | 5,695,675 |
| SHA-256 | `fa20e4bec8a765b82dd72b437d47bbff3fb4f3d3412fda56f483fc13ce18e243` |
| Validation | complete response valid; 731 postings |
| Saved at | `evidence/fetches/stripe/20261018T160635_483273Z/raw_response.bin` (+ `fetch_meta.json` with headers and timing) |

The raw file holds the exact bytes received and must not be edited. The demo
and sampling tools check its SHA-256 before use.

Aggregate observation (computed by Claude Code, titles only): 8 of the 731
titles contain a target title ("data analyst" or "business intelligence
analyst"). No per-posting record or model judgment was looked at for
sampling.
