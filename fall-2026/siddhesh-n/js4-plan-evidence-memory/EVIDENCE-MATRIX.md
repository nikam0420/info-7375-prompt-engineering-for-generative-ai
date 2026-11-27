# Tool evidence matrix

The board and direct lookup are independently structured fictional fixtures. They support checking how the mechanism responds to disagreements. They share an author and do not establish any fact about a current employer.

| Claim | Check | Failure caught | Why it fails differently |
|---|---|---|---|
| Live or gone in the replay | Compare board membership with the direct lookup's 200 or 404 for the same ID. | Stale collection or a posting omitted by the list. | The claim uses list membership while the check uses a separate per-ID status record. |
| New to this search memory | Compare the proposed flag with direct liveness and membership in the prior notes revision. | Repeated listings called new, or withdrawn listings called new. | Uses the persisted prior revision and direct status. Both paths rely on stable posting IDs. |
| Title | Compare exact board title with lookup title. | A mismatched or misjoined listing title. | Reads the detail record by ID independently of the board projection. |
| Location or remote status | Compare the verbatim location field with the detail record. | Labeling a Boston listing remote or broadening a US-only remote label. | Uses the separate source value, without a semantic classification. |
| Employer authorization or sponsorship wording | Compare exact text or null with the detail field. | Dropping negation or filling silence with an inference. | Uses literal lookup text. Null means the fixture provided no evidence. |
| Pay minimum and unit | Compare amount and unit with the detail record. | Fabricated amount, currency or cadence. | The verifier reads the lookup field independently of the reporting transformation. |
| Summary pay amount | Compare the summary amount with the verified trace. | A later reporting step changes 42 to 99. | Uses a previously persisted or retained value. This catches transcription drift, even if both paths still share a wrong source. |

The watcher scores are deterministic heuristic decisions under the fictional persona. They do not assert candidate eligibility.

The reviewed replay also checks a third liveness value. On day two, P-104 lacks both a board entry and a direct record, so the check requires unknown and cites the earlier notes revision and later fixture. Posting a has an explicit 404 and is recorded as gone.
