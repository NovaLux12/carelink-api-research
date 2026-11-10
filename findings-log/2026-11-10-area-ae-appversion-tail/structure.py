#!/usr/bin/env python3
"""Area AE — offline structural instrument, pass of 2026-11-10.

Zero requests.  Reads the ledger's bounded projection (results.jsonl), which
already carries what this pass needs: the raw body digests and the
tail-erased digests, computed at send time by probe.sh on the transient body.
Nothing here reads a body: no body is committed (AGENTS.md §7).

The question is not the status line.  AA recorded the trap: every 200 echoes
the requested tail into the body's `config` field, so the status alone is
constant across the whole ladder.  The discriminator is the tail-erased
digest — the document with the echo removed.

Counting rule for a "document class": one class per distinct
`erased_config_sha256`.  A class of size 1 proves nothing about constancy;
only a class of size >=2 is cited as evidence that the tail did not vary the
rest of the body.

The table-versus-threshold test is a statement over the ORDERING of classes
along the numeric ladder:

  * two classes, split at a single point  -> a threshold is sufficient
    (INFERRED; the boundary is bracketed to one gap, not measured exactly)
  * three or more classes, or a class that is not contiguous in the ladder
    -> no single threshold fits; the rule is a table keyed on the string
  * one class -> the tail does not select inside (3.6,3.9) at all
"""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "results.jsonl")


def load():
    rows = []
    with open(LEDGER) as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    rows.sort(key=lambda r: r["seq"])
    return rows


def main():
    rows = load()
    print(f"ledger rows: {len(rows)}")
    print()
    print("## Per-cell")
    hdr = (f"{'seq':>3} {'host':26s} {'base':4s} {'tail':6s} {'role':15s} "
           f"{'st':>3} {'bytes':>6} {'echo':>5} {'class':14s} {'structure'}")
    print(hdr)
    for r in rows:
        st = r.get("structure") or {}
        cls = (r.get("erased_config_sha256") or "-")[:12]
        struct = ("advCumulus=%s carelink=%s CP=%s ctry=%s sso=%s" % (
            st.get("adv_cumulus"), st.get("carelink"), st.get("n_cp"),
            st.get("n_ctry"), ",".join(st.get("sso") or []))) if st else "-"
        print(f"{r['seq']:3d} {r['host']:26s} {r['base']:4s} {r['appver']:6s} "
              f"{r['role']:15s} {r['status']:3d} {r['bytes']:6d} "
              f"{r.get('echo_n', 0):5d} {cls:14s} {struct}")

    print()
    print("## Classes, per (host, base)")
    groups = defaultdict(list)
    for r in rows:
        if r.get("erased_config_sha256"):
            groups[(r["host"], r["base"])].append(r)
    verdicts = {}
    for key in sorted(groups):
        cells = groups[key]
        by_class = defaultdict(list)
        for c in cells:
            by_class[c["erased_config_sha256"]].append(c["appver"])
        print(f"  {key[0]} base {key[1]}: {len(cells)} cells, "
              f"{len(by_class)} distinct class(es)")
        for csha, tails in by_class.items():
            print(f"    {csha[:12]}  n={len(tails)}  tails=[{', '.join(tails)}]")
        # ordering test on the numeric ladder
        num = [(float(c["appver"]), c["erased_config_sha256"]) for c in cells
               if c["appver"].replace(".", "", 1).isdigit()]
        num.sort()
        seen = []
        for _, csha in num:
            if not seen or seen[-1] != csha:
                seen.append(csha)
        contiguous = len(seen) == len(set(csha for _, csha in num))
        if len(by_class) == 1:
            verdicts[key] = "ONE CLASS (tail selects nothing in the swept range)"
        elif len(by_class) == 2 and contiguous:
            verdicts[key] = ("TWO CLASSES, CONTIGUOUS (a threshold is sufficient; "
                             "boundary bracketed, not measured)")
        else:
            verdicts[key] = ("NOT A SINGLE THRESHOLD (classes: %d, contiguous=%s) "
                             "-> table" % (len(by_class), contiguous))
        print(f"    -> {verdicts[key]}")

    print()
    print("## Controls")
    for r in rows:
        if r["role"].startswith("control"):
            print(f"  seq {r['seq']} {r['host']} {r['base']}/{r['appver']} "
                  f"{r['role']}: {r['status']} "
                  f"{r['content_type'] or '-'} {r['bytes']}B "
                  f"{r.get('x_amzn_errortype') or ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
