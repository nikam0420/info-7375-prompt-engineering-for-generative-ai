import unittest

from collect import content
from score import score
from tool_server import handle

class FilterTests(unittest.TestCase):
    def test_reporting_alone_is_not_relevant(self):
        self.assertEqual(score("Office Manager", "Reporting to the COO")["decision"], "reject")

    def test_repeated_sql_is_one_signal(self):
        self.assertEqual(score("Software Developer", "SQL SQL SQL SQL")["score"], 1)

    def test_title_and_one_signal_clear_baseline_only(self):
        self.assertEqual(score("Senior Data Engineer", "Build data pipelines.")["decision"], "keep")
        self.assertEqual(score("Senior Data Engineer", "Build data pipelines.", 5)["decision"], "reject")

    def test_distinct_body_signals_can_surface_adjacent_title(self):
        self.assertEqual(score("Platform Developer", "SQL and ETL, data modelling, dashboards.")["score"], 4)

    def test_missing_text_abstains(self):
        self.assertEqual(score("Data Engineer", " ")["decision"], "unknown")

    def test_literal_mention_does_not_become_a_requirement(self):
        result = score("Data Analyst", "SQL is nice to have.")
        self.assertEqual(result["mentions"], {"SQL": "SQL"})

    def test_greenhouse_html_visible_text(self):
        self.assertEqual(content("&lt;p&gt;SQL &amp;amp; dashboards&lt;/p&gt;"), "SQL & dashboards")

    def test_js2_allowlist_preserves_exact_endpoints(self):
        from js2_intake import BOARDS, PolicyError, require_request
        for _, _, url in BOARDS:
            require_request("GET", url)
            with self.assertRaises(PolicyError):
                require_request("GET", url + "#unexpected")
            with self.assertRaises(PolicyError):
                require_request("POST", url)

    def test_js2_missing_jobs_still_means_unknown(self):
        from js2_intake import count_jobs
        with self.assertRaisesRegex(ValueError, "invalid listing schema"):
            count_jobs("greenhouse", b'{"meta":{"total":0}}')

class ProtocolTests(unittest.TestCase):
    def test_malformed_message(self):
        self.assertEqual(handle("{", {})["error"]["code"], -32700)

    def test_tools_require_initialization(self):
        result = handle('{"jsonrpc":"2.0","id":1,"method":"tools/list"}', {"ready": False})
        self.assertEqual(result["error"]["code"], -32600)

if __name__ == "__main__":
    unittest.main()
