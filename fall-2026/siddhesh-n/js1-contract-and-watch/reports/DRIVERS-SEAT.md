# Driver's-seat evidence

This file records evidence that the human directed and checked the work. Every row cites an artifact.
Claude Code compiled it on 2026-10-19 from project files. The "By" column states only what the evidence
shows. Where a file does not record who acted, the row says so. Rows marked "by Siddhesh's own confirmation" rest on
Siddhesh's 2026-10-19 statement, not on independent evidence.

## Decisions and actions

| Decision / action | By | Evidence |
|---|---|---|
| Contract drafted | ChatGPT-assisted; the wording split between ChatGPT and Siddhesh is not recorded | `CONTRACT.md` status line |
| Contract accepted and committed before implementation | Siddhesh Nikam | Status line "10/18/26 AND 11.46AM"; commit `c978ff3` at 11:48:54 EDT |
| Failure-clause date left unfilled | Siddhesh Nikam (omission) | `CONTRACT.md` line 107 |
| Implementation request with explicit limits (no labels by AI, no fabricated results, no pushing) | Siddhesh Nikam | `BUILD-PROMPT.md` |
| Asked for a CLI backend because no API key was available | Siddhesh Nikam | `SOURCES.md` "second request" |
| Ran the tests (75 OK) after the first implementation | Probably Siddhesh, based on the file names; not recorded in the files | `evidence/my-test-run.txt`, `evidence/student-test-run.txt` (12:31/12:32 EDT) |
| Seeded two-run demo | Siddhesh Nikam, **by Siddhesh's own confirmation** (2026-10-19), with ChatGPT guidance. The files do not record the operator, so this is not independent proof | `demo/stripe/DEMO-RESULT.json` (16:33Z, all checks true) |
| Ran sample selection: title-stratified strategy, seed 20261018 (this followed Claude Code's README advice) | Siddhesh Nikam, **by Siddhesh's own confirmation** (2026-10-19), with ChatGPT guidance. The files do not record the operator, so this is not independent proof | `eval/sample.json` |
| Hand-labeled 20 postings before any model output for that split | Siddhesh Nikam **with ChatGPT assistance** | Label CSV notes and `labeled_at`; `eval/label_locks.json`; `reports/SAMPLING.md` |
| Froze the revision after seeing dev results | Siddhesh Nikam, **by Siddhesh's own confirmation** (2026-10-19), with ChatGPT guidance. The files do not record the operator, so this is not independent proof | `prompts/FROZEN.json` (17:51:35Z) |
| Ran the consistency run and all four experiment runs (dev and held-out × baseline and revision) | Siddhesh Nikam, **by Siddhesh's own confirmation** (2026-10-19), with ChatGPT guidance. The files do not record the operator, so this is not independent proof | `eval/results/experiment__*__heldout__*.json` |
| Performed the three action-surface trials | Siddhesh Nikam | `reports/ACTION-SURFACE-COMPARISON.md`; `claude_outputs/2026-10-19/` |
| Kept Trial 3 state separate from the default `state/` | Siddhesh Nikam | `evidence/action-surfaces/trial3-state/` |
| Did not allow the Trial 1 reply to be reconstructed. Instead, saved a partial recovery (code fences kept, prose omitted) as a new dated import, and kept the earlier mistaken import | Siddhesh Nikam | `evidence/action-surfaces/trial1-original-recovered.txt`; `claude_outputs/2026-10-19/manual-import/20261019T200152_969009Z…json`; Trial 1 section of `reports/ACTION-SURFACE-COMPARISON.md` |

## AI suggestions accepted and rejected

| Suggestion | Source | Outcome | Evidence |
|---|---|---|---|
| Use `--strategy title-stratified` because random sampling would yield no relevant postings | Claude Code (README, FRICTIONAL C4) | **Accepted** | `eval/sample.json` `strategy` |
| Use the revision prompt that states the literal rule | Claude Code (`prompts/REVISION.md`) | **Accepted** and frozen | `prompts/FROZEN.json` |
| ChatGPT help identifying SQL and title evidence and saving labels | ChatGPT | **Accepted**, with Siddhesh's review stated in the notes | Label CSV notes |
| Describe Trial 3 as one autonomous fetch-and-judge action | Implicit framing in the report template | **Rejected** by Siddhesh, who required "two user-invoked commands" | 2026-10-19 documentation request; `reports/ACTION-SURFACE-COMPARISON.md` |
| Report the held-out labels as all decided on October 18 | Claude Code's first draft of `FRICTIONAL.md` S6 | **Rejected and corrected** by Siddhesh: only 7921649 was decided on October 18 | `FRICTIONAL.md` S6; `reports/SAMPLING.md` |
| `--bare` mode for CLI calls | Claude Code docs | Rejected by Claude Code (it cannot use an OAuth login), not by Siddhesh | `SOURCES.md` |

Siddhesh should add any other overrides only with evidence, such as a diff, a file, or a timestamp.
