#!/usr/bin/env python3
"""audit-index.py — host coverage for every probed (path, method) in the corpus.

WHY THIS EXISTS. Area Y asks how many "on all three hosts" claims in `docs/`
rest on a single row. To answer that, the audit needs the ground truth FIRST:
which hosts actually have a row for a given path and method. Reading that off
the prose would make the audit an echo of the claim it is checking.

This script builds that index from the raw ledgers, under **all three** storage
conventions area Z identified, and prints it. A single-convention query sees a
fraction of the corpus and its error is silent -- `corpus-audit.txt` §4 measures
that as 2 cells against 12.

Pure post-processing. It issues NO requests and touches no network.
Run:  python3 audit-index.py            # human-readable index
      python3 audit-index.py --coverage "connect/carepartner/v13/display/message"
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(ROOT, "findings-log")
assert os.path.isdir(LOG), "ROOT %r has no findings-log/" % ROOT

ORIGIN_LONG, ORIGIN_SHORT = "access_control_allow_origin", "acao"
HOSTLESS = "(no host column)"


def acao(row):
    for k in (ORIGIN_LONG, ORIGIN_SHORT):
        v = row.get(k)
        if v and v != "(none)":
            return v
    c = row.get("ctype") or ""
    m = "access-control-allow-origin:"
    if m in c:
        return re.split(r"\s+(?:access-control|x-cache|x-amzn|x-ca|\")",
                        c.split(m, 1)[1])[0].strip()
    return None


MATRIX = os.path.join(
    ROOT, "findings-log/probe-2026-10-08/recon/ORACLE-PROBE-MATRIX.md")

# The JSONL ledgers are not the whole corpus. ORACLE-PROBE-MATRIX is the
# repo's own "one-request-per-row log behind recon/VERSION-AXIS.md" and carries
# host evidence for cells no results.jsonl records -- v6/display/message GET is
# the clearest: zero rows in any ledger, three hosts in the matrix. An audit
# that read only the JSONL would call that claim unevidenced, which is wrong.
# Columns: # | namespace | host | ver | method | path tail | status | ...
MATRIX_COLS = {"n": 0, "host": 2, "ver": 3, "method": 4, "path": 5, "status": 6}


def load_matrix():
    """Return rows shaped like ledger rows: host/method/path/status."""
    out = []
    if not os.path.exists(MATRIX):
        return out
    with open(MATRIX, encoding="utf-8") as fh:
        for line in fh:
            if not re.match(r"^\|\s*\d+\s*\|", line):
                continue
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(cells) < 7:
                continue
            tail = cells[MATRIX_COLS["path"]].strip("`")
            ns = cells[1].strip("`")          # already includes "connect/", e.g.
                                              # "connect/carepartner" -- prefixing it
                                              # again is what made v11/v12/discover
                                              # look single-host on the first attempt.
            ver = cells[MATRIX_COLS["ver"]].strip("`")
            # Some rows carry the version in the path tail (`v6/display/message`),
            # others leave it to the `ver` column. The ONLY bare-tail row in the
            # matrix is #68: ns `connect/v2`, ver `v2`, tail `display/message` --
            # and there the namespace already encodes the version, so splicing ver
            # in again would mint `connect/v2/v2/display/message`. Emit BOTH
            # readings when ambiguous rather than guessing, so a claim can never be
            # marked unevidenced because this script guessed.
            variants = [f"{ns}/{tail}"]
            # Only splice `ver` in when the namespace does not ALREADY carry it.
            # Row #68 (ns `connect/v2`, ver `v2`) otherwise mints a junk
            # `connect/v2/v2/display/message` cell, which is not a vendor path.
            if (not re.match(r"^v\d+/", tail) and re.match(r"^v\d+$", ver)
                    and not ns.endswith("/" + ver)):
                variants.append(f"{ns}/{ver}/{tail}")
            for full in variants:
                out.append({
                    "_ledger": "probe-2026-10-08/recon/ORACLE-PROBE-MATRIX.md",
                    "_row": cells[0],
                    "host": cells[MATRIX_COLS["host"]],
                    "method": cells[MATRIX_COLS["method"]],
                    "path": full,
                    "http_status": re.sub(r"[*]", "", cells[MATRIX_COLS["status"]]),
                })
            continue
    return out


def load():
    ledgers = {}
    for dirpath, _d, files in os.walk(LOG):
        for f in files:
            if f != "results.jsonl":
                continue
            path = os.path.join(dirpath, f)
            name = os.path.basename(dirpath)
            rows = []
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        r = json.loads(line)
                        r["_ledger"] = name
                        rows.append(r)
            ledgers[name] = rows
    return ledgers


def build_index(ledgers):
    """(method, path) -> {host -> [(ledger, status, method)]}"""
    idx = defaultdict(lambda: defaultdict(list))
    for name, rows in ledgers.items():
        for r in rows:
            host = r.get("host") or HOSTLESS
            status = r.get("http_status") or r.get("status") or "?"
            status = re.sub(r"^HTTP/[\d.]+\s*", "", str(status)).strip()
            idx[(r.get("method"), r.get("path"))][host].append(
                (name, status, r.get("x_amzn_errortype_token")
                 or r.get("x_amzn_errortype") or "(none)"))
    return idx


REAL_HOSTS = ("clcloud.minimed.eu", "clcloud.minimed.com", "clcloud-trials.minimed.com",
              "carelink.minimed.eu", "carelink.minimed.com", "carelink-trials.minimed.com",
              "carelink.medtronic.com", "carelinkhp.minimed.eu")


def coverage(idx, path, method=None):
    """How many distinct REAL hosts have a row for this path?"""
    hits = set()
    for (m, p), hosts in idx.items():
        if p != path:
            continue
        if method and m != method:
            continue
        for h in hosts:
            if h in REAL_HOSTS:
                hits.add(h)
    return hits


def main():
    ledgers = load()
    idx = build_index(ledgers)

    # Merge the matrix BEFORE any lookup. An earlier version returned from the
    # --coverage branch first, so every coverage query was matrix-blind and
    # reported v11/v12 discover as single-host. The full-table printout was
    # built after the merge, so the two views disagreed and only a spot-check
    # caught it: a lookup path that silently answers from a smaller corpus than
    # the report beside it is the same "check that cannot fail" shape this
    # repository already holds corrections for.
    matrix = load_matrix()
    for r in matrix:
        idx[(r["method"], r["path"])][r["host"]].append(
            (r["_ledger"], r["http_status"], "(matrix)"))

    # Both views must read THIS index. Assert it rather than describing it: the
    # bug this replaced was the lookup returning from a smaller corpus than the
    # report printed beside it, and a comment saying "they agree" would not have
    # caught that a second time.
    if "--selftest" in sys.argv:
        # MUST be method-scoped. `coverage()` unions across methods when given no
        # method, and area Z's ledger already carries 12 OPTIONS rows for this path
        # on the same three hosts -- so a method-agnostic probe returns 3 whether or
        # not the matrix was merged, and the guard cannot fail. The GET row for this
        # cell exists ONLY in ORACLE-PROBE-MATRIX.md (zero GET rows in any ledger),
        # so scoping to GET makes the merge the only thing that can satisfy it.
        probe = "connect/carepartner/v6/display/message"
        n = len(coverage(idx, probe, "GET"))
        ok = (n == 3)
        print(f"selftest: GET {probe} -> {n} hosts (expect 3; matrix-only cell)")
        print(f"selftest: {'PASS' if ok else 'FAIL — the matrix merge is not reaching the lookup'}")
        return 0 if ok else 1

    if len(sys.argv) > 2 and sys.argv[1] == "--coverage":
        target = sys.argv[2]
        meth = sys.argv[3] if len(sys.argv) > 3 else None
        hits = coverage(idx, target, meth)
        print(f"{target} {meth or '(any method)'}")
        print(f"  distinct real hosts with a row: {len(hits)}")
        for h in sorted(hits):
            print(f"    {h}")
        if HOSTLESS in idx.get((meth, target), {}):
            print(f"    plus rows in a ledger with NO host column: "
                  f"{len(idx[(meth, target)][HOSTLESS])}")
        return 0

    print("HOST-COVERAGE INDEX — findings-log/**/results.jsonl + ORACLE-PROBE-MATRIX")
    print(f"ledgers read: {len(ledgers)}   matrix rows: {len(matrix)}   "
          f"distinct (method, path) cells: {len(idx)}")
    print()
    print("Legend: N = distinct REAL hosts with a row. 'no-host' = rows whose ledger")
    print("has no host column, so they cannot be attributed at all.")
    print()
    rows = []
    for (method, path), hosts in idx.items():
        real = {h for h in hosts if h in REAL_HOSTS}
        rows.append((len(real), method, path, sorted(real),
                     len(hosts.get(HOSTLESS, []))))
    def short(h):
        """clcloud.minimed.eu -> cc.eu ; clcloud-trials.minimed.com -> cc-tr.com"""
        if h == HOSTLESS:
            return "NO-HOST"
        return h.replace("clcloud-", "cc-").replace("clcloud.", "cc.").replace("carelink.", "cl.")

    for n, method, path, real, nh in sorted(rows, key=lambda x: (-x[0], x[2])):
        rows_txt = " ".join(sorted(short(h) for h in real)) or "-"
        print(f"  N={n}  {method:<8}{path[:52]:<52} [{rows_txt}]"
              + (f"  no-host:{nh}" if nh else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())