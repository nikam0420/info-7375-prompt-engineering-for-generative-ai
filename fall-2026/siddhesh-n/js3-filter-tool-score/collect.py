"""Collect public job postings from three fixed endpoints."""
import concurrent.futures
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.request import (
    HTTPRedirectHandler, Request, build_opener,
)

BOARDS = {
    "stripe": "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true",
    "airbnb": "https://boards-api.greenhouse.io/v1/boards/airbnb/jobs?content=true",
    "wealthfront": "https://api.lever.co/v0/postings/wealthfront?mode=json",
}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

def content(html):
    from html import unescape
    parser = VisibleText()
    parser.feed(unescape(html or ""))
    return " ".join(" ".join(parser.parts).split())

def collect(board, url):
    opener = build_opener(NoRedirect())
    with opener.open(Request(url, headers={"User-Agent": "INFO7375 course project"}), timeout=30) as result:
        payload = result.read(16_000_001)
    if len(payload) > 16_000_000:
        raise ValueError("Response exceeds collection limit")
    value = json.loads(payload)
    raw = value if board == "wealthfront" else value["jobs"]
    if not isinstance(raw, list) or not raw:
        raise ValueError("Expected a nonempty postings array")
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
    return list(rows.values()), dict(
        returned=len(raw), usable=len(rows), sha256=hashlib.sha256(payload).hexdigest()
    )

def main():
    from datetime import datetime, timezone
    Path("local").mkdir(exist_ok=True)
    Path("evidence").mkdir(exist_ok=True)
    results = []
    report = {"started_utc": datetime.now(timezone.utc).isoformat(), "boards": {}}
    with concurrent.futures.ThreadPoolExecutor() as pool:
        tasks = {board: pool.submit(collect, board, url) for board, url in BOARDS.items()}
        for board, task in tasks.items():
            try:
                rows, stats = task.result()
                results.extend(rows)
                report["boards"][board] = stats
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
                report["boards"][board] = {"error": str(error)}
    report["coverage"] = "complete" if all("usable" in b for b in report["boards"].values()) else "incomplete"
    Path("evidence/collection.json").write_text(json.dumps(report, indent=2) + "\n")
    Path("local/postings.json").write_text(json.dumps(sorted(results, key=lambda row: row["id"])))
    print(json.dumps(report, indent=2))
    return int(not results)

if __name__ == "__main__":
    raise SystemExit(main())
