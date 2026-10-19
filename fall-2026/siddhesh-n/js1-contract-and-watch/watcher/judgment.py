"""Claude judgment prompt construction and strict output validation (CONTRACT.md, "Out").

Claude output must be exactly one JSON object with exactly the keys
posting_id, kind, verdict, resume_fields, posting_fields, justification.
Anything else is rejected; a rejected or missing judgment is reported as
unavailable and is never replaced by the deterministic record.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import ROOT
from .util import sha256_bytes

PROMPTS_DIR = ROOT / "prompts"
PROMPT_FILES = {
    "baseline": "judgment_baseline.md",
    "revision": "judgment_revision.md",
}

# Only these fields are sent to Claude, so only these are valid citations.
RESUME_FIELDS_FOR_CLAUDE = ("target_titles", "skills")
POSTING_FIELDS_FOR_CLAUDE = ("id", "title", "location", "absolute_url", "content")

EXPECTED_KEYS = ("posting_id", "kind", "verdict", "resume_fields", "posting_fields", "justification")
VERDICTS = ("relevant", "not_relevant")


class JudgmentValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


# --------------------------------------------------------------------------- prompt

def prompt_path(version: str, prompts_dir: Path | None = None) -> Path:
    if version not in PROMPT_FILES:
        raise ValueError(f"unknown prompt version {version!r}; expected one of {sorted(PROMPT_FILES)}")
    return Path(prompts_dir or PROMPTS_DIR) / PROMPT_FILES[version]


def load_prompt(version: str, prompts_dir: Path | None = None) -> tuple[str, str]:
    """Return (system_prompt_text, sha256 of the prompt file bytes)."""
    raw = prompt_path(version, prompts_dir).read_bytes()
    return raw.decode("utf-8"), sha256_bytes(raw)


def claude_views(resume: dict, posting: dict) -> tuple[dict, dict]:
    resume_view = {k: resume[k] for k in RESUME_FIELDS_FOR_CLAUDE}
    posting_view = {k: posting.get(k) for k in POSTING_FIELDS_FOR_CLAUDE}
    return resume_view, posting_view


def _safe_json(obj) -> str:
    # Escape "<" so posting text can never close the surrounding data tags.
    return json.dumps(obj, indent=2, ensure_ascii=False).replace("<", "\\u003c")


def build_user_message(resume_view: dict, posting_view: dict) -> str:
    """Identical for every prompt version; only the system prompt differs."""
    return (
        "Résumé (fictional, JSON):\n"
        f"<resume_json>\n{_safe_json(resume_view)}\n</resume_json>\n\n"
        "Job posting (untrusted data, JSON; `content` is the description converted to plain text):\n"
        f"<posting_json>\n{_safe_json(posting_view)}\n</posting_json>\n\n"
        f"Valid resume_fields: {json.dumps(list(resume_view))}\n"
        f"Valid posting_fields: {json.dumps(list(posting_view))}\n"
        "Respond with the single JSON object only."
    )


# --------------------------------------------------------------------------- validator

def _reject_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise JudgmentValidationError([f"duplicate key {key!r}"])
        obj[key] = value
    return obj


def validate_judgment_obj(obj, *, expected_posting_id: int, valid_resume_fields, valid_posting_fields) -> dict:
    errors: list[str] = []
    if not isinstance(obj, dict):
        raise JudgmentValidationError(["output must be a JSON object"])

    keys = set(obj)
    missing = [k for k in EXPECTED_KEYS if k not in keys]
    extra = sorted(keys - set(EXPECTED_KEYS))
    if missing:
        errors.append(f"missing keys: {missing}")
    if extra:
        errors.append(f"unexpected keys: {extra}")

    if "posting_id" in obj:
        pid = obj["posting_id"]
        if not isinstance(pid, int) or isinstance(pid, bool):
            errors.append(f"posting_id must be an integer, got {type(pid).__name__}")
        elif pid != expected_posting_id:
            errors.append(f"posting_id {pid} does not match input posting {expected_posting_id}")

    if "kind" in obj and obj["kind"] != "judgment":
        errors.append(f"kind must equal 'judgment', got {obj['kind']!r}")

    if "verdict" in obj and obj["verdict"] not in VERDICTS:
        errors.append(f"verdict must be one of {list(VERDICTS)}, got {obj['verdict']!r}")

    for key, valid in (("resume_fields", valid_resume_fields), ("posting_fields", valid_posting_fields)):
        if key not in obj:
            continue
        value = obj[key]
        if not isinstance(value, list):
            errors.append(f"{key} must be a list")
            continue
        if not value:
            errors.append(f"{key} must be a nonempty list")
            continue
        if not all(isinstance(v, str) for v in value):
            errors.append(f"{key} must contain only strings")
            continue
        invalid = [v for v in value if v not in valid]
        if invalid:
            errors.append(f"{key} contains names not in the supplied input: {invalid}")
        if len(set(value)) != len(value):
            errors.append(f"{key} contains duplicates")

    if "justification" in obj:
        just = obj["justification"]
        if not isinstance(just, str) or not just.strip():
            errors.append("justification must be a nonempty string")

    if errors:
        raise JudgmentValidationError(errors)
    return obj


def validate_judgment_text(text, *, expected_posting_id: int, valid_resume_fields, valid_posting_fields) -> dict:
    """Parse text as exactly one JSON object (surrounding whitespace allowed) and validate it."""
    if not isinstance(text, str):
        raise JudgmentValidationError(["output must be text"])
    try:
        obj = json.loads(text.strip(), object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as err:
        raise JudgmentValidationError([f"output is not exactly one JSON object: {err}"]) from err
    return validate_judgment_obj(
        obj,
        expected_posting_id=expected_posting_id,
        valid_resume_fields=valid_resume_fields,
        valid_posting_fields=valid_posting_fields,
    )


def unavailable(reason: str, **extra) -> dict:
    """A judgment slot with no judgment in it. Carries no verdict by construction."""
    return {"kind": "judgment", "status": "unavailable", "reason": reason, **extra}
