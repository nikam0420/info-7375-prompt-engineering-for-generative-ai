"""One bounded pass over an explicit public ATS plan."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic
from urllib.parse import urlsplit

from js1_decode import decode_json_bytes

MAX_BOARDS = 4
MAX_REQUESTS = 4
MAX_SECONDS = 50
REQUEST_SECONDS = 12
BOARDS = (
    ("greenhouse", "stripe", "https://boards-api.greenhouse.io/v1/boards/stripe/jobs"),
    ("greenhouse", "airbnb", "https://boards-api.greenhouse.io/v1/boards/airbnb/jobs"),
    ("lever", "wealthfront", "https://api.lever.co/v0/postings/wealthfront?mode=json"),
    ("greenhouse", "deliberate-invalid",
     "https://boards-api.greenhouse.io/v1/boards/js2-deliberately-nonexistent-9c9bf5/jobs"),
)
HOSTS = {"boards-api.greenhouse.io", "api.lever.co"}
URLS = {board[2] for board in BOARDS}
EXIT = {"finished": 0, "incomplete": 2, "budget-exhausted": 3, "error": 4}


class PolicyError(ValueError):
    pass


def require_request(method, url):
    parsed = urlsplit(url)
    if (method != "GET" or parsed.scheme != "https"
            or parsed.netloc not in HOSTS or url not in URLS):
        raise PolicyError("request outside read-only allow-list")


def persist(root, relative, data, *, approved=False):
    path = Path(relative)
    if path.parts != ("jobs", path.name) or not re.fullmatch(
        r"[a-zA-Z0-9][a-zA-Z0-9._-]*", path.name
    ):
        raise PolicyError("destination must be a direct child of jobs")
    if path.suffix == ".raw" and not approved:
        raise PolicyError("raw write requires operator approval")
    directory = os.open(root / "jobs", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        file = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                       0o600, dir_fd=directory)
        with os.fdopen(file, "wb") as output:
            output.write(data)
    finally:
        os.close(directory)


def fetch(url, seconds):
    require_request("GET", url)
    result = subprocess.run(
        ["curl", "-q", "--silent", "--show-error",
         "--proto", "=https", "--max-time", str(seconds),
         "--max-filesize", "8000000", "--write-out", "\n%{http_code}", url],
        capture_output=True, timeout=seconds, check=True,
    )
    body, _, status = result.stdout.rpartition(b"\n")
    return int(status), body


def count_jobs(provider, body):
    payload = decode_json_bytes(body)
    if provider == "greenhouse":
        # A missing jobs field is an unknown count, not an empty board.
        rows = payload.get("jobs") if isinstance(payload, dict) else None
    else:
        rows = payload
    if not isinstance(rows, list) or any(
        not isinstance(row, dict) or not row.get("id") for row in rows
    ):
        raise ValueError("invalid listing schema")
    return len(rows)


def collect(plan, get, save, *, clock=monotonic):
    started = clock()
    seen = set()
    observations = []
    requests = 0
    status = "finished"
    for index, (provider, label, url) in enumerate(plan):
        row = {"board": label, "provider": provider, "url": url, "count": None}
        observations.append(row)
        if url in seen:
            row["result"] = "repeat-skipped"
            continue
        remaining = MAX_SECONDS - (clock() - started)
        if len(seen) >= MAX_BOARDS or requests >= MAX_REQUESTS or remaining <= 0:
            row["result"] = "budget-blocked"
            status = "budget-exhausted"
        else:
            try:
                require_request("GET", url)
                seen.add(url)
                requests += 1
                http, raw = get(url, min(REQUEST_SECONDS, remaining))
                row["http"] = http
                row["raw"] = save(label, raw)
                if http != 200:
                    raise ValueError(f"HTTP {http}")
                row["count"] = count_jobs(provider, raw)
                row["result"] = "observed"
            except PolicyError as exc:
                row.update(result="policy-error", detail=str(exc))
                status = "error"
            except (subprocess.SubprocessError, ValueError) as exc:
                row.update(result="board-failed", detail=str(exc))
                status = "incomplete"
            except OSError as exc:
                row.update(result="local-error", detail=str(exc))
                status = "error"
            if status != "error" and clock() - started >= MAX_SECONDS:
                status = "budget-exhausted"
        if status in {"error", "budget-exhausted"}:
            for provider, label, url in plan[index + 1:]:
                observations.append({"board": label, "provider": provider, "url": url,
                                     "count": None, "result": "unattempted"})
            break
    return {"status": status, "requests": requests,
            "elapsed_seconds": round(clock() - started, 3), "observations": observations}


def main():
    from datetime import datetime, timezone

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--approve-raw", action="store_true", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", args.tag):
        parser.error("tag must be a simple filename prefix")
    root = Path.cwd()

    def save(label, raw):
        destination = f"jobs/{args.tag}-{label}.raw"
        persist(root, destination, raw, approved=args.approve_raw)
        return destination

    trace = collect(BOARDS, fetch, save)
    trace.update(mode="live", recorded_at=datetime.now(timezone.utc).isoformat())
    trace_bytes = (json.dumps(trace, indent=2) + "\n").encode()
    try:
        persist(root, f"jobs/{args.tag}-trace.json", trace_bytes)
    except (OSError, PolicyError) as exc:
        trace.update(status="error", persistence_error=str(exc))
    print(json.dumps(trace, indent=2))
    return EXIT[trace["status"]]


if __name__ == "__main__":
    sys.exit(main())
