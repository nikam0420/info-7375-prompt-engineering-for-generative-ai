# Job-Search Agent 1: contract and watcher

A public Greenhouse board watcher implemented against [`CONTRACT.md`](CONTRACT.md)
(committed before implementation as `c978ff3`; prepared with ChatGPT assistance).
Python 3.12, standard library only. No login, no applications, no messages.

**Status (2026-10-19):** the code, the tests, the demo, sampling, the AI-assisted hand labels, the consistency
run, the prompt experiment, and the three action-surface trials are done. The reports are in [`reports/`](reports/).
**The sign-off is WITHHELD** pending Siddhesh Nikam's review (see the end of this file). The 2026-10-19
documentation was written by Claude Code from the saved records. See [`SOURCES.md`](SOURCES.md).

## What it does

| Contract item | Where |
|---|---|
| Fictional résumé + checks | `data/fictional_resume.json`, `watcher/resume.py` |
| Allow-listed HTTPS fetch, redirects refused, no proxies | `watcher/netguard.py` |
| Raw bytes saved before parsing; complete response validated | `watcher/watch.py`, `watcher/postings.py` |
| Per-board seen-ID state (union), baseline = zero new | `watcher/state.py`, `watcher/watch.py` |
| Deterministic record + field-specific justification | `watcher/relevance.py` |
| Claude prompt, strict validator, unavailable-not-invented | `prompts/`, `watcher/judgment.py`, `watcher/claude.py` |
| Seeded two-run demo from a real response | `watcher/demo.py` |
| 20-posting sample, 10 dev / 10 held-out, label gates, freeze lock | `watcher/evaluation.py` |
| Tests (all fixtures labeled CONSTRUCTED) | `tests/` |

A new posting is reported with its ID, title, URL, a `record` verdict computed by
the contract rule, and a separate `judgment` slot. The judgment holds a validated
Claude output, or it says `unavailable` and gives the reason. It is never filled
from the record.

## Fresh-clone commands

Requires Python 3.12+ (`python3 --version`). No `pip install` is needed.

```sh
git clone <your-repo-url> js1-contract-and-watch
cd js1-contract-and-watch
python3 --version                       # must print 3.12 or newer

# 1. Tests (offline, no network, no Claude)
python3 -m unittest discover -s tests -v
```

### 2. Seeded two-run demonstration (offline, from the committed real response)

```sh
RAW=evidence/fetches/stripe/20261018T160635_483273Z/raw_response.bin
python3 -m watcher demo-prepare --raw "$RAW" --board stripe --withhold 3 --seed 20261018
python3 -m watcher demo-run --board stripe
```

Run 1 replays `demo/stripe/constructed_seeded_baseline.json`, a **constructed seeded
baseline**: the real response minus 3 postings picked with seed 20261018. It must
report zero new postings. Run 2 replays the unmodified real response and must report
exactly the 3 withheld IDs. The difference between the runs was constructed, not
observed on the board. Raw bytes and state snapshots for both runs are saved under
`demo/stripe/runs/`, and `demo/stripe/DEMO-RESULT.json` records the checks.
`demo-prepare` and `demo-run` refuse to overwrite an existing demo. Delete `demo/stripe/` to redo it.
In a clone of this submission the demo already exists, so these two commands will refuse. Inspect `demo/stripe/` instead.

### 3. Sampling and hand labels (you do this; no model output is shown)

In this submission the sample, labels, results, and freeze already exist. The commands below
document how they were produced, and the gates make the tools refuse to redraw or rerun them.

```sh
python3 -m watcher sample-select --raw "$RAW" --board stripe --seed <your-seed> --strategy title-stratified
# read eval/postings/<id>.txt and fill hand_label in
#   eval/hand_labels_dev.csv and eval/hand_labels_heldout.csv
# using the CONTRACT.md relevance rule
python3 -m watcher labels-status
```

The `--strategy` flag is required. Only 8 of the 731 `stripe` titles contain a target
title, so `random` will very likely yield 20 not_relevant postings. `title-stratified`
takes all 8 title matches plus 12 others, chosen by title only. Pick one and record why in
`reports/SAMPLING.md`.

### 4. Claude calls (API backend never used; every saved run used `--backend cli`)

Alternative: `--backend cli` on any of these commands makes each call one fresh
`claude -p` process on your existing Claude Code login (no API key). Settings
are **not identical** to the API backend; see `FRICTIONAL.md` C5–C9.

```sh
python3 -m watcher judge --backend cli --raw "$RAW" --posting-id <dev id>   # one smoke call
python3 -m watcher consistency-run --backend cli --prompt baseline
```

```sh
export ANTHROPIC_API_KEY=...            # never commit this
python3 -m watcher consistency-run --prompt baseline          # 5 dev postings x 4 fresh calls
python3 -m watcher experiment-run --prompt baseline --split dev
python3 -m watcher experiment-run --prompt revision --split dev
python3 -m watcher freeze-revision                             # locks both prompt hashes
python3 -m watcher experiment-run --prompt baseline --split heldout
python3 -m watcher experiment-run --prompt revision --split heldout
```

The tools refuse to run in these cases:
- any Claude run while the dev labels are incomplete;
- held-out runs while the held-out labels are incomplete or before `freeze-revision`;
- held-out runs if a prompt file changed after freezing;
- a second held-out run for the same prompt;
- any run if a label file changed after it was first used.

Every call is saved under `claude_outputs/<UTC date>/<purpose>/`: the request body
(without the key), the exact response bytes, start and finish timestamps, the
requested and reported model, the stop reason, usage, and validation errors.
Defaults: `--model claude-opus-5-5 --effort medium`.

### 5. Live watcher

```sh
python3 -m watcher watch --board stripe              # first success: baseline, zero new
python3 -m watcher watch --board stripe              # later: only unseen IDs
python3 -m watcher watch --board stripe --claude     # also one Claude call per new posting
```

State lives in `state/<board>.json`. Evidence for each run, including failures, goes in
`evidence/runs/<board>/<UTC stamp>/` (`raw_response.bin`, `fetch_meta.json`,
`state_before.json`, `state_after.json`, `report.json`).

### Other commands

```sh
python3 -m watcher prompt-diff                                   # the one baseline→revision change
python3 -m watcher prompt-show --raw "$RAW" --posting-id <id> --prompt baseline
python3 -m watcher judge --raw "$RAW" --posting-id <id> --prompt baseline   # one billed call
python3 -m watcher judgment-import --raw "$RAW" --posting-id <id> --prompt baseline \
    --response-file reply.txt --surface "claude.ai web" --model-declared "<as shown>"
```

`judgment-import` validates and saves a Claude reply that you obtained yourself, for
example from the action-surface trials. Model information for these replies is
recorded only as declared. `judge` and `judgment-import` refuse to run on a sampled
posting until that posting's split is fully hand-labeled.

## Design notes and interpretations

- **Claude sees** `target_titles` and `skills` from the résumé, plus `id`, `title`,
  `location`, `absolute_url` and plain-text `content` from the posting. These are the only
  valid names for `resume_fields` / `posting_fields`, given as bare key names (e.g.
  `"skills"`, not `"résumé.skills"`).
- **`posting_id`** must be a JSON integer equal to the posting's ID. A string such as `"123"` is rejected.
- **"One JSON object"** is enforced strictly: a reply wrapped in code fences or surrounded by
  other text fails validation and is reported as unavailable.
- **SQL whole word** uses the regex `\bsql\b`, case-insensitive, on HTML converted to text with entities
  decoded. `PostgreSQL`, `MySQL`, `NoSQL` and `SQLite` do not match. `T-SQL` and `SQL/Python` do.
- **Server-side refusal fallbacks are off** so that every judgment comes from the model that
  was requested. A refusal is reported as unavailable.
- The Claude API host (`api.anthropic.com`) is allow-listed separately from the job-board host.
  The contract's host restriction covers job-board fetches.

## Contract disclosure

- `CONTRACT.md` was **prepared with ChatGPT assistance**, as its status line says. It was accepted by Siddhesh Nikam
  ("10/18/26 AND 11.46AM") and committed as `c978ff3` at 2026-10-18 11:48:54 EDT, before implementation.
  It is preserved unmodified. Which wording came from ChatGPT is not recorded.
- The failure clause still reads **`[enter actual date and time, before running code]`**. It was **not filled in
  before execution**, and it has not been filled in or backdated since. The project therefore does **not** fully
  meet the contract-first requirement. The contract as a whole predates the code, but that clause carries no
  pre-execution timestamp.
- `CONTRACT.md.save` is an editor save buffer that holds shell commands. It is not part of the contract. It stays
  on the local disk, and `.gitignore` **excludes it from the submission**. Its content is quoted in `FRICTIONAL.md` S1.

## Results (all from saved records; see `reports/`)

| | Result | Report |
|---|---|---|
| Seeded demo (constructed baseline) | Run 1: 0 new. Run 2: exactly the 3 withheld IDs | `demo/stripe/DEMO-RESULT.json` |
| Consistency, baseline, 5 × 4 | 20/20 valid; every posting unanimous; all matched the hand labels | [`reports/SAMPLING.md`](reports/SAMPLING.md) |
| Dev, baseline → revision | 9/10 → 10/10 (the difference is one posting, 8230276) | [`reports/PROMPT-EXPERIMENT.md`](reports/PROMPT-EXPERIMENT.md) |
| Held-out, baseline vs. revision | 10/10 vs. 10/10, **no held-out improvement** | same |
| Action surfaces | Trial 1: Import A was a clipboard error (shell commands). Import B was a **partial** recovery (code fences kept, prose omitted) that was rejected for its fences. Trial 2 was valid. Trial 3 was two user-invoked commands (a baseline of 723 postings with 0 new, then a valid CLI judgment) | [`reports/ACTION-SURFACE-COMPARISON.md`](reports/ACTION-SURFACE-COMPARISON.md) |

Limits: n = 10 per split; a title-stratified sample that does not represent the board; AI-assisted labels with three
inconsistent dev rows; CLI backend only; one run per prompt per split.

## Tests

**Siddhesh Nikam authored none of the tests.** Claude Code wrote all 91 tests, along with the constructed fixtures in
`tests/fixtures/`.

| File | Tests | Covers (examples of actual test names) |
|---|---|---|
| `tests/test_watch.py` | 22 | `test_first_run_is_baseline_with_zero_new`, `test_repeat_run_reports_nothing_new`, `test_only_unseen_ids_reported`, `test_verdicts_stay_attached_to_ids_when_order_changes` (contract wrong implementation #1), `test_judgment_for_a_different_id_is_rejected`, `test_failed_fetch_redirect`, `test_failure_on_first_run_does_not_create_baseline`, `test_blocked_board_never_fetches`, `test_posting_instructions_are_not_executed` |
| `tests/test_judgment.py` | 15 | `test_empty_citations_rejected` (contract wrong implementation #2), `test_empty_citations_from_claude_reported_unavailable`, `test_wrong_posting_id_rejected`, `test_key_set_must_be_exact`, `test_not_exactly_one_object_rejected`, `test_default_transport_refuses_other_hosts`, `test_pasted_import_validates_and_saves` |
| `tests/test_postings_and_relevance.py` | 14 | `test_missing_required_fields`, `test_wrongly_typed_fields`, `test_case_insensitive_matching`, `test_sql_must_be_whole_word`, `test_absent_sql_described_as_absent_without_quotation` |
| `tests/test_evaluation_and_demo.py` | 13 | `test_heldout_locked_until_freeze_then_runs_once`, `test_prompt_edit_after_freeze_blocks_heldout`, `test_label_edits_after_use_are_refused`, `test_two_run_demo_reports_withheld_ids_only` |
| `tests/test_resume_and_netguard.py` | 11 | `test_bundled_resume_satisfies_contract`, `test_disallowed_hosts_and_urls`, `test_handler_declines_every_redirect`, `test_blocked_url_never_reaches_opener` |
| `tests/test_judgment_cli.py` | 16 | `test_tools_disabled_and_no_conversation_reuse`, `test_strict_validator_applied_without_repair`, `test_api_key_and_nested_session_env_removed` |

Recorded runs:

| Run | Who | Tests | Result | Evidence |
|---|---|---|---|---|
| 2026-10-18 12:31 and 12:32 EDT | The file names suggest Siddhesh; **not confirmed** | 75 (the first five files; `test_judgment_cli.py` did not exist yet) | OK, both runs | `evidence/student-test-run.txt`, `evidence/my-test-run.txt` |
| 2026-10-19 19:36:51Z | **Claude Code** (a Claude-run check) | 91 (all six files) | OK | `evidence/claude-test-run.txt` |

So far, no saved evidence shows that Siddhesh ran the 16 tests in `test_judgment_cli.py`, or any run on the final tree.

## Checks run by Claude Code on 2026-10-19 (not by Siddhesh)

- `python3 -m unittest discover -s tests -v`: **91 tests, OK** (Python 3.12.2), saved to `evidence/claude-test-run.txt`.
  The run left the project files unchanged (SHA-256 before and after). The documents were edited later, but
  no code or test file was changed after this run.
- Portability: the suite also passes from a copy at a different path, with no `.git` and no `__pycache__`.
  Nothing in `watcher/` or `tests/` depends on an absolute path. **However,** the five `eval/results/*.json`
  files store `raw_record` as absolute `/Users/…` paths (60 entries; `FRICTIONAL.md` C10). They are left unedited
  as saved results. Each record exists at the same relative path under `claude_outputs/`.
- Every saved verdict was re-derived from raw output with the project validator. All matched (62 CLI calls and 3 imports).
- Missing files: every path that the documents cite exists in the submission.
- Credentials: no API key, token, or password was found. The CLI records keep only `loggedIn`, `authMethod`, `apiProvider`,
  and `subscriptionType`. The only email addresses are `@example.com` and constructed test strings.
- Résumé data: only the fictional `data/fictional_resume.json`. No real résumé is present.
- Transcripts: none are included. `evidence/action-surface-chat-input.txt` is the generated prompt input.
  The Trial 1 and 2 files are single replies, not conversations.
- Packaging: `.gitignore` excludes `__pycache__/`, `*.pyc`, `.*.tmp`, `.DS_Store`, and `CONTRACT.md.save`. The
  submission is about 29 MB, and its largest file is 5.7 MB. Only `CONTRACT.md` is committed so far.

## Sign-off — Job-Search Agent 1

Claude Code prepared this section from the evidence. It is not signed, and Claude Code has not signed on anyone's behalf.

### Checked:

- *By Claude Code (2026-10-19), not by Siddhesh:*
  - the 91 unit tests pass;
  - every reported number matches the raw saved outputs: dev 9/10 → 10/10, held-out 10/10 vs. 10/10, and consistency 20/20;
  - the prompt and label-lock hashes match the freeze and locks, and `CONTRACT.md` is unchanged since `c978ff3`;
  - no held-out model output predates the held-out labels;
  - posting 8189909 is identical in both board fetches;
  - both Trial 1 imports and the Trial 2 import were re-validated with the same outcomes;
  - the packaging, credential, and résumé checks above.
- *Confirmed by Siddhesh's statement (2026-10-19), which is not independent proof:* Siddhesh personally ran the demo, sample
  selection, the consistency run, the four experiment runs, and the freeze, with ChatGPT guidance. Siddhesh also performed the three
  action-surface trials and saved the partial Trial 1 recovery. Only 7921649's held-out label was decided on October 18.
  The other nine were decided and saved on October 19.
Siddhesh ran the final 91 Claude-written unit tests on October 19, 2026; all passed. Evidence: evidence/siddhesh-final-test-run.txt.

### How:

Claude Code used read-only scripts that loaded each saved `*.stdout.bin` or imported text and ran the project's own
validator (`watcher/judgment.py`). It recomputed agreement from the label CSVs, compared SHA-256 hashes with
`prompts/FROZEN.json` and `eval/label_locks.json`, compared file timestamps, and ran `git diff` against `c978ff3`.
It did not re-run any model call, edit any label, result, or frozen prompt, or make any network request.
Each statement Siddhesh confirmed is recorded as that statement, in `SOURCES.md` and `reports/DRIVERS-SEAT.md`.

### Not checked:

- [ ] Siddhesh has not yet reviewed the code in `watcher/` or the Claude-written tests in `tests/`.
- [ ] Siddhesh has not yet confirmed or corrected `FRICTIONAL.md` S1–S6. S5 (the missing-attachment attempt) still has no details or evidence.
- [ ] The three inconsistent dev label rows (8094087, 8044391, 7913702) remain a disclosed limitation. Their per-condition columns were not re-reviewed.
- [ ] Siddhesh has not yet read and accepted `reports/SAMPLING.md`, `reports/PROMPT-EXPERIMENT.md`, and `reports/ACTION-SURFACE-COMPARISON.md`.
- [ ] Nobody has checked the claude.ai trials' actual model, tools, or context. They cannot be observed from this project.


### Not claiming:

- that the contract was fully contract-first, because the failure-clause timestamp was never filled in before execution;
- that the hand labels are independent human labels, because they were ChatGPT-assisted and three dev rows are internally inconsistent;
- that the operator confirmations are independently proven, because they are Siddhesh's statements;
- that the revision prompt is better, because held-out showed no improvement (10/10 vs. 10/10, n = 10);
- that any agreement rate generalizes to the board or to other boards, because the sample is title-stratified and small;
- that the CLI results represent the API backend or claude.ai, because settings differ and the API was never called;
- that `trial1-original-recovered.txt` is the complete original Trial 1 response, because its surrounding prose is omitted;
- that the first Trial 1 import (shell commands) says anything about Claude's output, because it was a clipboard error;
- that Trial 3 was an autonomous fetch-and-judge agent, because it was two commands a person invoked;
- that the demo's run-1/run-2 difference happened naturally, because it was constructed by withholding postings;
- that Siddhesh wrote the code or any test.

### Signed or withheld:

**WITHHELD** pending Siddhesh Nikam's review of the items under "Not checked:".

Name: Siddhesh Nikam
Signature: **WITHHELD**
Date/time: _withheld_
