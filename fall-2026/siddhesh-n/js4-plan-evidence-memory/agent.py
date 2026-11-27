"""Replay two fictional board snapshots and verify claims before writing notes."""
import argparse
from datetime import date
import fcntl
import json
from pathlib import Path

from score import score

ROOT = Path(__file__).resolve().parent
FIELDS = ("title", "location", "authorization", "pay", "pay_unit")
WATCHERS = {"threshold-4": 4, "threshold-5": 5}


class StaleWrite(Exception):
    pass


def dump(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def read(path):
    return json.loads(path.read_text())


def load_snapshot(name, prior_ids):
    path = ROOT / "fixtures" / name
    def unique_object(pairs):
        values = dict(pairs)
        if len(values) != len(pairs):
            raise ValueError("Duplicate JSON key")
        return values

    snapshot = json.loads(path.read_text(), object_pairs_hook=unique_object)
    date.fromisoformat(snapshot["date"])
    board, direct = snapshot["board"], snapshot["direct"]
    if len(board) > 20 or not set(board) <= set(direct) <= set(board) | prior_ids:
        raise ValueError("Posting budget exceeded or direct-lookup coverage differs")
    if any(row["status"] not in (200, 404) for row in direct.values()):
        raise ValueError("Direct lookup status cannot substantiate liveness")
    return snapshot


def propose(posting_id, snapshot, prior):
    board_row = snapshot["board"].get(posting_id)
    values = {field: board_row[field] if board_row else None for field in FIELDS}
    return {
        "value": dict(values, live=True if board_row else (False if posting_id in snapshot["direct"] else None), new=board_row is not None and posting_id not in prior),
        "source": {
            "snapshot": f"fixtures/{snapshot['file']}",
            "date": snapshot["date"],
            "id": posting_id,
            "details": "board",
            "status_check": "direct" if posting_id in snapshot["direct"] else "no direct record",
            "prior_revision": snapshot["prior_version"],
            "newness": f"notes version {snapshot['prior_version']}",
            "mode": "fictional seeded replay",
        },
    }


def check(posting_id, proposal, snapshot, prior):
    source_row = snapshot["direct"].get(posting_id)
    expected_live = source_row["status"] == 200 if source_row else None
    value = proposal["value"]
    expected = {
        "live": expected_live,
        "new": expected_live is True and posting_id not in prior,
        **{field: source_row[field] if expected_live else None for field in FIELDS},
    }
    return [
        {"id": posting_id, "check": field, "expected": observed,
         "actual": value[field], "passed": value[field] == observed}
        for field, observed in expected.items()
    ]


def summary_check(claim, trace):
    expected = trace["pay"]
    return {"check": "summary-pay-vs-trace", "expected": expected,
            "actual": claim["pay"], "passed": claim["pay"] == expected}


def commit(path, expected_version, changes, watcher, entries):
    lock_path = path.with_suffix(".lock")
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read(path)
        if state["version"] != expected_version:
            raise StaleWrite(f"expected version {expected_version}, found {state['version']}")
        state["version"] += 1
        state["postings"].update(changes)
        state["watchers"][watcher] = entries
        temporary = path.with_suffix(".tmp")
        dump(temporary, state)
        temporary.replace(path)
        return state


def run(output, plan=None):
    if plan is None:
        plan = ROOT / "PLAN.md"
    if "Pending. Add the real reviewer" in plan.read_text():
        raise ValueError("Plan review must be recorded before running")
    output.mkdir()
    notes = output / "notes.json"
    dump(notes, {"version": 0, "postings": {}, "watchers": {}})
    previous_date = ""
    for day, filename in enumerate(("day1.json", "day2.json"), start=1):
        starting = read(notes)
        prior = starting["postings"]
        snapshot = load_snapshot(filename, set(prior))
        if snapshot["date"] <= previous_date:
            raise ValueError("Snapshot dates must strictly increase")
        previous_date = snapshot["date"]
        snapshot.update(file=filename, prior_version=starting["version"])
        changes = {
            key: propose(key, snapshot, prior)
            for key in sorted(set(snapshot["board"]) | set(prior))
        }
        checks = [
            result for key, claim in changes.items()
            for result in check(key, claim, snapshot, prior)
        ]
        dump(output / f"day{day}-checks.json", checks)
        if not all(result["passed"] for result in checks):
            raise ValueError("Evidence check failed. See saved check results.")
        if day == 1:
            trace_path = output / "verified-trace.json"
            dump(trace_path, changes["a"]["value"])
            trace = read(trace_path)
            summary = {"id": "a", "pay": changes["a"]["value"]["pay"]}
            baseline = summary_check(summary, trace)
            dump(output / "summary.json", {"claim": summary, "result": baseline})
            if not baseline["passed"]:
                raise RuntimeError("Baseline summary failed verification")
            claim = dict(summary, pay=99)
            result = summary_check(claim, trace)
            dump(output / "planted-error.json", {"trace": trace, "claim": claim, "result": result})
            if result["passed"]:
                raise RuntimeError("Planted error escaped verification")
        # The two watchers stage independently before either commits.
        staged = {}
        for watcher, threshold in WATCHERS.items():
            staged[watcher] = {
                key: {"description": row["description"],
                      "source": changes[key]["source"],
                      "threshold": threshold,
                      "result": score(row["title"], row["description"], threshold)}
                for key, row in snapshot["board"].items()
            }
        first, second = staged
        version = starting["version"]
        first_state = commit(notes, version, changes, first, staged[first])
        before = notes.read_bytes()
        dump(output / f"revision-{first_state['version']}.json", first_state)
        try:
            commit(notes, version, changes, second, staged[second])
        except StaleWrite as error:
            unchanged = notes.read_bytes() == before
            if not unchanged:
                raise RuntimeError("Stale write changed notes")
            actual_version = read(notes)["version"]
            final = commit(notes, actual_version, changes, second, staged[second])
            dump(output / f"day{day}-conflict.json", {
                "expected": version, "actual": actual_version,
                "error": str(error), "unchanged": unchanged,
                "after_merge": final["version"], "watchers": sorted(final["watchers"]),
            })
        else:
            raise RuntimeError("Stale write unexpectedly succeeded")
        dump(output / f"day{day}-state.json", final)
    earlier = read(output / "day1-state.json")
    later = read(output / "day2-state.json")
    added = sorted(set(later["postings"]) - set(earlier["postings"]))
    changed = {
        key: {"before": row, "after": later["postings"][key]}
        for key, row in earlier["postings"].items()
        if row["value"] != later["postings"][key]["value"]
    }
    dump(output / "diff.json", {
        "mode": "fictional seeded replay", "from_revision": earlier["version"],
        "to_revision": later["version"], "added": added, "changed": changed,
    })
    (output / "notes.lock").unlink()
    print(f"Seeded replay: notes revision {later['version']}, added={added}, changed={sorted(changed)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        run(args.output)
    except (OSError, ValueError, KeyError, RuntimeError, StaleWrite) as error:
        parser.exit(2, f"Stopped: {error}\n")
