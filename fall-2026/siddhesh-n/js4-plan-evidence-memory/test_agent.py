import tempfile
import unittest
from pathlib import Path

from agent import StaleWrite, check, commit, dump, load_snapshot, propose, read, run, summary_check


class EvidenceTests(unittest.TestCase):
    def test_planted_pay_mismatch(self):
        self.assertFalse(summary_check({"pay": 99}, {"pay": 42})["passed"])

    def test_stale_writer_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "notes.json"
            dump(path, {"version": 0, "postings": {}, "watchers": {}})
            commit(path, 0, {}, "first", {"a": "saved"})
            original = path.read_bytes()
            with self.assertRaises(StaleWrite):
                commit(path, 0, {}, "second", {"b": "would overwrite"})
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(read(path)["watchers"], {"first": {"a": "saved"}})

    def test_lookup_refutes_stale_live_claim(self):
        proposal = {"value": {
            "live": True, "new": False, "title": None, "location": None,
            "authorization": None, "pay": None, "pay_unit": None,
        }}
        results = check("a", proposal, {"direct": {"a": {"status": 404}}}, {"a": {}})
        self.assertFalse(next(row["passed"] for row in results if row["check"] == "live"))

    def test_missing_authorization_remains_unknown(self):
        values = {"title": "Data Engineer", "location": "Remote — US",
                  "authorization": None, "pay": None, "pay_unit": None}
        results = check("b", {"value": dict(values, live=True, new=True)},
                        {"direct": {"b": dict(values, status=200)}}, {})
        self.assertTrue(all(row["passed"] for row in results))

    def test_missing_listing_and_lookup_remain_unknown(self):
        prior = {"a": {}, "P-104": {"value": {"live": True}}}
        snapshot = load_snapshot("day2.json", set(prior))
        snapshot.update(file="day2.json", prior_version=2)
        proposal = propose("P-104", snapshot, prior)
        self.assertIsNone(proposal["value"]["live"])
        self.assertTrue(all(result["passed"] for result in
                            check("P-104", proposal, snapshot, prior)))

    def test_review_gate_blocks_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan = root / "draft.md"
            plan.write_text("Pending. Add the real reviewer")
            with self.assertRaisesRegex(ValueError, "Plan review"):
                run(root / "output", plan)
            self.assertFalse((root / "output").exists())


if __name__ == "__main__":
    unittest.main()
