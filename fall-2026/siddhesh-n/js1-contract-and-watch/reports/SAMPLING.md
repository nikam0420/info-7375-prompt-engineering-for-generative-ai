# Sampling report

**Status: complete.** This report was written by Claude Code (Claude Opus 5.5) on 2026-10-19
from the saved records cited below. No model call was re-run for it. Claude Code
re-derived every verdict from the raw `*.stdout.bin` bytes using the project's own validator
(`watcher/judgment.py`), and each one matched the saved summaries. Siddhesh Nikam still
needs to review this report (see the sign-off in `README.md`).

## Source

- Board: `stripe`
- Raw response: `evidence/fetches/stripe/20261018T160635_483273Z/raw_response.bin`
  (SHA-256 `fa20e4bec8a765b82dd72b437d47bbff3fb4f3d3412fda56f483fc13ce18e243`,
  retrieved 2026-10-18T16:06:35.967132Z, 731 postings). The hash was rechecked on 2026-10-19 and is unchanged.

## Draw (from `eval/sample.json`)

- Created: 2026-10-18T16:35:41.238712Z. The file does not record the operator. Siddhesh confirms (2026-10-19) that Siddhesh
  personally ran `sample-select` and the consistency run, with ChatGPT guidance. This is Siddhesh's statement, not independent proof.
- Seed: `20261018`. This is the same value as the demo seed that Claude Code suggested in the README.
- Strategy: **title-stratified**. All 8 postings whose title contains a target title were included,
  plus 12 of the other 723. Selection used titles only. The reason is in `FRICTIONAL.md` C4: a random 20 out of 731
  would very likely contain no relevant posting.
- Consequence: the sample is **not representative of the board**. 8 of 20 sampled titles match (40%),
  against 8 of 731 on the board (≈1.1%). Agreement rates from this sample do not estimate
  agreement on the board as a whole.
- Dev IDs (10): 8189909, 5416444, 8194291, 8194287, 8094087, 8044391, 7913702, 8198323, 8110261, 8230276
- Held-out IDs (10): 7921649, 8186442, 8044924, 8230296, 8209649, 7544547, 8244515, 8224617, 7961101, 7728618

## Hand labels

- Labeler: Siddhesh Nikam, **with ChatGPT assistance**. Every row's `notes` says so, with wording like
  "ChatGPT helped identify this evidence; I reviewed it" or "ChatGPT assisted with saving". These are
  AI-assisted labels, not independent human labels.
- Dev: `labeled_at` runs from 2026-10-18 12:43:35 to 13:15:49 EDT (16:43–17:15Z). The lock was
  2026-10-18T17:29:03Z. Lock hash `23f4194a…` still matches the file.
- Held-out: `labeled_at` runs from 2026-10-19 14:52:06 to 15:07:56 EDT (18:52–19:07Z). The lock was
  2026-10-19T19:08:43Z. Lock hash `cdc5d71b…` still matches the file. The note on 7921649 says the label
  was chosen on October 18 and saved October 19. That applies to 7921649 only. Siddhesh states that the other nine were decided and saved on October 19.
- Model output before labeling: no saved Claude output for any posting exists before that split's labels were
  finished. The first Claude record (`claude_outputs/2026-10-18/adhoc/…172814…`, posting 8189909)
  starts at 17:28:14Z, after the last dev label. Held-out IDs appear only in the two held-out run
  directories, and both started after 19:08:43Z. This is a file-timestamp check. It cannot show what
  a labeler saw in other tools, such as ChatGPT.
- Counts: dev 4 relevant / 6 not_relevant. Held-out 4 relevant / 6 not_relevant.
- Every final hand label matches the deterministic record (`watcher/relevance.py`) on all 20 postings.

### Label-sheet defects (flagged, not changed)

The final `hand_label` column agrees with the contract rule on all 20 rows. In three dev rows, however, the
per-condition columns contradict the posting text. Two rows also have notes copied from another row:

| ID | Title | Hand c1/c2/c3 | Record c1/c2/c3 | Note issue |
|---|---|---|---|---|
| 8094087 | Privacy Operations Program Manager | yes/yes/yes | no/no/yes | The note says "Data Analyst title matches; description mentions SQL", which was copied from the row above. Its conditions say relevant, but the label is not_relevant. |
| 8044391 | Strategy and Operations Lead, Deal Pricing | yes/no/yes | no/no/yes | The title condition is marked yes. The note quotes posting text and does not explain the label. |
| 7913702 | Staff Product Manager, Dashboard | yes/no/yes | no/no/yes | The note is identical to 8044391's note. That text occurs in posting 8044391, not in 7913702. |

These rows are locked, and the label files were deliberately not edited. The defects mean the condition
columns cannot serve as evidence of per-condition reasoning on those rows.

## Consistency: 5 dev postings × 4 independent calls

Result file: `eval/results/consistency__baseline__20261018T172903_609917Z.json`.
These were the first 5 dev IDs in `sample.json` order, with the **baseline** prompt (`202e5613…`), backend `cli` (Claude Code
2.1.292, `claude -p`, one fresh process and session ID per call, tools disabled), `claude-opus-5-5`, effort
`medium`. The run went from 2026-10-18T17:29:03Z to 17:31:31Z. All 20 calls exited 0 with empty stderr.
Each `modelUsage` reported only `claude-opus-5-5`, and every one passed strict validation.

| Posting | Title | Hand label | Call 1 | Call 2 | Call 3 | Call 4 |
|---|---|---|---|---|---|---|
| 8189909 | Data Analyst, NYC | relevant | relevant | relevant | relevant | relevant |
| 5416444 | Data Analyst | relevant | relevant | relevant | relevant | relevant |
| 8194291 | Data Analyst, Intern | relevant | relevant | relevant | relevant | relevant |
| 8194287 | Data Analyst, Intern | relevant | relevant | relevant | relevant | relevant |
| 8094087 | Privacy Operations Program Manager | not_relevant | not_relevant | not_relevant | not_relevant | not_relevant |

Raw records (each has a `.json` record, plus `.stdout.bin` and `.stderr.bin`) are in `claude_outputs/2026-10-18/consistency-baseline/`:

| Posting | Call 1 | Call 2 | Call 3 | Call 4 |
|---|---|---|---|---|
| 8189909 | `20261018T172903_611069Z…call1of4` | `20261018T172909_354561Z…call2of4` | `20261018T172946_233685Z…call3of4` | `20261018T172951_654883Z…call4of4` |
| 5416444 | `20261018T172957_001509Z…call1of4` | `20261018T173003_015579Z…call2of4` | `20261018T173010_898741Z…call3of4` | `20261018T173016_768834Z…call4of4` |
| 8194291 | `20261018T173021_313284Z…call1of4` | `20261018T173025_940924Z…call2of4` | `20261018T173030_100025Z…call3of4` | `20261018T173038_804571Z…call4of4` |
| 8194287 | `20261018T173043_779126Z…call1of4` | `20261018T173048_688294Z…call2of4` | `20261018T173054_209354Z…call3of4` | `20261018T173104_192155Z…call4of4` |
| 8094087 | `20261018T173109_350996Z…call1of4` | `20261018T173113_709318Z…call2of4` | `20261018T173118_660232Z…call3of4` | `20261018T173124_279867Z…call4of4` |

### Repeatability is not correctness

- **Repeatability:** 5 of 5 postings got the same verdict in all 4 calls (20/20 calls available, 0 invalid).
  This only shows that the baseline prompt gave a stable verdict on these five inputs on that occasion.
- **Correctness against hand labels:** all 20 verdicts match the hand labels. This is a separate claim, and the
  stable verdicts do not prove it. A prompt can be consistently wrong. The baseline prompt was wrong on dev posting
  8230276 in the experiment run: it labeled it relevant against a hand label of not_relevant (see `PROMPT-EXPERIMENT.md`).
  8230276 was not among the five consistency postings, so its repeatability was never measured.
- **The five were easy cases:** four have an exact "Data Analyst" title with SQL, and one has neither. The
  hard boundary cases are titles with "Analyst" but not a target phrase, like 8230276. None of those were in the
  consistency set. "First 5 in sample order" selected easy cases, so this run says nothing about
  stability on hard cases.
- **The sample is small:** 4 calls per posting cannot detect instability rarer than roughly 1 in 4.
  Justification wording differed in all 4 calls for each of the 5 postings (4 distinct texts each). Only verdicts were compared.
- Only the baseline prompt was tested for consistency. The revision's repeatability was not measured.
