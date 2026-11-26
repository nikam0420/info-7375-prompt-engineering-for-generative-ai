# Job-Search Agent 3 — The Filter, the Tool, and the Score

Siddhesh Nikam | INFO 7375 | Fictional search persona: Morgan.

This project extends the submitted JS2 bounded collection loop and reuses the JS1 UTF-8 JSON decoder carried by JS2. JS1’s locked Stripe labels support a separate historical threshold check. It collects from Stripe and Airbnb Greenhouse and Wealthfront Lever, scores the visible posting text, samples decisions for review, and exposes a single scoring tool. The filter design was recorded before starting the implementation.

## Toolchain and run

Python 3.12.14, Git 2.56.1, and curl 8.14.1 were used for verification. Python uses the standard library. Live collection calls curl. A browser opens the locally generated review sheet. Use course-provided Claude Code access through Northeastern to verify the Claude exchange.

```sh
python3 -m unittest -v
python3 demo.py
python3 collect.py
python3 run.py
```

Run these commands from this directory. The first two work offline. The last two create a new snapshot and draw new samples if the boards changed. The recorded run collected 771 Stripe, 199 Airbnb, and 19 Wealthfront postings. The frozen score ledger covers all 989 postings. The normalized description corpus stays under ignored `local/`. The archived evidence contains derived results, manifests and small source excerpts. The adapted JS2 collector was then run and scored all 990 postings in a second snapshot. Its results are in `evidence/js2-live-*`. All 62 original review rows had identical normalized fields in the second run. The first sample remains frozen. Keep the matching `evidence/sample.json` and `evidence/scores.csv` when importing review labels for the recorded run.

### Student review

Open `local/review.html` in a browser or use the review sheet preserved for the original run. Read the duties and select a verdict with a reason. Click **Download judgments**, then run:

```sh
python3 run.py --labels /path/to/human-labels.json
```

This writes human verdicts and group-level counts to `evidence/`. The exported labels and computed audit are included. Complete the personal sign-off using the checks you actually performed.

| File | Contents |
|---|---|
| FILTER.md | Versioned rules, evidence contract and sampling amendment |
| AUDIT.md and evidence/sample.json | Reject audit design, sample manifest and observed false friend |
| SHORTLIST.md and evidence/shortlist.json | Claim evidence and an abstention example |
| TOOL-EVALUATION.md and evidence/demo-wire.jsonl | Both evaluations, actual Python-client wire exchange, and Claude setup |
| EXPERIMENT.md and evidence/run-summary.json | Threshold-only comparison and prediction changes |
| SIGN-OFF.md | Verification attribution and driver's seat |
| SOURCES.md and FRICTIONAL.md | Provenance and observed revisions |

The initial package records 11 passing tests and six checked server replies. For the 10 historical JS1 hand labels, rerun `python3 historical_check.py "/path/to/submitted-JS1.zip"`. The script verifies the held-out lock and scores the archived posting bodies at 4 and 5. The resulting historical ledger is in `evidence/js1-heldout.json`. All 62 current JS3 verdicts are included. A live Claude Code exchange is recorded in `evidence/claude-wire-excerpt.jsonl`. The personal sign-off remains withheld pending the student signature.
