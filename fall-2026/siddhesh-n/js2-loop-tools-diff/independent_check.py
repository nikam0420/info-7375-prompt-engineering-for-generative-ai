"""Independent schema oracle. Deliberately imports no agent modules."""
import json
from pathlib import Path
import sys

payload = json.loads(Path(sys.argv[1]).read_bytes())
trace = json.loads(Path(sys.argv[2]).read_bytes())
has_jobs_array = isinstance(payload, dict) and "jobs" in payload and isinstance(payload["jobs"], list)
row = trace["observations"][0]
if not has_jobs_array and (trace["status"] == "finished" or row["count"] is not None):
    print("MISMATCH: raw payload has no jobs array, but agent reported a successful count")
    sys.exit(1)
print("PASS: missing schema did not become a successful count")
