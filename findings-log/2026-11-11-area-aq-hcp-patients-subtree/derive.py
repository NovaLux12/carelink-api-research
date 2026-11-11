#!/usr/bin/env python3
"""Area AQ — derive the `hcp/patients/` route-literal set, offline, ZERO requests.

Two sources, because the build names its routes in two places and one of them is
lazily loaded:

  * the EAGER bundle fetched by this run (`main.<hash>.js`), read here; and
  * the COMMITTED chunk corpus, whose `hcp/patients` literal is recorded in
    `findings-log/2026-10-14-area-k-clinic-controlflow/route-delta.json`
    (`chunk_only`), derived there from the lazy chunks and hash-pinned. Reading
    the committed JSON rather than re-fetching every chunk keeps this derivation
    at zero requests; what it costs is that a chunk-corpus drift would not be
    seen here, which is stated as a limit rather than hidden.

The extraction separates two populations, because they are different claims:

  * PROBEABLE — no `((placeholder))` in the literal. The route is named
               outright, so requesting it is a route-shape question and nothing
               more.
  * NEEDS-ID  — contains `((patientId))` (Angular HttpClient interpolation,
               JS-API-SURFACE.md §3.1). Requesting one means inventing a patient
               id. HARD RULE: never. Recorded, not probed.

A third label exists for the opposite reason: CLAIM-ONLY, a name the claim
asserts that NEITHER source names. It is still probed, because "the claim says
this route exists and the build does not name it" is exactly the kind of
disagreement this pass is supposed to surface — but it is counted separately so
it can never be mistaken for a derived route.

Usage:  derive.py <eager-bundle> <chunk-route-json> <claimed-set> <out-txt> <out-set>
Exit:   0 = derivation completed (agreement or not; see the verdict line)
        2 = no `hcp/patients` literal in the eager bundle at all
"""
import hashlib
import json
import os
import re
import sys

bundle_path, chunk_json, claimed_arg, out_path, set_path = sys.argv[1:6]
claimed = sorted(claimed_arg.split())

body = open(bundle_path, "rb").read()
text = body.decode("utf-8", "replace")

# The literal vocabulary, read from the build rather than assumed: a double-
# quoted string starting (optionally after one space — the JS-API-SURFACE §2.1
# quirk) at `hcp/patients`.
LIT = re.compile(r'"\s*(hcp/patients[A-Za-z0-9._()/{}$+-]*(?:\?[^"]*)?)"')
OTHER = re.compile(r"['`]\s*(hcp/patients[A-Za-z0-9._()/{}$+-]*(?:\?[^'`]*)?)['`]")
raw = [m.group(1) for m in LIT.finditer(text)]
other = [m.group(1) for m in OTHER.finditer(text)]

chunk = json.load(open(chunk_json))
chunk_only = [p.lstrip("/") for p in chunk["chunk_only"] if p.lstrip("/").startswith("hcp/patients/")]


def key(lit):
    return lit.split("?", 1)[0].split("#", 1)[0].rstrip("/")


eager_probeable, needs_id = set(), set()
for lit in raw + other:
    k = key(lit)
    (needs_id if "((" in k else eager_probeable).add(k)

chunk_probeable = {k for k in map(key, chunk_only) if "((" not in k}
derived = eager_probeable | chunk_probeable
claim_only = [c for c in claimed if c not in derived]
missing_from_claim = sorted(derived - set(claimed))

# The sweep's actual GET list: everything derived, plus the claim-only names.
probe_set = sorted(derived) + sorted(claim_only)

out = []
out.append("== AREA AQ — derivation, zero requests ==")
out.append(f"eager bundle      : {bundle_path}")
out.append(f"eager bytes       : {len(body)}")
out.append(f"eager sha256      : {hashlib.sha256(body).hexdigest()}")
out.append(f"eager literal hits: {len(raw)} double-quoted, {len(other)} single/backtick")
out.append(f"chunk source      : {chunk_json}")
out.append(f"chunk chunk_only  : {chunk['chunk_only']}  (sha256 {chunk.get('chunk_routes_sha256','-')})")
out.append("")
out.append(f"PROBEABLE — eager bundle ({len(eager_probeable)}), no placeholder, safe to request:")
for p in sorted(eager_probeable):
    out.append(f"  {p}")
out.append("")
out.append(f"PROBEABLE — chunk-only ({len(chunk_probeable)}), from the committed route delta:")
for p in sorted(chunk_probeable):
    out.append(f"  {p}")
out.append("")
out.append(f"NEEDS-ID ({len(needs_id)}) — placeholder in the literal; RECORDED, NOT PROBED:")
for n in sorted(needs_id):
    out.append(f"  {n}")
out.append("")
out.append(f"CLAIM-ONLY ({len(claim_only)}) — the claim names these, neither source does:")
for c in sorted(claim_only):
    out.append(f"  {c}")
out.append("")
out.append(f"claimed set  ({len(claimed)}): {' '.join(claimed)}")
out.append(f"derived set  ({len(derived)}): {' '.join(sorted(derived))}")
out.append(f"claimed but NOT derived: {sorted(claim_only) or '(none)'}")
out.append(f"derived but NOT claimed: {missing_from_claim or '(none)'}")

# The claimed set is a human summary typed from the recon reports. It is compared
# here so the disagreement is on the record, and it is NOT the sweep's input.
out.append("")
out.append(f"DERIVE VERDICT: THE DERIVED SET WINS. {len(derived)} probeable literals derived "
           f"against {len(claimed)} claimed; {len(missing_from_claim)} derived names are absent "
           f"from the claim and {len(claim_only)} claimed name(s) appear in no build. "
           f"The sweep issues the DERIVED set plus the {len(claim_only)} claim-only name(s), "
           f"{len(probe_set)} candidates in total.")

txt = "\n".join(out) + "\n"
open(out_path, "w").write(txt)
open(set_path, "w").write("".join(p + "\n" for p in probe_set))
print(txt)

if not eager_probeable and not needs_id:
    print("DERIVE STOP: the eager bundle names no hcp/patients literal at all — this is not the portal build.")
    sys.exit(2)
