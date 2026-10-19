# Sign-off

**Status: NOT SIGNED. The signature is WITHHELD until Siddhesh Nikam reviews the work.**

The canonical sign-off, including its checklist and nonclaims, is the last section of [`README.md`](../README.md).
This file only summarizes the state as of 2026-10-19 (compiled by Claude Code).

| Item | State | Evidence |
|---|---|---|
| Unit tests pass | 91 OK, run by Claude Code on 2026-10-19 (a Claude-run check). The earlier 75-test runs (2026-10-18) were saved in two files | `evidence/claude-test-run.txt`; `evidence/my-test-run.txt` |
| Real board fetched | Done | `evidence/RETRIEVAL.md` |
| Seeded two-run demo | Done; all checks true | `demo/stripe/DEMO-RESULT.json` |
| 20-posting sample | Done; title-stratified | `eval/sample.json` |
| Hand labels (10 + 10) | Done, ChatGPT-assisted; 3 dev rows have inconsistent condition columns | `eval/hand_labels_*.csv`, `reports/SAMPLING.md` |
| Consistency (5 × 4) | Done; 20/20 valid and stable | `reports/SAMPLING.md` |
| Dev experiment | Baseline 9/10, revision 10/10 | `reports/PROMPT-EXPERIMENT.md` |
| Revision frozen | 2026-10-18T17:51:35Z | `prompts/FROZEN.json` |
| Held-out experiment | Baseline 10/10, revision 10/10; no improvement | `reports/PROMPT-EXPERIMENT.md` |
| Action-surface trials | Performed. Trial 1: a clipboard error (Import A), then a partial recovery that keeps the fences but omits the prose (Import B); both were rejected | `reports/ACTION-SURFACE-COMPARISON.md` |
| FRICTIONAL.md entries for the signer | Drafted from evidence; not yet confirmed | `FRICTIONAL.md` S1–S6 |
| Contract failure-clause timestamp | **Unfilled** in the committed contract | `CONTRACT.md` line 107 |

Signature: **WITHHELD**
Name: Siddhesh Nikam
Date/time: _withheld_
