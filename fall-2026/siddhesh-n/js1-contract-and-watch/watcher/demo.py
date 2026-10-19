"""Reproducible seeded two-run demonstration from a real fetched response.

prepare: withhold k seeded-random postings from a saved real response and
write a reduced snapshot labeled CONSTRUCTED SEEDED BASELINE. The original
response file is never modified (its hash is checked before and after).

run: on fresh demo state, run 1 replays the constructed baseline (reports zero
new); run 2 replays the unmodified real response (reports the withheld IDs as
new). The difference between the two runs was constructed, not observed.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from . import ROOT
from .postings import decode_json_bytes, parse_response
from .util import iso, read_json, rel, resolve_rel, sha256_bytes, sha256_file, utc_now, write_bytes_atomic, write_json
from .watch import run_watch

DEMO_ROOT = ROOT / "demo"
CONSTRUCTED_LABEL = "CONSTRUCTED SEEDED BASELINE"


def demo_dir_for(board: str, demo_root: Path = DEMO_ROOT) -> Path:
    return Path(demo_root) / board


def prepare_demo(raw_path: Path, board: str, *, withhold: int, seed: int, demo_root: Path = DEMO_ROOT) -> dict:
    raw_path = Path(raw_path)
    raw = raw_path.read_bytes()
    original_sha = sha256_bytes(raw)
    postings = parse_response(raw)  # validates the complete response
    if not 1 <= withhold < len(postings):
        raise ValueError(f"withhold must be between 1 and {len(postings) - 1}")
    ddir = demo_dir_for(board, demo_root)
    if (ddir / "manifest.json").exists():
        raise FileExistsError(f"{ddir / 'manifest.json'} exists; remove the demo directory to re-prepare")

    rng = random.Random(seed)
    withheld = sorted(rng.sample(sorted(p["id"] for p in postings), withhold))
    data = decode_json_bytes(raw)
    reduced = {k: v for k, v in data.items() if k != "jobs"}
    reduced["jobs"] = [j for j in data["jobs"] if j["id"] not in set(withheld)]

    fetch_meta_path = raw_path.parent / "fetch_meta.json"
    fetch_meta = read_json(fetch_meta_path) if fetch_meta_path.exists() else None
    label = {
        "label": CONSTRUCTED_LABEL,
        "statement": (
            f"This file was constructed from a real response by removing {withhold} postings chosen "
            f"with random.Random({seed}). Its difference from the full response was constructed for "
            "the demonstration and did not happen naturally on the job board. All other fields, "
            "including any 'meta' totals, are copied unchanged from the original."
        ),
        "original_file": rel(raw_path),
        "original_sha256": original_sha,
        "withheld_ids": withheld,
        "seed": seed,
    }
    reduced = {"_constructed_seeded_baseline": label, **reduced}
    reduced_path = ddir / "constructed_seeded_baseline.json"
    write_bytes_atomic(reduced_path, (json.dumps(reduced, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))

    if sha256_file(raw_path) != original_sha:
        raise RuntimeError("original response changed during preparation")
    manifest = {
        "prepared_at": iso(utc_now()),
        "board": board,
        "original_response": rel(raw_path),
        "original_sha256": original_sha,
        "original_retrieval": fetch_meta,
        "original_posting_count": len(postings),
        "constructed_seeded_baseline": rel(reduced_path),
        "constructed_seeded_baseline_sha256": sha256_file(reduced_path),
        "constructed_posting_count": len(postings) - withhold,
        "seed": seed,
        "withheld_ids": withheld,
        "label": CONSTRUCTED_LABEL,
    }
    write_json(ddir / "manifest.json", manifest)
    return manifest


def run_demo(board: str, resume: dict, *, demo_root: Path = DEMO_ROOT, judge=None) -> dict:
    ddir = demo_dir_for(board, demo_root)
    manifest = read_json(ddir / "manifest.json")
    state_dir = ddir / "state"
    if state_dir.exists() and any(state_dir.iterdir()):
        raise FileExistsError(f"{state_dir} already has state; the demo must start from empty state")
    original = resolve_rel(manifest["original_response"])
    reduced = resolve_rel(manifest["constructed_seeded_baseline"])
    if sha256_file(original) != manifest["original_sha256"]:
        raise RuntimeError("original response no longer matches its recorded hash")
    if sha256_file(reduced) != manifest["constructed_seeded_baseline_sha256"]:
        raise RuntimeError("constructed baseline no longer matches its recorded hash")

    retrieved = (manifest.get("original_retrieval") or {}).get("response_finished_at", "unknown time")
    run1 = run_watch(
        board, resume, state_dir=state_dir, evidence_dir=ddir / "runs", replay_path=reduced,
        replay_label=(f"{CONSTRUCTED_LABEL}: reduced snapshot of the real response "
                      f"(sha256 {manifest['original_sha256']}) with {len(manifest['withheld_ids'])} postings "
                      f"withheld using seed {manifest['seed']}. Constructed, not observed."),
        judge=judge,
    )
    run2 = run_watch(
        board, resume, state_dir=state_dir, evidence_dir=ddir / "runs", replay_path=original,
        replay_label=f"Replay of the unmodified real response retrieved at {retrieved}.",
        judge=judge,
    )
    reported_new = [e["posting_id"] for e in run2.get("new_postings", [])]
    checks = {
        "run1_is_baseline_with_zero_new": run1["status"] == "baseline_saved" and run1["new_count"] == 0,
        "run2_new_ids_equal_withheld_ids": sorted(reported_new) == manifest["withheld_ids"],
        "original_unchanged": sha256_file(original) == manifest["original_sha256"],
    }
    result = {
        "label": f"{CONSTRUCTED_LABEL} demonstration — the run-1/run-2 difference was constructed by withholding postings",
        "ran_at": iso(utc_now()),
        "board": board,
        "run1": {"status": run1["status"], "new_count": run1.get("new_count"), "evidence": run1["evidence_dir"]},
        "run2": {"status": run2["status"], "new_count": run2.get("new_count"), "new_ids": reported_new,
                 "evidence": run2["evidence_dir"]},
        "withheld_ids": manifest["withheld_ids"],
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }
    write_json(ddir / "DEMO-RESULT.json", result)
    return result
