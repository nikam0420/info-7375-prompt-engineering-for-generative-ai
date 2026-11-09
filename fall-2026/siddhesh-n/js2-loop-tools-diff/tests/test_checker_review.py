import subprocess
import sys
import unittest


class CheckerReview(unittest.TestCase):
    def test_checker_rejects_wrong_exit(self):
        result = subprocess.run(
            [
                sys.executable,
                "independent_check.py",
                "evidence/seed-missing-jobs.json",
                "evidence/student-constructed-wrong-exit.json",
            ],
            capture_output=True,
            text=True,
        )
                self.assertEqual(result.returncode, 1)
