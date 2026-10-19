"""Load and validate the bundled fictional résumé (CONTRACT.md, "In").

Only the bundled fictional résumé is supported. These checks do not prove that
arbitrary user-supplied data is fictional, so the CLI offers no option to load
any other résumé file.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import ROOT

BUNDLED_RESUME_PATH = ROOT / "data" / "fictional_resume.json"

REQUIRED_PHONE = "202-555-0147"
REQUIRED_TARGET_TITLES = ["data analyst", "business intelligence analyst"]
EMAIL_DOMAIN = "@example.com"


class ResumeError(ValueError):
    """The résumé does not satisfy the contract's fictional-résumé checks."""


def validate_resume(resume) -> dict:
    """Return the résumé unchanged if it passes every contract check, else raise ResumeError."""
    errors = []
    if not isinstance(resume, dict):
        raise ResumeError("résumé must be a JSON object")

    if resume.get("fictional") is not True:
        errors.append("fictional must be the boolean true")

    name = resume.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name must be a nonempty string")

    email = resume.get("email")
    if (
        not isinstance(email, str)
        or not email.endswith(EMAIL_DOMAIN)
        or len(email) <= len(EMAIL_DOMAIN)
        or email.count("@") != 1
        or email != email.strip()
    ):
        errors.append(f"email must be an address ending in {EMAIL_DOMAIN}")

    if resume.get("phone") != REQUIRED_PHONE:
        errors.append(f"phone must equal {REQUIRED_PHONE}")

    if resume.get("target_titles") != REQUIRED_TARGET_TITLES:
        errors.append(f"target_titles must equal {json.dumps(REQUIRED_TARGET_TITLES)}")

    skills = resume.get("skills")
    if not isinstance(skills, list) or not skills or not all(isinstance(s, str) for s in skills):
        errors.append("skills must be a nonempty list of strings")

    if errors:
        raise ResumeError("; ".join(errors))
    return resume


def load_bundled_resume() -> dict:
    with open(BUNDLED_RESUME_PATH, encoding="utf-8") as fh:
        return validate_resume(json.load(fh))
