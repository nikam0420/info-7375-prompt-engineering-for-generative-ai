# Prompt experiment report

**Status: complete.** Claude Code (Claude Opus 5.5) wrote this report on 2026-10-19 from the saved
records. No model calls were re-run. Every number below was recomputed from the raw `*.stdout.bin`
bytes with the project's validator and matches the `summary` block of each result file.
Siddhesh Nikam has not reviewed it yet.

## Prompts

- Baseline: `prompts/judgment_baseline.md`, SHA-256 `202e5613944f09d024bbf055eaa740d4fccaabd512fda4d9d9fc54bcc4b4415e`
- Revision: `prompts/judgment_revision.md`, SHA-256 `5c788b25a7b47d04c9dec94d0ae04d3171935d396c1105a9620265f4da4cccab`
- On 2026-10-19 both hashes still matched `prompts/FROZEN.json` and the `prompt_sha256` in every run record.
- **The one change** (line 6; `python3 -m watcher prompt-diff`): the baseline's
  "Decide whether this posting is a good match for the résumé's target titles and skills" became
  the contract's literal three-condition rule, followed by "Seniority, location, salary, visa sponsorship, and
  experience are not assessed."
- Model and settings: `claude-opus-5-5` (requested, and the only model in `modelUsage` for every call), effort `medium`,
  backend `cli` (Claude Code 2.1.292, `claude -p`, claude.ai Pro login, tools disabled, one fresh session per call).
  The CLI controls `max_tokens`, thinking, and retries (`FRICTIONAL.md` C6). The settings are therefore not
  identical to an API run, and these results do not transfer to the API backend.

## Development split (10)

| Prompt | Result file | Available | Unavailable/invalid | Agree | Disagree |
|---|---|---|---|---|---|
| baseline | `eval/results/experiment__baseline__dev__20261018T174658_807218Z.json` | 10 | 0 | **9** | 1 |
| revision | `eval/results/experiment__revision__dev__20261018T174930_224237Z.json` | 10 | 0 | **10** | 0 |

The only disagreement was posting **8230276**, "Strategy and Operations Analyst, Customer Success". The hand label
is not_relevant: the title contains neither target phrase, although SQL is present.

- Baseline said `relevant`
  (`claude_outputs/2026-10-18/experiment-baseline-dev/20261018T174746_269643Z__posting-8230276__baseline__cli.json`).
  It read the title as "an analyst role" whose duties align with data/BI analyst work. It also added a caveat about
  years of experience, a factor the contract excludes.
- Revision said `not_relevant`
  (`…/experiment-revision-dev/20261018T175012_217736Z__posting-8230276__revision__cli.json`). It stated that
  condition (1) fails because the title "contains neither 'data analyst' nor 'business intelligence analyst'
  as a case-insensitive substring".

This one dev posting is the whole difference between the prompts on dev. The revision was **not** written in
response to it. Claude Code drafted the revision and its hypothesis (`prompts/REVISION.md`) on 2026-10-18, before
any Claude call was made. The 8230276 result fits that pre-stated hypothesis, which was that an undefined
"good match" would let the model weigh related titles that the literal rule excludes.

## Freeze

`prompts/FROZEN.json` has `frozen_at` 2026-10-18T17:51:35.099691Z. That is after the dev revision run finished
(17:50:17Z), and the file lists both dev result files as `dev_results_considered`. The file does not record
who ran `freeze-revision`. Siddhesh confirms (2026-10-19) that Siddhesh personally ran the freeze and all four experiment
runs, with ChatGPT guidance. This is Siddhesh's statement, not independent proof.

## Held-out split (10), run once after the freeze

| Prompt | Result file | Available | Unavailable/invalid | Agree | Disagree |
|---|---|---|---|---|---|
| baseline | `eval/results/experiment__baseline__heldout__20261019T190843_660797Z.json` | 10 | 0 | **10** | 0 |
| revision | `eval/results/experiment__revision__heldout__20261019T191044_011859Z.json` | 10 | 0 | **10** | 0 |

Both results files embed the frozen record. The held-out labels were locked at 19:08:43Z, just before the
baseline run started. Each prompt has exactly one held-out result file.

Per-posting held-out verdicts (identical for both prompts; every one matches the hand label):

| ID | Title | Hand | Baseline | Revision |
|---|---|---|---|---|
| 7921649 | Staff Data Analyst | relevant | relevant | relevant |
| 8186442 | Financial Data Analyst Intern, Technical Operations | relevant | relevant | relevant |
| 8044924 | Data Analyst, Payments | relevant | relevant | relevant |
| 8230296 | Data Analyst, Global Growth | relevant | relevant | relevant |
| 8209649 | Engagement Manager, Professional Services | not_relevant | not_relevant | not_relevant |
| 7544547 | Operations Associate, New Grad (Mexico) | not_relevant | not_relevant | not_relevant |
| 8244515 | Immigration Specialist | not_relevant | not_relevant | not_relevant |
| 8224617 | Commercial Lead | not_relevant | not_relevant | not_relevant |
| 7961101 | Product Marketing Manager, Radar | not_relevant | not_relevant | not_relevant |
| 7728618 | Specialist Solutions Architect, Billing | not_relevant | not_relevant | not_relevant |

## Interpretation

- **No held-out improvement.** Both prompts scored 10/10 on held-out. The experiment shows no evidence that
  the revision generalizes better than the baseline.
- **The dev gain is one posting.** 9/10 → 10/10 on dev came from 8230276 alone. The revision was specified
  before dev was run, but the freeze decision was made after seeing dev results. A one-posting dev
  difference is therefore not evidence by itself.
- **The held-out set had no hard case.** Every held-out not_relevant posting fails the title condition *and* has no SQL.
  No held-out title is an "Analyst" title outside the target phrases, which is the kind of title that tripped the baseline on dev.
  The held-out split could not have revealed the one failure mode observed. A tie at 10/10 says nothing
  about which prompt handles that case better.
- **Small sample.** With n = 10 per split, one posting moves agreement by 10 points. A 10/10 result is
  compatible with a true agreement rate well below 100%: the exact 95% binomial interval for 10/10 is about 69–100%.
  These results support no claim about a rate.
- **Title-stratified sampling.** 8 of the 20 sampled postings have target titles, compared with about 1.1% of the board.
  Agreement here therefore does not estimate agreement on the board's real mix, where nearly every
  posting is an easy not_relevant (`SAMPLING.md`).
- **AI-assisted labels.** The hand labels were made with ChatGPT assistance, and three dev rows have
  inconsistent condition columns (`SAMPLING.md`). "Agreement with hand labels" means agreement with these
  AI-assisted labels. On these 20 postings they also equal the deterministic contract record.
- **One run per prompt per split.** There is no repeat run on dev or held-out, so the 8230276 result cannot be separated
  from run-to-run variation.
- **CLI backend only.** All results come from `claude -p` on a subscription login. None come from the API backend.
