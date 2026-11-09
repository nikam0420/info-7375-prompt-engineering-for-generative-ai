# Claude Code review packet — student to complete

## Baseline reproduced by Codex

A seeded HTTP 200 response with no jobs array produced a finished trace with count 0. See `evidence/seed-missing-jobs.json` and `evidence/seed-wrong-trace.json`. The independent checker imports no agent code. It found the contradiction and exited 1. The Codex-authored regression example failed before any patch. See `evidence/baseline-tests.txt`.

## My review evidence

- Pre-patch commit and date: [fill]
- My own test name and assertion: [fill]
- My pre-patch command, evidence filename and actual exit: [fill]
- Claude Code date, actual prompt excerpt, actual reply excerpt and changed file: [fill]
- Behavior before and after, with diff lines: [fill]
- Scope check from git diff and git status: [fill]
- Commands I ran after Claude Code and actual results: [fill]
- Decision and evidence to accept, revise or reject: [fill]
- A real case my test still misses: [fill]

Keep the Codex baseline separate from your personal evidence. Save only sanitized Claude excerpts and the code diff.
