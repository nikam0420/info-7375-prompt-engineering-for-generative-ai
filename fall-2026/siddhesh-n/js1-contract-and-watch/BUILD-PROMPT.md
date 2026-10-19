# Build prompt

The implementation request given to Claude Code (Claude Opus 5.5) on
2026-10-18, saved verbatim at the requester's instruction. This is the request
only, not a conversation transcript.

---

Read CONTRACT.md and implement this assignment against it using Python 3.12, preferably the standard library. Do not modify CONTRACT.md. It was committed before implementation as c978ff3 and is explicitly AI-assisted.

Work only inside this project folder. Do not read personal files, real résumés, contacts, application trackers, or other projects. Do not apply, message anyone, log in to job sites, push to GitHub, or spend money.

Build:
1. A bundled fictional résumé JSON satisfying CONTRACT.md.
2. A public Greenhouse board watcher with strict HTTPS host/path validation, redirects refused, raw response evidence saved, validated input, per-board seen-ID state, baseline reporting zero new postings, and later runs reporting only unseen IDs.
3. Deterministic relevance records with field-specific justifications.
4. A Claude judgment prompt and strict output validator matching CONTRACT.md. Provide an explicit way to obtain actual Claude judgments and save dated raw outputs. Never substitute deterministic results for Claude judgments.
5. Meaningful unittest tests covering the contract, including wrong-ID associations, empty citations, baseline, repeat runs, new IDs, failed fetches, malformed data, and blocked hosts. Clearly label constructed test fixtures.
6. Tools to prepare a reproducible seeded two-run demonstration from real fetched postings. Preserve the original response unchanged and label any reduced snapshot as constructed and seeded.
7. Tools to select 20 real postings, split them into 10 development and 10 held-out, and let ME hand-label them before model evaluation. Do not generate my hand labels or show model predictions first.
8. Tools for 5 postings × 4 independent fresh Claude calls, saving every actual response, timestamps, model information, and validation failures. Do not run these calls yet.
9. A baseline prompt and exactly one revision changing one thing. Keep held-out evaluation locked until the revision is frozen. Do not fabricate results or metrics.
10. README with exact fresh-clone commands, SOURCES.md naming ChatGPT’s contract assistance and your actual contributions, and report templates for sampling, prompt experiment, action-surface comparison, FRICTIONAL.md, driver's-seat evidence, and sign-off. Leave unperformed work explicitly pending and the signature withheld.

Save this implementation request in BUILD-PROMPT.md. Do not publish private conversation transcripts.

First implement and run local tests. You may fetch one public Greenhouse board through the allow-listed endpoint to obtain real evidence; choose one with at least 20 postings and record the exact board, URL, and retrieval time. If unavailable, report the failure rather than invent data.

Do not claim I wrote your tests, performed hand labels, checked results, or completed the three action-surface trials. Record only actions actually performed.

When finished, stop and give me:
- files created;
- exact test command and actual result;
- board retrieval outcome;
- the next command for me to run myself;
- any missing requirements or contract ambiguities.
