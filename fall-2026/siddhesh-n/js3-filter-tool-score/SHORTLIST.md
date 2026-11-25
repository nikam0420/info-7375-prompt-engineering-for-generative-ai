# Source-grounded shortlist

`evidence/shortlist.json` lists the top five by score with exact literal excerpts. Those machine-generated claims are deliberately limited to whether a term appears. A repeated employer description may occupy multiple positions because board IDs are distinct. The filter gives review priority and does not screen geography or work authorization. The Canada posting is an example of relevance to work type while geographic eligibility needs separate judgment.

| Posting | Atomic claim | Label | Evidence or answer |
|---|---|---|---|
| [Stripe Analytics Engineer](https://stripe.com/jobs/search?gh_jid=8415333) | SQL proficiency is specified. | Supported | “Proficiency in SQL and data modeling techniques.” |
| [Stripe Data Analyst, Canada](https://stripe.com/jobs/search?gh_jid=5416444) | Prior experience at a growth-stage internet or software company is required. | Contradicted | “Preferred qualifications Prior experience at a growth-stage internet or software company” and “preferred qualifications are a bonus, not a requirement.” |
| [Stripe Data Analyst, US](https://stripe.com/jobs/search?gh_jid=5601881) | SQL proficiency is mentioned. | Supported | “Proficiency in SQL.” |
| [Stripe Data Analyst, SF](https://stripe.com/jobs/search?gh_jid=8189909) | SQL proficiency is mentioned. | Supported | “Proficiency in SQL.” |
| [Airbnb Senior Data Software Engineer](https://careers.airbnb.com/positions/8300926?gh_jid=8300926) | The posting is US remote eligible. | Supported | “This position is US - Remote Eligible.” |
| Same Airbnb posting | An applicant can work remotely from every US state. | Contradicted | “you must live in a state where Airbnb, Inc. has a registered entity.” |
| Same Airbnb posting | SQL is tested in a live interview. | Insufficient | “Strong SQL skills” describes the desired skill. I cannot tell how the company tests it. |

Relevance-versus-entailment example: the Airbnb posting reached six points and includes SQL. That provides no direct evidence for a live SQL round. The abstention rule applies when a claim exceeds the source. Its limit appears in this seeded counterexample: an excerpt reading “Your Location: [details omitted]” warrants abstention on remote status even if the omitted source says “Remote Eligible.” The answer reflects available evidence, and fuller source coverage could reverse the abstention.
