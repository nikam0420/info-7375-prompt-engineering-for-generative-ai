"""Capture a seeded wrong run before patching count_jobs."""
import json
from pathlib import Path

from agent import BOARDS, collect

seed = Path("evidence/seed-missing-jobs.json")
raw = seed.read_bytes()
trace = collect(BOARDS[:1], lambda url, seconds: (200, raw), lambda *_: str(seed))
trace["mode"] = "seeded-simulation"
print(json.dumps(trace, indent=2))
