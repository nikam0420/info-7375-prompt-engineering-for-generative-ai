import os
from pathlib import Path
import tempfile
import unittest

from agent import BOARDS, PolicyError, persist, require_request


class Boundaries(unittest.TestCase):
    def test_request_policy(self):
        url = BOARDS[0][2]
        cases = (
            ("allow-read", "GET", url, True),
            ("deny-write", "POST", url, False),
            ("deny-off-list-host", "GET", "https://example.com/jobs", False),
            ("deny-insecure", "GET", url.replace("https:", "http:"), False),
            ("deny-credentials", "GET", url.replace("://", "://user@"), False),
            ("deny-alternate-port", "GET", url.replace(".io/", ".io:443/"), False),
            ("deny-application-path", "GET", url + "/123", False),
        )
        for name, method, endpoint, allowed in cases:
            with self.subTest(name=name):
                if allowed:
                    require_request(method, endpoint)
                else:
                    with self.assertRaises(PolicyError):
                        require_request(method, endpoint)

    def test_write_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "jobs").mkdir()
            (root / "jobs-evil").mkdir()
            outside = root / "jobs-evil" / "outside.txt"
            outside.write_bytes(b"protected")
            (root / "jobs" / "link.json").symlink_to(outside)
            cases = (
                ("allow-report", "jobs/report.json", False, True),
                ("deny-parent-traversal", "jobs/../escape.json", True, False),
                ("deny-prefix-sibling", "jobs-evil/escape.json", True, False),
                ("deny-absolute", str(root / "jobs" / "absolute.json"), True, False),
                ("deny-link", "jobs/link.json", True, False),
                ("deny-unapproved-raw", "jobs/no.raw", False, False),
                ("allow-approved-raw", "jobs/yes.raw", True, True),
                ("deny-overwrite", "jobs/report.json", True, False),
            )
            for name, path, approved, allowed in cases:
                with self.subTest(name=name):
                    if allowed:
                        persist(root, path, b"new", approved=approved)
                        self.assertEqual((root / path).read_bytes(), b"new")
                    else:
                        with self.assertRaises((PolicyError, OSError)):
                            persist(root, path, b"changed", approved=approved)
            self.assertEqual(outside.read_bytes(), b"protected")
            self.assertFalse((root / "jobs" / "no.raw").exists())
            self.assertFalse((root / "escape.json").exists())
            self.assertFalse((root / "jobs-evil" / "escape.json").exists())
            self.assertEqual((root / "jobs" / "report.json").read_bytes(), b"new")
            os.rename(root / "jobs", root / "original-jobs")
            (root / "jobs").symlink_to(root / "jobs-evil", target_is_directory=True)
            with self.assertRaises(OSError):
                persist(root, "jobs/root-link.json", b"blocked")
            self.assertFalse((root / "jobs-evil" / "root-link.json").exists())
