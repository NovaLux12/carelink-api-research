#!/usr/bin/env python3
"""verify-absence.py — re-derive every ABSENT verdict from the committed block
bodies alone. Zero requests, zero network.

The defect this file exists for. The S-L1 `servedness.py` locate publishes
FAMILY_ABSENT when two ADJACENT `cluster.idx` keys straddle the interval. That
inference is invalid: `cluster.idx` carries one line per CDX *block*, keyed by
the block's first SURT key, so a straddling pair says the interval lies INSIDE
one block — which is exactly where a present family lives. On CC-MAIN-2022-27
the straddling pair was
    eu,mini-parfemy)/...  <  eu,minimed,carelink)/...  <  eu,minimumwaste)/...
and the block keyed `eu,mini-parfemy)` contains those records. The key-only
verdict was therefore FALSE.

A sound absence needs a RECORD-level straddle inside ONE block: the block's
first record must sort below FAM_LO, its last record must sort at or above
FAM_HI, and no record between them may be in the family. Sorted order then
makes the absence a proof, not an inference: the interval's immediate
neighbours are present and adjacent, and nothing lives between them.

This script re-reads the committed block bodies (in .loop/, never in the tree)
and asserts exactly that for each crawl. It prints a table and exits non-zero
if any claimed absence fails the test.

Usage: python3 verify-absence.py [bodies_dir]
"""
import json
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
FAM_LO = b"eu,minimed)"
FAM_HI = b"eu,minimeda"


def load(path):
    raw = open(path, "rb").read()
    return zlib.decompressobj(31).decompress(raw)


def rec_key(line):
    return line.split(b" ")[0]


def main():
    bodies = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("L_BODIES")
    if not bodies or not os.path.isdir(bodies):
        # Exit 3, not 2, and say NOT VERIFIED. The bodies live in .loop/ and are
        # never committed, so this is the DEFAULT state for anyone running this
        # from a clean checkout. "nothing to verify" reads as "nothing wrong" to a
        # human, and a caller testing `exit == 1` would take a silent no-op for a
        # successful verification. Three states must stay distinguishable:
        #   0 = verified (family present/absent as expected)
        #   1 = a verdict failed
        #   3 = could not run, so nothing was verified
        print("NOT VERIFIED: no bodies dir (bodies live in .loop/, never committed) - "
              "this run verified NOTHING; exit 3 means could-not-run, not pass")
        return 3
    conf = json.load(open(os.path.join(HERE, "confirm.json")))

    # block-read bodies are identified by their seq in the committed ledger: a
    # role, a host and a range, so the pairing is checkable and not positional.
    led = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl")) if l.strip()]
    by_crawl = {}
    for r in led:
        if r["role"] == "block-read" and r["http_status"] == "206":
            for c in conf:
                if "/%s/" % c in r["path"]:
                    by_crawl[c] = os.path.join(bodies, "%d-%s.body" % (r["seq"], r["attempt_tag"]))

    print("== verify-absence: every ABSENT verdict re-derived from committed bytes. "
          "0 requests.")
    fails = 0
    for crawl, o in conf.items():
        if o["state"] != "FAMILY_ABSENT":
            print("   %-18s %-14s (presence: not this file's question)" % (crawl, o["state"]))
            continue
        p = by_crawl.get(crawl)
        if not p or not os.path.exists(p):
            print("   %-18s NO BODY - absence is UNVERIFIED" % crawl)
            fails += 1
            continue
        recs = [l for l in load(p).split(b"\n") if l]
        if not recs:
            print("   %-18s EMPTY BLOCK - absence is UNVERIFIED" % crawl)
            fails += 1
            continue
        k0, k1 = rec_key(recs[0]), rec_key(recs[-1])
        fam = [r for r in recs if FAM_LO <= rec_key(r) < FAM_HI]
        below = k0 < FAM_LO
        above = k1 >= FAM_HI
        # the interval's immediate neighbours must both be present AND adjacent
        i = j = None
        for n in range(len(recs) - 1):
            a, b = rec_key(recs[n]), rec_key(recs[n + 1])
            if a < FAM_LO and b >= FAM_HI:
                i, j = a, b
                break
        adj = i is not None
        ok = below and above and not fam and adj
        print("   %-18s block %d records, keys %r..%r" % (crawl, len(recs), k0[:34], k1[:34]))
        print("      first < FAM_LO: %s | last >= FAM_HI: %s | family records: %d | "
              "adjacent straddle pair: %s" % (below, above, len(fam), adj))
        if i is not None and j is not None:
            print("      pair: %r  ->  %r" % (i[:48], j[:48]))
        print("      -> %s" % ("ABSENCE PROVEN at record level" if ok
                               else "ABSENCE NOT PROVEN - the key-only verdict does not survive"))
        if not ok:
            fails += 1
    print()
    if fails:
        print("   %d absence verdict(s) failed record-level verification." % fails)
        return 1
    print("   every ABSENT verdict is record-bracketed inside one block: sound.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
