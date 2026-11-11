#!/usr/bin/env python3
"""Area AU — per-body census of the INSTINCT / model-mapping token set.

    census.py <body> <path>

Prints ONE JSON object on stdout:

    {"path":…, "bytes":n, "sha256":…,
     "counts":{label:{"cs":n,"ci":n,"q":n}},
     "hits":[{"token":…,"offset":n,"ident":…,"kind":"cs|ci","snippet":…}]}

WHY THREE COUNTS PER TOKEN (docs/09 §5 item 2). A case-sensitive count alone misses
`pDe` inside `propDecorators`; a case-insensitive count alone reports it as a hit. So
every token is counted three ways and every hit is recorded with its maximal enclosing
identifier, because that identifier is the only thing that tells a real directive from a
password-dictionary word or a camelCase coincidence.

WHY `7896[0-9]` AND NOT `7896` — measured, not preferred. A bare `7896` census over the
eager bundle returns 8 case-sensitive hits and **every one is an SVG path coordinate**:
`C151.607628,35.1487896` (8 occurrences, offsets 208163–210459). `7896[0-9]` returns 0
there, which is area AM's published figure. So the bare token is a coordinate fragment on
this corpus and a SKU-tail census on it must be the digit-anchored form. Both are counted
and both are reported, so the difference cannot be swallowed.

ZERO REQUESTS. Reads a body already on disk.
"""
import hashlib
import json
import re
import sys

# label -> regex. Anchored forms where a bare prefix would be a different question.
TOKENS = [
    ("7896",            r"7896"),
    # The SKU tail, anchored on BOTH sides of the digit run: a left `(?<![0-9])` stops
    # `1478963` (a zxcvbn dictionary entry) from matching as if it began at `7896`.
    ("7896[0-9]",       r"(?<![0-9])7896[0-9]"),
    ("SKU-",            r"SKU-"),
    ("productName",     r"productName"),
    ("marketingName",   r"marketingName"),
    ("Instinct",        r"Instinct"),
    ("model-mapping",   r"model-mapping"),
    ("modelMapping",    r"modelMapping"),
    ("ModelMapping",    r"ModelMapping"),
    ("deviceModelMapping", r"deviceModelMapping"),
    ("configuration/system", r"configuration/system"),
]

# Identifier alphabet: what can appear inside one JS token. `/` and `.` included
# because these bodies are full of paths and dotted property reads; `-` because the
# route literal itself is hyphenated.
IDENTCHAR = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_$.-/")


def enclosing_ident(body: bytes, pos: int, tok_len: int) -> str:
    start = pos
    while start > 0 and body[start - 1] in IDENTCHAR:
        start -= 1
    end = pos + tok_len
    while end < len(body) and body[end] in IDENTCHAR:
        end += 1
    return body[start:end].decode("utf-8", "replace")


def snippet(body: bytes, pos: int, width: int = 70) -> str:
    a = max(0, pos - width)
    b = min(len(body), pos + width)
    return body[a:b].decode("utf-8", "replace").replace("\n", "\\n").replace("\t", "\\t")


def main() -> int:
    body = open(sys.argv[1], "rb").read()
    path = sys.argv[2]
    out = {"path": path, "bytes": len(body),
           "sha256": hashlib.sha256(body).hexdigest(),
           "counts": {}, "hits": []}

    for label, pat in TOKENS:
        rb = pat.encode()
        cs = len(re.findall(rb, body))
        ci = len(re.findall(rb, body, re.IGNORECASE))
        q = len(re.findall(rb'["\']' + rb + rb'["\']', body))
        row = {"cs": cs, "ci": ci, "q": q}
        if label == "7896[0-9]":
            # Of the anchored hits, how many sit in a PURE DIGIT RUN? A SKU tail
            # never does: `SKU-78963-01` has hyphens, and a coordinate has a `.`.
            # A bare digit run is a password-list entry or a numeric literal, and
            # separating the two is what stops a dictionary match being read as a
            # device code — the false-hit class docs/09 §5 records.
            numeric = 0
            for m in re.finditer(rb, body):
                if enclosing_ident(body, m.start(), len(m.group(0))).isdigit():
                    numeric += 1
            row["in_pure_digit_run"] = numeric
            row["sku_like"] = cs - numeric
        out["counts"][label] = row

    # Every hit the case-INsensitive pass sees, with its identifier, so the
    # exclusion is visible rather than asserted. `hits` is capped per token so the
    # artefact stays small; a cap that bites is flagged in the row, never silent.
    for label, pat in TOKENS:
        rb = pat.encode()
        cs_starts = {m.start() for m in re.finditer(rb, body)}
        n = 0
        for m in re.finditer(rb, body, re.IGNORECASE):
            exact = m.start() in cs_starts
            out["hits"].append({
                "token": label,
                "offset": m.start(),
                "kind": "cs" if exact else "ci",
                "ident": enclosing_ident(body, m.start(), len(m.group(0))),
                "snippet": "" if exact else snippet(body, m.start()),
            })
            n += 1
            if n >= 300:
                out.setdefault("truncated", []).append(label)
                break

    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
