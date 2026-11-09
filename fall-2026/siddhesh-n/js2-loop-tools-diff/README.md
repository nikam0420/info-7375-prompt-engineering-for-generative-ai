# Job-Search Agent 2 — The Loop, the Tools, and the Diff

Siddhesh Nikam · INFO 7375 · Fall 2026

**Starter status.** Codex drafted and exercised this baseline. The seeded regression is intentionally red until the student completes the Claude Code review. The student's review, decision and sign-off are pending.

## Toolchain and run commands

Python 3.12+, curl with HTTPS support, and Git on macOS or Linux. Python uses the standard library. Claude Code is used during the development review only. Run these commands in the assignment folder of a fresh clone.

```sh
python3 --version
curl --version
python3 -m unittest discover -s tests -v
mkdir -p jobs
python3 agent.py --tag ta-live --approve-raw
```

Use a fresh tag for each run. Exit 2 is expected when the deliberate invalid board fails. The trace records each attempt and its board count or null. A body is saved before parsing when an HTTP response arrives. A transport failure may have no response bytes. The tool makes one pass and exits. It counts current listings per board and does not run as a daemon.

## Evidence

- `GATE.md` defines exits, budgets, repeat identity and the tool policy. `BOUNDARIES.md` maps predictions to the executed tests.
- `evidence/codex-live2-trace.json` and matching `.raw` files contain the Codex live run. Recorded trace paths refer to the original runtime `jobs/` directory. Committed copies sit beside the trace under `evidence/`.
- `evidence/seed-wrong-trace.json` is a **seeded simulation** from the baseline. It claims finished with zero jobs. The raw object lacks a jobs array.
- `evidence/baseline-tests.txt` records the expected red regression and passing loop and permission tests before the Claude patch.
- `REVIEW.md`, `SIGNOFF.md`, `FRICTIONAL.md` and `SOURCES.md` track ownership and verification.

Check the historical seeded demonstration independently. Exit 1 demonstrates the contradiction.

```sh
python3 independent_check.py evidence/seed-missing-jobs.json evidence/seed-wrong-trace.json
```

Run the same seed against the current code and check the result. A valid fix should produce incomplete, a null count and independent checker exit 0.

```sh
python3 wrong_demo.py > jobs/current-seed-trace.json
python3 independent_check.py evidence/seed-missing-jobs.json jobs/current-seed-trace.json
```

## Live run and recomputation

Codex's revised-budget run completed four requests in 14.656 seconds. Stripe had 772 listings, Airbnb 203, and Wealthfront 23. The intentionally invalid Greenhouse board returned HTTP 404 and an unknown count, so the overall exit was incomplete (2). Recompute all three counts from the saved response bytes.

```sh
python3 check_live.py evidence/codex-live2-trace.json
```

This verifies agreement with the observed responses at capture time. It does not establish that the providers listed every opening.
