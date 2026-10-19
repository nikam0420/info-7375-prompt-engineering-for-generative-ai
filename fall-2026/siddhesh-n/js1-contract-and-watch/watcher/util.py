"""Small shared helpers: UTC timestamps, hashing, atomic JSON writes."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import ROOT


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    """ISO-8601 UTC with microseconds, e.g. 2026-10-18T15:45:12.123456Z."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def stamp(dt: datetime) -> str:
    """Filesystem-safe UTC stamp, e.g. 20261018T154512_123456Z."""
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def write_bytes_atomic(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_json(path: Path, obj) -> None:
    text = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    write_bytes_atomic(path, text.encode("utf-8"))


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def unique_dir(parent: Path, name: str) -> Path:
    """Create and return parent/name, appending -2, -3, ... if it already exists."""
    parent = Path(parent)
    parent.mkdir(parents=True, exist_ok=True)
    candidate = parent / name
    n = 1
    while True:
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            n += 1
            candidate = parent / f"{name}-{n}"


def rel(path) -> str:
    """Path relative to the project root when inside it (keeps records portable across clones)."""
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_rel(path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p
