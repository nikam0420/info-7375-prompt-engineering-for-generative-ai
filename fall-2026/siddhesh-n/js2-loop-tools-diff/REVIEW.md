# Claude Code review packet

## Baseline reproduced by Codex

A seeded HTTP 200 response with no jobs array produced a finished trace with count 0. See `evidence/seed-missing-jobs.json` and `evidence/seed-wrong-trace.json`. The independent checker imports no agent code. It found the contradiction and exited 1. The Codex-authored regression example failed before any patch. See `evidence/baseline-tests.txt`.

## Diff review and decision — November 9, 2026

**Pre-patch commit:** `3c30bf1c1b0dd7530095a8295e8408c8a1357a20`

**Reproduction.** Before the patch, I ran `python3 -m unittest discover -s tests -v`. Two of the 10 tests failed because the agent reported `finished` for an HTTP 200 response with no `jobs` array. The failures were `test_missing_greenhouse_jobs_is_incomplete_with_unknown_count` and the AI-assisted `test_metadata_only_response_is_incomplete`. See `evidence/student-prepatch.txt`.

**Claude Code prompt excerpt.**
> Fix only the Greenhouse parser in agent.py. An HTTP 200 response with no jobs array must produce an incomplete run with an unknown count. An explicit empty jobs array must remain valid with count zero.

**Claude Code reply excerpt — November 9, 2026.**
> I fixed the Greenhouse parser in agent.py by removing a single default value. All 10 tests pass offline.

**What changed.** At `agent.py:75`, Claude changed `payload.get("jobs", [])` to `payload.get("jobs")`. The old default treated a missing field as an empty list and counted zero jobs. The new lookup returns `None` for a missing field. The existing schema check rejects that value, so the board is recorded as `board-failed` with an unknown count and the seeded run reports `incomplete`. A response with an explicit `{"jobs":[]}` still passes validation and counts as zero.

**Scope and verification.** I ran `git status --short`, `git diff --check`, and `git diff -- agent.py`. Only `agent.py` was modified at that point. The diff shows the lookup and its comment changing. I reran `python3 -m unittest discover -s tests -v` and all 10 tests passed with exit code 0. I also ran the independent checker on the post-patch seeded trace, and it printed `PASS`. See `evidence/claude-change.diff`, `evidence/student-postpatch.txt`, and `evidence/student-postpatch-check.txt`.

**Decision — Accept.** The patch corrected both reproduced failures, and the test for a genuinely empty array still passed.

**Coverage gap.** A provider could return a valid `jobs` array containing only some of its listings. These tests would count the rows received and miss the omitted listings.
