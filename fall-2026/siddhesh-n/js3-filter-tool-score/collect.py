"""Extend JS2 intake with full posting text for JS3 scoring."""
from datetime import datetime, timezone
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path

from js1_decode import decode_json_bytes
from js2_intake import BOARDS, collect, fetch

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

def content(html):
    parser = VisibleText()
    parser.feed(unescape(html or ""))
    return " ".join(" ".join(parser.parts).split())

def normalize(provider, board, payload):
    raw = payload["jobs"] if provider == "greenhouse" else payload
    rows = {}
    for item in raw:
        key = item.get("id")
        if key is None:
            raise ValueError("Posting ID missing; board batch excluded")
        if board == "wealthfront":
            location = (item.get("categories") or {}).get("location")
            body = item.get("descriptionBodyPlain") or item.get("descriptionPlain") or ""
            sections = [content(section.get("content")) for section in item.get("lists", [])]
            body = " ".join([body, *sections, item.get("additionalPlain") or ""]).strip()
            title = item.get("text")
            link = item.get("hostedUrl")
        else:
            location = (item.get("location") or {}).get("name")
            body = content(item.get("content"))
            title = item.get("title")
            link = item.get("absolute_url")
        rows[str(key)] = dict(id=f"{board}:{key}", title=title, text=body,
                              url=link, location=location)
    return list(rows.values())


def main():
    Path("local").mkdir(exist_ok=True)
    Path("evidence").mkdir(exist_ok=True)
    captured = {}

    def capture(board, payload):
        captured[board] = payload
        return hashlib.sha256(payload).hexdigest()

    started = datetime.now(timezone.utc).isoformat()
    trace = collect(BOARDS, fetch, capture)
    results = []
    boards = {}
    for row in trace["observations"]:
        board = row["board"]
        if row["result"] != "observed":
            boards[board] = {"error": row.get("detail", row["result"])}
            continue
        try:
            normalized = normalize(row["provider"], board, decode_json_bytes(captured[board]))
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            boards[board] = {"error": str(error)}
            continue
        results.extend(normalized)
        boards[board] = {"returned": row["count"], "usable": len(normalized), "sha256": row["raw"]}
    report = {
        "started_utc": started, "boards": boards, "js2_status": trace["status"],
        "requests": trace["requests"], "elapsed_seconds": trace["elapsed_seconds"],
        "coverage": "complete" if trace["status"] == "finished" and
        all("usable" in boards.get(board, {}) for _, board, _ in BOARDS) else "incomplete",
    }
    Path("evidence/collection.json").write_text(json.dumps(report, indent=2) + "\n")
    Path("local/postings.json").write_text(json.dumps(sorted(results, key=lambda row: row["id"])))
    print(json.dumps(report, indent=2))
    return int(not results)

if __name__ == "__main__":
    raise SystemExit(main())
