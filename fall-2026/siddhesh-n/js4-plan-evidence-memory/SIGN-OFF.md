# Sign-off — Job-Search Agent 4

**Checked and how**

- On my Mac, I reran all six unit tests and the fictional seeded replay. The tests passed and the notes reached revision 4.
- By hand, I checked `planted-error.json` and confirmed the pay check rejected the claim of 99 against the trace value of 42.
- In `diff.json`, I confirmed that posting `P-104` changed from live to unknown and posting `a` changed from live to gone in the replay.
- In `day2-conflict.json`, I confirmed that the stale writer expected revision 2, found revision 3, and left the notes unchanged. The merge reached revision 4 with both watchers.

Not checked in this scope: production ATS availability, whether actual employer language implies sponsorship eligibility, or correctness during multi-host concurrent writes. The seeded run demonstrates the behavior of the replay and file-based revision rule under the provided conditions.

**Signed** — Siddhesh Nikam, November 27, 2026

| Claude or another reviewer | Student | Why the student owns the decision |
|---|---|---|
| Challenge the order or provide a concrete counterexample. | Verify the counterexample using the draft and input data. | A reviewer can overlook prerequisites or share assumptions with the builder. |
| Suggest alternate evidence. | Decide whether the alternate evidence can fail independently. | The student can identify whether two apparent checks depend on the same field or parser. |
| Suggest edge cases or help read code. | Run tests, inspect evidence and sign or withhold. | The signature attests to personally completed work. |
