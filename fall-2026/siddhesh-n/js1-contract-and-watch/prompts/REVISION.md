# Prompt revision record

Status: **drafted by Claude Code on 2026-10-18 before any Claude call; frozen 2026-10-18T17:51:35Z**
(`prompts/FROZEN.json`). This status text was updated by Claude Code on 2026-10-19. The two prompt
files were not changed, and their hashes still match `FROZEN.json`.

## The one change

| | `judgment_baseline.md` | `judgment_revision.md` |
|---|---|---|
| Relevance criterion paragraph | "Decide whether this posting is a good match for the résumé's target titles and skills." | The contract's three-condition rule, stated literally (title substring, whole-word SQL in content, SQL skill), plus the list of factors not assessed. |

Everything else (untrusted-data warning, judgment-not-fact sentence, output
format) is byte-identical. The user message built by `watcher/judgment.py` is
identical for both versions. `tests/test_evaluation_and_demo.py` checks that the two
files differ in exactly one contiguous block of lines.

## Hypothesis (not a result)

The baseline leaves "good match" undefined, so Claude may weigh seniority or
related titles that the contract's rule ignores. Stating the rule may raise
agreement with hand labels made under that same rule. No experiment has been
run; no result exists yet.

## Freeze record

`prompts/FROZEN.json`: frozen_at 2026-10-18T17:51:35.099691Z. Baseline `202e5613…`, revision `5c788b25…`.
Dev results considered: the baseline and revision dev runs. Results are in `reports/PROMPT-EXPERIMENT.md`.
The hypothesis above is unchanged from before the experiment.
