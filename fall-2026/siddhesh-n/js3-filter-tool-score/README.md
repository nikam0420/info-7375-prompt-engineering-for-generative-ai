# Job-Search Agent 3 — The Filter, the Tool, and the Score

Siddhesh Nikam | INFO 7375 | Fictional search persona: Morgan.

This project builds on the public board choices of JS2. It collects from Stripe and Airbnb Greenhouse and Wealthfront Lever, scores the visible posting text, samples decisions for review, and exposes a single scoring tool. The filter design was recorded before starting the implementation.

## Toolchain and run

Python 3.12.14 and Git 2.56.1 were used for verification. Python uses the standard library only. A browser opens the locally generated review sheet. Claude Code is optional for verifying the live client exchange.

```sh
python3 -m unittest -v
python3 demo.py
python3 collect.py
python3 run.py
```

Run these commands from this directory. The first two work offline. The last two create a new snapshot and draw new samples if the boards changed. The recorded run collected 771 Stripe, 199 Airbnb, and 19 Wealthfront postings. The frozen score ledger covers all 989 postings. The normalized description corpus stays under ignored `local/`. The archived evidence contains derived results, manifests and small source excerpts. Keep the matching `evidence/sample.json` and `evidence/scores.csv` when importing review labels for the recorded run.

### Student review

Open `local/review.html` in a browser or use the review sheet preserved for the original run. Read the duties and select a verdict with a reason. Click **Download judgments**, then run:

```sh
python3 run.py --labels /path/to/human-labels.json
```

This writes human verdicts and group-level counts to `evidence/`. Before submission, fill in the audit result and sign-off using the checks you actually performed.

| File | Contents |
|---|---|
| FILTER.md | Versioned rules, evidence contract and sampling amendment |
| AUDIT.md and evidence/sample.json | Reject audit design, sample manifest and observed false friend |
| SHORTLIST.md and evidence/shortlist.json | Claim evidence and an abstention example |
| TOOL-EVALUATION.md and evidence/demo-wire.jsonl | Both evaluations, actual Python-client wire exchange, and Claude setup |
| EXPERIMENT.md and evidence/run-summary.json | Threshold-only comparison and prediction changes |
| SIGN-OFF.md | Verification attribution and driver's seat |
| SOURCES.md and FRICTIONAL.md | Provenance and observed revisions |

The initial package records 10 passing tests and six checked server replies. Human labels, a live Claude exchange, and student sign-off are pending at initial packaging.
