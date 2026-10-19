"""One watch run (CONTRACT.md, "Out" and "Watch and evidence").

Order of operations:
 1. validate the résumé and board name; build the allow-listed URL (no I/O yet);
 2. load existing state (a corrupt state file is an error, never a fresh baseline);
 3. obtain response bytes (live fetch, or replay of a saved file) and save them
    unchanged as evidence before any parsing;
 4. validate the complete response;
 5. compute new IDs, records, and (optionally) Claude judgments, keyed by ID;
 6. only then write state = previously seen IDs ∪ current IDs.
A fetch or validation failure writes evidence and a failure report but leaves state untouched.
"""

from __future__ import annotations

from pathlib import Path

from . import ROOT
from .netguard import FetchError, FetchResult, build_jobs_url, fetch
from .postings import PostingValidationError, parse_response
from .relevance import evaluate
from .resume import validate_resume
from .state import load_state, save_state, state_path
from .judgment import unavailable
from .util import iso, rel, sha256_bytes, stamp, unique_dir, utc_now, write_bytes_atomic, write_json

DEFAULT_STATE_DIR = ROOT / "state"
DEFAULT_EVIDENCE_DIR = ROOT / "evidence" / "runs"

NOT_REQUESTED = "Claude judgment not requested for this run (re-run with --claude to obtain one)."


def run_watch(
    board: str,
    resume: dict,
    *,
    state_dir: Path = DEFAULT_STATE_DIR,
    evidence_dir: Path = DEFAULT_EVIDENCE_DIR,
    fetcher=None,
    replay_path: Path | None = None,
    replay_label: str | None = None,
    judge=None,
) -> dict:
    """Run once and return the report dict (also saved as report.json in the run's evidence dir).

    fetcher(url) -> FetchResult is injectable for tests; judge(posting) -> judgment dict is optional.
    """
    validate_resume(resume)
    url = build_jobs_url(board)  # raises BlockedRequestError before any I/O
    state_before = load_state(state_dir, board)  # raises StateError on a corrupt file
    started = utc_now()
    run_dir = unique_dir(Path(evidence_dir) / board, stamp(started))
    write_json(run_dir / "state_before.json", {"exists": state_before is not None, "state": state_before})

    report = {
        "board": board,
        "url": url,
        "run_started_at": iso(started),
        "evidence_dir": rel(run_dir),
        "state_file": rel(state_path(state_dir, board)),
    }

    def finish(status: str, **extra) -> dict:
        report.update(status=status, **extra)
        report["run_finished_at"] = iso(utc_now())
        state_after = load_state(state_dir, board)
        write_json(run_dir / "state_after.json", {"exists": state_after is not None, "state": state_after})
        write_json(run_dir / "report.json", report)
        return report

    # 3. obtain bytes and save them before parsing
    if replay_path is not None:
        raw = Path(replay_path).read_bytes()
        source = {
            "type": "replay",
            "replayed_file": rel(replay_path),
            "label": replay_label or "replay of a saved response file (not a live fetch)",
            "note": "No network request was made for this run.",
        }
        status_code = 200
    else:
        try:
            result: FetchResult = (fetcher or fetch)(url)
        except FetchError as err:
            write_json(run_dir / "fetch_meta.json", {"type": "live", "url": url, "error": str(err)})
            return finish("fetch_failed", error=str(err), state_updated=False, new_postings=[])
        raw = result.body
        source = {"type": "live", **result.metadata()}
        status_code = result.status

    write_bytes_atomic(run_dir / "raw_response.bin", raw)
    source.update(raw_sha256=sha256_bytes(raw), raw_bytes=len(raw), raw_file="raw_response.bin")
    write_json(run_dir / "fetch_meta.json", source)
    report["source"] = source

    if status_code != 200:
        why = "redirect refused" if 300 <= status_code < 400 else f"HTTP {status_code}"
        return finish("fetch_failed", error=why, state_updated=False, new_postings=[])

    # 4. validate the complete response
    try:
        postings = parse_response(raw)
    except PostingValidationError as err:
        return finish("input_validation_failed", error=str(err), state_updated=False, new_postings=[])

    by_id = {p["id"]: p for p in postings}
    current_ids = set(by_id)

    # 5. compute results keyed by posting ID
    if state_before is None:
        new_ids: list[int] = []
        seen_after = current_ids
        runs = 1
        status = "baseline_saved"
    else:
        seen_before = set(state_before["seen_ids"])
        new_ids = sorted(current_ids - seen_before)
        seen_after = seen_before | current_ids
        runs = state_before.get("successful_runs", 0) + 1
        status = "ok"

    entries = []
    for pid in new_ids:
        posting = by_id[pid]
        record = evaluate(resume, posting)
        if judge is None:
            judgment = unavailable(NOT_REQUESTED, posting_id=pid)
        else:
            try:
                judgment = judge(posting)
            except Exception as err:
                judgment = unavailable(f"Claude judgment unavailable: {err}", posting_id=pid)
            if judgment.get("status") == "available" and judgment.get("posting_id") != pid:
                judgment = unavailable("judgment rejected: it names a different posting ID", posting_id=pid)
        entries.append({
            "posting_id": pid,
            "title": posting["title"],
            "url": posting["absolute_url"],
            "record": record,
            "judgment": judgment,
        })

    # 6. update state only after everything above succeeded
    save_state(state_dir, board, seen_after, updated_at=iso(utc_now()), successful_runs=runs)
    return finish(
        status,
        state_updated=True,
        postings_in_response=len(postings),
        previously_seen=0 if state_before is None else len(state_before["seen_ids"]),
        new_count=len(entries),
        new_postings=entries,
    )


def format_report(report: dict) -> str:
    lines = [f"board: {report['board']}", f"status: {report['status']}"]
    if report.get("error"):
        lines.append(f"error: {report['error']}")
    lines.append(f"state updated: {report.get('state_updated')}")
    if "postings_in_response" in report:
        lines.append(f"postings in response: {report['postings_in_response']}")
        lines.append(f"new postings: {report['new_count']}")
    for e in report.get("new_postings", []):
        rec, jud = e["record"], e["judgment"]
        lines.append("")
        lines.append(f"- [{e['posting_id']}] {e['title']}")
        lines.append(f"  {e['url']}")
        lines.append(f"  record (deterministic rule): {rec['verdict']}")
        lines.append(f"    {rec['justification']}")
        if jud.get("status") == "available":
            lines.append(f"  judgment (Claude, a model opinion, not a fact): {jud['verdict']}")
            lines.append(f"    cites résumé {jud['resume_fields']} and posting {jud['posting_fields']}: {jud['justification']}")
        else:
            lines.append(f"  judgment: unavailable ({jud['reason']})")
    lines.append("")
    lines.append(f"evidence: {report['evidence_dir']}")
    return "\n".join(lines)
