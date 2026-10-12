#!/usr/bin/env python3
"""corpus-audit.py — derive every corpus-shaped number the area Z docs cite.

WHY THIS EXISTS. Five figures appear in `docs/06` and `docs/11` about the shape
of the findings-log corpus: how many conventions it uses, how the ledgers
distribute across them, how many ACAO-bearing rows and cells it holds, and what
a single-convention query returns. Each was ASSERTED in prose before it was
derived, and three were wrong in successive review rounds — most recently
"two ledgers each", which held only if area Z's own ledger is counted, and the
counting rule four lines above excludes exactly that.

So: the numbers live here, they are printed by running this, and the docs cite
this. If a figure in the docs disagrees with this output, this output is right.

Pure post-processing. It issues NO requests and touches no network.
Run:  python3 corpus-audit.py
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

# findings-log/<this dir>/corpus-audit.py  ->  repo root is three levels up.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
assert os.path.isdir(os.path.join(ROOT, "findings-log")), (
    "ROOT resolved to %r, which has no findings-log/ -- the walk would silently "
    "find nothing and every figure below would print as 0." % ROOT)
LOG = os.path.join(ROOT, "findings-log")
SELF = "2026-10-12-area-z-origin-reflection"   # excluded; see SCOPE below

# SCOPE. The claims in docs/06 and docs/11 are about the corpus that existed
# BEFORE this pass. Area Z's own ledger is excluded throughout, and that
# exclusion is load-bearing: including it makes the short-key convention look
# like it has two ledgers when it has one.
EXCLUDE = {SELF}

SHORT_KEYS = ("acao", "acam")
LONG_KEYS = ("access_control_allow_origin", "access_control_allow_methods")


def convention(keys):
    """Which of the three storage conventions does this ledger use?"""
    if any(k in keys for k in LONG_KEYS):
        return "full-name key"
    if any(k in keys for k in SHORT_KEYS):
        return "short keys"
    if "ctype" in keys:
        return "embedded in the ctype string"
    return "no CORS value captured"


def acao_of(row):
    """Read ACAO under whichever convention this ledger uses."""
    for k in LONG_KEYS[:1] + SHORT_KEYS[:1]:          # long key first, then short
        v = row.get(k)
        if v and v != "(none)":
            return v
    c = row.get("ctype") or ""
    marker = "access-control-allow-origin:"
    if marker in c:
        tail = c.split(marker, 1)[1]
        return re.split(r"\s+(?:access-control|x-cache|x-amzn|x-ca|\")", tail)[0].strip()
    return None


def load():
    ledgers = {}
    for dirpath, _dirs, files in os.walk(LOG):
        for f in files:
            if f != "results.jsonl":
                continue
            path = os.path.join(dirpath, f)
            name = os.path.basename(dirpath)
            keys, rows = set(), []
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    keys |= set(r.keys())
                    rows.append(r)
            ledgers[name] = (keys, rows)
    return ledgers


def main():
    ledgers = load()
    pre = {k: v for k, v in ledgers.items() if k not in EXCLUDE}
    out = []
    w = out.append

    w("CORPUS AUDIT — the shape of findings-log/results.jsonl")
    w("Derived by corpus-audit.py. No request is issued by this script.")
    w(f"Scope: the {len(pre)} ledgers that pre-date area Z. "
      f"{len(EXCLUDE)} ledger(s) excluded by name: {sorted(EXCLUDE)}")
    w("")

    # 1. conventions -----------------------------------------------------------
    groups = defaultdict(list)
    for name, (keys, _rows) in pre.items():
        groups[convention(keys)].append(name)
    dist = sorted((len(v) for v in groups.values()), reverse=True)

    w("1. STORAGE CONVENTIONS FOR access-control-allow-origin")
    w(f"   {'convention':<30}{'ledgers':<9}which")
    for c in sorted(groups):
        w(f"   {c:<30}{len(groups[c]):<9}{', '.join(sorted(groups[c]))}")
    w("")
    w(f"   conventions = {len(groups)}   ledgers = {len(pre)}   distribution = {dist}")
    w(f"   -> state it as \"{len(groups)} conventions across {len(pre)} ledgers — "
      f"{' and '.join(str(d) for d in dist)}\".")
    w("   -> DO NOT write \"N ledgers each\": the distribution is NOT uniform.")
    w("")

    # 2. ACAO rows per ledger --------------------------------------------------
    acao_rows = []
    for name in sorted(pre):
        _keys, rows = pre[name]
        n = sum(1 for r in rows if acao_of(r))
        acao_rows.append((name, n))
    total_rows = sum(n for _n, n in acao_rows)

    w("2. ACAO-BEARING ROWS per ledger")
    for name, n in acao_rows:
        w(f"   {name:<34}{n}")
    w(f"   {'TOTAL':<34}{total_rows}")
    w("")

    # 3. rows -> cells ---------------------------------------------------------
    cells_hosted, cells_unattributable = set(), set()
    for name, (_keys, rows) in pre.items():
        for r in rows:
            if not acao_of(r):
                continue
            key = (r.get("host"), r.get("method"), r.get("path"))
            (cells_hosted if key[0] else cells_unattributable).add(key)
    total_cells = len(cells_hosted) + len(cells_unattributable)

    w("3. ROWS -> CELLS (deduplicate to host + method + route)")
    w(f"   ACAO-bearing rows                       {total_rows}")
    w(f"   distinct cells where host IS recorded   {len(cells_hosted)}")
    w(f"   distinct cells with NO host column      {len(cells_unattributable)}")
    w(f"   CELLS                                    {total_cells}")
    w("   -> the host-less rows each count as a cell; that is why the")
    w("      subtraction is smaller than the row count suggests.")
    w("")

    # 4. the single-convention query -------------------------------------------
    short_only = set()
    for _name, (_keys, rows) in pre.items():
        for r in rows:
            v = r.get("acao")
            if v and v != "(none)":
                short_only.add((r.get("host"), r.get("method"), r.get("path")))

    w("4. WHAT A SINGLE-CONVENTION QUERY RETURNS")
    w(f"   filtering on the short key `r.acao` alone -> {len(short_only)} cells")
    w(f"   all three conventions                    -> {total_cells} cells")
    w(f"   -> the under-count factor is {total_cells}/{len(short_only)} = "
      f"{total_cells/len(short_only):.0f}x, and it is SILENT.")
    w("")

    # 5. the under-report this causes ------------------------------------------
    w("5. WHICH ROUTES LOSE THEIR .eu EVIDENCE (the cost, not just the count)")
    hostless = set()
    for name, (keys, rows) in pre.items():
        if "host" in keys:
            continue
        for r in rows:
            if acao_of(r):
                hostless.add(r.get("path"))
    w(f"   ledgers with no `host` column: "
      f"{sorted(n for n, (k, _r) in pre.items() if 'host' not in k)}")
    w(f"   ACAO-bearing rows that cannot be attributed to any host: "
      f"{len(cells_unattributable)}")
    for p in sorted(hostless):
        w(f"      unattributable: {p}")
    w("")

    print("\n".join(out))
    # Non-zero exit if the docs' figures and this derivation ever disagree.
    ok = (len(groups) == 3 and len(pre) == 5 and dist == [2, 2, 1]
          and total_rows == 17 and total_cells == 12 and len(short_only) == 2)
    if not ok:
        print("MISMATCH: the derivation moved. Re-check the figures cited in "
              "docs/06 and docs/11 before trusting either.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())