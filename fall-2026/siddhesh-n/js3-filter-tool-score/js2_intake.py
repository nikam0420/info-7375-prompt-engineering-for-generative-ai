"""Bounded collection loop adapted from the submitted Job-Search Agent 2."""
import subprocess
from time import monotonic
from urllib.parse import urlsplit

from js1_decode import decode_json_bytes

MAX_BOARDS = 4
MAX_REQUESTS = 4
MAX_SECONDS = 50
REQUEST_SECONDS = 12
BOARDS = (
    ("greenhouse", "stripe", "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true"),
    ("greenhouse", "airbnb", "https://boards-api.greenhouse.io/v1/boards/airbnb/jobs?content=true"),
    ("lever", "wealthfront", "https://api.lever.co/v0/postings/wealthfront?mode=json"),
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
