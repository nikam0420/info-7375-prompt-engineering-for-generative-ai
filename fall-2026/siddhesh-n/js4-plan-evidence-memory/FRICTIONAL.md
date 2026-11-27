# Frictional

## November 27, 2026

- The initial public course branch did not contain JS3. Codex located the relevant work on the student's fork at c113611958b1323808267464ed8d91c64a1ef685. The implementation reuses that scorer and introduces a bounded replay.
- Codex drafted two distinct verification paths for the pay claim. The detail lookup tests the claim against a fixture. The summary comparison targets later transcription drift using the verified trace. Neither can establish real-world pay.
- The plan draft is preserved in evidence/plan-draft.md. The intended ordering is plan, actual review and amendment, then first agent run. PREMORTEM.md records a prediction before any failure demonstration.
- I asked Claude to review my plan before the run. It pointed out that the original plan could stop if a previously seen posting disappeared from both the board and the direct lookup. In my Mac replay, I checked that P-104 became unknown and posting a became gone. I also confirmed that the stale write left the notes unchanged and the merge reached revision 4. This showed me why a missing lookup and an explicit 404 support different conclusions.
- After the review, Codex reproduced the original loader's rejection by inspecting its ID-set equality requirement. The amendment accepted P-104 as an unknown status when neither source gave a current signal. We retained a separate 404 case to demonstrate a verified withdrawal in the simulation. See test_missing_listing_and_lookup_remain_unknown and evidence/replay/diff.json.
- Codex ran six tests and the full seeded replay, then recomputed the expected conflict, liveness, error rejection and inert-text results from JSON. I later reran the tests and seeded replay on my Mac, inspected the three JSON outputs, and signed `SIGN-OFF.md`.