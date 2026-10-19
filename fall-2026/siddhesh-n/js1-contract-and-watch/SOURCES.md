# Sources and contributions

Only actions that actually happened are recorded here. Anything not yet done
is marked pending.

## ChatGPT (OpenAI): contract assistance

`CONTRACT.md` says it was "Prepared with ChatGPT assistance before
implementation." It was committed as `c978ff3` before any implementation
started, and it has not been modified since. Which wording came from ChatGPT and
which from Siddhesh Nikam is not recorded in this repository.

## Siddhesh Nikam: recorded contributions

- Accepted the contract. `CONTRACT.md` records "Reviewed and accepted by
  Siddhesh Nikam: [10/18/26 AND 11.46AM]", and Siddhesh committed it as `c978ff3`.
- Wrote the implementation request saved in `BUILD-PROMPT.md`.
- Hand-labeled all 20 sampled postings **with ChatGPT assistance**, as each row's notes say
  (`eval/hand_labels_*.csv`): dev on 2026-10-18 and held-out on 2026-10-19. One held-out label
  (7921649) was decided on 2026-10-18. These labels are AI-assisted.
- Performed the three action-surface trials on 2026-10-19: two in claude.ai, and one as two separate terminal
  commands (`reports/ACTION-SURFACE-COMPARISON.md`).
- Two saved test-output files, `evidence/my-test-run.txt` and `evidence/student-test-run.txt` (2026-10-18
  12:31/12:32 EDT, 75 tests OK), appear to be Siddhesh's runs. The files themselves do not record who ran them.
- **Confirmed by Siddhesh on 2026-10-19 (Siddhesh's own statement; the files do not record the operator):** Siddhesh personally
  ran the demo (16:33Z), sample selection (16:35Z), the consistency run, the four experiment runs, and
  `freeze-revision`, **with ChatGPT guidance**. This is a self-report, not independent proof.
- Saved a partial recovery of the Trial 1 claude.ai reply (`evidence/action-surfaces/trial1-original-recovered.txt`;
  code fences kept, surrounding prose omitted) and imported it at 2026-10-19T20:01:52Z. The import was rejected.
- Still pending: Siddhesh's review of the code and of the 2026-10-19 reports, and the signature.
- The tests were **not** written by Siddhesh. Claude Code wrote all of them.

## Claude Code (Anthropic, model Claude Opus 5.5, `claude-opus-5-5`): implementation

Done on 2026-10-18, in response to `BUILD-PROMPT.md`:

- Wrote all code in `watcher/`, all tests and constructed fixtures in `tests/`,
  the fictional résumé `data/fictional_resume.json`, both prompts and
  `prompts/REVISION.md`, `README.md`, this file, `FRICTIONAL.md`, the templates in `reports/`,
  `evidence/RETRIEVAL.md`, and `.gitignore`.
- Ran the unit tests: `python3 -m unittest discover -s tests`, 75 tests, OK.
- Mutation-checked the tests in a scratch copy outside the project. Nine deliberate bugs
  were injected one at a time (wrong-ID association, accepting empty citations,
  baseline reporting new, state replaced rather than unioned, case-sensitive titles,
  any host allowed, state written after a validation failure, record substituted for
  judgment, redirects followed). The suite failed on each one.
- Made one live fetch of the `stripe` board (see `evidence/RETRIEVAL.md`).
- Dry-ran `demo-prepare`, `demo-run`, `sample-select`, `labels-status`, and the
  consistency, held-out, and blocked-board refusals **in a scratch copy outside
  this project**. Those outputs were not kept here, and the project's `demo/`, `eval/`,
  `state/`, and `claude_outputs/` directories were not created.
- Made **no** Claude API calls and produced **no** judgments, hand labels, or metrics.

### Claude Code CLI judgment backend (2026-10-18, second request)

Requested by Siddhesh after the 10 dev labels were complete, because
`ANTHROPIC_API_KEY` is not configured. Done by Claude Code (Claude Opus 5.5):

- Checked support. Ran `claude --version` (2.1.292), `claude --help`, `claude auth --help`, and
  `claude auth status`. Only `loggedIn`, `authMethod` (`claude.ai`), `apiProvider` and
  `subscriptionType` were used; the email and org fields were not recorded. Read the official docs
  `https://code.claude.com/docs/en/headless` and `https://code.claude.com/docs/en/cli-reference`.
  Conclusion: `claude -p` supports fresh, noninteractive, tool-free runs on the existing
  subscription login. `--bare` was rejected because it never reads OAuth/keychain credentials.
- Added `watcher/claude_cli.py` and a `--backend api|cli` option (default `api`, unchanged) to
  `judge`, `watch`, `demo-run`, `consistency-run` and `experiment-run`. Consistency and experiment
  results now record `"backend"`. The API backend (`watcher/claude.py`) was not changed.
- Added `tests/test_judgment_cli.py` (16 tests, constructed fake `claude` processes, no real calls).
  `python3 -m unittest discover -s tests`: 91 tests, OK. Mutation-checked in a scratch copy:
  12 injected bugs (tools re-enabled, session persistence on, session-ID check off, turn check off,
  tool-denial check off, model check off, env not stripped, envelope check skipped, output
  "repaired" by stripping fences, auth check off, fixed session ID). All were caught after one
  test bug was fixed. The wrong-session test had passed for the wrong reason: its fake raised a
  `TypeError`.
- Did **not** run any real `claude -p` judgment call, did not read held-out posting texts or labels,
  and did not purchase API credits. Only the first dev posting ID was read from `eval/sample.json`
  to write the suggested smoke-test command.

### Documentation pass (2026-10-19, third request)

Done by Claude Code (Claude Opus 5.5) in response to Siddhesh's documentation request:

- Re-derived every saved verdict from the raw `*.stdout.bin` bytes with the project validator. All 62 CLI judgments
  and all three manual imports (including the later Trial 1 partial recovery) matched their saved records. Rechecked the prompt, label-lock, and raw-response hashes.
- Compared posting 8189909 across the 2026-10-18 and 2026-10-19 board responses. It is identical.
- Wrote `reports/SAMPLING.md`, `reports/PROMPT-EXPERIMENT.md`, `reports/ACTION-SURFACE-COMPARISON.md`,
  `reports/DRIVERS-SEAT.md`, and `reports/SIGN-OFF.md`. Updated `README.md`, this file, `FRICTIONAL.md`
  (C10–C12; drafted S1–S6 for Siddhesh to confirm), and the status text in `prompts/REVISION.md`.
- Ran the unit tests (91, OK) and saved the output as a **Claude-run check** in `evidence/claude-test-run.txt`.
  Also ran portability and packaging checks (see `README.md`).
- Did **not** re-run any model call, change any label, results file, or frozen prompt, edit `CONTRACT.md`, commit,
  push, or sign.

## Data and software

- Greenhouse public Job Board API: `https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true`,
  public, no credentials. Raw response saved unchanged.
- Python 3.12 standard library.
- Anthropic Messages API (`https://api.anthropic.com/v1/messages`) is the target of the API backend.
  It has never been called (there is no API key).
- Claude Code CLI 2.1.292 (`claude -p`), logged in with a claude.ai Pro subscription. This was the backend for
  every saved CLI judgment: 1 smoke call, 20 consistency calls, 40 experiment calls, and 1 Trial 3 call, all in `claude_outputs/`.
  The API backend has never been called.
- claude.ai web chat (model declared as "Opus 5.5") for action-surface Trials 1–2. No transcripts are included.
