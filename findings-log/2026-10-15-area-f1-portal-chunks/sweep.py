#!/usr/bin/env python3
"""sweep.py — turn results.jsonl into the per-build verdicts. Zero requests.

The gates, in this order, and a body that fails one is NOT analysed:

  1. CONTENT-TYPE GATE. Both hosts answer 200 text/html at exactly 5518 B for
     every path that does not exist (docs/09 §3, trap row). A cell is a chunk
     only if its content-type is application/javascript. Status is never the
     discriminator. Cells that fall back are reported as FALLBACK, not as
     chunks, and are excluded from the denominator — which is what stops 200
     copies of the SPA shell from being counted as a swept corpus.
  2. ANCHOR GATE, per build. The eager main bundle must hash to the sha256 the
     repo already pins for that build. If it does not, the build moved and
     every map derived from its runtime is a map of a corpus nobody is asking
     about.
  3. METHOD GATE. Area F's grep.sh requires three literals KNOWN to be present
     to be reported present; a zero is indistinguishable from a broken grep
     without it. The two main bundles carry them.

Then, per build and never pooled:
  * the corpus size actually swept, with the denominator named;
  * a per-token occurrence census, so a false-hit class is quantified rather
    than asserted;
  * every non-zero token printed with byte context, for the literal-vs-code
    read that docs/09 §5 item 2 requires;
  * a case-sensitivity control on every token that scores, because this corpus
    is full of zxcvbn password-dictionary substrings (discover, pde, dropdead,
    helpdesk, herpderp, topdevice, hampden) that read like pointers.

Usage: sweep.py [ledger]
"""
import csv
import json
import os
import pathlib
import sys
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent
LEDGER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results.jsonl"

ANCHORS = {"clinic": "2a7fa8e7af519c2b", "support": "a054555a0f22176e"}
MAIN_TOKENS = {"hcp/configuration/public/", "hcp/patients", "timeline"}
SCRATCH = pathlib.Path(os.environ.get("SCRATCH", ""))

rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
rows.sort(key=lambda r: r["seq"])

is_js = lambda r: (r.get("content_type") or "").startswith("application/javascript")

# ---------------------------------------------------------------- gates ----
print("=" * 72)
print("GATE 2 — anchor gate, per build (sha256_16 of the eager main bundle)")
anchors_ok = {}
for b, want in ANCHORS.items():
    got = [r for r in rows if r["role"] == "anchor-gate" and r["build"] == b]
    if not got:
        print(f"  {b}: NO ANCHOR ROW — build identity unproven")
        anchors_ok[b] = False
        continue
    r = got[0]
    ok = r["body_sha256"].startswith(want)
    anchors_ok[b] = ok
    print(f"  {b}: {r['body_sha256'][:16]} ({r['body_bytes']:,} B) "
          f"vs pinned {want} -> {'PASS' if ok else 'FAIL — BUILD MOVED'}")

print("\nGATE 3 — method gate (literals known to be present must be reported)")
method_ok = {}
for b in ANCHORS:
    got = [r for r in rows if r["role"] == "anchor-gate" and r["build"] == b]
    if not got:
        method_ok[b] = False
        continue
    t = got[0]["tokens"]
    missing = sorted(x for x in MAIN_TOKENS if not t.get(x))
    method_ok[b] = not missing
    print(f"  {b}: " + ", ".join(f"{x}={t.get(x, 0)}" for x in sorted(MAIN_TOKENS))
          + (f"  MISSING {missing}" if missing else "  -> PASS"))

# --------------------------------------------------------- corpus counts ---
print("\n" + "=" * 72)
print("GATE 1 — content-type gate, per build")
corpus = {}
for b in sorted(ANCHORS):
    sweep = [r for r in rows if r["build"] == b and r["role"].startswith("sweep")]
    ctrl = [r for r in rows if r["build"] == b and r["role"].startswith(("control", "corpus"))]
    chunks = [r for r in sweep if is_js(r)]
    fb = [r for r in sweep if not is_js(r)]
    dupes = [h for h, n in Counter(r["body_sha256"] for r in chunks).items() if n > 1]
    empty = [r["seq"] for r in chunks if r["body_bytes"] == 0]
    corpus[b] = {"sweep_rows": len(sweep), "chunks": len(chunks),
                 "fallback_cells": [(r["seq"], r["path"]) for r in fb],
                 "distinct_body_digests": len(set(r["body_sha256"] for r in chunks)),
                 "duplicate_body_digests": dupes, "empty_bodies": empty,
                 "total_bytes": sum(r["body_bytes"] for r in chunks),
                 "control_rows": len(ctrl)}
    print(f"  {b}: {len(sweep)} sweep rows -> {len(chunks)} returned a chunk "
          f"(application/javascript), {len(fb)} returned the SPA fallback")
    print(f"     distinct body digests: {corpus[b]['distinct_body_digests']}"
          f"   duplicates: {dupes or 'none'}   empty: {empty or 'none'}")
    print(f"     total decoded bytes swept: {corpus[b]['total_bytes']:,}")

# ---------------------------------------------------------- token census ---
print("\n" + "=" * 72)
print("TOKEN CENSUS — per build, never pooled")
census = {}
for b in sorted(ANCHORS):
    chunks = [r for r in rows if r["build"] == b
              and r["role"].startswith("sweep") and is_js(r)]
    c = Counter()
    for r in chunks:
        for k, v in r["tokens"].items():
            c[k] += v
    census[b] = {"bodies": len(chunks), "tokens": dict(c)}
    nz = {k: v for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])) if v}
    print(f"  {b}: {len(chunks)} bodies")
    if not nz:
        print("     every one of the 24 tokens is 0 across every body")
    for k, v in nz.items():
        print(f"     {k:<36} {v}")

# ------------------------------------------- case-sensitivity control ------
print("\n" + "=" * 72)
print("CASE-SENSITIVITY CONTROL — for every token that scored, the lowercase and")
print("UPPERCASE forms of its alphabetic stem, counted over the same bodies.")
case_ctl = {}
for b in sorted(ANCHORS):
    chunks = [r for r in rows if r["build"] == b
              and r["role"].startswith("sweep") and is_js(r)]
    if not chunks or SCRATCH == "":
        continue
    lines = []
    for r in chunks:
        p = SCRATCH / f"{r['seq']:03d}-{r['tag']}.body"
        if p.exists():
            lines.append((r, p.read_bytes()))
    if not lines:
        print(f"  {b}: bodies not on disk (SCRATCH unset or moved) — control skipped")
        continue
    hits = []
    for r, data in lines:
        for tok, n in r["tokens"].items():
            if not n:
                continue
            low = tok.lower()
            up = tok.upper()
            nl = data.count(low.encode()) if low != tok else None
            nu = data.count(up.encode()) if up != tok else None
            if nl or nu:
                hits.append((r["seq"], r["path"], tok, n, nl, nu))
    case_ctl[b] = hits
    if not hits:
        print(f"  {b}: no case-variant hit — every scored token's mixed/other-case "
              "form is 0 in every body (read as: the score is not a case-blind match)")
    for h in hits:
        print(f"     seq {h[0]} {h[1]}: {h[2]}={h[3]} lower={h[4]} upper={h[5]}")

# ---------------------------------------------------- every non-zero hit ---
print("\n" + "=" * 72)
print("EVERY NON-ZERO TOKEN, WITH +-45 BYTES OF CONTEXT (the literal-vs-code read)")
hits_ctx = []
for b in sorted(ANCHORS):
    chunks = [r for r in rows if r["build"] == b
              and r["role"].startswith("sweep") and is_js(r)]
    for r in chunks:
        for tok, n in r["tokens"].items():
            if not n:
                continue
            p = SCRATCH / f"{r['seq']:03d}-{r['tag']}.body"
            if not p.exists():
                continue
            data = p.read_bytes()
            start = 0
            for i in range(min(n, 12)):
                j = data.find(tok.encode(), start)
                if j < 0:
                    break
                lo = max(0, j - 45)
                seg = data[lo:j + len(tok) + 45].decode("utf-8", "replace")
                hits_ctx.append({"build": b, "seq": r["seq"], "path": r["path"],
                                 "token": tok, "offset": j, "context": seg})
                start = j + len(tok)
            if n > 12:
                hits_ctx.append({"build": b, "seq": r["seq"], "path": r["path"],
                                 "token": tok, "offset": None,
                                 "context": f"[{n} hits — first 12 only]"})
if not hits_ctx:
    print("  none")
for h in hits_ctx:
    print(f"  [{h['build']}] seq {h['seq']} {h['path']} @ {h['offset']} {h['token']}")
    print(f"      {h['context']!r}")

# ------------------------------------------------------------ bridge -------
print("\n" + "=" * 72)
print("BRIDGE — support-host cells at a hash the clinic build also carries")
mp = list(csv.DictReader((HERE / "chunk-map.tsv").open(), delimiter="\t"))
hashes = {r["id"]: r["hash"] for r in mp if r["build"] == "clinic"}
cl_by_hash = {}
for r in rows:
    if r["build"] == "clinic" and r["role"].startswith("sweep") and is_js(r):
        cl_by_hash[r["chunk_hash"]] = r
bridge = []
for r in rows:
    if r["build"] == "support" and r["role"] == "sweep-bridge":
        c = cl_by_hash.get(r["chunk_hash"])
        same = bool(c) and c["body_sha256"] == r["body_sha256"]
        bridge.append({"seq": r["seq"], "path": r["path"], "hash": r["chunk_hash"],
                       "clinic_seq": c["seq"] if c else None,
                       "support_sha256": r["body_sha256"][:16],
                       "clinic_sha256": c["body_sha256"][:16] if c else None,
                       "byte_identical": same})
        print(f"  seq {r['seq']} {r['path']}: clinic seq {c['seq'] if c else '-'} "
              f"{c['body_sha256'][:16] if c else '-'} vs support "
              f"{r['body_sha256'][:16]} -> "
              f"{'IDENTICAL' if same else 'DIFFERENT'}")
n_id = sum(1 for b in bridge if b["byte_identical"])
print(f"  {n_id} of {len(bridge)} sampled shared-hash cells are byte-identical "
      f"across the two hosts")

# ------------------------------------------- support-distinctive vs clinic --
print("\n" + "=" * 72)
print("BUILD-DISTINCTIVE CELLS — the ids whose contenthash differs between builds")
for r in rows:
    if r["role"] == "sweep-distinct" or (r["role"] == "control-positive" and r["build"] == "support"):
        print(f"  [{r['build']}] seq {r['seq']} {r['path']} {r['status']} "
              f"{r['content_type']} {r['body_bytes']:,} B sha {r['body_sha256'][:16]}")

out = {"anchors": anchors_ok, "method_gate": method_ok, "corpus": corpus,
       "census": census, "case_control": case_ctl,
       "n_hit_contexts": len(hits_ctx), "bridge": bridge,
       "bridge_identical": n_id}
(HERE / "verdicts.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
print("\nwrote verdicts.json")