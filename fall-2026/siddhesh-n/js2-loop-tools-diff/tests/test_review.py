"""Codex-authored example. The student should add their own independent test."""
import unittest

from agent import BOARDS, collect


class Review(unittest.TestCase):
    def test_missing_greenhouse_jobs_is_incomplete_with_unknown_count(self):
        trace = collect(
            BOARDS[:1],
            lambda *_: (200, b'{"message":"upstream payload incomplete"}'),
            lambda *_: "seed.raw",
        )
        self.assertEqual(trace["status"], "incomplete")
        self.assertIsNone(trace["observations"][0]["count"])

    def test_explicit_empty_greenhouse_jobs_remains_valid(self):
        trace = collect(BOARDS[:1], lambda *_: (200, b'{"jobs":[]}'), lambda *_: "seed.raw")
        self.assertEqual(trace["status"], "finished")
        self.assertEqual(trace["observations"][0]["count"], 0)

    def test_metadata_only_response_is_incomplete(self):
        trace = collect(
            BOARDS[:1],
            lambda *_: (200, b'{"meta":{"total":17}}'),
            lambda *_: "metadata-only.raw",
        )
        observation = trace["observations"][0]
        self.assertEqual(trace["status"], "incomplete")
        self.assertIsNone(observation["count"])
        self.assertEqual(observation["result"], "board-failed")
