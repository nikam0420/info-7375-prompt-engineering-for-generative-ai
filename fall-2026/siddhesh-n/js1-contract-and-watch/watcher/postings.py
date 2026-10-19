"""Parse and validate a complete Greenhouse jobs response.

Posting text is untrusted data. Nothing here interprets it as instructions; it
is only converted to plain text and checked for types.
"""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

# Required posting fields and their types. Missing or wrongly typed fields are
# input-validation errors, never relevance verdicts.
REQUIRED_FIELDS = {"id": int, "title": str, "absolute_url": str, "content": str}


class PostingValidationError(ValueError):
    """The response or a posting in it is malformed."""


_BLOCK_TAGS = {
    "p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
    "tr", "td", "th", "table", "section", "article", "header", "footer", "hr",
    "blockquote", "pre",
}
_SKIP_TAGS = {"script", "style"}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip:
            self._skip -= 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(content: str) -> str:
    """Convert posting HTML to plain text with HTML entities decoded.

    Greenhouse returns `content` as entity-escaped HTML (``&lt;p&gt;...``), so
    when the string has no literal tags but does have escaped ones it is
    unescaped once before tag stripping.
    """
    if "<" not in content and re.search(r"&lt;\s*/?\s*[a-zA-Z]", content):
        content = html.unescape(content)
    parser = _TextExtractor()
    parser.feed(content)
    parser.close()
    text = "".join(parser.parts).replace("\xa0", " ")
    lines = [re.sub(r"[ \t\r\f\v]+", " ", line).strip() for line in text.split("\n")]
    out, blank = [], False
    for line in lines:
        if line:
            out.append(line)
            blank = False
        elif not blank and out:
            out.append("")
            blank = True
    return "\n".join(out).strip()


def decode_json_bytes(raw: bytes):
    if not isinstance(raw, (bytes, bytearray)):
        raise PostingValidationError("response body must be bytes")
    try:
        text = bytes(raw).decode("utf-8")
    except UnicodeDecodeError as err:
        raise PostingValidationError(f"response is not valid UTF-8: {err}") from err
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise PostingValidationError(f"response is not valid JSON: {err}") from err


def validate_job(job, index: int) -> None:
    where = f"jobs[{index}]"
    if not isinstance(job, dict):
        raise PostingValidationError(f"{where} must be an object")
    for name, typ in REQUIRED_FIELDS.items():
        if name not in job:
            raise PostingValidationError(f"{where} is missing required field {name!r}")
        value = job[name]
        if typ is int:
            ok = isinstance(value, int) and not isinstance(value, bool)
        else:
            ok = isinstance(value, typ)
        if not ok:
            raise PostingValidationError(
                f"{where}.{name} must be {typ.__name__}, got {type(value).__name__}"
            )
    if job["id"] <= 0:
        raise PostingValidationError(f"{where}.id must be a positive integer")
    if not job["title"].strip():
        raise PostingValidationError(f"{where}.title must be nonempty")
    url = urlsplit(job["absolute_url"])
    if url.scheme not in ("http", "https") or not url.netloc:
        raise PostingValidationError(f"{where}.absolute_url must be an http(s) URL")


def normalize_job(job: dict) -> dict:
    location = job.get("location")
    location_name = location.get("name") if isinstance(location, dict) else None
    updated_at = job.get("updated_at")
    return {
        "id": job["id"],
        "title": job["title"],
        "location": location_name if isinstance(location_name, str) else None,
        "absolute_url": job["absolute_url"],
        "updated_at": updated_at if isinstance(updated_at, str) else None,
        "content": html_to_text(job["content"]),
    }


def parse_response(raw: bytes) -> list[dict]:
    """Validate the complete response, then return normalized postings in response order.

    Any malformed posting invalidates the whole response.
    """
    data = decode_json_bytes(raw)
    if not isinstance(data, dict):
        raise PostingValidationError("response must be a JSON object")
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        raise PostingValidationError("response must contain a 'jobs' list")
    seen: set[int] = set()
    for i, job in enumerate(jobs):
        validate_job(job, i)
        if job["id"] in seen:
            raise PostingValidationError(f"duplicate posting id {job['id']}")
        seen.add(job["id"])
    return [normalize_job(job) for job in jobs]
