#!/usr/bin/env python3
"""Re-derive the clinic chunk map from the build's own f.u and diff it against the
committed list BY HASH, not by name.

Why hash and not name (docs/09 trap row 3, "A committed filename list is not a URL
list"): f.u substitutes a different NAME for one id (2076 -> "common"), so a name
diff reports a difference for a file that is identical, and a hash diff reports the
join key that actually identifies the asset. Both are computed; the hash set is the
verdict and the name set is reported beside it.

Inputs: the live runtime body (control C4), and the committed map copied verbatim
from the 2026-10-13 clinic-denominator pass. Zero requests.
"""
import hashlib
import json
import re
import sys

runtime_path, committed_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

body = open(runtime_path, "rb").read()
text = body.decode("utf-8", "replace")

# The publicPath, so the emitted URL is derived rather than assumed.
pm = re.search(r'f\.p\s*=\s*"([^"]*)"', text)
public_path = pm.group(1) if pm else None

# f.u = e => (2076===e?"common":e)+"."+{...}[e]+".js"
um = re.search(r'f\.u\s*=\s*e\s*=>\s*\(([^)]*?)\)\s*\+\s*"\."\s*\+\s*(\{.*?\})\s*\[\s*e\s*\]\s*\+\s*"\.js"', text)
if not um:
    print("FAIL: f.u not found in the runtime body")
    sys.exit(2)

cond = um.group(1)
pairs = dict(re.findall(r'(\d+)\s*:\s*"([0-9a-f]+)"', um.group(2)))

# The special case is READ from the source, not assumed: it is a ternary of the
# form <id>===e?"<name>":e .
sub = re.search(r'(\d+)===\s*e\?\s*"([^"]*)"\s*:\s*e', cond)
sub_id, sub_name = (sub.group(1), sub.group(2)) if sub else (None, None)

def emitted_name(cid: str) -> str:
    return sub_name if (sub_id is not None and cid == sub_id) else cid

rederived = {cid: (emitted_name(cid), h) for cid, h in pairs.items()}

committed = {}
for line in open(committed_path):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    p = line.split()
    if len(p) != 3:
        print(f"FAIL: malformed committed line: {line!r}")
        sys.exit(2)
    committed[p[0]] = (p[1], p[2])

rd_ids, cm_ids = set(rederived), set(committed)
rd_hashes = {h for _, h in rederived.values()}
cm_hashes = {h for _, h in committed.values()}

out = {
    "runtime_body_sha256": hashlib.sha256(body).hexdigest(),
    "runtime_body_bytes": len(body),
    "f_publicPath": public_path,
    "f_u_ternary_condition_as_read": cond,
    "f_u_special_case_id": sub_id,
    "f_u_special_case_name": sub_name,
    "rederived_entry_count": len(rederived),
    "committed_entry_count": len(committed),
    "id_sets_equal": rd_ids == cm_ids,
    "ids_only_in_rederived": sorted(rd_ids - cm_ids, key=int),
    "ids_only_in_committed": sorted(cm_ids - rd_ids, key=int),
    "id_to_hash_equal": {k: v for k, v in rederived.items()} == {k: v for k, v in committed.items()},
    "hash_set_equal": rd_hashes == cm_hashes,
    "hashes_only_in_rederived": sorted(rd_hashes - cm_hashes),
    "hashes_only_in_committed": sorted(cm_hashes - rd_hashes),
    "duplicate_hashes_in_rederived": sorted({h for h in rd_hashes if list(rederived.values()).count((None, h)) > 1}),
    "name_moves": [
        {"id": k, "committed_name": committed[k][0], "rederived_name": rederived[k][0], "hash": rederived[k][1]}
        for k in sorted(rd_ids & cm_ids, key=int)
        if committed[k][0] != rederived[k][0]
    ],
    "order_equal": [k for k in sorted(rd_ids, key=int)] == [k for k in sorted(cm_ids, key=int)],
}

# Emit the re-derived list in the runtime's own (committed) order, so the sweep
# runs in a recorded order rather than a sorted one.
ordered_ids = [k for k, _ in re.findall(r'(\d+)\s*:\s*"([0-9a-f]+)"', um.group(2))]
out["rederived_order_equals_committed_order"] = ordered_ids == [
    l.split()[0] for l in open(committed_path) if l.strip()
]

with open(out_path, "w") as f:
    json.dump(out, f, indent=2, sort_keys=False)

print(json.dumps(out, indent=2))

if not out["hash_set_equal"] or not out["id_to_hash_equal"]:
    print("\nVERDICT: THE BUILD HAS MOVED — do not sweep the committed list.")
    sys.exit(3)
print("\nVERDICT: hash-identical to the committed list; the corpus is current.")