"""Per-board seen-ID state. One file per board; written atomically."""

from __future__ import annotations

import json
from pathlib import Path

from .netguard import validate_board_token
from .util import write_json


class StateError(ValueError):
    """State file exists but is unreadable or malformed. Never treated as 'no state'."""


def state_path(state_dir: Path, board: str) -> Path:
    validate_board_token(board)
    return Path(state_dir) / f"{board}.json"


def load_state(state_dir: Path, board: str) -> dict | None:
    path = state_path(state_dir, board)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise StateError(f"cannot read state file {path}: {err}") from err
    if not isinstance(data, dict) or data.get("board") != board:
        raise StateError(f"state file {path} is not state for board {board!r}")
    ids = data.get("seen_ids")
    if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
        raise StateError(f"state file {path} has malformed seen_ids")
    return data


def save_state(state_dir: Path, board: str, seen_ids, *, updated_at: str, successful_runs: int) -> dict:
    state = {
        "board": board,
        "seen_ids": sorted(set(seen_ids)),
        "updated_at": updated_at,
        "successful_runs": successful_runs,
    }
    write_json(state_path(state_dir, board), state)
    return state
