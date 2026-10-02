"""Shared helpers for both halves of the patcher: hashing, paths, atomic writes.

Both the operator-side release builder and the community-side client import this,
so it stays stdlib-only and free of anything Windows-specific that would break a
release build on another machine.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile

MANIFEST_FORMAT = 1
BUNDLE_EXT = ".scdaupd"
READ_CHUNK = 1 << 20


def norm(rel: str) -> str:
    """Manifest paths are forward-slashed and relative to the install root."""
    return rel.replace("\\", "/").strip("/")


def local(root: str, rel: str) -> str:
    return os.path.join(root, *norm(rel).split("/"))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(READ_CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_file(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def atomic_write(path: str, data: bytes) -> None:
    """Temp file + rename, so an interrupted write can never leave half a file."""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix=".scda-tmp-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, obj: dict) -> None:
    atomic_write(path, json.dumps(obj, indent=2, sort_keys=False).encode("utf-8"))


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024 or unit == "GB":
            return f"{n:,.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} GB"
