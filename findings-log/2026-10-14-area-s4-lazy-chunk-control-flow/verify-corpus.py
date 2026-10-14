#!/usr/bin/env python3
"""Area S4 — verify a chunk-body corpus against the committed capture ledger.

WHY THIS EXISTS. A continuation pass built its entire offset table from a
corpus directory that turned out to hold ONE corrupt body: `k-6746-…-js.b` at
101,595 bytes with a spurious leading `X`, where the captured body is 101,594
bytes with no `X`. Every byte offset quoted from that chunk was consequently
off by exactly +1, and none of it was visible locally. An independent verifier
found it by comparing against a different copy on disk. The pass's own manifest
digest had enshrined the corrupt file, so the identity oracle could not catch it.

The fix is not "be careful". It is that the authoritative digests are ALREADY
COMMITTED, one per body, in
`findings-log/2026-10-13-area-k-patient-chunks/results.jsonl` (`body_sha256`,
`body_bytes`) — 215 rows from the 2026-10-13 GET sweep. So the corpus is
checkable without trusting any copy on disk.

Usage:
    python3 verify-corpus.py <corpus-dir>

Exit 0 = every body matches the ledger. Exit 1 = at least one does not, and the
mismatching files are named. Pure string analysis; zero requests.
"""
import hashlib
import json
import os
import sys

LEDGER = os.path.join("findings-log", "2026-10-13-area-k-patient-chunks",
                      "results.jsonl")


def load_ledger(path=LEDGER):
    """tag -> (bytes, sha256) for every captured body."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            tag = d.get("host_tag", "")
            if tag.startswith("k-") and d.get("body_sha256"):
                out[tag] = (int(d["body_bytes"]), d["body_sha256"])
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    corpus = sys.argv[1]
    if not os.path.isdir(corpus):
        sys.exit("no such corpus directory: %s" % corpus)
    ledger = load_ledger()

    present = sorted(f for f in os.listdir(corpus) if f.endswith(".b"))
    matched, mismatched, absent = [], [], []
    for f in present:
        tag = f[:-2]
        blob = open(os.path.join(corpus, f), "rb").read()
        want = ledger.get(tag)
        if want is None:
            absent.append(f)
            continue
        size, sha = want
        if len(blob) == size and hashlib.sha256(blob).hexdigest() == sha:
            matched.append(f)
        else:
            mismatched.append((f, len(blob), size,
                               hashlib.sha256(blob).hexdigest()[:16], sha[:16]))

    missing = sorted(set(ledger) - {f[:-2] for f in present})

    # The identity oracle the findings quote: sha256 over the "<sha256>  "
    # manifest joined with newlines and NO trailing newline. This MUST match
    # extract-call-sites.py byte for byte, or the pass ends up quoting two
    # different "manifest digests" for one corpus — which is the same class of
    # defect this script exists to prevent. Filename order, not hash order.
    manifest = ["%s  %s" % (hashlib.sha256(
        open(os.path.join(corpus, f), "rb").read()).hexdigest(), f)
        for f in sorted(present)]
    oracle = hashlib.sha256("\n".join(manifest).encode()).hexdigest()

    print("corpus:        %s" % corpus)
    print("bodies:        %d" % len(present))
    print("ledger rows:   %d" % len(ledger))
    print("matched:       %d" % len(matched))
    print("MISMATCHED:    %d" % len(mismatched))
    for f, got, want, gs, ws in mismatched:
        print("    %s\n        got  %d bytes  %s…\n        want %d bytes  %s…"
              % (f, got, gs, want, ws))
    print("not in ledger: %d" % len(absent))
    for f in absent:
        print("    %s" % f)
    print("missing:       %d" % len(missing))
    for t in missing:
        print("    %s.b" % t)
    print("total bytes:   %d" % sum(
        os.path.getsize(os.path.join(corpus, f)) for f in present))
    print("manifest sha256: %s" % oracle)

    return 1 if (mismatched or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
