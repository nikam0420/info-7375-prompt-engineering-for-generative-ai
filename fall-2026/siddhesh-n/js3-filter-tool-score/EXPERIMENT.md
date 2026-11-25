# One change at a time

| Input | Origin |
|---|---|
| Title weight 3 | Hand-set before implementation to favor explicit role titles |
| Distinct signal weight 1 | Hand-set before implementation, equal per concept |
| Baseline threshold 4 | Hand-set so one corroborating signal can promote a title match |
| Variant threshold 5 | Hand-set experimental change to raise the bar by one point |
| Claude prompt | No Claude prompt participates in scoring. The tool demonstration prompt is an interface request. |
| Seed 7375, sample counts, result limit 5 | Fixed reproducibility and review-size parameters. They do not affect individual scores. |

The baseline and variant use the same 989-posting intake, parsing, dictionaries, and weights. The comparison changes the threshold only. Seventeen rows are held out, including two intentionally reserved at the score-4 boundary. Two held-out predictions move from keep to reject. This is a measured behavioral difference on actual postings.

Student labels are pending in the initial package. TP, FP, TN, FN and accuracy require those labels. Import them without revising the variant or choosing examples after seeing their verdicts. Compare only definite human labels and report the resulting denominator. The held-out group is a small stratified check with boundary oversampling. Even with all labels it does not estimate board-wide performance. Raising the threshold trades two kept predictions for two rejected ones. Whether that helps depends on the two labels.

The scorer rereads the same Python rules on each launch. A persistent output change is consistent with saved code, configuration, or context. Separate evidence would be needed to establish that any model weights were updated.
