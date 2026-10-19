"""Résumé checks and the host/path allow-list. Uses CONSTRUCTED inputs only; no network."""

import io
import unittest
import urllib.error
import urllib.request
from email.message import Message

from helpers import resume
from watcher.netguard import (
    BlockedRequestError,
    FetchError,
    RefuseRedirectHandler,
    build_jobs_url,
    build_opener,
    fetch,
    validate_board_token,
    validate_url,
)
from watcher.resume import ResumeError, load_bundled_resume, validate_resume

GOOD = "https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true"


class ResumeTests(unittest.TestCase):
    def test_bundled_resume_satisfies_contract(self):
        r = load_bundled_resume()
        self.assertIs(r["fictional"], True)
        self.assertTrue(r["email"].endswith("@example.com"))
        self.assertEqual(r["phone"], "202-555-0147")
        self.assertEqual(r["target_titles"], ["data analyst", "business intelligence analyst"])

    def test_each_violation_rejected(self):
        bad = [
            {"fictional": False}, {"fictional": "true"}, {"name": "  "}, {"name": None},
            {"email": "a@gmail.com"}, {"email": "@example.com"}, {"email": "a@b@example.com"},
            {"phone": "617-555-0147"}, {"target_titles": ["data analyst"]},
            {"target_titles": ["Data Analyst", "Business Intelligence Analyst"]},
            {"skills": []}, {"skills": ["SQL", 3]}, {"skills": "SQL"},
        ]
        for override in bad:
            with self.subTest(override=override), self.assertRaises(ResumeError):
                validate_resume(resume(**override))

    def test_missing_field_rejected(self):
        r = resume()
        del r["phone"]
        with self.assertRaises(ResumeError):
            validate_resume(r)


class AllowListTests(unittest.TestCase):
    def test_build_url_is_exact_endpoint(self):
        self.assertEqual(build_jobs_url("acme"), GOOD)
        self.assertEqual(validate_url(GOOD), "acme")
        self.assertEqual(validate_url(GOOD.replace(".io/", ".io:443/")), "acme")

    def test_disallowed_hosts_and_urls(self):
        blocked = [
            "http://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true",
            "https://evil.example.com/v1/boards/acme/jobs?content=true",
            "https://boards-api.greenhouse.io.evil.com/v1/boards/acme/jobs?content=true",
            "https://boards.greenhouse.io/v1/boards/acme/jobs?content=true",
            "https://api.greenhouse.io/v1/boards/acme/jobs?content=true",
            "https://user:pw@boards-api.greenhouse.io/v1/boards/acme/jobs?content=true",
            "https://boards-api.greenhouse.io@evil.com/v1/boards/acme/jobs?content=true",
            "https://boards-api.greenhouse.io:8443/v1/boards/acme/jobs?content=true",
            "https://BOARDS-API.greenhouse.io/v1/boards/acme/jobs?content=true",
            "https://boards-api.greenhouse.io/v1/boards/acme/jobs/123?content=true",
            "https://boards-api.greenhouse.io/v1/boards/acme/jobs/?content=true",
            "https://boards-api.greenhouse.io/v1/boards/acme/departments?content=true",
            "https://boards-api.greenhouse.io/v1/boards/../acme/jobs?content=true",
            "https://boards-api.greenhouse.io/v1/boards/acme/jobs",
            "https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true&x=1",
            "https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true#frag",
            "https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true ",
            "https://boards-api.greenhouse.io\\@evil.com/v1/boards/acme/jobs?content=true",
            "file:///etc/passwd",
            None,
        ]
        for url in blocked:
            with self.subTest(url=url), self.assertRaises(BlockedRequestError):
                validate_url(url)

    def test_bad_board_tokens(self):
        for board in ["", "Acme", "acme/jobs", "../x", "acme.com", "a b", "acme?x=1", "-acme", "a" * 101, None, 5]:
            with self.subTest(board=board), self.assertRaises(BlockedRequestError):
                validate_board_token(board)

    def test_blocked_url_never_reaches_opener(self):
        class ExplodingOpener:
            calls = 0

            def open(self, *a, **k):
                ExplodingOpener.calls += 1
                raise AssertionError("network must not be touched")

        with self.assertRaises(BlockedRequestError):
            fetch("https://evil.example.com/v1/boards/acme/jobs?content=true", opener=ExplodingOpener())
        self.assertEqual(ExplodingOpener.calls, 0)


class RedirectTests(unittest.TestCase):
    def _headers(self, location):
        m = Message()
        m["Location"] = location
        return m

    def test_handler_declines_every_redirect(self):
        req = urllib.request.Request(GOOD)
        h = RefuseRedirectHandler()
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                self.assertIsNone(h.redirect_request(req, io.BytesIO(b""), code, "moved",
                                                     self._headers("https://evil.example.com/"),
                                                     "https://evil.example.com/"))

    def test_opener_raises_instead_of_following(self):
        opener = build_opener()
        req = urllib.request.Request(GOOD)
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            opener.error("https", req, io.BytesIO(b"moved"), 302, "Found",
                         self._headers("https://evil.example.com/steal"))
        self.assertEqual(ctx.exception.code, 302)

    def test_fetch_reports_redirect_as_refused_status(self):
        class RedirectingOpener:
            def open(self, request, timeout=None):
                raise urllib.error.HTTPError(request.full_url, 301, "Moved",
                                             RedirectTests._headers(None, "https://evil.example.com/"),
                                             io.BytesIO(b"constructed redirect body"))

        result = fetch(GOOD, opener=RedirectingOpener())
        self.assertEqual(result.status, 301)
        self.assertTrue(result.redirect_refused)
        self.assertEqual(result.body, b"constructed redirect body")

    def test_transport_failure_is_fetch_error(self):
        class DownOpener:
            def open(self, request, timeout=None):
                raise urllib.error.URLError("constructed DNS failure")

        with self.assertRaises(FetchError):
            fetch(GOOD, opener=DownOpener())


if __name__ == "__main__":
    unittest.main()
