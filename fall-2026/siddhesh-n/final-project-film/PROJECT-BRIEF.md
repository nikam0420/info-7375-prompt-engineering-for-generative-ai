# PROJECT-BRIEF — CheckedSQL

Siddhesh Nikam · INFO 7375 · Fall 2026 · Target role: Data Analyst (marketing analytics)

**Status (updated 2026-10-24):** a pitch with its first piece running. The dataset, ten test questions, answer key and checker exist in `checkedsql/` and score the baseline SQL (drafted with Claude) 10/10 (`checkedsql/results/baseline.md`). The Claude step, prompt contract and evaluation log do not exist yet. Past tense is used only for what exists; everything else is "will".

## 1. What is it?

CheckedSQL will let a marketing analyst ask a campaign question in plain English, have Claude write the SQL, run it on a campaign database, and show the answer together with the query and whether it matched a hand-verified answer.

When it is done, it will be a **GitHub repository** containing:
- a **synthetic** marketing-campaign dataset, so no real company data (**exists**: 24 rows in `checkedsql/data/campaigns.csv`);
- the question tool, written in **Python** (SQLite so a reviewer can run it without a database server; queries written for the same schema I used in PostgreSQL);
- a **test set** of about 30 questions, each with an answer worked out before any query runs (**10 exist**, with an answer key and `HAND-CHECK.md`);
- an **evaluation log** recording every pass and every miss, plus a short **failure write-up**.

Stack: Python, SQLite (PostgreSQL-compatible SQL), pandas, the Claude API.

## 2. Why would anyone care?

It saves a marketing analyst from trusting a number they can't check. Two real alternatives I looked at:

- **A fixed dashboard (Tableau).** My `marketing-campaign-analytics` project links one, which I made with AI help. *Correction 2026-10-24: the first version of this brief said I built it myself; I didn't.* A dashboard answers the questions planned in advance; a new question means building a new view.
- **Pasting the question into a general chat assistant.** **Tested 2026-10-24:** I attached `checkedsql/data/campaigns.csv` to a new ChatGPT chat (GPT-6.1 Sol Light) and asked *"Which channel had the highest ROAS in this data?"* It answered **Search, 3.98×**, with Email 2.29× and Social 1.05×, which matches my answer key exactly (screenshot: `build/chat_test_full.png`). So on this question it was right. The gap is that it was one answer to one question. Nothing records how often it is right across a fixed set of my questions, or which ones it gets wrong, and I couldn't see the query it ran.

What CheckedSQL does that they don't: every answer is run, shown with its query, and scored against a fixed answer key, and the misses are logged. Being right once (as ChatGPT was) isn't the same as a measured hit rate.

## 3. Who opens it, and what do they do with it?

Target role: data analyst. First reader: a **hiring manager** for that role. In the first sixty seconds they will open the README, see the score table from the test set, and run one command. Part of that works today: `python3 checker.py` prints the score table for my own queries (10/10). Later the same command will score Claude's queries.

## 4. What does it prove about me?

- That I can get marketing metrics right (CTR, conversion rate, ROAS) and check them against an answer key. I'm still building the SQL skill (see §7).
- From this course: a **prompt contract** (schema, metric definitions, read-only SELECT only, fixed output format), **verification** against known answers, a repeatable **evaluation**, and **source grounding** (every answer comes with the query and the rows it came from).

A reviewer could fairly conclude that I can measure how often an AI-assisted analysis tool is right and explain why it is wrong when it is. Evidence: the test set and checker exist now (verification and a repeatable score); the evaluation log and failure write-up will come once Claude's queries are scored. It will not prove the tool works on other schemas or on real company data.

## 5. What is in, what is out, what comes first?

- **In:** one campaign schema, read-only questions, the test set, the log.
- **Out (deliberately):** it will not change the database. No INSERT, UPDATE or DELETE, no dashboards, no real company data.
- **First (done 2026-10-24):** the test set and the checker, before any Claude call. Ten questions, an answer key computed without SQL and laid out for a calculator in `HAND-CHECK.md`, my own SQL, and `checker.py`. It printed **10/10**. Two deliberately wrong queries that average ROAS row by row were both **failed** by the checker. **Next:** Claude gets the same ten questions, graded by the same checker.

## 6. What could sink it?

An answer that looks right but isn't. ROAS is a ratio: averaging it row by row gives a different number than total revenue over total spend, and both look plausible. In my synthetic data the trap changes the answer itself: averaging Email's eight row ratios gives **9.75** and makes Email the best channel; total revenue ÷ total spend gives **2.29**, and the best channel is **Search (3.98)**. My response: the metric definitions go in the prompt contract, and the test set has ratio questions (Q06, Q07). The checker already caught the trap when I fed it the wrong query on purpose.

## 7. Why this project?

**Mostly learning.** Honestly assessed on 2026-10-24:
- **What I already have:** the domain. I know which campaign metrics matter (CTR, conversion rate, ROAS, profit) and that a ratio has to be total ÷ total. Evidence: I checked the answer key's ROAS answers by hand on a calculator (FRICTIONAL, 2026-10-24). My earlier repos (`nikam0420/marketing-campaign-analytics`, `nikam0420/Individual_Siddhesh-Nikam_ExplorataryDataAnalysis`) show the domain I work in, but **AI wrote most of their code and the dashboard**, so they are weak evidence of coding skill. I don't count them as proof.
- **New to me:** writing and checking SQL myself, calling Claude from Python, writing prompt contracts, and building an evaluation harness with a failure analysis. CheckedSQL is how I will prove these: from here on, I write the queries for new test questions myself, and the checker scores them the same way it will score Claude's.

**I don't know yet** whether 30 questions is enough. I'll find out by watching whether new questions keep turning up new kinds of failure; if they do, the test set grows.

---

**Exists today**
- `nikam0420/marketing-campaign-analytics` (my earlier project: SQL, PostgreSQL, Python; its Tableau dashboard was made with AI help)
- `nikam0420/Individual_Siddhesh-Nikam_ExplorataryDataAnalysis` (my earlier EDA notebook)
- This brief, the beat sheet, and the pitch film
- `checkedsql/`: the synthetic dataset, 10 test questions, the answer key, `HAND-CHECK.md`, my 10 SQL queries plus 2 deliberate trap queries, and `checker.py` (baseline 10/10, traps caught 2/2, run 2026-10-24)
- My ChatGPT test on Q06 (2026-10-24): it answered Search 3.98×, which matches the key (`build/chat_test_full.png`)
**Will exist**
- The prompt contract (schema, ROAS = total revenue ÷ total spend, read-only SELECT, output format)
- The Claude step: question → Claude-written SQL → checker (Python + Claude API)
- The test set grown from 10 to about 30 questions
- The evaluation log of Claude's passes and misses
- The failure write-up
