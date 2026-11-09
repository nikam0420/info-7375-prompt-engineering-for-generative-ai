import unittest
from unittest.mock import patch

from agent import BOARDS, collect


def get(url, seconds):
    if url == BOARDS[3][2]:
        return 404, b'{"error":"seeded"}'
    return 200, b"[]" if url == BOARDS[2][2] else b'{"jobs":[{"id":1}]}'


class Loop(unittest.TestCase):
    def run_plan(self, plan):
        return collect(plan, get, lambda label, raw: label + ".raw")

    def test_seeded_failure_continues_and_count_is_unknown(self):
        trace = self.run_plan((BOARDS[0], BOARDS[3], BOARDS[2]))
        self.assertEqual(trace["status"], "incomplete")
        self.assertIsNone(trace["observations"][1]["count"])
        self.assertEqual(trace["observations"][2]["result"], "observed")

    def test_repeat_skips_without_spending_request(self):
        trace = self.run_plan((BOARDS[0], BOARDS[0], BOARDS[1]))
        self.assertEqual(trace["status"], "finished")
        self.assertEqual(trace["requests"], 2)
        self.assertEqual(trace["observations"][1]["result"], "repeat-skipped")

    def test_request_budget_reports_unattempted_boards(self):
        with patch("agent.MAX_REQUESTS", 1):
            trace = self.run_plan(BOARDS)
        self.assertEqual(trace["status"], "budget-exhausted")
        self.assertEqual(trace["requests"], 1)
        self.assertEqual(trace["observations"][1]["result"], "budget-blocked")
        self.assertEqual(trace["observations"][2]["result"], "unattempted")

    def test_time_budget_stops_collection(self):
        times = iter((0, 0, 51, 51))
        trace = collect(BOARDS, get, lambda label, raw: label, clock=lambda: next(times))
        self.assertEqual(trace["status"], "budget-exhausted")
        self.assertEqual(trace["requests"], 1)

    def test_off_list_plan_is_error(self):
        trace = self.run_plan((("lever", "unsafe", "https://example.com"),))
        self.assertEqual(trace["status"], "error")
        self.assertEqual(trace["requests"], 0)
