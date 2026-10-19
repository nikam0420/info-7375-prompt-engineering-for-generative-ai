"""Allow-listed HTTPS fetching (CONTRACT.md, "In" and "Refuses").

The only permitted job-board request is
    https://boards-api.greenhouse.io/v1/boards/<board>/jobs?content=true
on port 443. Redirects are refused, no credentials are sent, and environment
proxies are ignored so the request goes straight to the allow-listed host.
"""

from __future__ import annotations

import re
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .util import iso, utc_now

ALLOWED_HOST = "boards-api.greenhouse.io"
BOARD_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,99}")
JOBS_PATH_RE = re.compile(r"/v1/boards/([a-z0-9][a-z0-9_-]{0,99})/jobs")
REQUIRED_QUERY = "content=true"
USER_AGENT = "js1-contract-and-watch/0.1 (public job-board watcher; no login)"
DEFAULT_MAX_BYTES = 64 * 1024 * 1024


class BlockedRequestError(ValueError):
    """A request outside the allow-list was attempted and refused before any network I/O."""


class FetchError(RuntimeError):
    """The network request could not complete (DNS, TLS, timeout, oversize body, ...)."""


def validate_board_token(board) -> str:
    if not isinstance(board, str) or not BOARD_TOKEN_RE.fullmatch(board):
        raise BlockedRequestError(
            f"invalid board name {board!r}: expected lowercase letters, digits, '-' or '_'"
        )
    return board


def build_jobs_url(board: str) -> str:
    validate_board_token(board)
    url = f"https://{ALLOWED_HOST}/v1/boards/{board}/jobs?{REQUIRED_QUERY}"
    validate_url(url)
    return url


def validate_url(url) -> str:
    """Return the board token if url is exactly the allow-listed endpoint, else raise."""
    if not isinstance(url, str):
        raise BlockedRequestError("URL must be a string")
    if any(c.isspace() or c == "\\" or ord(c) < 0x20 or ord(c) > 0x7E for c in url):
        raise BlockedRequestError(f"URL contains disallowed characters: {url!r}")
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise BlockedRequestError(f"scheme must be https: {url!r}")
    if parts.netloc not in (ALLOWED_HOST, f"{ALLOWED_HOST}:443"):
        # Rejects other hosts, look-alike subdomains, userinfo, and non-443 ports.
        raise BlockedRequestError(f"host not in allow-list ({ALLOWED_HOST}:443): {url!r}")
    match = JOBS_PATH_RE.fullmatch(parts.path)
    if not match:
        raise BlockedRequestError(f"path is not the public board jobs endpoint: {url!r}")
    if parts.query != REQUIRED_QUERY:
        raise BlockedRequestError(f"query must be exactly {REQUIRED_QUERY!r}: {url!r}")
    if parts.fragment:
        raise BlockedRequestError(f"fragments are not allowed: {url!r}")
    return match.group(1)


class RefuseRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect. Returning None makes urllib raise HTTPError for the 3xx."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def build_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        RefuseRedirectHandler(),
    )


@dataclass
class FetchResult:
    url: str
    status: int
    reason: str
    headers: list = field(default_factory=list)
    body: bytes = b""
    started_at: str = ""
    finished_at: str = ""
    final_url: str | None = None

    @property
    def redirect_refused(self) -> bool:
        return 300 <= self.status < 400

    def metadata(self) -> dict:
        return {
            "url": self.url,
            "final_url": self.final_url,
            "status": self.status,
            "reason": self.reason,
            "headers": self.headers,
            "request_started_at": self.started_at,
            "response_finished_at": self.finished_at,
            "redirect_refused": self.redirect_refused,
        }


def fetch(url: str, *, opener=None, timeout: float = 30.0, max_bytes: int = DEFAULT_MAX_BYTES) -> FetchResult:
    """GET the allow-listed URL and return the raw response (any HTTP status).

    Raises BlockedRequestError before any I/O if url is not allow-listed, and
    FetchError for transport-level failures.
    """
    validate_url(url)
    opener = opener or build_opener()
    request = urllib.request.Request(
        url, method="GET", headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    started = iso(utc_now())
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as err:
        # Non-2xx responses, including refused redirects, are kept as evidence.
        try:
            body = err.read(max_bytes + 1) or b""
        except Exception:
            body = b""
        return FetchResult(
            url=url,
            status=err.code,
            reason=str(err.reason),
            headers=list(err.headers.items()) if err.headers else [],
            body=body[:max_bytes],
            started_at=started,
            finished_at=iso(utc_now()),
            final_url=None,
        )
    except (urllib.error.URLError, OSError, ValueError) as err:
        raise FetchError(f"request to {url} failed: {err}") from err

    with response:
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise FetchError(f"response from {url} exceeded {max_bytes} bytes")
        result = FetchResult(
            url=url,
            status=response.status,
            reason=str(response.reason),
            headers=list(response.headers.items()),
            body=body,
            started_at=started,
            finished_at=iso(utc_now()),
            final_url=response.geturl(),
        )
    if result.final_url != url:
        raise FetchError(f"final URL {result.final_url!r} differs from requested {url!r}")
    return result
