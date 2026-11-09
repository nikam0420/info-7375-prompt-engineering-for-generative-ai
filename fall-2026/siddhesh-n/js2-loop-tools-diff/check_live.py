"""Recompute observed counts from a saved live trace and raw files."""
import json
from pathlib import Path
import sys

trace_path = Path(sys.argv[1])
trace = json.loads(trace_path.read_bytes())
if trace["mode"] != "live" or trace["status"] != "incomplete" or trace["requests"] != 4:
    sys.exit("Expected a live incomplete run with four requests")

expected = {"stripe", "airbnb", "wealthfront", "deliberate-invalid"}
rows = trace["observations"]
if len(rows) != 4 or {row["board"] for row in rows} != expected:
    sys.exit("Wrong board coverage")
for row in rows:
    payload = json.loads((trace_path.parent / Path(row["raw"]).name).read_bytes())
    if row["board"] == "deliberate-invalid":
        if (row["http"], row["count"], row["result"]) != (404, None, "board-failed"):
            sys.exit("Expected deliberate 404 with unknown count")
        print("deliberate-invalid: HTTP 404, count unknown")
        continue
    jobs = payload["jobs"] if row["provider"] == "greenhouse" else payload
    if not isinstance(jobs, list) or (row["http"], row["count"], row["result"]) != (
        200, len(jobs), "observed"
    ):
        sys.exit(f"Mismatch for {row['board']}")
    print(f"{row['board']}: {len(jobs)} raw listings match reported count")
