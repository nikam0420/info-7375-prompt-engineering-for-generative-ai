"""Command-line entry point: python3 -m watcher <command> ..."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ROOT
from . import claude as claude_mod
from . import claude_cli
from .demo import DEMO_ROOT, prepare_demo, run_demo
from .evaluation import (
    EVAL_DIR,
    EvaluationGateError,
    STRATEGIES,
    assert_not_unlabeled_sample_posting,
    changed_hunks,
    freeze_revision,
    labels_status,
    prompt_diff,
    run_consistency,
    run_experiment,
    select_sample,
)
from .judgment import PROMPT_FILES, PROMPTS_DIR, build_user_message, claude_views, load_prompt
from .netguard import BlockedRequestError, FetchError, build_jobs_url, fetch
from .postings import PostingValidationError, parse_response
from .resume import ResumeError, load_bundled_resume
from .state import StateError
from .util import iso, rel, sha256_bytes, stamp, unique_dir, utc_now, write_bytes_atomic, write_json
from .watch import DEFAULT_EVIDENCE_DIR, DEFAULT_STATE_DIR, format_report, run_watch

FETCH_DIR = ROOT / "evidence" / "fetches"


def _claude_judge(args, resume):
    """Return judge(posting) making one fresh, saved Claude call per posting."""
    effort = None if args.effort == "none" else args.effort

    def judge(posting, purpose="watch", call_label=None):
        if args.backend == "cli":
            return claude_cli.obtain_judgment_cli(
                resume, posting, prompt_version=args.prompt, purpose=purpose, model=args.model,
                effort=effort, call_label=call_label,
            )
        return claude_mod.obtain_judgment(
            resume, posting, prompt_version=args.prompt, purpose=purpose, model=args.model,
            effort=effort, call_label=call_label,
        )
    return judge


def _posting_from_raw(raw_file: str, posting_id: int) -> dict:
    postings = parse_response(Path(raw_file).read_bytes())
    for p in postings:
        if p["id"] == posting_id:
            return p
    raise PostingValidationError(f"posting {posting_id} not found in {raw_file}")


def cmd_fetch(args) -> int:
    """Live fetch of one board's public jobs endpoint; saves raw evidence; never touches state."""
    url = build_jobs_url(args.board)
    started = utc_now()
    out = unique_dir(FETCH_DIR / args.board, stamp(started))
    try:
        result = fetch(url)
    except FetchError as err:
        write_json(out / "fetch_meta.json", {"url": url, "attempted_at": iso(started), "error": str(err)})
        print(f"fetch failed: {err}\nevidence: {rel(out)}")
        return 1
    write_bytes_atomic(out / "raw_response.bin", result.body)
    meta = {**result.metadata(), "raw_file": "raw_response.bin", "raw_bytes": len(result.body),
            "raw_sha256": sha256_bytes(result.body), "board": args.board}
    try:
        postings = parse_response(result.body) if result.status == 200 else None
        meta["validation"] = {"valid": postings is not None, "postings": len(postings) if postings else None,
                              "error": None if result.status == 200 else f"HTTP {result.status}"}
    except PostingValidationError as err:
        meta["validation"] = {"valid": False, "postings": None, "error": str(err)}
    write_json(out / "fetch_meta.json", meta)
    print(json.dumps({k: meta[k] for k in ("url", "status", "response_finished_at", "raw_bytes",
                                           "raw_sha256", "validation")}, indent=2))
    print(f"evidence: {rel(out)}")
    return 0 if meta["validation"]["valid"] else 1


def cmd_watch(args) -> int:
    resume = load_bundled_resume()
    judge = _claude_judge(args, resume) if args.claude else None
    report = run_watch(
        args.board, resume, state_dir=Path(args.state_dir), evidence_dir=Path(args.evidence_dir),
        replay_path=Path(args.replay) if args.replay else None, replay_label=args.replay_label, judge=judge,
    )
    print(format_report(report))
    return 0 if report["status"] in ("ok", "baseline_saved") else 1


def cmd_judge(args) -> int:
    resume = load_bundled_resume()
    posting = _posting_from_raw(args.raw, args.posting_id)
    assert_not_unlabeled_sample_posting(args.posting_id)
    j = _claude_judge(args, resume)(posting, purpose="adhoc")
    print(json.dumps(j, indent=2, ensure_ascii=False))
    return 0 if j.get("status") == "available" else 1


def cmd_prompt_show(args) -> int:
    resume = load_bundled_resume()
    posting = _posting_from_raw(args.raw, args.posting_id)
    system, sha = load_prompt(args.prompt)
    rv, pv = claude_views(resume, posting)
    print(f"=== SYSTEM PROMPT ({args.prompt}, sha256 {sha}) ===\n{system}\n=== USER MESSAGE ===\n"
          f"{build_user_message(rv, pv)}")
    return 0


def cmd_judgment_import(args) -> int:
    resume = load_bundled_resume()
    posting = _posting_from_raw(args.raw, args.posting_id)
    assert_not_unlabeled_sample_posting(args.posting_id)
    text = Path(args.response_file).read_text(encoding="utf-8")
    j = claude_mod.import_pasted_judgment(resume, posting, prompt_version=args.prompt, pasted_text=text,
                                          surface=args.surface, model_declared=args.model_declared)
    print(json.dumps(j, indent=2, ensure_ascii=False))
    return 0 if j.get("status") == "available" else 1


def cmd_demo_prepare(args) -> int:
    m = prepare_demo(Path(args.raw), args.board, withhold=args.withhold, seed=args.seed)
    print(json.dumps(m, indent=2))
    return 0


def cmd_demo_run(args) -> int:
    resume = load_bundled_resume()
    judge = _claude_judge(args, resume) if args.claude else None
    r = run_demo(args.board, resume, judge=judge)
    print(json.dumps(r, indent=2))
    return 0 if r["all_checks_passed"] else 1


def cmd_sample_select(args) -> int:
    s = select_sample(Path(args.raw), args.board, resume=load_bundled_resume(), seed=args.seed,
                      strategy=args.strategy)
    print(json.dumps({k: s[k] for k in ("board", "source_raw_file", "seed", "strategy", "strategy_note",
                                        "dev", "heldout")}, indent=2))
    print("Blank label sheets: eval/hand_labels_dev.csv, eval/hand_labels_heldout.csv")
    print("Posting texts to read: eval/postings/<id>.txt")
    return 0


def cmd_labels_status(args) -> int:
    print(json.dumps(labels_status(), indent=2))
    return 0


def cmd_consistency(args) -> int:
    resume = load_bundled_resume()
    r = run_consistency(args.prompt, judge_fn=_claude_judge(args, resume), n_postings=args.postings,
                        calls=args.calls, backend=args.backend)
    print(json.dumps(r, indent=2))
    return 0


def cmd_experiment(args) -> int:
    resume = load_bundled_resume()
    r = run_experiment(args.prompt, args.split, resume=resume, judge_fn=_claude_judge(args, resume),
                       prompts_dir=PROMPTS_DIR, backend=args.backend)
    print(json.dumps(r["summary"], indent=2))
    return 0


def cmd_freeze(args) -> int:
    print(json.dumps(freeze_revision(prompts_dir=PROMPTS_DIR), indent=2))
    return 0


def cmd_prompt_diff(args) -> int:
    print(prompt_diff(PROMPTS_DIR))
    print(f"changed blocks: {len(changed_hunks(PROMPTS_DIR))}")
    return 0


def _add_claude_opts(p, *, flag: bool):
    if flag:
        p.add_argument("--claude", action="store_true",
                       help="make one actual Claude call per new posting (see --backend)")
    p.add_argument("--backend", choices=("api", "cli"), default="api",
                   help="api: Messages API, needs ANTHROPIC_API_KEY. cli: one fresh `claude -p` process per "
                        "call using your Claude Code login; not identical to API settings")
    p.add_argument("--prompt", choices=sorted(PROMPT_FILES), default="baseline")
    p.add_argument("--model", default=claude_mod.DEFAULT_MODEL)
    p.add_argument("--effort", default=claude_mod.DEFAULT_EFFORT,
                   help="api: output_config.effort; cli: --effort (low|medium|high|xhigh|max), or 'none' to omit")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python3 -m watcher", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("fetch", help="live-fetch one board and save raw evidence (no state change)")
    p.add_argument("--board", required=True)
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("watch", help="run the watcher once (baseline on first success)")
    p.add_argument("--board", required=True)
    p.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    p.add_argument("--evidence-dir", default=str(DEFAULT_EVIDENCE_DIR))
    p.add_argument("--replay", help="replay a saved response file instead of fetching")
    p.add_argument("--replay-label")
    _add_claude_opts(p, flag=True)
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("judge", help="one actual Claude judgment for one posting in a saved response")
    p.add_argument("--raw", required=True)
    p.add_argument("--posting-id", type=int, required=True)
    _add_claude_opts(p, flag=False)
    p.set_defaults(func=cmd_judge)

    p = sub.add_parser("prompt-show", help="print the exact prompt for one posting (no call)")
    p.add_argument("--raw", required=True)
    p.add_argument("--posting-id", type=int, required=True)
    p.add_argument("--prompt", choices=sorted(PROMPT_FILES), default="baseline")
    p.set_defaults(func=cmd_prompt_show)

    p = sub.add_parser("judgment-import", help="validate and save a Claude output you obtained yourself")
    p.add_argument("--raw", required=True)
    p.add_argument("--posting-id", type=int, required=True)
    p.add_argument("--prompt", choices=sorted(PROMPT_FILES), default="baseline")
    p.add_argument("--response-file", required=True)
    p.add_argument("--surface", required=True, help="where you obtained it, e.g. 'claude.ai web chat'")
    p.add_argument("--model-declared", required=True, help="model as shown by that surface")
    p.set_defaults(func=cmd_judgment_import)

    p = sub.add_parser("demo-prepare", help="build a CONSTRUCTED SEEDED BASELINE from a real response")
    p.add_argument("--raw", required=True)
    p.add_argument("--board", required=True)
    p.add_argument("--withhold", type=int, default=3)
    p.add_argument("--seed", type=int, required=True)
    p.set_defaults(func=cmd_demo_prepare)

    p = sub.add_parser("demo-run", help="run the two-run demonstration on fresh demo state")
    p.add_argument("--board", required=True)
    _add_claude_opts(p, flag=True)
    p.set_defaults(func=cmd_demo_run)

    p = sub.add_parser("sample-select", help="select 20 real postings, split 10 dev / 10 held-out")
    p.add_argument("--raw", required=True)
    p.add_argument("--board", required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--strategy", choices=STRATEGIES, required=True)
    p.set_defaults(func=cmd_sample_select)

    p = sub.add_parser("labels-status", help="report hand-label completeness (never shows model output)")
    p.set_defaults(func=cmd_labels_status)

    p = sub.add_parser("consistency-run", help="5 dev postings x 4 fresh Claude calls (needs complete dev labels)")
    p.add_argument("--postings", type=int, default=5)
    p.add_argument("--calls", type=int, default=4)
    _add_claude_opts(p, flag=False)
    p.set_defaults(func=cmd_consistency)

    p = sub.add_parser("experiment-run", help="run one prompt over one split (held-out locked until freeze)")
    p.add_argument("--split", choices=("dev", "heldout"), required=True)
    _add_claude_opts(p, flag=False)
    p.set_defaults(func=cmd_experiment)

    p = sub.add_parser("freeze-revision", help="freeze baseline+revision hashes; unlocks held-out")
    p.set_defaults(func=cmd_freeze)

    p = sub.add_parser("prompt-diff", help="show the single change between baseline and revision")
    p.set_defaults(func=cmd_prompt_diff)
    return ap


def main(argv=None) -> int:
    if sys.version_info < (3, 12):
        print("Python 3.12 or newer is required", file=sys.stderr)
        return 2
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (BlockedRequestError, ResumeError, StateError, PostingValidationError, EvaluationGateError,
            FileExistsError, ValueError) as err:
        print(f"refused: {type(err).__name__}: {err}", file=sys.stderr)
        return 2
