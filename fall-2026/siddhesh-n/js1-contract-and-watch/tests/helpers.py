"""Builders for CONSTRUCTED TEST FIXTURES. Nothing here is real Greenhouse data."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from watcher.netguard import FetchResult

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CONSTRUCTED_NOTE = "CONSTRUCTED TEST FIXTURE - not real Greenhouse data."


def fixture_payload() -> dict:
    return json.loads((FIXTURES / "constructed_board_response.json").read_text(encoding="utf-8"))


def constructed_job(job_id: int, title: str = "Data Analyst", content: str = "&lt;p&gt;SQL&lt;/p&gt;") -> dict:
    return {
        "id": job_id,
        "title": title,
        "absolute_url": f"https://jobs.example.com/{job_id}",
        "location": {"name": "Remote"},
        "updated_at": "2026-10-01T00:00:00-04:00",
        "content": content,
    }


def payload_bytes(jobs: list[dict]) -> bytes:
    return json.dumps({"_constructed_test_fixture": CONSTRUCTED_NOTE, "jobs": jobs}).encode("utf-8")


def resume(**overrides) -> dict:
    base = {
        "fictional": True,
        "name": "Test Person (constructed)",
        "email": "test.person@example.com",
        "phone": "202-555-0147",
        "target_titles": ["data analyst", "business intelligence analyst"],
        "skills": ["SQL", "Python"],
    }
    base.update(overrides)
    return base


class FakeFetcher:
    """Returns queued constructed responses; records every URL requested."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.urls: list[str] = []

    def __call__(self, url):
        self.urls.append(url)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        status, body = item
        return FetchResult(url=url, status=status, reason="constructed", headers=[("X-Fixture", "constructed")],
                           body=body, started_at="t0", finished_at="t1", final_url=url)


def ok(jobs) -> tuple[int, bytes]:
    return 200, payload_bytes(copy.deepcopy(jobs))
