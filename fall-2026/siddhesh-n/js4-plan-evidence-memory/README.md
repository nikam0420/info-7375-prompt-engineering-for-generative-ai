# Job-Search Agent 4 — The Plan, the Evidence, and the Memory

Siddhesh Nikam · INFO 7375 · Fictional persona Morgan

The replay extends the JS3 Python scorer. Two watchers apply different thresholds to identical input. They share code and source data, so they are neither independent reviewers nor independent evidence about a posting. Each watcher stages its own notes from the same version. The shared file uses an exclusive POSIX file lock, revision comparison and atomic replacement.

## Run locally

Use Python 3.12 on macOS or Linux. Git is needed for version posting. No Python packages or credentials are needed for the replay. Northeastern's Claude access is available through the university portal for plan review.

From this folder, after recording the real review in PLAN.md, run these commands. Choose an unused output path for another replay.

```sh
python3 -B -m unittest -v
python3 -B agent.py --output replay-output
```

PLAN.md records dependencies and guardrails. PREMORTEM.md records the predicted overwrite. EVIDENCE-MATRIX.md maps every posting claim to a check. The two fixtures are fictional, seeded observations. Fixture pay 42 represents a fictional USD hourly minimum. Null means unknown.

A successful replay writes positive check ledgers, the rejected planted pay summary, daily conflict records, end-of-day states, notes and a diff. The day-two 404 supersedes the earlier fictional live observation. The CLI refuses an existing output directory. On a failed positive check it writes the failed ledger and stops before merging the failing day's claims.

Recorded run: six unit tests passed under Python 3.12.14. Inspect evidence/unit-tests.txt and evidence/replay. Notes reached revision 4. Posting a went from live to gone with direct 404 evidence. P-104 changed from live to unknown after both records were absent. The pay control rejected 99 against the trace value 42. Both stale writes were rejected. Siddhesh Nikam reran the six tests and seeded replay on macOS and recorded his verification in `SIGN-OFF.md`.
