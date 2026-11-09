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

Draft budget revision (2026-11-09, Codex): the five-second request ceiling produced two timeouts on the initial live run. The proposed 12-second per-request and 50-second collection ceilings cover up to four bounded requests. Operator decision: [record dated approval or revision before Claude Code].

## Wrong implementations

- Missing Greenhouse jobs field becomes zero and finished.
- HTTP failure has zero jobs instead of an unknown count.
- Duplicate URLs consume another request.
- An off-list hostname, redirected request, POST, prefix sibling, or symlink crosses the tool boundary.
- Request and time budget exits look like success.
- Raw files can be persisted without explicit approval.
