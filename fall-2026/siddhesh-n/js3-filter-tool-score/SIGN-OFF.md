# Sign-off — Job-Search Agent 3

| Checked property | Method and attribution |
|---|---|
| Standalone reporting and repeated SQL do not pass the filter | Codex wrote and ran `test_reporting_alone_is_not_relevant` and `test_repeated_sql_is_one_signal`. |
| Title corroboration, multiple body signals, and missing evidence | Codex wrote and ran `test_title_and_one_signal_clear_baseline_only`, `test_distinct_body_signals_can_surface_adjacent_title` and `test_missing_text_abstains`. |
| Startup and tool dispatch | Codex ran `test_tools_require_initialization`, `test_malformed_message` and the live subprocess transcript test `demo.py`. |
| Board collection and sample counts | Codex ran both collection versions and checked sample stability. |
| Historical threshold sensitivity | Codex verified the locked JS1 CSV and recomputed both thresholds on 10 prior judgments that Siddhesh recorded in JS1. |
| Student's independent checks | Siddhesh entered and exported 62 verdicts. Codex provided suggestions during the review and recomputed the counts. Add any separate tests you personally performed. |

Siddhesh ran the fictional Claude Code tool check. The supplied wire trace shows initialization, discovery of the tool via `tools/list`, and call ID 2 returning `5, keep`. Codex verified the pasted exchange.

**Not checked:** Newer MCP discovery interoperability. Independent repeat labeling by a second reviewer. Results on sources outside the allow-list. Complete MCP conformance. Hiring eligibility.

**Not claiming:** Market-wide coverage, qualification for a specific job, or evidence of model training.

**Signed or withheld:** Withheld pending student verification. Student name/date: ____________________

## Driver's seat

| Claude can do | I should do | Why |
|---|---|---|
| Call the score tool and summarize its literal matches | Read the duties and requirements in context | A word can appear in management, boilerplate or preferred qualifications. |
| Highlight evidence for each claim | Validate the exact quote, modality and source | I need to distinguish requirements, preferences and missing information. |
| Suggest alternate thresholds or signals | Fix the audit plan, enter my own judgments and decide the cost of misses | My job search determines which opportunities are worth time. |
| Explain why the system abstained | Check the posting and decide whether to look for more evidence | Gaps in the snapshot can leave a real question unanswered. |
