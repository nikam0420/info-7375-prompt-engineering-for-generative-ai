# Frictional

## Codex-assisted starter record — 2026-11-09

- The seeded Greenhouse error-shaped object arrived with HTTP 200. The baseline converted its missing jobs field to zero and finished. A schema check independent of agent code found the mismatch. See the seed trace and check in `evidence/`.
- A live trial bypassed the environment's HTTPS proxy and failed DNS resolution. Using the configured transport reached Airbnb and the deliberate HTTP 404, while two boards timed out on the five-second ceiling. See `evidence/codex-network-attempt.json` and `evidence/codex-initial-live-trace.json`. The draft gate records the revised budgets before the later trial.

## Personal entries

### November 9, 2026 — Reproducing and reviewing the parser bug

- My first run discovered only the nine starter tests. After adding the AI-assisted metadata-only case, I reran the suite and confirmed that it discovered ten tests. Both missing-field cases failed because the agent returned `finished` for an HTTP 200 response without a `jobs` array. See `evidence/student-prepatch.txt`.
- Claude Code initially reported that my login had expired. I signed in again with `/login`, resent the scoped prompt, and inspected the resulting diff. Claude removed the empty-list fallback from the Greenhouse parser.
- I reran all ten tests and got exit code 0. The independent seed checker printed `PASS`, and the explicit empty-array test still passed. See `evidence/claude-change.diff` and `evidence/student-postpatch.txt`.
- A valid-looking response could still omit listings. Recomputing the saved counts only verifies what was in the captured responses.
