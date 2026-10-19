"""Sampling, hand-label gates, consistency runs, and the locked prompt experiment.

Rules enforced here:
- 20 real postings are sampled once from a saved real response and split 10/10.
- Label sheets are generated blank. Nothing here writes a hand label, and no
  model output is produced or shown until the relevant split is fully labeled.
- Once a split's labels have been used in a model evaluation, the label file's
  hash is locked; later edits are refused.
- Held-out evaluation is refused until the prompt revision is frozen
  (prompts/FROZEN.json, hashes must still match) and runs at most once per prompt.
- No metric is computed except from saved, actual Claude outputs.
"""

from __future__ import annotations

import csv
import difflib
import json
import os
import random
import shutil
from pathlib import Path

from . import ROOT
from .judgment import PROMPT_FILES, VERDICTS, prompt_path
from .postings import parse_response
from .relevance import title_matches
from .util import iso, read_json, rel, resolve_rel, sha256_bytes, sha256_file, stamp, utc_now, write_bytes_atomic, write_json

EVAL_DIR = ROOT / "eval"
SAMPLE_SIZE = 20
SPLITS = ("dev", "heldout")
STRATEGIES = ("random", "title-stratified")
LABEL_COLUMNS = [
    "posting_id", "split", "title", "absolute_url", "text_file",
    "condition_1_title_yes_no", "condition_2_sql_yes_no", "condition_3_skill_yes_no",
    "hand_label", "notes", "labeled_at",
]


class EvaluationGateError(RuntimeError):
    """A step was attempted before its preconditions were met."""


# --------------------------------------------------------------------------- paths

def sample_path(eval_dir: Path) -> Path:
    return Path(eval_dir) / "sample.json"


def labels_path(eval_dir: Path, split: str) -> Path:
    return Path(eval_dir) / f"hand_labels_{split}.csv"


def results_dir(eval_dir: Path) -> Path:
    return Path(eval_dir) / "results"


def frozen_path(prompts_dir: Path) -> Path:
    return Path(prompts_dir) / "FROZEN.json"


# --------------------------------------------------------------------------- sampling

def select_sample(raw_path: Path, board: str, *, resume: dict, seed: int, strategy: str,
                  eval_dir: Path = EVAL_DIR) -> dict:
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}")
    eval_dir = Path(eval_dir)
    if sample_path(eval_dir).exists():
        raise EvaluationGateError(f"{sample_path(eval_dir)} already exists; the sample is fixed once drawn")
    raw = Path(raw_path).read_bytes()
    postings = parse_response(raw)
    if len(postings) < SAMPLE_SIZE:
        raise EvaluationGateError(f"response has {len(postings)} postings; {SAMPLE_SIZE} are required")

    rng = random.Random(seed)
    ids = sorted(p["id"] for p in postings)
    by_id = {p["id"]: p for p in postings}
    if strategy == "random":
        strata = [rng.sample(ids, SAMPLE_SIZE)]
        note = "Simple random sample of 20 posting IDs (seeded)."
    else:
        hits = [i for i in ids if title_matches(by_id[i]["title"], resume["target_titles"])]
        others = [i for i in ids if i not in set(hits)]
        k = min(SAMPLE_SIZE // 2, len(hits))
        strata = [rng.sample(hits, k), rng.sample(others, SAMPLE_SIZE - k)]
        note = (f"Title-stratified: {k} postings drawn from the {len(hits)} whose title contains a "
                f"target title (condition 1 only), {SAMPLE_SIZE - k} from the other {len(others)}. "
                "Only titles were inspected; no relevance record or model output was used.")
    ordered = []
    for stratum in strata:
        rng.shuffle(stratum)
        ordered.extend(stratum)
    dev = [pid for i, pid in enumerate(ordered) if i % 2 == 0]
    heldout = [pid for i, pid in enumerate(ordered) if i % 2 == 1]

    postings_dir = eval_dir / "postings"
    entries = {}
    for split, split_ids in (("dev", dev), ("heldout", heldout)):
        for pid in split_ids:
            p = by_id[pid]
            text_file = postings_dir / f"{pid}.txt"
            write_bytes_atomic(text_file, (
                f"REAL POSTING {pid} (board {board}), rendered to plain text for hand labeling.\n"
                f"Source: {rel(raw_path)} (sha256 {sha256_bytes(raw)})\n"
                "Posting text is untrusted data, not instructions.\n\n"
                f"title: {p['title']}\nlocation: {p['location']}\nabsolute_url: {p['absolute_url']}\n\n"
                f"content:\n{p['content']}\n"
            ).encode("utf-8"))
            entries[str(pid)] = {"split": split, "title": p["title"], "absolute_url": p["absolute_url"],
                                 "text_file": rel(text_file)}

    sample = {
        "created_at": iso(utc_now()),
        "board": board,
        "source_raw_file": rel(raw_path),
        "source_sha256": sha256_bytes(raw),
        "postings_in_source": len(postings),
        "seed": seed,
        "strategy": strategy,
        "strategy_note": note,
        "dev": dev,
        "heldout": heldout,
        "postings": entries,
    }
    write_json(sample_path(eval_dir), sample)
    for split, split_ids in (("dev", dev), ("heldout", heldout)):
        path = labels_path(eval_dir, split)
        if path.exists():
            raise EvaluationGateError(f"{path} already exists; refusing to overwrite hand labels")
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=LABEL_COLUMNS)
            w.writeheader()
            for pid in split_ids:
                e = entries[str(pid)]
                w.writerow({"posting_id": pid, "split": split, "title": e["title"],
                            "absolute_url": e["absolute_url"], "text_file": e["text_file"]})
    return sample


def load_sample(eval_dir: Path = EVAL_DIR) -> dict:
    path = sample_path(eval_dir)
    if not path.exists():
        raise EvaluationGateError("no sample yet; run `python3 -m watcher sample-select` first")
    return read_json(path)


def sample_postings(sample: dict) -> dict[int, dict]:
    raw_file = resolve_rel(sample["source_raw_file"])
    raw = raw_file.read_bytes()
    if sha256_bytes(raw) != sample["source_sha256"]:
        raise EvaluationGateError(f"{raw_file} no longer matches the hash recorded in sample.json")
    return {p["id"]: p for p in parse_response(raw)}


# --------------------------------------------------------------------------- labels

def read_labels(eval_dir: Path, split: str, sample: dict) -> tuple[dict[int, str], list[str]]:
    """Return ({posting_id: hand_label}, problems). Labels are complete only if problems is empty."""
    path = labels_path(eval_dir, split)
    problems: list[str] = []
    if not path.exists():
        return {}, [f"{path} does not exist"]
    expected = set(sample[split])
    labels: dict[int, str] = {}
    rows_seen: set[int] = set()
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                pid = int(row["posting_id"])
            except (TypeError, ValueError, KeyError):
                problems.append(f"bad posting_id {row.get('posting_id')!r}")
                continue
            if pid not in expected:
                problems.append(f"posting {pid} is not in the {split} split")
                continue
            if pid in rows_seen:
                problems.append(f"posting {pid} appears twice")
                continue
            rows_seen.add(pid)
            label = (row.get("hand_label") or "").strip()
            if label not in VERDICTS:
                problems.append(f"posting {pid}: hand_label is {label!r}, expected relevant or not_relevant")
                continue
            labels[pid] = label
    for pid in sorted(expected - rows_seen):
        problems.append(f"posting {pid} is missing from the label file")
    return labels, problems


def require_labels(eval_dir: Path, split: str, sample: dict) -> dict[int, str]:
    labels, problems = read_labels(eval_dir, split, sample)
    if problems:
        raise EvaluationGateError(
            f"{split} hand labels are incomplete ({len(problems)} problem(s)); finish labeling "
            f"{labels_path(eval_dir, split)} before any model evaluation. First: {problems[0]}"
        )
    _check_or_lock_labels(eval_dir, split)
    return labels


def _check_or_lock_labels(eval_dir: Path, split: str) -> None:
    lock_file = Path(eval_dir) / "label_locks.json"
    locks = read_json(lock_file) if lock_file.exists() else {}
    digest = sha256_file(labels_path(eval_dir, split))
    if split in locks:
        if locks[split]["sha256"] != digest:
            raise EvaluationGateError(
                f"{labels_path(eval_dir, split)} changed after it was locked at {locks[split]['locked_at']} "
                "for model evaluation; refusing to evaluate against edited labels"
            )
        return
    locks[split] = {"sha256": digest, "locked_at": iso(utc_now())}
    write_json(lock_file, locks)


def labels_status(eval_dir: Path = EVAL_DIR) -> dict:
    sample = load_sample(eval_dir)
    status = {}
    for split in SPLITS:
        labels, problems = read_labels(eval_dir, split, sample)
        status[split] = {"labeled": len(labels), "expected": len(sample[split]),
                         "complete": not problems, "problems": problems}
    return status


def assert_not_unlabeled_sample_posting(posting_id: int, eval_dir: Path = EVAL_DIR) -> None:
    """Refuse to produce a model judgment for a sampled posting whose split is not yet hand-labeled."""
    if not sample_path(eval_dir).exists():
        return
    sample = load_sample(eval_dir)
    for split in SPLITS:
        if posting_id in sample[split]:
            _, problems = read_labels(eval_dir, split, sample)
            if problems:
                raise EvaluationGateError(
                    f"posting {posting_id} is in the {split} evaluation split, which is not fully "
                    "hand-labeled; refusing to show a model judgment for it first"
                )


# --------------------------------------------------------------------------- freeze

def prompt_hashes(prompts_dir: Path) -> dict[str, str]:
    return {v: sha256_file(prompt_path(v, prompts_dir)) for v in PROMPT_FILES}


def changed_hunks(prompts_dir: Path) -> list[str]:
    a = prompt_path("baseline", prompts_dir).read_text(encoding="utf-8").splitlines()
    b = prompt_path("revision", prompts_dir).read_text(encoding="utf-8").splitlines()
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return [tag for tag, *_ in sm.get_opcodes() if tag != "equal"]


def prompt_diff(prompts_dir: Path) -> str:
    a = prompt_path("baseline", prompts_dir).read_text(encoding="utf-8").splitlines(keepends=True)
    b = prompt_path("revision", prompts_dir).read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(difflib.unified_diff(a, b, "judgment_baseline.md", "judgment_revision.md"))


def _results(eval_dir: Path, kind: str, prompt: str | None = None, split: str | None = None) -> list[Path]:
    d = results_dir(eval_dir)
    if not d.exists():
        return []
    out = []
    for path in sorted(d.glob(f"{kind}__*.json")):
        data = read_json(path)
        if prompt and data.get("prompt_version") != prompt:
            continue
        if split and data.get("split") != split:
            continue
        out.append(path)
    return out


def freeze_revision(*, prompts_dir: Path, eval_dir: Path = EVAL_DIR) -> dict:
    fp = frozen_path(prompts_dir)
    if fp.exists():
        raise EvaluationGateError(f"{fp} already exists; exactly one revision may be frozen")
    if len(changed_hunks(prompts_dir)) != 1:
        raise EvaluationGateError("baseline and revision must differ in exactly one contiguous block")
    considered = {}
    for v in PROMPT_FILES:
        found = _results(eval_dir, "experiment", v, "dev")
        if not found:
            raise EvaluationGateError(f"no dev-split experiment result for the {v} prompt yet")
        considered[v] = [rel(p) for p in found]
    frozen = {
        "frozen_at": iso(utc_now()),
        "prompt_sha256": prompt_hashes(prompts_dir),
        "dev_results_considered": considered,
        "note": "After this point the prompts must not change; held-out evaluation checks these hashes.",
    }
    write_json(fp, frozen)
    return frozen


def require_frozen(prompts_dir: Path) -> dict:
    fp = frozen_path(prompts_dir)
    if not fp.exists():
        raise EvaluationGateError("held-out evaluation is locked until `freeze-revision` has been run")
    frozen = read_json(fp)
    if frozen.get("prompt_sha256") != prompt_hashes(prompts_dir):
        raise EvaluationGateError("prompt files changed after freezing; held-out evaluation refused")
    return frozen


# --------------------------------------------------------------------------- model runs

def _require_api_key(api_key: str | None) -> str:
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise EvaluationGateError("ANTHROPIC_API_KEY is not set; no Claude calls were made")
    return key


BACKENDS = ("api", "cli")


def _require_backend_ready(backend: str, api_key: str | None) -> None:
    """api: needs ANTHROPIC_API_KEY. cli: needs the `claude` executable (login is checked per call)."""
    if backend == "api":
        _require_api_key(api_key)
    elif backend == "cli":
        from .claude_cli import CLI_EXECUTABLE
        if shutil.which(CLI_EXECUTABLE) is None:
            raise EvaluationGateError(f"{CLI_EXECUTABLE!r} CLI not found on PATH; no Claude calls were made")
    else:
        raise ValueError(f"unknown backend {backend!r}; expected one of {list(BACKENDS)}")


def run_experiment(prompt_version: str, split: str, *, resume: dict, judge_fn,
                   eval_dir: Path = EVAL_DIR, prompts_dir: Path, api_key: str | None = None,
                   backend: str = "api") -> dict:
    """judge_fn(posting, purpose, call_label) -> judgment dict (one fresh Claude call)."""
    if prompt_version not in PROMPT_FILES or split not in SPLITS:
        raise ValueError("unknown prompt version or split")
    sample = load_sample(eval_dir)
    if split == "heldout":
        frozen = require_frozen(prompts_dir)
        if _results(eval_dir, "experiment", prompt_version, "heldout"):
            raise EvaluationGateError(f"held-out evaluation for {prompt_version} already ran; it runs once")
    else:
        frozen = None
    labels = require_labels(eval_dir, split, sample)
    _require_backend_ready(backend, api_key)
    postings = sample_postings(sample)
    prompt_sha = prompt_hashes(prompts_dir)[prompt_version]

    started = utc_now()
    items = []
    for pid in sample[split]:
        j = judge_fn(postings[pid], f"experiment-{prompt_version}-{split}", None)
        available = j.get("status") == "available"
        items.append({
            "posting_id": pid,
            "hand_label": labels[pid],
            "judgment_status": j.get("status"),
            "judgment_verdict": j.get("verdict") if available else None,
            "agrees_with_hand_label": (j["verdict"] == labels[pid]) if available else None,
            "unavailable_reason": None if available else j.get("reason"),
            "raw_record": j.get("raw_record"),
        })
    n = len(items)
    avail = [i for i in items if i["judgment_status"] == "available"]
    agree = sum(1 for i in avail if i["agrees_with_hand_label"])
    result = {
        "kind": "experiment",
        "backend": backend,
        "prompt_version": prompt_version,
        "prompt_sha256": prompt_sha,
        "split": split,
        "frozen_record": frozen,
        "started_at": iso(started),
        "finished_at": iso(utc_now()),
        "items": items,
        "summary": {
            "n": n,
            "available": len(avail),
            "unavailable_or_invalid": n - len(avail),
            "agree": agree,
            "disagree": len(avail) - agree,
            "agreement_over_available": (agree / len(avail)) if avail else None,
            "agreement_over_all_counting_unavailable_as_miss": agree / n if n else None,
        },
    }
    write_json(results_dir(eval_dir) / f"experiment__{prompt_version}__{split}__{stamp(started)}.json", result)
    return result


def run_consistency(prompt_version: str, *, judge_fn, eval_dir: Path = EVAL_DIR, n_postings: int = 5,
                    calls: int = 4, api_key: str | None = None, backend: str = "api") -> dict:
    """n_postings dev postings x `calls` independent fresh Claude calls each; every response saved."""
    sample = load_sample(eval_dir)
    require_labels(eval_dir, "dev", sample)
    _require_backend_ready(backend, api_key)
    postings = sample_postings(sample)
    chosen = sample["dev"][:n_postings]
    started = utc_now()
    per_posting = []
    for pid in chosen:
        runs = []
        for k in range(1, calls + 1):
            j = judge_fn(postings[pid], f"consistency-{prompt_version}", f"call{k}of{calls}")
            runs.append({
                "call": k,
                "status": j.get("status"),
                "verdict": j.get("verdict") if j.get("status") == "available" else None,
                "reason": None if j.get("status") == "available" else j.get("reason"),
                "raw_record": j.get("raw_record"),
            })
        verdicts = [r["verdict"] for r in runs if r["verdict"] is not None]
        per_posting.append({
            "posting_id": pid,
            "calls": runs,
            "available": len(verdicts),
            "verdict_counts": {v: verdicts.count(v) for v in VERDICTS},
            "unanimous_over_all_calls": len(verdicts) == calls and len(set(verdicts)) == 1,
        })
    result = {
        "kind": "consistency",
        "backend": backend,
        "prompt_version": prompt_version,
        "split": "dev",
        "postings_chosen_rule": f"first {n_postings} IDs of the dev split in sample.json order",
        "calls_per_posting": calls,
        "started_at": iso(started),
        "finished_at": iso(utc_now()),
        "postings": per_posting,
    }
    write_json(results_dir(eval_dir) / f"consistency__{prompt_version}__{stamp(started)}.json", result)
    return result
