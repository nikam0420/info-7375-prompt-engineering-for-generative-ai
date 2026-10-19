"""Sampling, label gates, freeze lock, consistency runs, and the seeded demo.

Uses a CONSTRUCTED 24-posting response and fake judges; no network, no Claude.
"""

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import constructed_job, payload_bytes, resume
from watcher import ROOT
from watcher import demo, evaluation as ev
from watcher.judgment import unavailable
from watcher.util import sha256_file

TITLES = ["Data Analyst", "Chef", "Senior Data Analyst", "Welder", "Business Intelligence Analyst", "Nurse"]


def constructed_response(n=24) -> bytes:
    return payload_bytes([constructed_job(500 + i, TITLES[i % len(TITLES)], "SQL" if i % 3 else "none")
                          for i in range(n)])


def fill_labels(eval_dir, split, label="not_relevant"):
    path = ev.labels_path(eval_dir, split)
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["hand_label"] = label
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ev.LABEL_COLUMNS)
        w.writeheader()
        w.writerows(rows)


class FakeJudge:
    """Constructed stand-in for Claude: returns 'relevant' for every posting."""

    def __init__(self):
        self.calls = []

    def __call__(self, posting, purpose, call_label):
        self.calls.append((posting["id"], purpose, call_label))
        return {"kind": "judgment", "status": "available", "posting_id": posting["id"], "verdict": "relevant",
                "resume_fields": ["skills"], "posting_fields": ["title"], "justification": "constructed",
                "raw_record": f"constructed/{len(self.calls)}.json"}


class EvalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.eval_dir = base / "eval"
        self.prompts = base / "prompts"
        shutil.copytree(ROOT / "prompts", self.prompts, ignore=shutil.ignore_patterns("FROZEN.json"))
        self.raw = base / "raw_response.bin"
        self.raw.write_bytes(constructed_response())
        self.sample = ev.select_sample(self.raw, "acme", resume=resume(), seed=7, strategy="title-stratified",
                                       eval_dir=self.eval_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def experiment(self, prompt, split, judge=None):
        return ev.run_experiment(prompt, split, resume=resume(), judge_fn=judge or FakeJudge(),
                                 eval_dir=self.eval_dir, prompts_dir=self.prompts, api_key="constructed")

    def test_sample_is_20_split_10_10_disjoint_and_deterministic(self):
        s = self.sample
        self.assertEqual((len(s["dev"]), len(s["heldout"])), (10, 10))
        self.assertFalse(set(s["dev"]) & set(s["heldout"]))
        other = Path(self.tmp.name) / "eval2"
        s2 = ev.select_sample(self.raw, "acme", resume=resume(), seed=7, strategy="title-stratified", eval_dir=other)
        self.assertEqual((s["dev"], s["heldout"]), (s2["dev"], s2["heldout"]))

    def test_sample_refuses_redraw_and_small_responses(self):
        with self.assertRaises(ev.EvaluationGateError):
            ev.select_sample(self.raw, "acme", resume=resume(), seed=8, strategy="random", eval_dir=self.eval_dir)
        small = Path(self.tmp.name) / "small.bin"
        small.write_bytes(constructed_response(19))
        with self.assertRaises(ev.EvaluationGateError):
            ev.select_sample(small, "acme", resume=resume(), seed=1, strategy="random",
                             eval_dir=Path(self.tmp.name) / "e3")

    def test_label_sheets_are_blank_and_show_no_predictions(self):
        for split in ev.SPLITS:
            text = ev.labels_path(self.eval_dir, split).read_text()
            header = text.splitlines()[0]
            self.assertNotIn("record", header)
            self.assertNotIn("judgment", header)
            self.assertNotIn("not_relevant", text)
            with open(ev.labels_path(self.eval_dir, split), encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertTrue(all(r["hand_label"] == "" for r in rows))
        posting_text = next((self.eval_dir / "postings").glob("*.txt")).read_text()
        self.assertNotIn("relevant", posting_text.lower().replace("irrelevant", ""))

    def test_model_runs_refused_until_labels_complete(self):
        judge = FakeJudge()
        with self.assertRaises(ev.EvaluationGateError):
            self.experiment("baseline", "dev", judge)
        with self.assertRaises(ev.EvaluationGateError):
            ev.run_consistency("baseline", judge_fn=judge, eval_dir=self.eval_dir, api_key="constructed")
        with self.assertRaises(ev.EvaluationGateError):
            ev.assert_not_unlabeled_sample_posting(self.sample["dev"][0], eval_dir=self.eval_dir)
        self.assertEqual(judge.calls, [])

    def test_runs_refused_without_api_key(self):
        fill_labels(self.eval_dir, "dev")
        judge = FakeJudge()
        with self.assertRaises(ev.EvaluationGateError):
            ev.run_experiment("baseline", "dev", resume=resume(), judge_fn=judge, eval_dir=self.eval_dir,
                              prompts_dir=self.prompts, api_key="")
        self.assertEqual(judge.calls, [])

    def test_heldout_locked_until_freeze_then_runs_once(self):
        fill_labels(self.eval_dir, "dev")
        fill_labels(self.eval_dir, "heldout")
        with self.assertRaises(ev.EvaluationGateError):
            self.experiment("baseline", "heldout")
        with self.assertRaises(ev.EvaluationGateError):
            ev.freeze_revision(prompts_dir=self.prompts, eval_dir=self.eval_dir)  # no dev results yet
        self.experiment("baseline", "dev")
        self.experiment("revision", "dev")
        ev.freeze_revision(prompts_dir=self.prompts, eval_dir=self.eval_dir)
        with self.assertRaises(ev.EvaluationGateError):
            ev.freeze_revision(prompts_dir=self.prompts, eval_dir=self.eval_dir)  # exactly one freeze
        r = self.experiment("revision", "heldout")
        self.assertEqual(r["summary"]["n"], 10)
        with self.assertRaises(ev.EvaluationGateError):
            self.experiment("revision", "heldout")

    def test_prompt_edit_after_freeze_blocks_heldout(self):
        fill_labels(self.eval_dir, "dev")
        fill_labels(self.eval_dir, "heldout")
        self.experiment("baseline", "dev")
        self.experiment("revision", "dev")
        ev.freeze_revision(prompts_dir=self.prompts, eval_dir=self.eval_dir)
        p = self.prompts / "judgment_revision.md"
        p.write_text(p.read_text() + "\nextra\n")
        with self.assertRaises(ev.EvaluationGateError):
            self.experiment("revision", "heldout")

    def test_label_edits_after_use_are_refused(self):
        fill_labels(self.eval_dir, "dev")
        self.experiment("baseline", "dev")
        fill_labels(self.eval_dir, "dev", "relevant")
        with self.assertRaises(ev.EvaluationGateError):
            self.experiment("baseline", "dev")

    def test_metrics_come_only_from_returned_judgments(self):
        fill_labels(self.eval_dir, "dev", "relevant")
        dev = self.sample["dev"]

        def half_unavailable(posting, purpose, label):
            if posting["id"] in dev[:4]:
                return unavailable("constructed failure", posting_id=posting["id"])
            return FakeJudge()(posting, purpose, label)
        s = self.experiment("baseline", "dev", half_unavailable)["summary"]
        self.assertEqual((s["n"], s["available"], s["unavailable_or_invalid"], s["agree"]), (10, 6, 4, 6))
        self.assertEqual(s["agreement_over_available"], 1.0)
        self.assertEqual(s["agreement_over_all_counting_unavailable_as_miss"], 0.6)

    def test_consistency_is_5_postings_by_4_fresh_calls(self):
        fill_labels(self.eval_dir, "dev")
        judge = FakeJudge()
        r = ev.run_consistency("baseline", judge_fn=judge, eval_dir=self.eval_dir, api_key="constructed")
        self.assertEqual(len(judge.calls), 20)
        self.assertEqual(len({(pid, lbl) for pid, _, lbl in judge.calls}), 20)
        self.assertEqual([p["posting_id"] for p in r["postings"]], self.sample["dev"][:5])
        self.assertTrue(all(len(p["calls"]) == 4 for p in r["postings"]))
        self.assertFalse(set(pid for pid, *_ in judge.calls) & set(self.sample["heldout"]))

    def test_baseline_and_revision_differ_in_exactly_one_block(self):
        self.assertEqual(len(ev.changed_hunks(ROOT / "prompts")), 1)


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.raw = base / "fetch" / "raw_response.bin"
        self.raw.parent.mkdir()
        self.raw.write_bytes(constructed_response())
        self.demo_root = base / "demo"

    def tearDown(self):
        self.tmp.cleanup()

    def test_prepare_preserves_original_and_labels_snapshot(self):
        before = sha256_file(self.raw)
        m = demo.prepare_demo(self.raw, "acme", withhold=3, seed=11, demo_root=self.demo_root)
        self.assertEqual(sha256_file(self.raw), before)
        self.assertEqual(len(m["withheld_ids"]), 3)
        reduced = json.loads(Path(m["constructed_seeded_baseline"]).read_text())
        self.assertEqual(reduced["_constructed_seeded_baseline"]["label"], "CONSTRUCTED SEEDED BASELINE")
        self.assertIn("did not happen naturally", reduced["_constructed_seeded_baseline"]["statement"])
        self.assertEqual(len(reduced["jobs"]), 21)
        m2 = demo.prepare_demo(self.raw, "acme", withhold=3, seed=11, demo_root=Path(self.tmp.name) / "d2")
        self.assertEqual(m["withheld_ids"], m2["withheld_ids"])

    def test_two_run_demo_reports_withheld_ids_only(self):
        m = demo.prepare_demo(self.raw, "acme", withhold=3, seed=11, demo_root=self.demo_root)
        r = demo.run_demo("acme", resume(), demo_root=self.demo_root)
        self.assertTrue(r["all_checks_passed"], r["checks"])
        self.assertEqual(r["run1"]["new_count"], 0)
        self.assertEqual(sorted(r["run2"]["new_ids"]), m["withheld_ids"])
        for run in ("run1", "run2"):
            d = Path(r[run]["evidence"])
            for name in ("raw_response.bin", "state_before.json", "state_after.json", "report.json", "fetch_meta.json"):
                self.assertTrue((d / name).exists(), f"{run}/{name}")
        run1_meta = json.loads((Path(r["run1"]["evidence"]) / "fetch_meta.json").read_text())
        self.assertIn("CONSTRUCTED SEEDED BASELINE", run1_meta["label"])
        self.assertEqual((Path(r["run2"]["evidence"]) / "raw_response.bin").read_bytes(), self.raw.read_bytes())
        with self.assertRaises(FileExistsError):
            demo.run_demo("acme", resume(), demo_root=self.demo_root)


if __name__ == "__main__":
    unittest.main()
