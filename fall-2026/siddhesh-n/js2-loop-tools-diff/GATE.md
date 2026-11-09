# Gate draft for operator review

This draft preceded the starter implementation. Review the choices, edit this file if needed, and record your decision before opening Claude Code.

| Exit | Condition and report |
|---|---|
| finished (0) | All unique planned boards returned HTTP 200 and valid payloads. Report observations and counts. |
| incomplete (2) | The plan was visited but one or more boards could not be validated. Report board errors with unknown counts. |
| budget-exhausted (3) | Board, request, or elapsed collection limit prevented completion. Record the current and any unattempted boards. |
| error (4) | Local policy or persistence failure prevented trustworthy collection. Report the failure and completed observations when possible. |

Maximum four unique boards, four requests, and 50 seconds of collection per run, including a per-request ceiling of 12 seconds. Collection is checked against a monotonic deadline. Reporting and operating-system cleanup are outside the collection deadline. Only the human operator can change budgets via a new dated written decision and a reviewed code change.

Repeat identity is the exact configured GET URL. Log later occurrences as skipped and spend zero extra requests on them. Failed boards are logged once and collection moves to the next board. Zero retries keeps attribution clear and requests bounded. Investigate a failed board manually.

Only unauthenticated HTTPS GET calls to exact configured public listing URLs on boards-api.greenhouse.io and api.lever.co. Reject redirects, credentials, alternative ports and paths, and network writes. The agent never applies, emails, messages, or logs in. No résumé, contacts, or tracker. Use only fresh files directly inside the operator-created jobs directory. Raw persistence requires the operator's explicit --approve-raw flag. Reject traversal, sibling prefixes, links, and existing destinations. Run from a trusted checkout under the operator's account. The transport uses the operator’s configured HTTPS proxy environment if present and disables curl startup configuration.

Draft budget revision (2026-11-09, Codex): the five-second request ceiling produced two timeouts on the initial live run. The proposed 12-second per-request and 50-second collection ceilings cover up to four bounded requests. Operator decision — November 9, 2026. I kept the draft limits of four boards, four requests, 12 seconds per request, and 50 seconds for collection. Four requests at the per-request limit take 48 seconds, leaving two seconds of margin. I kept zero retries so a failed board uses one request and the loop can continue. The draft limits were written before the Claude Code patch. I recorded my decision after the patch review.

## Wrong implementations

- Missing Greenhouse jobs field becomes zero and finished.
- HTTP failure has zero jobs instead of an unknown count.
- Duplicate URLs consume another request.
- An off-list hostname, redirected request, POST, prefix sibling, or symlink crosses the tool boundary.
- Request and time budget exits look like success.
- Raw files can be persisted without explicit approval.

## Second review — November 9, 2026

I ran the independent checker on a constructed copy of the missing-schema
trace with its run status changed to error. The checker printed PASS and
exited 0. For this single-board seed, I expect the checker to accept only
a run with status incomplete, a board result of board-failed, and an
explicit null count. It should reject a mismatch with exit 1.

I am limiting this review to independent_check.py. I will commit the
failing test before asking Claude Code for a patch. The agent loop,
budgets, and permissions are outside the scope of this review.
