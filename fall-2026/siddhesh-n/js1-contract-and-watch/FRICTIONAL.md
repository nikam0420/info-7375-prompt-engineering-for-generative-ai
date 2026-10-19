# FRICTIONAL.md

A log of friction: places where the work, the tools, or the contract made it
hard to do the right thing. Each entry records what happened, when, and who saw it.

## Observed by Claude Code during implementation (2026-10-18)

These entries are Claude Code's observations, not Siddhesh Nikam's.

| # | What | Effect | Resolution |
|---|---|---|---|
| C1 | `CONTRACT.md` "What a failure looks like" still has the placeholder `[enter actual date and time, before running code]`. | It was not filled in before code ran, so the contract has no pre-run timestamp for this clause. | Left untouched; `CONTRACT.md` must not be modified by the implementer. |
| C2 | An untracked `CONTRACT.md.save` (editor save buffer containing shell commands) sits in the repo root. | It could be committed by accident. | Left untouched and not deleted; your decision. |
| C3 | The contract does not say whether citation names are bare (`skills`) or prefixed (`résumé.skills`), or whether `posting_id` may be a string. | Validator strictness was a judgment call. | Bare names and integer only; documented in README. |
| C4 | Only 8 of 731 `stripe` titles contain a target title. | A random 20-posting sample will likely contain no relevant postings, making agreement metrics uninformative. | `sample-select` requires choosing `--strategy` explicitly. |
| C5 | No `ANTHROPIC_API_KEY`; the only authenticated route is the Claude Code CLI on a claude.ai subscription. | Added a CLI backend. `--bare` (the documented mode for scripts) cannot be used, because it refuses OAuth logins. | `--safe-mode` + `--restricted` + an empty temp working directory are used instead to keep CLAUDE.md, memory, hooks, plugins, settings and personal files out. |
| C6 | CLI and API settings are **not identical**. The CLI chooses `max_tokens`, thinking, retries and any context it injects. `--system-prompt` replaces its default prompt, but the exact wire request cannot be observed from outside. | CLI results are not directly comparable with API results, and the CLI may also differ across versions. | Each record saves `backend`, `cli_version`, argv, system prompt, user message, raw stdout/stderr, and the `modelUsage` model names. Don't mix backends within one comparison. |
| C7 | The flag combination (`--restricted --safe-mode --tools "" --disallowedTools "*" --strict-mcp-config --permission-mode dontAsk --max-turns 1` on an OAuth login) is documented but untested here, since no real call was allowed. | The first real call may fail on a flag conflict or an auth issue. | That failure is saved as `unavailable` with stderr. Run one smoke call before any experiment. |
| C8 | The CLI's `total_cost_usd` is a client-side estimate, and subscription use counts against plan usage limits, not API billing. | A rate or usage limit mid-run would make some calls `unavailable`. | Strict validation counts those as unavailable and never fills them in. Check `validation.errors` in the saved records. |
| C9 | Model fallback: Claude Code can switch models automatically on overload. | A judgment could silently come from a different model. | When `--model` is a full `claude-*` ID that the CLI's `modelUsage` doesn't report, the call is rejected as unavailable. Aliases such as `opus` cannot be checked this way. |

### Observed by Claude Code during the documentation pass (2026-10-19)

| # | What | Effect | Resolution |
|---|---|---|---|
| C10 | Each `raw_record` path in the five `eval/results/*.json` files is absolute (`/Users/siddheshnikam/…`), 60 in total. `watcher/util.py` has a `rel()` helper, but the experiment and consistency code paths did not use it. | The paths break on any other machine and reveal the local account name. The records themselves still sit at the matching relative paths under `claude_outputs/`. | The result files were not edited, since they are saved evidence. The reports cite relative paths instead. |
| C11 | The CLI judge record does not save the `--raw` file it read. | For Trial 3, the record cannot show which board snapshot the judge used. | In this case both snapshots hold an identical 8189909 object (`reports/ACTION-SURFACE-COMPARISON.md`). |
| C12 | `prompts/REVISION.md` still said "not yet frozen" and cited a nonexistent `tests/test_evaluation.py`. | The text was stale and wrong. | The status text and freeze record were updated. The two frozen prompt files were not touched, and their hashes still match `FROZEN.json`. |

## Observed in Siddhesh Nikam's work

Claude Code drafted these entries on 2026-10-19 from artifacts in the project, plus the items Siddhesh named
in the documentation request. **Siddhesh still needs to confirm or correct each one.** Nothing here is
inferred beyond what the cited evidence shows.

| # | Date/time | Stage | What happened | Evidence | What it cost | What was done |
|---|---|---|---|---|---|---|
| S1 | 2026-10-18 11:42:53 EDT | Contract setup | Shell commands (`mkdir -p …`, `cd …`, `touch CONTRACT.md`, `open -a TextEdit CONTRACT.md`) and an arrow-key escape sequence (`^[[C`) ended up inside an editor buffer instead of running in the terminal. The buffer was saved as `CONTRACT.md.save`, which is the name nano uses when it exits without a normal save. | `CONTRACT.md.save` (kept on local disk, excluded from the submission by `.gitignore`; its content is quoted here); `CONTRACT.md` created 11:43:02, last modified 11:47:24 | A stray file in the repo root, and some minutes before the contract was written | The contract was written and saved separately and committed at 11:48:54 (`c978ff3`). The `.save` file was left in place. |
| S2 | 2026-10-18 before 11:48 EDT | Contract | The failure-clause placeholder `[enter actual date and time, before running code]` was never filled in. | `CONTRACT.md` line 107; commit `c978ff3` | The contract has no pre-execution timestamp for that clause | Left unfilled. It is disclosed in `README.md` and was not backdated. |
| S3 | 2026-10-18 12:49–12:51 EDT | Dev labeling | In three rows of the label CSV, the condition columns or notes were copied from the wrong row. The final labels were still correct. | `eval/hand_labels_dev.csv` rows 8094087, 8044391, 7913702 (`reports/SAMPLING.md`) | The per-condition reasoning cannot be trusted on those rows | Not corrected. The labels are locked and were used. |
| S4 | 2026-10-19 15:15:50 EDT | Action-surface Trial 1 | **Failed clipboard save.** `pbpaste > evidence/action-surfaces/trial1-chat-response.json` saved the clipboard, but the clipboard held the terminal commands rather than Claude's reply. | `evidence/action-surfaces/trial1-chat-response.json`; import record `claude_outputs/2026-10-19/manual-import/20261019T192010_559175Z…json` (invalid, char 0) | The complete Trial 1 reply was never saved | Trial 2 followed with a file attachment in a fresh chat at 15:29 EDT. Later, a partial recovery (fences kept, prose omitted) was saved at 15:57–16:00 EDT and imported at 20:01:52Z, which was also rejected, this time because of the code fences. The mistaken import was kept. |
| S5 | 2026-10-19, between Trials 1 and 2 (time not recorded) | Action-surface Trial 2 | **Missing-attachment attempt.** Siddhesh reported this in the documentation request. No file, screenshot, or record captures it. | Siddhesh's statement only | Not recorded | Siddhesh to add details: what was attempted, what was missing, and how it was fixed. |
| S6 | 2026-10-18 / 2026-10-19 | Held-out labeling | One held-out label, 7921649, was decided on October 18 and saved on October 19. The other nine were decided and saved on October 19 (Siddhesh's correction of 2026-10-19). ChatGPT assisted with saving. | `eval/hand_labels_heldout.csv` note on 7921649; `labeled_at` 2026-10-19 for all ten | For 7921649, the written record comes a day after the decision | Saved before the lock and before any held-out model call (`reports/SAMPLING.md`). |
