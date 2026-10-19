"""Obtain Claude judgments through the locally installed Claude Code CLI (`claude -p`).

This is a second backend beside watcher.claude (the Messages API). It uses the
experimenter's existing Claude Code login (claude.ai subscription or OAuth token),
not ANTHROPIC_API_KEY.

Each call is one new `claude -p` process with:
- a fresh, explicitly chosen --session-id and --no-session-persistence, never
  --resume/--continue, so no conversation history is shared or kept;
- --system-prompt (replaces Claude Code's whole default system prompt) set to the
  fixed prompt file text, and the user message (fictional résumé view + posting
  view) on stdin, nothing else;
- all tools disabled (--tools "" and --disallowedTools "*"), no MCP servers,
  --restricted and --safe-mode (no CLAUDE.md, hooks, plugins, skills, auto memory,
  user/project settings files), --max-turns 1;
- an empty temporary working directory, and an environment with ANTHROPIC_* and
  CLAUDE_CODE_* variables removed, so an API key cannot silently take over billing.

The CLI is NOT the same as the API backend: Claude Code's own client decides
max_tokens, thinking, retries, and any context it adds; this module cannot observe
the exact wire request. See SOURCES.md and FRICTIONAL.md.

Every attempt that starts the main process is saved under
claude_outputs/<UTC date>/<purpose>/ with the exact argv, system prompt, user
message, raw stdout/stderr bytes, timestamps, the model(s) the CLI reports, and the
validation outcome. Output is checked with the same strict validator as the API
backend and is never repaired.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from .judgment import (
    JudgmentValidationError,
    build_user_message,
    claude_views,
    load_prompt,
    unavailable,
    validate_judgment_text,
)
from .util import iso, stamp, utc_now, write_bytes_atomic, write_json

CLI_EXECUTABLE = "claude"
BACKEND_NAME = "claude-code-cli"
DEFAULT_TIMEOUT = 300.0
# Login methods that use the experimenter's existing account rather than API-key billing.
ACCEPTED_AUTH_METHODS = ("claude.ai", "oauth_token")
AUTH_FIELDS_KEPT = ("loggedIn", "authMethod", "apiProvider", "subscriptionType")  # never email/org
STRIPPED_ENV_PREFIXES = ("ANTHROPIC_", "CLAUDE_CODE_")
STRIPPED_ENV_NAMES = ("CLAUDECODE",)
# Flags that would reuse or continue an earlier conversation. Never sent.
FORBIDDEN_FLAGS = ("--resume", "-r", "--continue", "-c", "--fork-session", "--from-pr", "--teleport")


class ClaudeCLIError(RuntimeError):
    pass


def default_runner(argv: list[str], stdin: bytes, cwd: str, env: dict, timeout: float):
    """Run one process. Returns (returncode, stdout_bytes, stderr_bytes)."""
    try:
        proc = subprocess.run(argv, input=stdin, cwd=cwd, env=env, capture_output=True, timeout=timeout,
                              check=False)
    except subprocess.TimeoutExpired as err:
        raise ClaudeCLIError(f"claude CLI timed out after {timeout}s") from err
    except OSError as err:
        raise ClaudeCLIError(f"could not start claude CLI: {err}") from err
    return proc.returncode, proc.stdout, proc.stderr


def child_env(base: dict | None = None) -> tuple[dict, list[str]]:
    """Copy of the environment without API-key / provider / nested-session variables."""
    base = dict(os.environ if base is None else base)
    removed = sorted(k for k in base if k.startswith(STRIPPED_ENV_PREFIXES) or k in STRIPPED_ENV_NAMES)
    for k in removed:
        del base[k]
    return base, removed


def build_cli_argv(system: str, *, executable: str, model: str, effort: str | None, session_id: str) -> list[str]:
    argv = [
        executable, "-p",
        "--output-format", "json",
        "--session-id", session_id,
        "--no-session-persistence",
        "--system-prompt", system,
        "--tools", "",
        "--disallowedTools", "*",
        "--strict-mcp-config",
        "--restricted",
        "--safe-mode",
        "--disable-slash-commands",
        "--permission-mode", "dontAsk",
        "--permission-prompts", "none",
        "--max-turns", "1",
        "--model", model,
    ]
    if effort:
        argv += ["--effort", effort]
    bad = [a for a in argv if a in FORBIDDEN_FLAGS]
    if bad:
        raise ClaudeCLIError(f"refusing to send conversation-reuse flags {bad}")
    return argv


def _probe(runner, executable: str, args: list[str], env: dict, cwd: str) -> tuple[int, bytes, bytes]:
    return runner([executable, *args], b"", cwd, env, 30.0)


def _auth_summary(runner, executable: str, env: dict, cwd: str) -> dict:
    code, out, _ = _probe(runner, executable, ["auth", "status"], env, cwd)
    try:
        data = json.loads(out.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"exit_code": code, "parse_error": "auth status output is not JSON"}
    if not isinstance(data, dict):
        return {"exit_code": code, "parse_error": "auth status output is not an object"}
    return {"exit_code": code, **{k: data.get(k) for k in AUTH_FIELDS_KEPT}}


def _model_matches(requested: str, reported: list[str]) -> bool:
    return any(r == requested or r.startswith(requested + "[") for r in reported)


def check_cli_result(result, *, requested_session_id: str, model: str) -> tuple[str | None, str | None]:
    """Return (result_text, None) if the CLI envelope is acceptable, else (None, reason)."""
    if not isinstance(result, dict):
        return None, "CLI output is not a JSON object"
    if result.get("type") != "result":
        return None, f"CLI output type was {result.get('type')!r}, not 'result'"
    if result.get("is_error") is not False:
        return None, f"CLI reported is_error={result.get('is_error')!r}"
    if result.get("subtype") != "success":
        return None, f"CLI subtype was {result.get('subtype')!r}, not 'success'"
    if result.get("session_id") != requested_session_id:
        return None, "CLI session_id does not match the fresh session requested"
    if result.get("num_turns") not in (None, 1):
        return None, f"CLI used {result.get('num_turns')!r} turns, expected 1"
    if result.get("permission_denials"):
        return None, "CLI reported permission denials (a tool was attempted)"
    reported = sorted(result.get("modelUsage") or {})
    if model.startswith("claude-") and not _model_matches(model, reported):
        return None, f"requested model {model!r} not among models the CLI reports {reported}"
    text = result.get("result")
    if not isinstance(text, str):
        return None, "CLI output has no text result"
    return text, None


def obtain_judgment_cli(
    resume: dict,
    posting: dict,
    *,
    prompt_version: str,
    purpose: str,
    model: str,
    effort: str | None,
    runner=None,
    executable: str = CLI_EXECUTABLE,
    outputs_dir: Path | None = None,
    prompts_dir: Path | None = None,
    call_label: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """One fresh `claude -p` call for one posting; return a validated judgment or an unavailable slot."""
    from .claude import OUTPUTS_DIR

    posting_id = posting["id"]
    runner = runner or default_runner
    if runner is default_runner and shutil.which(executable) is None:
        return unavailable(f"Claude unavailable: {executable!r} CLI not found on PATH; no call was made.",
                           posting_id=posting_id)

    system, prompt_sha = load_prompt(prompt_version, prompts_dir)
    resume_view, posting_view = claude_views(resume, posting)
    user = build_user_message(resume_view, posting_view)
    session_id = str(uuid.uuid4())
    argv = build_cli_argv(system, executable=executable, model=model, effort=effort, session_id=session_id)
    env, removed_env = child_env()

    started_dt = utc_now()
    out_root = Path(outputs_dir or OUTPUTS_DIR) / started_dt.strftime("%Y-%m-%d") / purpose
    name = f"{stamp(started_dt)}__posting-{posting_id}__{prompt_version}__cli"
    if call_label:
        name += f"__{call_label}"
    meta_path = out_root / f"{name}.json"
    record = {
        "saved_by": "watcher.claude_cli.obtain_judgment_cli",
        "backend": BACKEND_NAME,
        "purpose": purpose,
        "posting_id": posting_id,
        "prompt_version": prompt_version,
        "prompt_sha256": prompt_sha,
        "model_requested": model,
        "effort_requested": effort,
        "session_id_requested": session_id,
        "argv": argv,
        "system_prompt": system,
        "user_message": user,
        "env_removed": removed_env,
        "not_controlled_by_this_backend": [
            "max_tokens", "thinking configuration", "retries", "any context Claude Code adds",
            "exact wire request (not observable)",
        ],
    }

    with tempfile.TemporaryDirectory(prefix="watcher-claude-cli-") as cwd:
        try:
            v_code, v_out, _ = _probe(runner, executable, ["--version"], env, cwd)
            record["cli_version"] = v_out.decode("utf-8", "replace").strip() if v_code == 0 else None
            auth = _auth_summary(runner, executable, env, cwd)
        except Exception as err:
            record.update({"preflight_error": str(err),
                           "validation": {"valid": False, "errors": ["CLI preflight failed: " + str(err)]}})
            write_json(meta_path, record)
            return unavailable(f"Claude unavailable: {err}", posting_id=posting_id, raw_record=str(meta_path))
        record["auth"] = auth
        if not auth.get("loggedIn") or auth.get("authMethod") not in ACCEPTED_AUTH_METHODS:
            reason = (f"Claude Code CLI is not logged in with an account login "
                      f"(authMethod={auth.get('authMethod')!r}); no judgment call was made")
            record["validation"] = {"valid": False, "errors": [reason]}
            write_json(meta_path, record)
            return unavailable(f"Claude unavailable: {reason}", posting_id=posting_id, raw_record=str(meta_path))

        record["request_started_at"] = iso(utc_now())
        try:
            code, out, err_bytes = runner(argv, user.encode("utf-8"), cwd, env, timeout)
        except Exception as err:
            record.update({
                "response_received_at": iso(utc_now()),
                "transport_error": str(err),
                "validation": {"valid": False, "errors": ["no response: " + str(err)]},
            })
            write_json(meta_path, record)
            return unavailable(f"Claude unavailable: {err}", posting_id=posting_id, raw_record=str(meta_path))

    record["response_received_at"] = iso(utc_now())
    stdout_path = out_root / f"{name}.stdout.bin"
    stderr_path = out_root / f"{name}.stderr.bin"
    write_bytes_atomic(stdout_path, out)
    write_bytes_atomic(stderr_path, err_bytes)
    record.update({"exit_code": code, "raw_stdout_file": stdout_path.name, "raw_stderr_file": stderr_path.name})

    reason = None
    text = None
    try:
        result = json.loads(out.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        result = None
        reason = f"CLI stdout is not JSON: {err}"
    if isinstance(result, dict):
        record.update({
            "session_id_reported": result.get("session_id"),
            "subtype": result.get("subtype"),
            "is_error": result.get("is_error"),
            "num_turns": result.get("num_turns"),
            "stop_reason": result.get("stop_reason"),
            "duration_ms": result.get("duration_ms"),
            "duration_api_ms": result.get("duration_api_ms"),
            "usage": result.get("usage"),
            "model_usage": result.get("modelUsage"),
            "model_reported": sorted(result.get("modelUsage") or {}) or None,
            "total_cost_usd_client_estimate": result.get("total_cost_usd"),
        })
    if reason is None and code != 0:
        reason = f"claude CLI exited with code {code}"
    if reason is None:
        text, reason = check_cli_result(result, requested_session_id=session_id, model=model)
    record["output_text"] = text

    parsed_obj = None
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
    write_json(meta_path, record)

    if parsed_obj is None:
        return unavailable(f"Claude judgment unavailable: {reason}", posting_id=posting_id,
                           raw_record=str(meta_path))
    return {
        **parsed_obj,
        "status": "available",
        "label": "Claude judgment — a model opinion, not an established fact",
        "backend": BACKEND_NAME,
        "model_reported": record.get("model_reported"),
        "prompt_version": prompt_version,
        "raw_record": str(meta_path),
    }
