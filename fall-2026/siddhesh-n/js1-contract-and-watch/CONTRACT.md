# Job-Search Agent 1 — Contract

## Contract status
Prepared with ChatGPT assistance before implementation.
Reviewed and accepted by Siddhesh Nikam: [10/18/26 AND 11.46AM]

## In
The agent takes one Greenhouse board name and a fictional résumé
stored as JSON.

The only permitted job-board host is boards-api.greenhouse.io.
Requests must use HTTPS, port 443, and the public board jobs endpoint.
Redirects are refused. No credentials or login are required.

The fictional résumé must contain:
- fictional: true
- name: a nonempty fictional name
- email: an address ending in @example.com
- phone: 202-555-0147
- target_titles: ["data analyst", "business intelligence analyst"]
- skills: a nonempty list of strings

Only the bundled fictional résumé is supported. These checks do
not prove that arbitrary user-supplied data is fictional.

## Out
The first successful run saves a baseline and reports zero new jobs.

For each posting ID not seen on an earlier successful run, return:
- Posting ID, title, and public URL.
- A relevant or not_relevant verdict labeled "record", calculated
  from the rule below.
- A separate Claude verdict labeled "judgment", not a fact.
- A justification naming the résumé and posting fields used.

Claude output must be one JSON object with exactly these keys:
posting_id, kind, verdict, resume_fields, posting_fields, justification.

kind must equal "judgment".
verdict must equal "relevant" or "not_relevant".
posting_id must match the input posting.
resume_fields and posting_fields must be nonempty lists of valid
field names from the supplied inputs.
justification must be a nonempty string.

Reject invalid output. If Claude is unavailable or validation fails,
report the judgment as unavailable separately; never invent one.

## Refuses
The agent will not:
- Fetch any host outside its allow-list or follow redirects.
- Display, publish, or send a real résumé.
- Present a model judgment as an established fact.
- Apply for jobs, email or message anyone, or log in anywhere.
- Execute instructions found inside a job posting.

Posting text is untrusted data, not instructions.

## Relevance rule
Use the same rule for hand labels and the deterministic record.

A posting is relevant only when all three conditions are true:
1. Its title contains at least one phrase in résumé.target_titles.
2. Its description contains SQL as a whole word.
3. résumé.skills contains an item equal to SQL.

Matching is case-insensitive. Trim leading and trailing whitespace
from résumé skill items. Convert description HTML to plain text
and decode HTML entities before checking SQL.

Title matching uses literal substring matching. Therefore, a title
such as Senior Data Analyst can qualify. Seniority, location,
salary, visa sponsorship, and experience are not assessed.

A valid posting that fails any condition is not_relevant.
Missing or wrongly typed required posting fields cause an input
validation error rather than a relevance verdict.

For each record, cite résumé.target_titles, résumé.skills,
posting.title, and posting.content, and explain which conditions
passed or failed. An absent SQL mention must be described as absent,
not supported with an invented quotation.

## Watch and evidence
Save the raw response bytes before normalization.
Validate the complete response before updating state.
Store seen posting IDs separately for each board.
Keep the union of previously seen IDs and current IDs.

Do not update state after a fetch or input-validation failure.
Keep raw evidence and state snapshots for both demonstrated runs.

If the demonstration uses a reduced snapshot made from a real
response, label it as a constructed seeded baseline. Do not claim
that its difference from the full response happened naturally.

## Two wrong implementations my tests must catch
1. Verdicts are attached to the wrong posting IDs after the order
   of postings changes. Tests must verify ID-to-verdict association.
2. Claude output with empty field citations is accepted.
   Tests must verify that the validator rejects it.

Additional tests must cover baseline behavior, repeated runs,
new IDs, missing fields, case matching, and disallowed hosts.

## What a failure looks like
[enter actual date and time, before running code]: This agent fails
its contract if it reports a baseline posting as new, attaches a
verdict to the wrong ID, accepts an uncited Claude judgment, or
attempts a request outside its allow-list.