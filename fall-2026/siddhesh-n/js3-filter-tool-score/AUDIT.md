# Reject audit

The 2026-11-25 run scored all 989 collected postings: 15 kept, 974 rejected, 0 unknown. Collection details and payload hashes are in `evidence/collection.json`. The manifest contains 30 seeded uniform random rejects without replacement, five supplemental closest rejects, five closest available keeps, five random keeps, and 17 disjoint held-out rows. Ties used board/ID order. The 30 random rejects are the only simple random reject group. The boundary groups intentionally oversample cases near the decision line.

## Hand verdicts

Siddhesh exported verdicts and reasons for all 62 rows. Codex suggested wording and verdicts for postings discussed during review. These are student-entered, AI-assisted judgments. The sheet hid the filter decisions and scores. The export and recomputed counts are in `evidence/human-labels.json` and `evidence/comparison.json`.

| Audit group | Judged | Agreed with filter | Filter errors |
|---|---:|---:|---:|
| Random rejects | 30 | 27 | 3 false negatives |
| Closest rejects | 5 | 1 | 4 false negatives |
| Closest keeps | 5 | 5 | 0 |
| Random keeps | 5 | 5 | 0 |

The random-reject misses were Wealthfront Data Scientist, Marketing, Airbnb Senior Data Scientist, Guest & Host, and Stripe Renewals Analyst. The filter missed **3 of 30 (10%)** in this random reject sample. Each judgment changes that estimate by 3.3 percentage points. The result is a noisy estimate for rejects in this snapshot only. The closest cases were deliberately oversampled and should be read separately. Four of the five closest rejects were relevant under the entered labels, which exposes a weakness around noncanonical analytics titles.

## False friend and rule decisions

The AI-assisted inspection traced **reporting** in Airbnb Senior Talent Partner, India, to “Reporting to the Talent Director, APAC & India.” It describes a management relationship. Reporting supplied one point, and the posting was rejected. [Source posting](https://careers.airbnb.com/positions/8305593?gh_jid=8305593)

| Proposal | Measurement on same intake | Decision |
|---|---|---|
| Let the word reporting qualify by itself | 190 additional baseline rejects would be kept, including the false friend above | Rejected. This count measures changed decisions. |
| Count each SQL occurrence | 10 additional baseline rejects would be kept | Rejected. Repeated words can create independent-looking score without independent evidence. |
| Remove all reporting matches | The inspected phrase shows a precision problem. Relevant Airbnb text includes “operations reporting.” | Rejected. Context-sensitive handling would require more labeled examples. |
| Exclude management-relationship uses of reporting | One concrete occurrence was inspected | Deferred as an unmeasured rule. |
| Raise threshold to 5 | Two held-out keeps flipped to reject. Both were entered as relevant. | Retain 4 for this submission. |

No baseline scoring rule was added or cut after measurement. The measurement changed the sampling design as recorded in FILTER.md.
