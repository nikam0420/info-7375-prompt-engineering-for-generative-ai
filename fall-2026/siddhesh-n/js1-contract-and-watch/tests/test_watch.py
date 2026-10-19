"""Watch runs: baseline, repeats, new IDs, failures, and ID-to-verdict association.

All responses are CONSTRUCTED fixtures served by a fake fetcher; no network.
"""

import json
import random
import tempfile
import unittest
from pathlib import Path

from helpers import FakeFetcher, constructed_job, fixture_payload, ok, resume
from watcher.judgment import unavailable
from watcher.netguard import BlockedRequestError, FetchError
from watcher.state import StateError, load_state
from watcher.watch import run_watch

BASE = [constructed_job(1, "Data Analyst", "SQL"), constructed_job(2, "Chef", "SQL"),
        constructed_job(3, "BI Engineer", "none")]


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "state"
        self.evidence = Path(self.tmp.name) / "evidence"

    def tearDown(self):
        self.tmp.cleanup()

    def run_once(self, fetcher, board="acme", judge=None, r=None):
        return run_watch(board, r or resume(), state_dir=self.state, evidence_dir=self.evidence,
                         fetcher=fetcher, judge=judge)

    def seen(self, board="acme"):
        s = load_state(self.state, board)
        return None if s is None else s["seen_ids"]

    # ---- baseline and repeats

    def test_first_run_is_baseline_with_zero_new(self):
        rep = self.run_once(FakeFetcher(ok(BASE)))
        self.assertEqual(rep["status"], "baseline_saved")
        self.assertEqual(rep["new_count"], 0)
        self.assertEqual(rep["new_postings"], [])
        self.assertEqual(self.seen(), [1, 2, 3])

    def test_repeat_run_reports_nothing_new(self):
        f = FakeFetcher(ok(BASE), ok(BASE), ok(list(reversed(BASE))))
        self.run_once(f)
        self.assertEqual(self.run_once(f)["new_count"], 0)
        self.assertEqual(self.run_once(f)["new_count"], 0)
        self.assertEqual(self.seen(), [1, 2, 3])

    def test_only_unseen_ids_reported(self):
        f = FakeFetcher(ok(BASE), ok(BASE + [constructed_job(9, "Data Analyst", "SQL")]),
                        ok(BASE + [constructed_job(9), constructed_job(10, "Nurse")]))
        self.run_once(f)
        rep2 = self.run_once(f)
        self.assertEqual([e["posting_id"] for e in rep2["new_postings"]], [9])
        rep3 = self.run_once(f)
        self.assertEqual([e["posting_id"] for e in rep3["new_postings"]], [10])

    def test_state_keeps_union_so_reappearing_ids_are_not_new(self):
        f = FakeFetcher(ok(BASE), ok(BASE[:1]), ok(BASE))
        self.run_once(f)
        self.assertEqual(self.run_once(f)["new_count"], 0)
        self.assertEqual(self.seen(), [1, 2, 3], "IDs absent from the current response stay seen")
        self.assertEqual(self.run_once(f)["new_count"], 0)

    def test_state_is_per_board(self):
        self.run_once(FakeFetcher(ok(BASE)), board="acme")
        rep = self.run_once(FakeFetcher(ok(BASE + [constructed_job(4)])), board="other-co")
        self.assertEqual(rep["status"], "baseline_saved")
        self.assertEqual(rep["new_count"], 0)
        self.assertEqual(self.seen("acme"), [1, 2, 3])
        self.assertEqual(self.seen("other-co"), [1, 2, 3, 4])

    # ---- new posting output

    def test_new_posting_carries_id_title_url_record_and_separate_judgment(self):
        f = FakeFetcher(ok(BASE), ok(BASE + [constructed_job(9, "Senior Data Analyst", "&lt;p&gt;SQL&lt;/p&gt;")]))
        self.run_once(f)
        [e] = self.run_once(f)["new_postings"]
        self.assertEqual((e["posting_id"], e["title"], e["url"]), (9, "Senior Data Analyst", "https://jobs.example.com/9"))
        self.assertEqual(e["record"]["kind"], "record")
        self.assertEqual(e["record"]["verdict"], "relevant")
        self.assertEqual(e["judgment"]["kind"], "judgment")
        self.assertEqual(e["judgment"]["status"], "unavailable")
        self.assertNotIn("verdict", e["judgment"], "a missing judgment must never borrow the record's verdict")

    def test_verdicts_stay_attached_to_ids_when_order_changes(self):
        """Contract wrong implementation #1."""
        new_jobs = [constructed_job(100 + i, title, "SQL" if sql else "none")
                    for i, (title, sql) in enumerate([("Data Analyst", True), ("Chef", True), ("Data Analyst", False),
                                                      ("Business Intelligence Analyst", True), ("Welder", False)])]
        expected = {100: "relevant", 101: "not_relevant", 102: "not_relevant", 103: "relevant", 104: "not_relevant"}
        for seed in range(5):
            with self.subTest(seed=seed):
                shuffled = new_jobs[:]
                random.Random(seed).shuffle(shuffled)
                with tempfile.TemporaryDirectory() as d:
                    f = FakeFetcher(ok(BASE), ok(list(reversed(BASE)) + shuffled))
                    run_watch("acme", resume(), state_dir=Path(d), evidence_dir=Path(d) / "e", fetcher=f)
                    rep = run_watch("acme", resume(), state_dir=Path(d), evidence_dir=Path(d) / "e", fetcher=f)
                got = {e["posting_id"]: e["record"]["verdict"] for e in rep["new_postings"]}
                self.assertEqual(got, expected)
                for e in rep["new_postings"]:
                    self.assertEqual(e["record"]["posting_id"], e["posting_id"])
                    title = next(j["title"] for j in new_jobs if j["id"] == e["posting_id"])
                    self.assertEqual(e["title"], title)
                    self.assertIn(json.dumps(title), e["record"]["justification"])

    def test_judgment_for_a_different_id_is_rejected(self):
        def crossed_judge(posting):
            return {"kind": "judgment", "status": "available", "posting_id": posting["id"] + 1,
                    "verdict": "relevant", "resume_fields": ["skills"], "posting_fields": ["title"],
                    "justification": "constructed"}
        f = FakeFetcher(ok(BASE), ok(BASE + [constructed_job(9)]))
        self.run_once(f)
        [e] = self.run_once(f, judge=crossed_judge)["new_postings"]
        self.assertEqual(e["judgment"]["status"], "unavailable")
        self.assertNotIn("verdict", e["judgment"])

    def test_judge_exception_is_unavailable_not_fatal(self):
        def broken(posting):
            raise RuntimeError("constructed outage")
        f = FakeFetcher(ok(BASE), ok(BASE + [constructed_job(9)]))
        self.run_once(f)
        rep = self.run_once(f, judge=broken)
        self.assertEqual(rep["new_postings"][0]["judgment"]["status"], "unavailable")
        self.assertEqual(self.seen(), [1, 2, 3, 9])

    def test_unavailable_judge_passthrough(self):
        f = FakeFetcher(ok(BASE), ok(BASE + [constructed_job(9)]))
        self.run_once(f)
        rep = self.run_once(f, judge=lambda p: unavailable("constructed: no key", posting_id=p["id"]))
        self.assertIn("no key", rep["new_postings"][0]["judgment"]["reason"])

    # ---- failures never update state

    def assert_failed_without_state_change(self, response, expected_status):
        self.run_once(FakeFetcher(ok(BASE)))
        before = (self.state / "acme.json").read_bytes()
        rep = self.run_once(FakeFetcher(response))
        self.assertEqual(rep["status"], expected_status)
        self.assertFalse(rep["state_updated"])
        self.assertEqual((self.state / "acme.json").read_bytes(), before)
        return rep

    def test_failed_fetch_http_error(self):
        rep = self.assert_failed_without_state_change((503, b"constructed outage"), "fetch_failed")
        self.assertEqual((Path(rep["evidence_dir"]) / "raw_response.bin").read_bytes(), b"constructed outage")

    def test_failed_fetch_redirect(self):
        rep = self.assert_failed_without_state_change((302, b""), "fetch_failed")
        self.assertEqual(rep["error"], "redirect refused")

    def test_failed_fetch_transport_error(self):
        self.assert_failed_without_state_change(FetchError("constructed timeout"), "fetch_failed")

    def test_malformed_json(self):
        self.assert_failed_without_state_change((200, b'{"jobs": [ '), "input_validation_failed")

    def test_one_malformed_posting_invalidates_whole_response(self):
        bad = constructed_job(50)
        del bad["title"]
        self.assert_failed_without_state_change(ok(BASE + [constructed_job(9), bad]), "input_validation_failed")
        self.assertEqual(self.run_once(FakeFetcher(ok(BASE + [constructed_job(9)])))["new_count"], 1,
                         "posting 9 from the rejected response must still count as new later")

    def test_failure_on_first_run_does_not_create_baseline(self):
        rep = self.run_once(FakeFetcher((500, b"x")))
        self.assertEqual(rep["status"], "fetch_failed")
        self.assertIsNone(self.seen())
        rep = self.run_once(FakeFetcher(ok(BASE)))
        self.assertEqual(rep["status"], "baseline_saved")

    def test_corrupt_state_is_an_error_not_a_new_baseline(self):
        self.state.mkdir(parents=True)
        (self.state / "acme.json").write_text("{not json")
        f = FakeFetcher(ok(BASE))
        with self.assertRaises(StateError):
            self.run_once(f)
        self.assertEqual(f.urls, [])

    def test_blocked_board_never_fetches(self):
        f = FakeFetcher(ok(BASE))
        for board in ("evil.com", "acme/../x", "ACME", ""):
            with self.subTest(board=board), self.assertRaises(BlockedRequestError):
                self.run_once(f, board=board)
        self.assertEqual(f.urls, [])

    def test_requested_url_is_allow_listed_endpoint(self):
        f = FakeFetcher(ok(BASE))
        self.run_once(f)
        self.assertEqual(f.urls, ["https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true"])

    # ---- evidence

    def test_raw_bytes_and_state_snapshots_saved(self):
        body = json.dumps(fixture_payload(), indent=3).encode()
        rep = self.run_once(FakeFetcher((200, body)))
        d = Path(rep["evidence_dir"])
        self.assertEqual((d / "raw_response.bin").read_bytes(), body)
        self.assertFalse(json.loads((d / "state_before.json").read_text())["exists"])
        self.assertEqual(json.loads((d / "state_after.json").read_text())["state"]["seen_ids"], [1001, 1002, 1003, 1004])
        self.assertEqual(json.loads((d / "report.json").read_text())["status"], "baseline_saved")

    def test_posting_instructions_are_not_executed(self):
        payload = fixture_payload()
        base = [j for j in payload["jobs"] if j["id"] != 1004]
        f = FakeFetcher(ok(base), ok(payload["jobs"]))
        self.run_once(f)
        [e] = self.run_once(f)["new_postings"]
        self.assertEqual(e["posting_id"], 1004)
        self.assertEqual(e["record"]["verdict"], "relevant")  # by the rule: title + "sql" word + skill
        self.assertEqual(f.urls[-1], "https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true")

    def test_invalid_resume_refused_before_fetch(self):
        f = FakeFetcher(ok(BASE))
        with self.assertRaises(Exception):
            self.run_once(f, r=resume(fictional=False))
        self.assertEqual(f.urls, [])


if __name__ == "__main__":
    unittest.main()
