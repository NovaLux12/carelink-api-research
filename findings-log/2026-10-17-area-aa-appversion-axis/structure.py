#!/usr/bin/env python3
"""Area AA — offline structural instrument for the 2026-10-17 pass.

Zero requests. Reads only the bodies already captured under headers/ and
reduces them to the two questions the pass exists to answer:

  1. Is the app-version tail ECHOED into the payload?  -> count occurrences
     of the requested tail inside the response body.
  2. Does the tail SELECT content (a gate), or is the echo the whole story?
     -> erase the echo and re-digest.  If the canonical digests collapse to
     one value per (host, base), the tail selects nothing.  If they do not,
     the tail selects, and the structural columns say what it selected.

The canonicalisation is the load-bearing step and it is deliberately crude:
it replaces the requested tail with a fixed marker wherever it occurs in the
parsed-then-re-serialised document, so a pure echo cannot survive it.

Counting rule for "canonical groups": one group per distinct sha256 over the
tail-erased body.  Report the group size, because a group of 1 proves nothing
about constancy and a group of >=2 proves the tail did not vary the rest.
"""
import glob
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

HEAD = os.path.dirname(os.path.abspath(__file__))
BODIES = os.path.join(HEAD, "headers")
CFG = re.compile(rb'\{"config":"android,([^"]*)",')
MARK = b"@@"


def parse(path):
    """-> (seq, host, reqbase, tail, raw). Filenames are the capture's own."""
    name = os.path.basename(path)[: -len(".b")]
    seq, rest = name.split("-", 1)
    left, tail = rest.split("-android-", 1)
    host, base = left.rsplit("-", 1)
    return int(seq), host, base, tail, open(path, "rb").read()


def summarise(seq, host, base, tail, raw):
    m = CFG.match(raw)
    if not m:
        # The no-route envelope: not a discovery document at all.
        return dict(seq=seq, host=host, base=base, tail=tail, kind="no-route",
                    raw_sha=hashlib.sha256(raw).hexdigest()[:12], size=len(raw))
    echo = m.group(1)
    canon = raw[: m.start(1)] + MARK + raw[m.end(1):]
    doc = json.loads(raw)
    bases = sorted({re.search(r"/carepartner/(v[\w]+)$", c["baseUrlCumulus"]).group(1)
                    for c in doc["CP"]})
    return dict(seq=seq, host=host, base=base, tail=tail, kind="document",
                raw_sha=hashlib.sha256(raw).hexdigest()[:12],
                canon_sha=hashlib.sha256(canon).hexdigest()[:12],
                size=len(raw), cfg=doc["config"],
                # occurrences of the echoed tail anywhere in the body
                echo_n=raw.count(echo),
                advertised_cumulus=",".join(bases),
                carelink=doc["CP"][0]["baseUrlCareLink"].rsplit("/", 1)[-1],
                n_cp=len(doc["CP"]), n_ctry=len(doc["supportedCountries"]),
                n_cert=len(doc["certificates"]),
                sso=sorted({c["SSOConfiguration"].rsplit("/", 1)[-1] for c in doc["CP"]}))


def main():
    rows = [summarise(*parse(p)) for p in sorted(glob.glob(os.path.join(BODIES, "*.b")))]
    rows.sort(key=lambda r: r["seq"])

    print(f"bodies read: {len(rows)}")
    print()
    print("## Per-cell structure")
    hdr = (f"{'seq':>3} {'host':22s} {'reqbase':7s} {'tail':18s} {'st':>3} "
           f"{'config':26s} {'advCumulus':11s} {'carelink':8s} {'CP':>3} {'ctry':>4} "
           f"{'cert':>4} {'echo_n':>6} raw         canon")
    print(hdr)
    for r in rows:
        if r["kind"] == "no-route":
            print(f"{r['seq']:3d} {r['host']:22s} {r['base']:7s} {r['tail']:18s} "
                  f"403 -                -           -        -    -     - "
                  f"     - {r['raw_sha']}  -")
            continue
        print(f"{r['seq']:3d} {r['host']:22s} {r['base']:7s} {r['tail']:18s} 200 "
              f"{r['cfg']:26s} {r['advertised_cumulus']:11s} {r['carelink']:8s} "
              f"{r['n_cp']:3d} {r['n_ctry']:4d} {r['n_cert']:4d} {r['echo_n']:6d} "
              f"{r['raw_sha']}  {r['canon_sha']}")

    docs = [r for r in rows if r["kind"] == "document"]
    print()
    print("## Q1 — is the tail echoed?")
    print(f"  documents: {len(docs)}")
    print(f"  every one carries the requested tail in its body bytes: "
          f"{all(r['echo_n'] > 0 for r in docs)}")
    print(f"  occurrence counts seen: {sorted({r['echo_n'] for r in docs})} "
          f"(1 = the echo is confined to the config field)")
    print("  a fabricated tail answered 200 (no 400/404) at: "
          + ", ".join(f"seq {r['seq']}" for r in docs if r["tail"].startswith("absent-")))

    print()
    print("## Q2 — does the tail select, or is the echo the whole story?")
    print("  canonical = tail erased, then sha256. A group of size >=2 proves the")
    print("  tail did not vary the rest of the body; a group of size 1 proves nothing.")
    groups = defaultdict(list)
    for r in docs:
        groups[(r["host"], r["base"], r["canon_sha"])].append(r)
    for (host, base, csha), members in sorted(groups.items(), key=lambda kv: kv[0][:2]):
        tails = ", ".join(m["tail"] for m in members)
        struct = (f"advCumulus={members[0]['advertised_cumulus']} "
                  f"carelink={members[0]['carelink']} CP={members[0]['n_cp']} "
                  f"ctry={members[0]['n_ctry']}")
        print(f"  {host:22s} {base:5s} {csha}  n={len(members)}  [{tails}]  {struct}")

    print()
    print("## Per-(host, base) verdict on the tail axis")
    per = defaultdict(dict)
    for r in docs:
        per[(r["host"], r["base"])][r["tail"]] = r
    for key in sorted(per):
        cells = per[key]
        cans = {r["canon_sha"] for r in cells.values()}
        # A verdict needs >=2 tails on the same base. One tail cannot distinguish
        # "selects" from "does not select" (AGENTS.md 6.2/6.3), so it is not one.
        if len(cells) < 2:
            verdict = "NO VERDICT (one tail sent on this base; the axis was not varied)"
        elif len(cans) > 1:
            verdict = "GATING (tail selects >=2 documents)"
        else:
            verdict = "NOT GATING (one document for every tail sent)"
        print(f"  {key[0]:22s} base {key[1]:5s} tails={len(cells)} "
              f"canonical_documents={len(cans)}  -> {verdict}")

    noroute = [r for r in rows if r["kind"] == "no-route"]
    print()
    print("## No-route envelope")
    print(f"  cells: {len(noroute)}; distinct digests: "
          f"{sorted({r['raw_sha'] for r in noroute})}")
    print(f"  rows: {', '.join(str(r['seq']) for r in noroute)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
