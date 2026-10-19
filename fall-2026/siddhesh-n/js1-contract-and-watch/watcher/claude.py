"""Obtain actual Claude judgments and save every raw output.

Uses the Messages API over raw HTTPS with the standard library (the project
prefers no third-party dependencies). Each call is a fresh, single-turn request
with no shared conversation history. Every attempt that reaches the network is
saved under claude_outputs/<UTC date>/<purpose>/ with timestamps, the request
body (never the API key), the exact response bytes, the model reported by the
API, and the validation outcome.

If the key is missing, the call fails, or validation fails, the judgment is
reported as unavailable. The deterministic record is never used as a stand-in.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from . import ROOT
from .judgment import (
    JudgmentValidationError,
    build_user_message,
    claude_views,
    load_prompt,
    unavailable,
    validate_judgment_text,
)
from .netguard import RefuseRedirectHandler
from .util import iso, stamp, utc_now, write_bytes_atomic, write_json

API_URL = "https://api.anthropic.com/v1/messages"
API_HOST = "api.anthropic.com"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "medium"
DEFAULT_MAX_TOKENS = 8000
OUTPUTS_DIR = ROOT / "claude_outputs"


class ClaudeCallError(RuntimeError):
    pass


def default_transport(url: str, headers: dict, body: bytes, timeout: float):
    """POST to the Messages API. Returns (status, header_pairs, body_bytes). No redirects, no proxies."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != API_HOST or parts.path != "/v1/messages":
        raise ClaudeCallError(f"refusing Claude request to non-allow-listed URL {url!r}")
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        RefuseRedirectHandler(),
    )
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, list(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as err:
        return err.code, list(err.headers.items()) if err.headers else [], err.read() or b""
    except (urllib.error.URLError, OSError, ValueError) as err:
        raise ClaudeCallError(f"Claude request failed: {err}") from err


def build_request_body(system: str, user: str, *, model: str, max_tokens: int, effort: str | None) -> dict:
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if effort:
        body["output_config"] = {"effort": effort}
    return body


def extract_text(response: dict) -> str:
    blocks = response.get("content")
    if not isinstance(blocks, list):
        raise ClaudeCallError("response has no content list")
    texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    if not texts:
        raise ClaudeCallError("response contains no text block")
    return "".join(texts)


def obtain_judgment(
    resume: dict,
    posting: dict,
    *,
    prompt_version: str,
    purpose: str,
    model: str = DEFAULT_MODEL,
    effort: str | None = DEFAULT_EFFORT,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    api_key: str | None = None,
    transport=None,
    outputs_dir: Path | None = None,
    prompts_dir: Path | None = None,
    call_label: str | None = None,
    timeout: float = 180.0,
) -> dict:
    """Make one fresh Claude call for one posting; return a validated judgment or an unavailable slot."""
    api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    posting_id = posting["id"]
    if not api_key:
        return unavailable("Claude unavailable: ANTHROPIC_API_KEY is not set; no call was made.",
                           posting_id=posting_id)

    system, prompt_sha = load_prompt(prompt_version, prompts_dir)
    resume_view, posting_view = claude_views(resume, posting)
    user = build_user_message(resume_view, posting_view)
    body = build_request_body(system, user, model=model, max_tokens=max_tokens, effort=effort)
    body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "anthropic-version": API_VERSION,
        "x-api-key": api_key,
    }

    started_dt = utc_now()
    out_root = Path(outputs_dir or OUTPUTS_DIR) / started_dt.strftime("%Y-%m-%d") / purpose
    name = f"{stamp(started_dt)}__posting-{posting_id}__{prompt_version}"
    if call_label:
        name += f"__{call_label}"
    record = {
        "saved_by": "watcher.claude.obtain_judgment",
        "purpose": purpose,
        "posting_id": posting_id,
        "prompt_version": prompt_version,
        "prompt_sha256": prompt_sha,
        "model_requested": model,
        "request_started_at": iso(started_dt),
        "request_body": body,
    }

    transport = transport or default_transport
    try:
        status, resp_headers, resp_bytes = transport(API_URL, headers, body_bytes, timeout)
    except Exception as err:  # transport failure: nothing came back
        record.update({
            "response_received_at": iso(utc_now()),
            "transport_error": str(err),
            "validation": {"valid": False, "errors": ["no response: " + str(err)]},
        })
        meta_path = out_root / f"{name}.json"
        write_json(meta_path, record)
        return unavailable(f"Claude unavailable: {err}", posting_id=posting_id, raw_record=str(meta_path))

    received = iso(utc_now())
    raw_path = out_root / f"{name}.response.bin"
    write_bytes_atomic(raw_path, resp_bytes)
    record.update({
        "response_received_at": received,
        "http_status": status,
        "response_headers": [(k, v) for k, v in resp_headers if k.lower().startswith(("request-id", "anthropic-", "content-type", "date"))],
        "raw_response_file": raw_path.name,
    })

    reason = None
    parsed_obj = None
    text = None
    try:
        response = json.loads(resp_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        response = None
        reason = f"response body is not JSON: {err}"
    if response is not None:
        record["model_reported"] = response.get("model") if isinstance(response, dict) else None
        record["response_id"] = response.get("id") if isinstance(response, dict) else None
        record["stop_reason"] = response.get("stop_reason") if isinstance(response, dict) else None
        record["usage"] = response.get("usage") if isinstance(response, dict) else None
        if status != 200:
            reason = f"HTTP {status} from Claude API"
        elif not isinstance(response, dict):
            reason = "response is not a JSON object"
        elif response.get("stop_reason") != "end_turn":
            reason = f"stop_reason was {response.get('stop_reason')!r}, not 'end_turn'"
        else:
            try:
                text = extract_text(response)
            except ClaudeCallError as err:
                reason = str(err)
    record["output_text"] = text

    errors: list[str] = []
    if reason is None:
        try:
            parsed_obj = validate_judgment_text(
                text,
                expected_posting_id=posting_id,
                valid_resume_fields=list(resume_view),
                valid_posting_fields=list(posting_view),
            )
        except JudgmentValidationError as err:
            errors = err.errors
            reason = "validation failed: " + "; ".join(errors)
    else:
        errors = [reason]

    record["validation"] = {"valid": parsed_obj is not None, "errors": errors}
    meta_path = out_root / f"{name}.json"
    write_json(meta_path, record)

    if parsed_obj is None:
        return unavailable(f"Claude judgment unavailable: {reason}", posting_id=posting_id,
                           raw_record=str(meta_path))
    return {
        **parsed_obj,
        "status": "available",
        "label": "Claude judgment — a model opinion, not an established fact",
        "model_reported": record.get("model_reported"),
        "prompt_version": prompt_version,
        "raw_record": str(meta_path),
    }


def import_pasted_judgment(
    resume: dict,
    posting: dict,
    *,
    prompt_version: str,
    pasted_text: str,
    surface: str,
    model_declared: str,
    outputs_dir: Path | None = None,
    prompts_dir: Path | None = None,
) -> dict:
    """Validate and save output that the experimenter obtained from Claude themselves
    (e.g. by pasting the rendered prompt into a Claude interface). Model info is as declared."""
    _, prompt_sha = load_prompt(prompt_version, prompts_dir)
    resume_view, posting_view = claude_views(resume, posting)
    now = utc_now()
    out_root = Path(outputs_dir or OUTPUTS_DIR) / now.strftime("%Y-%m-%d") / "manual-import"
    name = f"{stamp(now)}__posting-{posting['id']}__{prompt_version}"
    raw_path = out_root / f"{name}.response.txt"
    write_bytes_atomic(raw_path, pasted_text.encode("utf-8"))
    record = {
        "saved_by": "watcher.claude.import_pasted_judgment",
        "purpose": "manual-import",
        "posting_id": posting["id"],
        "prompt_version": prompt_version,
        "prompt_sha256": prompt_sha,
        "surface_declared": surface,
        "model_declared": model_declared,
        "imported_at": iso(now),
        "raw_response_file": raw_path.name,
    }
    try:
        obj = validate_judgment_text(
            pasted_text,
            expected_posting_id=posting["id"],
            valid_resume_fields=list(resume_view),
            valid_posting_fields=list(posting_view),
        )
        record["validation"] = {"valid": True, "errors": []}
    except JudgmentValidationError as err:
        obj = None
        record["validation"] = {"valid": False, "errors": err.errors}
    meta_path = out_root / f"{name}.json"
    write_json(meta_path, record)
    if obj is None:
        return unavailable("pasted output failed validation: " + "; ".join(record["validation"]["errors"]),
                           posting_id=posting["id"], raw_record=str(meta_path))
    return {**obj, "status": "available",
            "label": "Claude judgment — a model opinion, not an established fact",
            "model_declared": model_declared, "prompt_version": prompt_version,
            "raw_record": str(meta_path)}
