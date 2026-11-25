"""Run filter, sample audit rows, and compare two thresholds on human labels."""
import argparse
import csv
from html import escape
import json
from pathlib import Path
import random

from score import THRESHOLD, score

SEED = 7375
EVIDENCE = Path("evidence")
LOCAL = Path("local")

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

def review_html(samples):
    cards = []
    for group, row in samples:
        link = row.get("url") or ""
        heading = escape(f"{row['title']} — {row['id']}")
        if link.startswith("https://"):
            heading = f'<a href="{escape(link)}" target="_blank" rel="noopener">{heading}</a>'
        key = escape(row["id"])
        cards.append(f"""
<article data-id="{key}" data-group="{group}">
<h2>{heading}</h2><p>{escape(str(row.get('location') or 'Unknown location'))}</p>
<p>{escape(row['text'])}</p>
<label>Relevant to Morgan? <select><option value="">Pending</option>
<option value="relevant">Relevant</option><option value="irrelevant">Irrelevant</option>
<option value="uncertain">Uncertain</option></select></label>
<label>Reason <input size="55" placeholder="Add a brief reason"></label>
</article>""")
    return """<!doctype html><meta charset="utf-8">
<title>JS3 posting review</title>
<style>body{font:16px system-ui;max-width:1000px;margin:25px auto;padding:0 16px}
article{border-top:1px solid #ccc;padding:10px 0 20px}
p{max-height:160px;overflow:auto}header{position:sticky;top:0;background:white;padding:8px}
button{font:inherit}</style>
<header><h1>Posting review</h1>
<p>Judge whether the duties materially involve data analytics, BI, analytics engineering, or data engineering. Use Uncertain for ambiguous evidence.</p>
<button id="download">Download judgments</button></header>
""" + "\n".join(cards) + """
<script>
const cards = [...document.querySelectorAll('article')];
for (const card of cards) {
  const fields = [...card.querySelectorAll('select,input')];
  const key = 'js3-' + card.dataset.id;
  try {
    const saved = JSON.parse(localStorage.getItem(key) || '[]');
    fields.forEach((field, index) => field.value = saved[index] || '');
    card.addEventListener('change', () => {
      localStorage.setItem(key, JSON.stringify(fields.map(field => field.value)));
    });
  } catch {}
}
document.getElementById('download').onclick = () => {
  const rows = cards.map(card => ({
    id: card.dataset.id, group: card.dataset.group,
    verdict: card.querySelector('select').value,
    reason: card.querySelector('input').value.trim()
  }));
  const url = URL.createObjectURL(new Blob([JSON.stringify(rows, null, 2)],
                                         {type:'application/json'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'human-labels.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
</script>"""

def run():
    rows = json.loads((LOCAL / "postings.json").read_text())
    scored = [(row, score(row["title"], row["text"])) for row in rows]
    ranked = sorted((item for item in scored if item[1]["score"] is not None),
                    key=lambda item: (-item[1]["score"], item[0]["id"]))
    keep = [item for item in ranked if item[1]["decision"] == "keep"]
    reject = [item for item in ranked if item[1]["decision"] == "reject"]
    rng = random.Random(SEED)
    random_reject = rng.sample(reject, min(30, len(reject)))
    used = {item[0]["id"] for item in random_reject}
    near_reject = [item for item in reject if item[0]["id"] not in used][:5]
    boundary = [item for item in keep if item[1]["score"] == THRESHOLD][:2]
    boundary_ids = {item[0]["id"] for item in boundary}
    near_keep = sorted((item for item in keep if item[0]["id"] not in boundary_ids), key=lambda item: (item[1]["score"], item[0]["id"]))[:5]
    used.update(item[0]["id"] for item in near_keep + near_reject)
    remaining = [item for item in keep if item[0]["id"] not in used | boundary_ids]
    random_keep = rng.sample(remaining, min(5, len(remaining)))
    used.update(item[0]["id"] for item in random_keep)
    pool_keep = [item for item in keep if item[0]["id"] not in used | boundary_ids]
    pool_reject = [item for item in reject if item[0]["id"] not in used]
    holdout = boundary + rng.sample(pool_keep, min(12 - len(boundary), len(pool_keep)))
    holdout += rng.sample(pool_reject, min(12, len(pool_reject)))
    groups = {"random_reject": random_reject, "near_reject": near_reject,
              "near_keep": near_keep, "random_keep": random_keep, "heldout": holdout}
    samples = [(group, row) for group, items in groups.items() for row, result in items]
    rng.shuffle(samples)
    (LOCAL / "review.html").write_text(review_html(samples))
    write_json(EVIDENCE / "sample.json", [
        {"id": row["id"], "group": group, "title": row["title"], "url": row["url"]}
        for group, row in samples
    ])
    write_json(EVIDENCE / "shortlist.json", [
        {"id": row["id"], "url": row["url"], "title": row["title"], "score": result["score"],
         "claims": [{"claim": f"Posting mentions {name}", "label": "supported",
                     "excerpt": excerpt} for name, excerpt in result["mentions"].items()]}
        for row, result in keep[:5]
    ])
    with (EVIDENCE / "scores.csv").open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["id", "title", "decision", "score", "title_match", "signals"])
        for row, result in scored:
            writer.writerow([row["id"], row["title"], result["decision"], result["score"],
                             result.get("title_match"), "|".join(result.get("mentions", {}))])
    summary = {"total": len(scored), "kept": len(keep), "rejected": len(reject),
               "unknown": len(scored) - len(ranked), "seed": SEED,
               "sample_counts": {group: len(items) for group, items in groups.items()},
               "heldout_threshold_flips": sum(result["score"] == THRESHOLD for _, result in holdout)}
    write_json(EVIDENCE / "run-summary.json", summary)
    print(json.dumps(summary, indent=2))

def compare(label_path):
    labels = json.loads(Path(label_path).read_text())
    manifest = json.loads((EVIDENCE / "sample.json").read_text())
    groups = {row["id"]: row["group"] for row in manifest}
    ids = [row["id"] for row in labels]
    if len(ids) != len(set(ids)) or not set(ids) <= groups.keys():
        raise ValueError("Labels must contain unique IDs from the recorded sample")
    allowed = {"relevant", "irrelevant", "uncertain", ""}
    if any(row["verdict"] not in allowed or row["verdict"] and not row["reason"].strip()
           for row in labels):
        raise ValueError("Use a documented verdict and provide a reason for each judgment")
    with (EVIDENCE / "scores.csv").open(newline="") as file:
        scores = {row["id"]: int(row["score"]) for row in csv.DictReader(file) if row["score"]}
    judgments = {row["id"]: row for row in labels if row["verdict"]}
    counts = {}
    for key, group in groups.items():
        group_counts = counts.setdefault(group, {"pending": 0, "uncertain": 0, "correct": 0, "wrong": 0})
        verdict = judgments.get(key, {}).get("verdict")
        if verdict is None:
            group_counts["pending"] += 1
        elif verdict == "uncertain":
            group_counts["uncertain"] += 1
        else:
            correct = (scores[key] >= THRESHOLD) == (verdict == "relevant")
            group_counts["correct" if correct else "wrong"] += 1
    heldout = [(scores[key], row["verdict"] == "relevant") for key, row in judgments.items()
               if groups[key] == "heldout" and row["verdict"] != "uncertain"]
    comparison = {}
    for threshold in (THRESHOLD, THRESHOLD + 1):
        matrix = dict(tp=0, fp=0, tn=0, fn=0)
        for points, actual in heldout:
            predicted = points >= threshold
            label = {(True, True): "tp", (True, False): "fp",
                     (False, True): "fn", (False, False): "tn"}[predicted, actual]
            matrix[label] += 1
        comparison[threshold] = {"confusion": matrix, "n": len(heldout),
                                 "accuracy": (matrix["tp"] + matrix["tn"]) / len(heldout) if heldout else None}
    write_json(EVIDENCE / "human-labels.json", [
        {**row, "group": groups[key]} for key, row in judgments.items()
    ])
    write_json(EVIDENCE / "comparison.json", {"audit": counts, "heldout": comparison})
    print(json.dumps({"audit": counts, "heldout": comparison}, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", help="Compare frozen scores with independently entered human labels")
    args = parser.parse_args()
    compare(args.labels) if args.labels else run()
