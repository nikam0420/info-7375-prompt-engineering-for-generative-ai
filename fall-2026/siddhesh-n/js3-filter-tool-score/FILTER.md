# Filter v1.0 — design before implementation

Fictional persona: Morgan, seeking US data analytics, business intelligence, analytics engineering, or data engineering roles. For relevance judgments, consider whether the work is materially in these areas. Score is a review priority, independent of eligibility.

| Rule | Reason |
|---|---|
| Whole-phrase title match on data analyst, business intelligence, analytics engineer, data engineer, or business analyst, including ordinary inflections | These titles are strong signals for the target work. |
| Add 3 for a title match | A title match should dominate a single body keyword. |
| Add 1 per distinct body signal: SQL, dashboard(s), ETL, data pipeline(s), data modeling, or reporting | Multiple independent concepts can surface unconventional titles. |
| Keep at 4 or higher | A matching title needs corroboration, while four body signals can surface an adjacent role. |
| Require title and description to score | Missing text is an unknown, kept out of ranking and reported separately. |
| Sort by descending score and then stable board/ID key | Ties are reproducible. |

Everything above is hand-set. Wrong alternatives to test: keep whenever reporting appears, and count repeated copies of SQL as independent evidence.

Expected public sources: Stripe and Airbnb Greenhouse feeds, plus Wealthfront Lever. Expect board, stable ID, title, visible description, URL and location when supplied. A missing board or records array means coverage is incomplete. Missing ID is unusable. Missing URL or location is unknown. Avoid inferences from board names or URL slugs.

## Claim evidence

Supported means a direct statement attributable to this role establishes the atomic claim. Contradicted means an explicit statement establishes its opposite. Insufficient includes silence, wrong context, ambiguous language, and a claim stronger than its quote. Say “I cannot tell” on insufficient evidence. Preserve exact excerpts and board/ID. A literal SQL mention can support “mentions SQL”; it cannot by itself support “SQL required.” Manual reading handles modality and actor scope. If a board returned truncated content, abstention can hide a requirement actually stated on the full page.

## Planned sample

Reproducible simple random sample of 30 rejected rows, seed 7375. Supplement with five closest rejects, five closest keeps and five random keeps, with no row repeated in the audit. Separately reserve up to 24 other rows balanced by baseline keep/reject and lock human labels before comparing threshold 4 with threshold 5. Coverage and threshold strata describe these samples only. Change threshold alone; preserve all weights, inputs and parsing. Do not tune on reserved labels.

## Sampling amendment v1.0.1

The first sample layout had no held-out rows on the boundary between 4 and 5. Before any human labels were received, the audit plan was amended to reserve up to two score-4 rows in the holdout before drawing closest/random keeps, with ID-order ties and seeded draws for the remaining rows. The random reject draw remains identical. This is a change to the sampling design. The filter itself and the two thresholds stayed the same.
