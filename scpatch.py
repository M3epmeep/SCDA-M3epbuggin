"""SCPD1 -- the binary delta format the SCDA CE patcher ships.

A patch turns one BASE byte string into one TARGET byte string. It exists so a
release carries the *difference* between a community member's own stock file and
our build, not a fresh copy of an 8 MB map. A modified `.sds` normally differs
from stock in a few hundred KB, so the delta is far smaller than the file -- and
a member's own shipped bytes never leave their disk.

Matching is rsync's: the base is indexed in aligned blocks by a rolling Adler-32
(weak, cheap to slide one byte at a time) confirmed by SHA-1 (strong). A hit is
then grown forward and backward byte-for-byte, so an edit that shifts the tail of
a file by three bytes still resyncs instead of re-sending the tail.

Stdlib only, on purpose: the community-facing exe must freeze with no wheels.

Container:  MAGIC | varint(len(header_json)) | header_json | zlib(op stream)
Ops:        0x01 COPY varint(base_offset) varint(length)
            0x02 LIT  varint(length) bytes
            0x00 END
"""

from __future__ import annotations

import hashlib
import json
import zlib

MAGIC = b"SCPD1\n"
BLOCK = 4096
MOD = 65521
CHUNK = 1 << 16

OP_END = 0
OP_COPY = 1
OP_LIT = 2


class PatchError(Exception):
    """A patch is malformed, or was applied to the wrong base."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- varint ---------------------------------------------------------------


def _put_varint(out: bytearray, n: int) -> None:
    if n < 0:
        raise ValueError("varint is unsigned")
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | 0x80 if n else b)
        if not n:
            return


def _get_varint(buf: bytes, pos: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise PatchError("truncated varint")
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not b & 0x80:
            return n, pos
        shift += 7
        if shift > 63:
            raise PatchError("varint too long")


# --- match growth ---------------------------------------------------------


def _grow_forward(base: bytes, bpos: int, target: bytes, tpos: int) -> int:
    """Bytes that agree from base[bpos:] and target[tpos:], compared in blocks."""
    grown = 0
    while True:
        step = min(CHUNK, len(base) - (bpos + grown), len(target) - (tpos + grown))
        if step <= 0:
            return grown
        bb = base[bpos + grown : bpos + grown + step]
        tb = target[tpos + grown : tpos + grown + step]
        if bb == tb:
            grown += step
            continue
        k = 0
        while bb[k] == tb[k]:
            k += 1
        return grown + k


def _grow_backward(base: bytes, bpos: int, target: bytes, tpos: int, limit: int) -> int:
    """Bytes that agree running backwards, capped at `limit` (the pending literal)."""
    grown = 0
    while grown < limit and bpos - grown > 0 and tpos - grown > 0:
        if base[bpos - grown - 1] != target[tpos - grown - 1]:
            break
        grown += 1
    return grown


# --- diff -----------------------------------------------------------------


def diff(base: bytes, target: bytes, block: int = BLOCK) -> bytes:
    """Build a patch carrying `base` to `target`."""
    index: dict[int, list[tuple[int, bytes]]] = {}
    for off in range(0, len(base) - block + 1, block):
        chunk = base[off : off + block]
        index.setdefault(zlib.adler32(chunk), []).append((off, hashlib.sha1(chunk).digest()))

    ops = bytearray()
    n = len(target)
    lit_start = 0
    i = 0

    if n >= block and index:
        window = zlib.adler32(target[0:block])
        a = window & 0xFFFF
        b = (window >> 16) & 0xFFFF
        while i + block <= n:
            hit = None
            candidates = index.get((b << 16) | a)
            if candidates:
                strong = hashlib.sha1(target[i : i + block]).digest()
                for off, digest in candidates:
                    if digest == strong:
                        hit = off
                        break
            if hit is not None:
                length = block + _grow_forward(base, hit + block, target, i + block)
                back = _grow_backward(base, hit, target, i, i - lit_start)
                if i - back > lit_start:
                    ops.append(OP_LIT)
                    _put_varint(ops, i - back - lit_start)
                    ops += target[lit_start : i - back]
                ops.append(OP_COPY)
                _put_varint(ops, hit - back)
                _put_varint(ops, length + back)
                i += length
                lit_start = i
                if i + block > n:
                    break
                window = zlib.adler32(target[i : i + block])
                a = window & 0xFFFF
                b = (window >> 16) & 0xFFFF
                continue
            if i + block >= n:
                break
            out_byte = target[i]
            in_byte = target[i + block]
            a = (a - out_byte + in_byte) % MOD
            b = (b + a - 1 - block * out_byte) % MOD
            i += 1

    if lit_start < n:
        ops.append(OP_LIT)
        _put_varint(ops, n - lit_start)
        ops += target[lit_start:]
    ops.append(OP_END)

    header = json.dumps(
        {
            "block": block,
            "base_sha256": sha256_bytes(base),
            "base_size": len(base),
            "target_sha256": sha256_bytes(target),
            "target_size": n,
        },
        sort_keys=True,
    ).encode("utf-8")

    out = bytearray(MAGIC)
    _put_varint(out, len(header))
    out += header
    out += zlib.compress(bytes(ops), 9)
    return bytes(out)


# --- apply ----------------------------------------------------------------


def read_header(patch: bytes) -> tuple[dict, int]:
    if not patch.startswith(MAGIC):
        raise PatchError("not an SCPD1 patch")
    size, pos = _get_varint(patch, len(MAGIC))
    header = json.loads(patch[pos : pos + size].decode("utf-8"))
    return header, pos + size


def apply(base: bytes, patch: bytes) -> bytes:
    """Apply `patch` to `base`, verifying both ends by hash."""
    header, pos = read_header(patch)
    if sha256_bytes(base) != header["base_sha256"]:
        raise PatchError("base file does not match the patch (wrong or already-modified source)")

    try:
        ops = zlib.decompress(patch[pos:])
    except zlib.error as exc:
        raise PatchError(f"corrupt patch payload: {exc}") from exc

    out = bytearray()
    i = 0
    while i < len(ops):
        op = ops[i]
        i += 1
        if op == OP_END:
            break
        if op == OP_COPY:
            off, i = _get_varint(ops, i)
            length, i = _get_varint(ops, i)
            if off + length > len(base):
                raise PatchError("copy runs past the end of the base file")
            out += base[off : off + length]
        elif op == OP_LIT:
            length, i = _get_varint(ops, i)
            if i + length > len(ops):
                raise PatchError("literal runs past the end of the op stream")
            out += ops[i : i + length]
            i += length
        else:
            raise PatchError(f"unknown op {op:#04x}")

    result = bytes(out)
    if len(result) != header["target_size"] or sha256_bytes(result) != header["target_sha256"]:
        raise PatchError("patched result does not match the expected hash")
    return result
