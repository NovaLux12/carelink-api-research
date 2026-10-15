#!/usr/bin/env python3
"""diff-distinct.py — what actually differs between the two builds' 4
build-distinctive chunks. Zero requests; reads the transient bodies.

The two builds' maps differ in exactly 4 of 225 chunk ids (derive-map.py). This
script says how, so the "the two builds are two corpora" instruction is a
measurement rather than a precaution — and so the one cell where a support-host
fetch carries information a clinic-host fetch cannot is characterised rather
than merely labelled.

Counting rule for "the same file with a different build tag": a byte-level diff
is not attempted. Each pair is compared on (a) length, (b) sha256, and (c) the
token census of each body, and then the LONGEST COMMON PREFIX and SUFFIX are
reported, which is what distinguishes "the same source with one substituted
string" from "two different modules".
"""
import hashlib
import json
import os
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SCRATCH = pathlib.Path(os.environ["SCRATCH"])
TOKENS = json.loads((HERE / "token-census-template.json").read_text()) \
    if (HERE / "token-census-template.json").exists() else None

rows = [json.loads(l) for l in (HERE / "results.jsonl").read_text().splitlines() if l.strip()]
rows.sort(key=lambda r: r["seq"])

by_id = {}
for r in rows:
    if r.get("chunk_id") and r["chunk_id"] != "-":
        # A chunk id can appear on more than one ledger row — the support build's
        # id 2076 is fetched twice, once as the positive control under its
        # emitted name and once as the form-defect control under its id form.
        # Only the application/javascript row is the chunk; the other is the SPA
        # shell. Asserting that, rather than letting last-write-wins pick,
        # because a hash comparison over a lookup that returned the wrong row is
        # AGENTS.md §6 item 3 wearing a different hat.
        prev = by_id.setdefault(r["chunk_id"], {}).get(r["build"])
        is_js = (r.get("content_type") or "").startswith("application/javascript")
        if prev is None or (is_js and not (prev.get("content_type") or "")
                            .startswith("application/javascript")):
            by_id[r["chunk_id"]][r["build"]] = r

out = []
for cid in ("2076", "2873", "6831", "8285"):
    pair = by_id.get(cid, {})
    c, s = pair.get("clinic"), pair.get("support")
    entry = {"chunk_id": cid, "clinic_seq": c["seq"] if c else None,
             "support_seq": s["seq"] if s else None}
    if not (c and s):
        out.append(entry)
        continue
    cb = (SCRATCH / f"{c['seq']:03d}-{c['tag']}.body").read_bytes()
    sb = (SCRATCH / f"{s['seq']:03d}-{s['tag']}.body").read_bytes()
    p = 0
    while p < min(len(cb), len(sb)) and cb[p] == sb[p]:
        p += 1
    q = 0
    while q < min(len(cb), len(sb)) - p and cb[len(cb) - 1 - q] == sb[len(sb) - 1 - q]:
        q += 1
    entry.update({
        "clinic_bytes": len(cb), "support_bytes": len(sb),
        "length_delta": len(sb) - len(cb),
        "clinic_sha256_16": hashlib.sha256(cb).hexdigest()[:16],
        "support_sha256_16": hashlib.sha256(sb).hexdigest()[:16],
        "identical": cb == sb,
        "longest_common_prefix": p, "longest_common_suffix": q,
        "divergent_middle_bytes_clinic": len(cb) - p - q,
        "divergent_middle_bytes_support": len(sb) - p - q,
        "first_divergence_clinic": cb[p:p + 90].decode("utf-8", "replace"),
        "first_divergence_support": sb[p:p + 90].decode("utf-8", "replace"),
        "clinic_token_nonzero": {k: v for k, v in c["tokens"].items() if v},
        "support_token_nonzero": {k: v for k, v in s["tokens"].items() if v},
    })
    out.append(entry)

(HERE / "distinct-diff.json").write_text(json.dumps(out, indent=2) + "\n")
for e in out:
    print(f"--- chunk {e['chunk_id']} (clinic seq {e['clinic_seq']}, "
          f"support seq {e['support_seq']})")
    if "identical" not in e:
        print("    only one build's body was fetched"); continue
    print(f"    clinic {e['clinic_bytes']:,} B sha {e['clinic_sha256_16']} | "
          f"support {e['support_bytes']:,} B sha {e['support_sha256_16']} | "
          f"identical: {e['identical']}")
    print(f"    common prefix {e['longest_common_prefix']:,} B, "
          f"common suffix {e['longest_common_suffix']:,} B, "
          f"divergent middle {e['divergent_middle_bytes_clinic']:,} B (clinic) / "
          f"{e['divergent_middle_bytes_support']:,} B (support)")
    print(f"    clinic   @ {e['longest_common_prefix']}: {e['first_divergence_clinic']!r}")
    print(f"    support  @ {e['longest_common_prefix']}: {e['first_divergence_support']!r}")
    print(f"    tokens clinic : {e['clinic_token_nonzero'] or 'all zero'}")
    print(f"    tokens support: {e['support_token_nonzero'] or 'all zero'}")