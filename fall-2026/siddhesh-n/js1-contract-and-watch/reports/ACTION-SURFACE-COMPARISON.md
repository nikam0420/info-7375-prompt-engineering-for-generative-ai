# Action-surface comparison

**Status: trials performed by Siddhesh Nikam on 2026-10-19. Report written by Claude Code (Claude
Opus 5.5) on 2026-10-19 from the saved records. Siddhesh Nikam has not reviewed this report yet.**
Claude Code did not perform any of the trials and could not observe the two browser trials (see
"Limits of observation").

**Trial 1 evidence is partial.** The first saved Trial 1 "response" is three shell commands (a clipboard
error). A later partial recovery keeps the code-fenced JSON but **omits the original surrounding prose**, so
the complete original reply is not in this project. Both imports are preserved. See Trial 1 below.

## Common setup

- Task: judge posting **8189909** ("Data Analyst, NYC", a dev posting, not held-out) with the frozen
  **revision** prompt (`5c788b25…`), and check the output with the same strict validator.
- Input given to the browser surfaces: `evidence/action-surface-chat-input.txt`, created
  2026-10-19 15:14:18 EDT. Claude Code checked on 2026-10-19 that its system-prompt section is byte-equal (after
  trimming) to `prompts/judgment_revision.md`, and that its user-message section equals the message
  `watcher/judgment.py` builds for 8189909. The input therefore contains only the fictional résumé's
  `target_titles` and `skills` plus public posting fields.

## Trials

| | Trial 1 | Trial 2 | Trial 3 |
|---|---|---|---|
| Surface | claude.ai web chat; prompt and posting **pasted** | claude.ai web chat, **fresh chat, input file attached** | Local terminal: live watcher, then CLI judge (`claude -p`) |
| Performed by / when | Siddhesh Nikam; Import A 19:20:10Z; partial recovery imported as Import B at 20:01:52Z | Siddhesh Nikam; response file 15:29:37 EDT, import 19:29:58Z | Siddhesh Nikam; fetch 19:31:13Z, judge 19:31:55Z |
| Model as shown | "Opus 5.5" (`model_declared`; cannot be verified) | "Opus 5.5" (`model_declared`; cannot be verified) | `claude-opus-5-5` requested; `modelUsage` reports only `claude-opus-5-5` |
| What it could do | Unknown beyond chat (see Limits). It received only the pasted text | Unknown beyond chat; it received the attached file | Watcher: one HTTPS GET to the allow-listed host, local file writes. Judge: model call only; `--tools ""`, `--disallowedTools "*"`, `--max-turns 1` |
| Beyond the task | Not observable | Not observable | None recorded: `num_turns` 1, `permission_denials` [], stderr empty |
| Raw output saved at | `evidence/action-surfaces/trial1-chat-response.json` = `claude_outputs/2026-10-19/manual-import/20261019T192010_559175Z__posting-8189909__revision.response.txt` (Import A; identical bytes; **not Claude's reply**). `evidence/action-surfaces/trial1-original-recovered.txt` = `…/20261019T200152_969009Z__posting-8189909__revision.response.txt` (Import B; **partial**, prose omitted) | `evidence/action-surfaces/trial2-file-response.txt` = `claude_outputs/2026-10-19/manual-import/20261019T192958_658840Z__posting-8189909__revision.response.txt` (identical bytes) | `evidence/action-surfaces/trial3-runs/stripe/20261019T193113_587576Z/` and `claude_outputs/2026-10-19/adhoc/20261019T193155_210992Z__posting-8189909__revision__cli.{json,stdout.bin,stderr.bin}` |
| Passed validator? | **No**, for both imports, with the same error string (`…Expecting value: line 1 column 1 (char 0)`). A: shell commands (clipboard error). B: code fences around otherwise valid JSON | **Yes** (`valid: true`). Verdict `relevant`; cites `target_titles`, `skills` / `id`, `title`, `content` | **Yes** (`valid: true`). Verdict `relevant`; cites `target_titles`, `skills` / `title`, `content` |
| Contract refusals respected? | Only partly assessable: B's JSON gives a labeled judgment with no instruction-following; the omitted prose cannot be assessed | Yes, as far as the reply shows: it gives a labeled judgment and no instruction-following. Nothing else is observable | Yes: only the allow-listed host was fetched; no redirect (`redirect_refused: false`, final URL unchanged); no tools; the judgment was saved separately from the record |

### Trial 1: pasted into claude.ai (two separate imports, two different failures)

There are two Trial 1 imports on record. They fail for different reasons, and both are preserved.

**Import A: clipboard error, the wrong text (19:20:10Z).** The file
`evidence/action-surfaces/trial1-chat-response.json` holds exactly this:

```
mkdir -p evidence/action-surfaces
pbpaste > evidence/action-surfaces/trial1-chat-response.json
python3 -m watcher judgment-import --help
```

When `pbpaste` ran, the clipboard held these terminal commands, not Claude's reply. The import
(`claude_outputs/2026-10-19/manual-import/20261019T192010_559175Z__posting-8189909__revision.json`) rejected
them at char 0. This failure says **nothing** about Claude's output. It is a mistake in saving the reply, and
it is kept unedited as evidence of that mistake (`FRICTIONAL.md` S4).

**Import B: partial recovery, a code-fence validation failure (20:01:52Z).** The file
`evidence/action-surfaces/trial1-original-recovered.txt` (created 15:57:05 EDT, last modified 16:00:06 EDT) is
byte-identical to the text imported as
`claude_outputs/2026-10-19/manual-import/20261019T200152_969009Z__posting-8189909__revision.json`
(`surface_declared`: "claude.ai web chat — partial recovery retaining code fences"). It is a leading newline, then a
```` ```json ```` fence, one JSON object, and a closing fence. The validator rejected it:
`output is not exactly one JSON object: Expecting value: line 1 column 1 (char 0)`.
- That error string is the same as Import A's. Only the saved texts show that the two causes differ.
- Diagnostic only (Claude Code, 2026-10-19; nothing saved or imported): with the fences removed, the
  inner object passes every other check, with verdict `relevant` citing `target_titles`, `skills` / `title`, `content`.
  The fence is the **only** reason for the rejection. The contract requires exactly one JSON object, so the
  rejection is correct, and the validator does not repair output.
- **What this recovery is not.** Siddhesh states that it omits the prose that surrounded the code block in the
  original reply. It is therefore **not the complete original response**. The project does not record how
  it was recovered, and the omitted prose is not available. The recovered text supports this claim: Trial 1's reply
  contained a code-fenced JSON object that strict validation rejects. The claim that the original also had surrounding prose
  rests on Siddhesh's statement only.
- Import B happened about 41 minutes after Import A and after Trials 2 and 3. It is a later re-import, not a
  record made at the time of the trial.

### Trial 2: attached file in a fresh claude.ai chat

The reply is one bare JSON object. It passed, and its verdict matches the hand label and the deterministic record.
The surface's own record holds only the declared surface and model. Everything else about the chat, such as
tools, memory, other context, and whether the reply was edited before copying, is unobserved.

### Trial 3: two separate user-invoked commands, not one autonomous action

Trial 3 consisted of **two commands that Siddhesh ran by hand**. No single Claude action fetched the board
and then judged a posting, and Claude did not decide to fetch.

1. **Live watcher, separate state.** This run wrote its evidence to `evidence/action-surfaces/trial3-runs/`
   and its state to `evidence/action-surfaces/trial3-state/stripe.json`, not to the default `state/`.
   - `fetch_meta.json`: `https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true`, 200 OK,
     final URL unchanged, 5,636,747 bytes, SHA-256 `2923b540…159a`, 19:31:13.596801Z → 19:31:14.178176Z.
   - `report.json`: `status: baseline_saved`, `postings_in_response: 723`, `previously_seen: 0`,
     `new_count: 0`, `new_postings: []`, `state_updated: true`.
   - `state_before.json`: `{"exists": false}`. `state_after.json` and `trial3-state/stripe.json`: 723 seen IDs,
     `successful_runs: 1`. This is the contract's baseline behavior: the first success reports zero new postings.
   - No Claude call was made by the watcher in this run.
2. **CLI judge, separately invoked.** The record's `purpose: adhoc` and `saved_by: watcher.claude_cli` match
   `python3 -m watcher judge --backend cli --prompt revision --posting-id 8189909 --raw …`, but the exact shell
   command line was not saved. Record: `claude_outputs/2026-10-19/adhoc/20261019T193155_210992Z__posting-8189909__revision__cli.json`.
   Exit code 0, `subtype: success`, 1 turn, `stop_reason: end_turn`, valid, verdict `relevant`.
   Auth: claude.ai Pro login (Claude Code 2.1.292).
   - The record does **not** store the `--raw` path, so it cannot show whether the judge read the
     2026-10-18 response or the Trial 3 live response. In this case that does not change the input (see next section).

### Original vs. live content for posting 8189909

Claude Code compared the two saved raw responses on 2026-10-19:

| | Original (2026-10-18) | Live (Trial 3, 2026-10-19) |
|---|---|---|
| File | `evidence/fetches/stripe/20261018T160635_483273Z/raw_response.bin` | `evidence/action-surfaces/trial3-runs/stripe/20261019T193113_587576Z/raw_response.bin` |
| SHA-256 | `fa20e4be…e243` | `2923b540…159a` |
| Postings on board | 731 | 723 (14 removed, 6 added) |
| Posting 8189909 raw JSON object | — | **identical in every field** (title, content, location, URL, `updated_at` 2026-10-07T19:02:27-04:00, and all others) |

The normalized posting, and therefore the user message sent to Claude, is the same for either file. All
20 sampled postings are still on the live board, and none of them changed. The two whole-board responses differ, but
the posting used in every trial did not change between the fetches.

## Access, authority, and risk

| | Reads | Writes | Sends (leaves the machine) | Authority required |
|---|---|---|---|---|
| Trial 1 (pasted chat) | The pasted text | Nothing locally. A person copies the reply and saves it | The prompt + fictional résumé fields + public posting, sent to claude.ai (Anthropic) | Siddhesh's claude.ai login; a person doing copy and paste |
| Trial 2 (attached file) | The attached file | Nothing locally. A person saves the reply | The same content as a file upload to claude.ai | The same, plus a file upload |
| Trial 3 step 1 (watcher) | Public board JSON; `data/fictional_resume.json`; prior state | Raw evidence, metadata, state snapshots, state file | One HTTPS GET to `boards-api.greenhouse.io` (no credentials) | Network access to one allow-listed host; write access to the project directory |
| Trial 3 step 2 (CLI judge) | One saved raw response; prompt file; résumé subset | `claude_outputs/…` record, stdout, stderr | System prompt + user message to Anthropic via Claude Code | The Claude Code OAuth login on this machine (a stored credential), which counts against subscription usage |

**Risks**
- *Browser surfaces:* there is no machine record of what was sent or received. Copy and paste can save the wrong text,
  which happened in Trial 1. The model and tool settings are declared, not verified. A person could alter or pick
  the reply before saving it.
- *Watcher:* untrusted posting HTML is parsed locally, and a bad fetch could corrupt state. These risks are mitigated by host and path
  allow-listing, refused redirects, validating the full response before writing state, and keeping raw bytes.
- *CLI judge:* it uses a stored login credential, posting text could attempt prompt injection, and the CLI may add its own context
  (C6). These risks are mitigated by tools disabled, one turn, a fresh session, strict output validation, unavailable-not-invented,
  and model-reported checking.
- *Combining fetch and judge into one autonomous loop* (`watch --claude`) would let one unattended process
  both pull untrusted text and spend model usage under a stored credential. This was not done in these trials.

**Least autonomy sufficient**
- *One judgment:* no network fetch and no standing credential use beyond one call. Pass the
  saved posting to a tool-less, one-turn model call, either as a person-initiated `judge` call or as a pasted or attached chat,
  and run strict validation. Trial 2 and Trial 3 step 2 both meet this. Trial 3 step 2 is better evidenced because
  the surface records model, settings, and raw bytes itself.
- *Ongoing watching:* read-only network access to one allow-listed host, plus write access to the project's
  evidence and state directories. Nothing else is needed for watching itself. Judging new postings adds model-call
  authority. That should stay a separate, person-invoked step until watching has run reliably, and it should never gain
  tools, send messages, or apply for jobs (CONTRACT "Refuses").

## Limits of observation

- Claude Code (this author) had no access to the claude.ai sessions in Trials 1 and 2. It cannot see the
  conversation, the model actually used, enabled tools (web search, code execution, connectors), memory,
  project knowledge, custom instructions, or whether the reply was edited or regenerated. No
  screenshot or transcript is saved. Private conversation transcripts are deliberately not included in this project.
- The two claude.ai import timestamps record when the text was **imported**, not when the chat ran.
- "Opus 5.5" for Trials 1–2 is as typed by Siddhesh into `--model-declared`.
- Trial 3's CLI record cannot rule out context that Claude Code injects itself (`FRICTIONAL.md` C6). It does not store
  the `--raw` argument.
- One posting and one attempt per surface. This is a description of three runs, not a reliability comparison.

## Comparison and conclusion

Only the local CLI surface left a machine-generated, verifiable record of input, model, settings, and raw
output. Both browser trials depend on manual copying, and Trial 1 shows two ways that fails. First, the clipboard
saved shell commands instead of the reply. Second, the later partial recovery lost the surrounding prose. The recovered
part shows the pasted-prompt chat wrapped its JSON in a code fence, which strict validation rejects. The
attached-file chat (Trial 2) returned a bare object. With one attempt each, this is an observation, not a
comparison of rates. Trial 2 and Trial 3 produced the same
verdict (`relevant`), matching the hand label and the deterministic record, on input that was identical across both board fetches.
Trial 3 was two separate commands that a person invoked. It does not demonstrate an autonomous fetch-and-judge agent.
