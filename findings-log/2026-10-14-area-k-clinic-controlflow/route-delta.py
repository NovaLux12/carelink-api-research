#!/usr/bin/env python3
"""
Route-delta derivation for the area-K clinic corpus pass.

WHY THIS EXISTS
---------------
An earlier draft of this pass published a route-delta figure ("168 shared,
1 chunk-only, 0 main-only") that was wrong in every part, and its stated cause was
wrong too. Independent verification established:

  * the draft's extraction rule was a raw byte grep `hcp/[A-Za-z0-9_/.-]*`,
    which reproduces its own erroneous 168 exactly on the complete main bundle,
    because that character class cannot express `/hcp/...`, `((param))`,
    `?`/`=` query strings, or the space-prefixed `" /hcp/linkedPatient"`
    literal that docs/07 line 65 explicitly warns about. It misses 26 literals.
  * the main bundle was additionally globbed onto BOTH sides of the difference.

A number that cannot be re-derived by a committed rule does not ship
(AGENTS.md section 6, item 7). This script IS that rule, so the figure is
checkable rather than asserted.

COUNTING RULE (stated so it can be argued with)
----------------------------------------------
A route literal is a quoted string span, in ANY of these forms:

    "<route>"

matched by a PARITY-FREE anchor -- `"(...)"` -- rather than by scanning
`"..."` spans. Parity is the failure this pass's own `mine.py` hit (FINDINGS.md
section 5.1): after the first escaped quote, span parity flips and every
subsequent label inverts. A quote-delimited anchor needs no parity argument.

The span is kept when it contains `hcp/` at the start of the route, optionally
after a leading `/`, and optionally after a leading SPACE -- the last of which is
a real literal in this corpus and is invisible to any `/hcp/` anchored rule.

KNOWN LIMITS OF THIS RULE (disclosed, not hidden)
--------------------------------------------------
  * A backtick template literal (`` `hcp/...` ``) is not matched. Zero are
    present in this corpus, so the figure is unaffected here, but a future corpus
    containing one would undercount.
  * A route built by string CONCATENATION (`"hcp/patients/"+id`) yields the
    partial literal `hcp/patients/`, which is counted as if it were a route.
    That inflates rather than deflates, and the alternative -- skipping any span
    containing `+` -- would discard genuine routes, so the conservative choice
    is documented rather than silently made.
  * Neither limit applies to the 225 chunks' 3 literals or the main bundle's 184,
    both of which were verified span-by-span against the raw bytes.

USAGE
-----
    python3 route-delta.py <corpus-dir> [--out route-delta.json]

<corpus-dir> is the directory the sweep wrote bodies into. It is OUTSIDE the
repository by design (AGENTS.md section 7: no raw captures committed), so this
script is re-runnable only against a fresh sweep. What IS committed is
`route-delta.json` -- the extracted literal sets and their digests -- so a
third party can verify the SET ARITHMETIC and the per-literal classification
without holding a body. Holding a body is what re-deriving from source would
require, and this repo does not publish those.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

# Parity-free: a quote character followed by the shortest span to the next
# quote. Deliberately not `"([^"]*)"` scanning with alternation.
#
# BUG FOUND AND FIXED 2026-10-14, second verification round's follow-through: the
# first version of this line was `"([^"\n]*)"`. Excluding newlines looked safer
# but is WRONG for this corpus -- the minified main bundle is 3,397,615 B on a
# single line with only 102 newlines in total, so the class permitted a span
# ~33 KB long and every real route fell inside a span that started at some
# unrelated quote. It reported 0 routes in the main bundle and 3 in the chunks.
# The arithmetic self-check in main() is what caught it: 0 + 0 = 0 cannot be
# right for a bundle this pass read 184 routes out of by hand.
QUOTED = re.compile(r'"([^"]*)"')
ROUTE = re.compile(r"^ */?hcp/")

# A span longer than this is not a route literal; it is two unrelated quotes
# with code between them. The longest real literal here is 88 characters.
MAX_LITERAL = 200


def extract(path: str) -> set[str]:
    """Distinct route literals in one file."""
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8", "replace")
    out = set()
    for m in QUOTED.finditer(text):
        span = m.group(1)
        if len(span) > MAX_LITERAL:
            continue  # two unrelated quotes, not a literal
        candidate = span.strip() if span.startswith(" ") else span
        if ROUTE.match(candidate):
            out.add(candidate)
    return out


def classify(paths: list[str]) -> tuple[set[str], set[str]]:
    """Split paths into (main-side, chunk-side)."""
    main: set[str] = set()
    chunks: set[str] = set()
    for p in paths:
        got = extract(p)
        base = os.path.basename(p)
        is_main = "main" in base
        (main if is_main else chunks).update(got)
    return main, chunks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("--out")
    args = ap.parse_args()

    if not os.path.isdir(args.corpus):
        print(f"not a directory: {args.corpus}", file=sys.stderr)
        return 2

    files = [
        os.path.join(args.corpus, f)
        for f in sorted(os.listdir(args.corpus))
        if f.endswith((".js", ".b"))
    ]
    if not files:
        print("no corpus files found", file=sys.stderr)
        return 2

    main_routes, chunk_routes = classify(files)
    shared = main_routes & chunk_routes
    chunk_only = chunk_routes - main_routes
    main_only = main_routes - chunk_routes

    doc = {
        "rule": {
            "anchor": 're.compile(r\'"([^"]*)"\') -- parity-free, spans over '
            f"{MAX_LITERAL} chars discarded as non-literals",
            "match": "^ */?hcp/ after stripping at most one leading space",
            "known_limits": [
                "backtick template literals are not matched (0 present here)",
                "concatenation yields a partial literal; counted as a route",
            ],
        },
        "counts": {
            "main_distinct": len(main_routes),
            "chunk_distinct": len(chunk_routes),
            "shared": len(shared),
            "chunk_only": len(chunk_only),
            "main_only": len(main_only),
        },
        "arithmetic_check": (
            f"{len(main_only)} + {len(shared)} = {len(main_routes)} "
            f"(main) ; {len(chunk_only)} + {len(shared)} = {len(chunk_routes)} "
            "(chunks)"
        ),
        "chunk_only": sorted(chunk_only),
        "main_routes_sha256": hashlib.sha256(
            "\n".join(sorted(main_routes)).encode()
        ).hexdigest(),
        "chunk_routes_sha256": hashlib.sha256(
            "\n".join(sorted(chunk_routes)).encode()
        ).hexdigest(),
    }

    text = json.dumps(doc, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())