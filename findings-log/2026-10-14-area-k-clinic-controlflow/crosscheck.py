#!/usr/bin/env python3
"""Cross-check this pass's emitted filenames and body digests against the
2026-10-13 clinic-denominator ledger, and measure the real same-host spacing.

Three questions, three answers, all re-derived rather than inherited:

 1. NAME SET. Does the set of filenames this pass REQUESTED equal the set the
    2026-10-13 pass requested, id by id? A name difference is reported per cell
    with status, content-type and size so a reader can see which of the two
    readings it is. This is a REPORT, not the verdict — docs/09 trap row 3 says a
    name diff cannot distinguish "same file, wrong name" from "two different
    files", so question 2 is the one that decides.

 2. HASH SET / BODY DIGEST. The verdict. For every id, the CONTENT HASH in the
    URL and the sha256 of the body actually received. A cell whose body digest
    moved is a corpus that moved, whatever its filename says.

 3. SPACING. Measured from t_sent AND from the kernel body-write mtimes, because
    docs/09 trap row 11 established that the harness date series is the suspect
    and the kernel's write time is not. Both are reported; neither is rounded.

Also flags, per sweep cell, any response that is NOT application/javascript —
those are the cells whose "chunk" verdict would be false (docs/09 trap row 2:
this host answers 200 text/html 5518 B for every unknown path, so status proves
nothing).

Usage: crosscheck.py <my-ledger.jsonl> <2026-10-13-ledger.jsonl> <out.json>
"""
import json
import re
import sys
from datetime import datetime

mine_p, prior_p, out_p = sys.argv[1], sys.argv[2], sys.argv[3]
JS = "application/javascript"
SPA_SHA = "0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d"


def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")


mine, prior = load(mine_p), load(prior_p)

mine_sweep = [r for r in mine if str(r.get("role", "")).startswith("SWEEP")]
mine_ctl = [r for r in mine if not str(r.get("role", "")).startswith("SWEEP")]
prior_sweep = [r for r in prior if r.get("id") is not None]

out = {
    "row_counts": {
        "this_pass_total_rows": len(mine),
        "this_pass_sweep_rows": len(mine_sweep),
        "this_pass_control_rows": len(mine_ctl),
        "prior_pass_rows": len(prior),
        "prior_pass_rows_with_an_id": len(prior_sweep),
    }
}

# ---------------------------------------------------------------- 1. name set
m_by_id = {r["id"]: r for r in mine_sweep}
p_by_id = {r["id"]: r for r in prior_sweep}
out["sweep_cells_this_pass"] = len(m_by_id)
out["sweep_cells_prior_pass"] = len(p_by_id)
out["ids_missing_from_this_pass"] = sorted(set(p_by_id) - set(m_by_id))
out["ids_new_in_this_pass"] = sorted(set(m_by_id) - set(p_by_id))

name_diffs, hash_diffs, digest_diffs, size_diffs, ct_diffs, status_diffs = [], [], [], [], [], []
for cid in sorted(set(m_by_id) & set(p_by_id), key=lambda x: (x is None, x)):
    a, b = m_by_id[cid], p_by_id[cid]
    cell = {"id": cid, "this": a["emitted"], "prior": b["emitted"],
            "this_status": a["status"], "this_ct": a["content_type"], "this_size": a["size"],
            "prior_status": b["status"], "prior_ct": b["content_type"], "prior_size": b["size"]}
    if a["emitted"] != b["emitted"]:
        name_diffs.append(cell)
    if a.get("hash") != b.get("hash"):
        hash_diffs.append(cell)
    if a["sha256"] != b["sha256"]:
        digest_diffs.append(cell)
    if a["size"] != b["size"]:
        size_diffs.append(cell)
    if a["content_type"] != b["content_type"]:
        ct_diffs.append(cell)
    if a["status"] != b["status"]:
        status_diffs.append(cell)

out["name_differences"] = name_diffs
out["url_hash_differences"] = hash_diffs
out["body_sha256_differences"] = digest_diffs
out["size_differences"] = size_diffs
out["content_type_differences"] = ct_diffs
out["status_differences"] = status_diffs

# ------------------------------------------------- the false-verdict cell flag
# A sweep cell that came back as anything other than application/javascript, or
# whose body is the SPA shell, did not fetch a chunk. Its verdict is false and it
# must not be counted as swept.
false_cells = [r for r in mine_sweep
               if JS not in r["content_type"] or r["sha256"] == SPA_SHA]
out["sweep_cells_that_did_not_return_a_chunk"] = [
    {"seq": r["seq"], "id": r["id"], "emitted": r["emitted"], "status": r["status"],
     "content_type": r["content_type"], "size": r["size"], "sha256": r["sha256"]}
    for r in false_cells
]
out["sweep_cells_returning_javascript"] = len(mine_sweep) - len(false_cells)
out["distinct_body_digests_among_sweep_cells"] = len({r["sha256"] for r in mine_sweep})
out["duplicate_body_digests_among_sweep_cells"] = (
    len(mine_sweep) - len({r["sha256"] for r in mine_sweep}))

# Content-encoding census, reported because the 2026-10-13 patient sweep found
# brotli and identity on this family and no gzip at all. One cell answering gzip
# is a fact about that cell, not about the host.
enc = {}
for r in mine:
    enc[r.get("content_encoding")] = enc.get(r.get("content_encoding"), 0) + 1
out["content_encoding_census"] = enc

# ---------------------------------------------------------------- 3. spacing
def gaps(rows, key):
    ser = []
    for r in rows:
        v = r.get(key)
        if v in (None, "", "(none)", "(unrecorded)"):
            continue
        ser.append((r["seq"], v))
    out_g = []
    for (s0, v0), (s1, v1) in zip(ser, ser[1:]):
        out_g.append({"from_seq": s0, "to_seq": s1, "gap_s": round((ts(v1) - ts(v0)).total_seconds(), 3)})
    return out_g


def summarise(gs, label, floor):
    if not gs:
        return {"series": label, "gaps": 0}
    vals = [g["gap_s"] for g in gs]
    under = [g for g in gs if g["gap_s"] < floor]
    neg = [g for g in gs if g["gap_s"] < 0]
    return {
        "series": label, "gaps": len(gs),
        "min_gap_s": min(vals), "max_gap_s": max(vals),
        "under_declared_2_5s": len(under), "under_declared_2_5s_detail": under,
        "under_repo_floor_2_0s": sum(1 for v in vals if v < 2.0),
        "negative_gaps": len(neg),
        "under_declared_2_5s_seqs": [[g["from_seq"], g["to_seq"], g["gap_s"]] for g in under],
    }


ts_gaps = gaps(mine, "t_sent")
mt_gaps = []
prev = None
for r in mine:
    v = r.get("body_mtime_ns")
    if v in (None, "", "(none)"):
        continue
    if prev is not None:
        mt_gaps.append({"from_seq": prev[0], "to_seq": r["seq"],
                        "gap_s": round((int(v) - prev[1]) / 1e9, 3)})
    prev = (r["seq"], int(v))

out["spacing_t_sent"] = summarise(ts_gaps, "t_sent (harness clock)", 2.5)
out["spacing_body_mtime"] = summarise(mt_gaps, "kernel body-write mtime", 2.5)

with open(out_p, "w") as f:
    json.dump(out, f, indent=2)

# human summary
print(json.dumps({k: v for k, v in out.items()
                  if k not in ("name_differences", "url_hash_differences",
                               "body_sha256_differences", "size_differences",
                               "content_type_differences", "status_differences")},
                 indent=2)[:6000])
print("\n--- differences vs 2026-10-13 (per-cell, with status/ct/size) ---")
for k in ("name_differences", "url_hash_differences", "body_sha256_differences",
          "size_differences", "content_type_differences", "status_differences"):
    print(f"{k}: {len(out[k])}")
    for row in out[k][:10]:
        print("   ", json.dumps(row))