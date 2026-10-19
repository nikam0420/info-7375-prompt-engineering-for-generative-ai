"""Response validation and the deterministic relevance record. CONSTRUCTED fixtures only."""

import json
import unittest

from helpers import constructed_job, fixture_payload, payload_bytes, resume
from watcher.postings import PostingValidationError, html_to_text, parse_response
from watcher.relevance import evaluate


def posting(title="Data Analyst", content="SQL"):
    return {"id": 7, "title": title, "content": content, "absolute_url": "https://jobs.example.com/7",
            "location": None, "updated_at": None}


class ParseTests(unittest.TestCase):
    def test_fixture_parses_and_converts_html(self):
        postings = parse_response(json.dumps(fixture_payload()).encode())
        self.assertEqual([p["id"] for p in postings], [1001, 1002, 1003, 1004])
        self.assertEqual(postings[0]["content"], "You will write SQL daily & build dashboards.")
        self.assertNotIn("<", postings[1]["content"])

    def test_missing_required_fields(self):
        for field in ("id", "title", "absolute_url", "content"):
            job = constructed_job(1)
            del job[field]
            with self.subTest(field=field), self.assertRaises(PostingValidationError):
                parse_response(payload_bytes([constructed_job(2), job]))

    def test_wrongly_typed_fields(self):
        cases = [("id", "1"), ("id", True), ("id", 1.0), ("id", 0), ("title", None), ("title", "  "),
                 ("content", None), ("content", ["SQL"]), ("absolute_url", 5), ("absolute_url", "javascript:x")]
        for field, value in cases:
            job = constructed_job(1)
            job[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(PostingValidationError):
                parse_response(payload_bytes([job]))

    def test_malformed_responses(self):
        for raw in [b"", b"not json", b"\xff\xfe", b"[]", b'{"jobs": {}}', b'{"no_jobs": []}',
                    b'{"jobs": [1]}', payload_bytes([constructed_job(1), constructed_job(1)])]:
            with self.subTest(raw=raw[:30]), self.assertRaises(PostingValidationError):
                parse_response(raw)

    def test_html_entities_decoded(self):
        self.assertEqual(html_to_text("&lt;p&gt;S&amp;#81;L&lt;/p&gt;"), "SQL")
        self.assertEqual(html_to_text("<p>Fish &amp; chips&nbsp;now</p><script>sql()</script>"), "Fish & chips now")


class RelevanceTests(unittest.TestCase):
    def test_all_three_conditions_pass(self):
        rec = evaluate(resume(), posting("Senior Data Analyst", "Daily SQL work."))
        self.assertEqual(rec["kind"], "record")
        self.assertEqual(rec["verdict"], "relevant")
        self.assertEqual(rec["posting_id"], 7)

    def test_case_insensitive_matching(self):
        r = resume(skills=["  sQl  ", "Excel"])
        rec = evaluate(r, posting("BUSINESS INTELLIGENCE ANALYST", "strong sql skills"))
        self.assertEqual(rec["verdict"], "relevant")
        self.assertIn('"  sQl  "', rec["justification"])

    def test_sql_must_be_whole_word(self):
        for text in ["PostgreSQL", "MySQL", "NoSQL stores", "sqlalchemy", "SQLite"]:
            with self.subTest(text=text):
                rec = evaluate(resume(), posting(content=text))
                self.assertEqual(rec["verdict"], "not_relevant")
                self.assertFalse(rec["conditions"]["content_contains_sql_word"]["passed"])
        for text in ["SQL.", "(SQL)", "T-SQL", "SQL/Python", "sql"]:
            with self.subTest(text=text):
                self.assertEqual(evaluate(resume(), posting(content=text))["verdict"], "relevant")

    def test_title_condition_fails(self):
        rec = evaluate(resume(), posting("Data Scientist", "SQL"))
        self.assertEqual(rec["verdict"], "not_relevant")
        self.assertIn("Condition 1 (title) failed", rec["justification"])

    def test_skill_condition_fails(self):
        for skills in (["Python"], ["SQL Server"], ["PostgreSQL"]):
            with self.subTest(skills=skills):
                rec = evaluate(resume(skills=skills), posting())
                self.assertEqual(rec["verdict"], "not_relevant")
                self.assertIn("Condition 3 (SQL skill) failed", rec["justification"])

    def test_absent_sql_described_as_absent_without_quotation(self):
        rec = evaluate(resume(), posting("Data Analyst", "Excel and Tableau dashboards."))
        j = rec["justification"]
        self.assertIn("absent from posting.content", j)
        cond2 = j.split("Condition 2")[1].split("Condition 3")[0]
        self.assertNotIn('"', cond2, "no quotation may support an absent SQL mention")

    def test_justification_cites_all_four_fields(self):
        for p in (posting(), posting("Chef", "none")):
            j = evaluate(resume(), p)["justification"]
            for field in ("résumé.target_titles", "résumé.skills", "posting.title", "posting.content"):
                with self.subTest(field=field, title=p["title"]):
                    self.assertIn(field, j)

    def test_seniority_and_location_not_assessed(self):
        rec = evaluate(resume(), posting("Principal Staff Data Analyst (Onsite, no visa sponsorship)", "SQL"))
        self.assertEqual(rec["verdict"], "relevant")

    def test_entity_encoded_sql_in_real_shaped_content(self):
        postings = parse_response(payload_bytes([constructed_job(5, content="&lt;li&gt;S&amp;#81;L&lt;/li&gt;")]))
        self.assertEqual(evaluate(resume(), postings[0])["verdict"], "relevant")


if __name__ == "__main__":
    unittest.main()
