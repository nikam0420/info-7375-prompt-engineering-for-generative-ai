"""Exercise the real server over stdio with a seeded fictional posting."""
import json
from pathlib import Path
import subprocess
import sys

from tool_server import VERSION

REQUESTS = [
    {"id": 1, "method": "initialize", "params": {"protocolVersion": VERSION,
     "capabilities": {}, "clientInfo": {"name": "js3-demo", "version": "1.0"}}},
    {"method": "notifications/initialized"},
    {"id": 2, "method": "tools/list"},
    {"id": 3, "method": "tools/call", "params": {"name": "score_posting",
     "arguments": {"title": "Data Analyst", "text": "Use SQL to build dashboards."}}},
    {"id": 4, "method": "tools/call", "params": {"name": "score_posting",
     "arguments": {"title": "Data Analyst", "text": ""}}},
    {"id": 5, "method": "tools/call", "params": {"name": "score_posting",
     "arguments": {"title": "Data Analyst", "text": "SQL", "url": "https://example.org"}}},
    {"id": 6, "method": "tools/call", "params": {"name": "apply", "arguments": {}}},
]

def main():
    wire_file = Path("local/demo-wire.jsonl")
    wire_file.unlink(missing_ok=True)
    messages = "".join(json.dumps({"jsonrpc": "2.0", **row}) + "\n" for row in REQUESTS)
    run = subprocess.run([sys.executable, "tool_server.py", "--record", "demo"],
                         input=messages, text=True, capture_output=True,
                         check=True, timeout=10)
    replies = {row["id"]: row for row in map(json.loads, run.stdout.splitlines())}
    assert list(replies) == [1, 2, 3, 4, 5, 6]
    assert replies[2]["result"]["tools"][0]["name"] == "score_posting"
    assert json.loads(replies[3]["result"]["content"][0]["text"])["score"] == 5
    assert json.loads(replies[4]["result"]["content"][0]["text"])["decision"] == "unknown"
    assert replies[5]["result"]["isError"]
    assert replies[6]["error"]["code"] == -32602
    Path("evidence/demo-wire.jsonl").write_bytes(wire_file.read_bytes())
    print("Verified 6 replies and recorded both directions in evidence/demo-wire.jsonl")

if __name__ == "__main__":
    main()
