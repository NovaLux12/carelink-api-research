#!/usr/bin/env python3
"""derive-map.py — re-derive each build's lazy-chunk map from its OWN live
runtime `f.u`. Zero requests: it reads the two runtime bodies the phase-1
ledger already fetched (seq 3 clinic, seq 8 support) out of the caller's
scratch directory.

WHY THIS EXISTS RATHER THAN A COMMITTED LIST. docs/09 §4, trap row 3:
"a committed filename list is not a URL list … re-derive the filenames from the
runtime's f.u and diff by HASH, not by name. The hash is the join key; the name
is what moved." Area K measured the same special case in the PATIENT build and
area K-pool measured it in the CLINIC build (`(2076===e?"common":e)`), and the
two builds' runtimes have different names and different digests, so the
substitution state of one says nothing about the other until it is read.

WHAT IT DOES NOT ASSUME:
  * that the ternary exists at all on either build — it is matched out of the
    source and the answer recorded either way;
  * that the two builds share a map — they are parsed independently and only
    compared afterwards;
  * that a name diff means anything — the join is on the hash.

OUTPUT: chunk-map.json, chunk-map.tsv (id, name, hash, url, build), and a
map-diff.json holding the by-hash comparison against the committed clinic list.
"""
import hashlib
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRATCH = pathlib.Path(os.environ["SCRATCH"])

# sha256 anchors the repo already pins for the two main bundles. They gate the
# build identity: a runtime body whose host serves a different build would
# still parse, and its map would be a map of the wrong corpus.
BUILD_ANCHORS = {
    "clinic": ("2a7fa8e7af519c2b", "main.fb5f8cb7eb60c4d5.js"),
    "support": ("a054555a0f22176e", "main.759cddab23085086.js"),
}

BODIES = {"clinic": "003-eu-runtime.body", "support": "008-sup-runtime.body"}

# f.u looks like:  e => (2076===e?"common":e) + "." + {12:"cfb2…",…}[e] + ".js"
TERMINAL = re.compile(
    r'(\d+)\s*===\s*e\s*\?\s*"([^"]*)"\s*:\s*e')          # the name substitution
FU = re.compile(r'f\.u\s*=\s*e\s*=>\s*(.+?),\s*f\.miniCssF')
ENTRY = re.compile(r'(\d+)\s*:\s*"([0-9a-f]{8,40})"')


def parse(body: bytes, build: str):
    text = body.decode("utf-8", "replace")
    m = FU.search(text)
    if not m:
        # The fallback pattern: whatever f.u's body is, find the assignment.
        m = re.search(r'f\.u\s*=\s*e\s*=>\s*([^\n]{0,4000}?)\.js"', text)
    if not m:
        raise SystemExit(f"{build}: no f.u assignment found in the runtime body")
    expr = m.group(1)
    sub = TERMINAL.search(expr)
    special = None
    if sub:
        special = {"id": sub.group(1), "name": sub.group(2)}
        expr = expr[:sub.start()] + expr[sub.end():]        # drop the ternary
    pairs = ENTRY.findall(expr)
    entries = {cid: h for cid, h in pairs}
    if not entries:
        raise SystemExit(f"{build}: f.u found but the id->hash table parsed empty")
    return {"build": build, "f_u_expression": m.group(1)[:400],
            "special_case_id_to_name": special,
            "entries": entries,
            "n_entries": len(entries),
            "n_duplicate_ids": len(pairs) - len(entries),
            "distinct_hashes": len(set(entries.values()))}


def main():
    maps = {}
    for build, fname in BODIES.items():
        p = SCRATCH / fname
        if not p.exists():
            raise SystemExit(f"missing runtime body: {p} (run probe.sh phase 1 first)")
        raw = p.read_bytes()
        parsed = parse(raw, build)
        parsed["runtime_bytes"] = len(raw)
        parsed["runtime_sha256_16"] = hashlib.sha256(raw).hexdigest()[:16]
        parsed["runtime_etag_sha256_16"] = None
        special = parsed["special_case_id_to_name"]
        rows = []
        for cid, h in parsed["entries"].items():
            name = special["name"] if special and cid == special["id"] else cid
            rows.append({"build": build, "id": cid, "name": name, "hash": h,
                         "url_name": f"{name}.{h}.js",
                         "id_form_url": f"{cid}.{h}.js"})
        parsed["cells"] = rows
        maps[build] = parsed

    # ---- by-HASH comparison between the two builds -------------------------
    hs = {b: {r["hash"]: r for r in m["cells"]} for b, m in maps.items()}
    shared = sorted(set(hs["clinic"]) & set(hs["support"]))

    # ---- by-HASH comparison against the COMMITTED clinic list -------------
    committed = HERE.parent / "2026-10-14-area-k-clinic-controlflow" / "committed-map.txt"
    diff = {}
    if committed.exists():
        rows_c = []
        for line in committed.read_text().splitlines():
            f = line.split()
            if len(f) == 3:
                rows_c.append({"id": f[0], "name": f[1], "hash": f[2]})
        ch_clinic = {r["hash"]: r for r in maps["clinic"]["cells"]}
        ch_comm = {r["hash"]: r for r in rows_c}
        only_live = sorted(set(ch_clinic) - set(ch_comm))
        only_comm = sorted(set(ch_comm) - set(ch_clinic))
        name_diff = [
            {"hash": h, "committed_name": ch_comm[h]["name"],
             "re_derived_name": ch_clinic[h]["name"],
             "id": ch_clinic[h]["id"]}
            for h in sorted(set(ch_clinic) & set(ch_comm))
            if ch_comm[h]["name"] != ch_clinic[h]["name"]
        ]
        id_diff = [
            {"hash": h, "committed_id": ch_comm[h]["id"],
             "re_derived_id": ch_clinic[h]["id"]}
            for h in sorted(set(ch_clinic) & set(ch_comm))
            if ch_comm[h]["id"] != ch_clinic[h]["id"]
        ]
        diff = {
            "committed_file": "findings-log/2026-10-14-area-k-clinic-controlflow/committed-map.txt",
            "committed_rows": len(rows_c),
            "re_derived_rows": len(ch_clinic),
            "shared_hashes": len(set(ch_clinic) & set(ch_comm)),
            "hashes_only_in_re_derived": only_live,
            "hashes_only_in_committed": only_comm,
            "name_differences": name_diff,
            "id_differences": id_diff,
        }

    out = {
        "builds": {b: {k: v for k, v in m.items() if k != "cells"} for b, m in maps.items()},
        "cross_build": {
            "clinic_hashes": len(hs["clinic"]),
            "support_hashes": len(hs["support"]),
            "shared_hashes": len(shared),
            "shared_hash_list": shared,
        },
        "vs_committed_clinic_map": diff,
        "pinned_main_anchors": BUILD_ANCHORS,
    }
    (HERE / "chunk-map.json").write_text(json.dumps(out, indent=2) + "\n")

    with (HERE / "chunk-map.tsv").open("w") as fh:
        fh.write("build\tid\tname\thash\turl_name\tid_form_url\n")
        for build in ("clinic", "support"):
            for r in sorted(maps[build]["cells"], key=lambda r: (int(r["id"]), r["hash"])):
                fh.write(f"{build}\t{r['id']}\t{r['name']}\t{r['hash']}\t"
                         f"{r['url_name']}\t{r['id_form_url']}\n")

    for b, m in maps.items():
        print(f"{b}: {m['n_entries']} entries, {m['n_duplicate_ids']} duplicate ids, "
              f"{m['distinct_hashes']} distinct hashes, runtime {m['runtime_bytes']} B "
              f"sha {m['runtime_sha256_16']}, special case {m['special_case_id_to_name']}")
    print(f"cross-build shared hashes: {len(shared)}")
    print(json.dumps(diff, indent=2)[:2000])


if __name__ == "__main__":
    main()