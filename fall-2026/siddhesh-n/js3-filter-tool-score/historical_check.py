"""Recompute a threshold comparison from the student's locked JS1 held-out labels."""
import argparse
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZipFile

from score import THRESHOLD, score

LOCK = "cdc5d71b070be4ed56696bc1ccf444ea14b7e16a18e78b548b94174eb6549d71"

def check(archive):
    with ZipFile(archive) as submitted:
        labels_path, = (name for name in submitted.namelist()
                        if name.endswith("/eval/hand_labels_heldout.csv"))
        prefix = labels_path.removesuffix("eval/hand_labels_heldout.csv")
        labels = submitted.read(labels_path)
        lock = json.loads(submitted.read(prefix + "eval/label_locks.json"))["heldout"]
        if sha256(labels).hexdigest() != LOCK or lock["sha256"] != LOCK:
            raise ValueError("Historical held-out labels differ from the submitted lock")
        ledger = []
        for row in csv.DictReader(io.StringIO(labels.decode("utf-8"))):
            posting = submitted.read(prefix + row["text_file"]).decode("utf-8")
            _, marker, text = posting.partition("\ncontent:\n")
            if not marker or row["hand_label"] not in {"relevant", "not_relevant"}:
                raise ValueError("Invalid historical posting or label")
            baseline = score(row["title"], text, THRESHOLD)
            variant = score(row["title"], text, THRESHOLD + 1)
            ledger.append({
                "id": "stripe:" + row["posting_id"], "title": row["title"],
                "label": row["hand_label"], "score": baseline["score"],
                "title_match": baseline.get("title_match"),
                "signals": list(baseline.get("mentions", {})),
                "baseline": baseline["decision"], "variant": variant["decision"],
            })
    metrics = {}
    for key in ("baseline", "variant"):
        counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        for row in ledger:
            if row[key] not in {"keep", "reject"}:
                raise ValueError("Historical evaluation requires a score for every row")
            positive = row["label"] == "relevant"
            prediction = row[key] == "keep"
            counts[{(True, True): "tp", (False, True): "fp",
                    (False, False): "tn", (True, False): "fn"}[positive, prediction]] += 1
        metrics[key] = {**counts, "accuracy": (counts["tp"] + counts["tn"]) / len(ledger)}
    return {"scope": "Historical JS1 Stripe heldout labels under the JS1 relevance rule",
            "sha256": LOCK, "locked_at": lock["locked_at"], "metrics": metrics, "rows": ledger}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Submitted JS1 ZIP used as an offline evidence source")
    args = parser.parse_args()
    output = json.dumps(check(args.archive), indent=2) + "\n"
    Path("evidence/js1-heldout.json").write_text(output)
    print(output, end="")
