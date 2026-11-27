# JS4 run plan

Drafted November 27, 2026, before implementation and execution. Starting point: JS3 scorer at c113611958b1323808267464ed8d91c64a1ef685. Fictional persona: Morgan.

| Step | Inputs and permissions | Testable handoff |
|---|---|---|
| A. Review | Read this plan. Student verifies reviewer feedback and owns budget changes. | Record reviewer, date, criticism, counterexample and disposition before execution. |
| B. Load | Read only two bundled fictional snapshots. | Each snapshot has a distinct ordered date, unique IDs and a matching direct lookup for each currently listed ID. Invalid inputs stop the run. |
| C. Propose | Read prior memory and snapshot. Run JS3 scoring at thresholds 4 and 5. | Write typed proposed claims keyed by posting ID with source references and separate scoring traces. |
| D. Verify | Read original fixtures and prior memory separately from proposal logic. | Exact checks cover status, newness, location, employer wording and pay. Compare the summary minimum to the saved trace. A mismatch prevents that proposal from reaching notes. |
| E. Persist | Both watchers read the same version. Only the notes store can write within the output directory. | First write increments version. Second write with the old version fails. It can reread and merge once. |
| F. Report | Read state versions from both seeded days and check results. | Report added IDs and changes, with explicit evidence for any formerly live posting that is now gone. |

Dependencies: A → B → C → D → E → F. B also supplies raw fixtures to D. Process the earlier day through E before passing its final state into C for the later day. This is executable because both fixture files and the scorer exist locally and day one starts from empty version 0. Unroll the two executions by date and there is no cycle.

Budget: two snapshots, at most 20 postings per snapshot, two watchers, one conflict merge per watcher per day, zero network requests and zero model calls during execution. Only the student can change these limits by recording a plan amendment. Use Python 3.12 and a fresh output directory. The agent has no login, application, email or messaging capability.

Stop on invalid fixture, failed positive evidence check or conflict after the one merge. A negative control passes only when the planted claim is rejected. A failed evidence check receives no identical retry. A stale write is retried once only after rereading and merging.

## Review record

Claude, reported by Siddhesh on November 27, 2026, identified P-104: a job present on day one is absent from both views on day two. Codex checked the draft and original loader: the required equality between the direct IDs and the union of current and remembered IDs would reject that input before verification. Siddhesh's personal verification remains for sign-off.

Amendment before the first replay: accept a missing direct record for remembered IDs absent from the current list. Save the current list, lookup status or lack of response, and prior state revision as evidence. Report `live = null` (unknown) when both current list and direct evidence are absent. A direct 404 supports `live = false` in this replay. Claude proposed calling list absence gone. We adopted the distinction between current and remembered IDs and kept the stronger requirement for a gone claim because list omissions can happen without withdrawal. Preserve the original in evidence/plan-draft.md.
