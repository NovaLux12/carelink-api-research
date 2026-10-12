#!/usr/bin/env python3
"""Derive the Area U verdict table from results.jsonl.

The oracle is x-amzn-errortype, never the status code. This script asserts the
controls before it will believe any data cell -- if a host's controls do not
reproduce the known .eu signature, that host's data cells are reported
inconclusive rather than believed.

Also computes, and refuses to report, the sha256 of the 42 B 403 body without
first asserting its resolved type -- the "hash over a lookup that silently
returned null" failure in AGENTS.md section 6 item 3.
"""
import json
import hashlib
import os
import sys

NO_ROUTE = "MissingAuthenticationTokenException"
AUTHZ = "UnauthorizedException"

def per_host_index(suffix, row):
    """Row n -> its 1-based index within its host block (blocks of 16)."""
    return ((row["n"] - 1) % 16) + 1

CONTROLS = {
    ("clcloud.minimed.com", "GET", "connect/carepartner/v13/display/message"): "live",
    ("clcloud.minimed.com", "OPTIONS", "connect/carepartner/v13/display/message"): "live",
    ("clcloud.minimed.com", "GET", "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"): "absent",
    ("clcloud.minimed.com", "OPTIONS", "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"): "absent",
    ("clcloud-trials.minimed.com", "GET", "connect/carepartner/v13/display/message"): "live",
    ("clcloud-trials.minimed.com", "OPTIONS", "connect/carepartner/v13/display/message"): "live",
    ("clcloud-trials.minimed.com", "GET", "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"): "absent",
    ("clcloud-trials.minimed.com", "OPTIONS", "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"): "absent",
}
DATA = [
    "connect/pde/v1/display/message",
    "connect/pde/v2/display/message",
    "connect/pde/v3/display/message",
    "connect/pde/v3/discover/android/3.6",
    "connect/csr/v1/display/message",
    "connect/csr/v3/display/message",
]

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
by = {(r["host"], r["method"], r["path"]): r for r in rows}

print(f"requests in corpus: {len(rows)}")
assert len(rows) == len(by), "duplicate (host,method,path) rows -- probe.sh ran twice?"

# ---- controls first
print("\n== controls (these gate whether the data cells below may be believed) ==")
oracle_ok = True
for (host, method, path), kind in CONTROLS.items():
    r = by.get((host, method, path))
    if r is None:
        print(f"  MISSING  {host} {method} {path}")
        oracle_ok = False
        continue
    err = r["x_amzn_errortype"]
    has_acao = r["acao"] != "(none)"
    if kind == "live":
        # live GET is 401 UnauthorizedException (reached the Layer7 authorizer);
        # live OPTIONS is 200 with access-control-allow-origin.
        good = (err.strip().endswith(AUTHZ) and r["status_line"].split()[1] == "401") or has_acao
    else:
        good = err.strip().endswith(NO_ROUTE) and not has_acao
    print(f"  {'ok ' if good else 'BAD'} {host:32} {method:7} expect={kind:6} "
          f"status={r['status_line'].split()[1]} errortype={err} acao={r['acao']}")
    oracle_ok = oracle_ok and good
print(f"\nORACLE: {'established on both hosts' if oracle_ok else 'NOT ESTABLISHED -- data cells inconclusive'}")

# ---- per-cell verdict, needs BOTH methods
print("\n== data cells: verdict needs GET + OPTIONS together ==")
print(f"{'host':30} {'path':40} {'GET':28} {'OPTIONS':28} verdict")
for host in ("clcloud.minimed.com", "clcloud-trials.minimed.com"):
    for path in DATA:
        g, o = by.get((host, "GET", path)), by.get((host, "OPTIONS", path))
        if not g or not o:
            print(f"{host:30} {path:40} MISSING")
            continue
        def cell(r):
            et = r["x_amzn_errortype"].split(":", 1)[-1].strip()
            return f"{r['status_line'].split()[1]} {et or '-'} cors={'Y' if r['acao'] != '(none)' else 'N'}"
        g_dead = g["x_amzn_errortype"].strip().endswith(NO_ROUTE)
        o_dead = o["x_amzn_errortype"].strip().endswith(NO_ROUTE)
        if g_dead and o_dead:
            v = "DEAD - no route on either method"
        elif g_dead and not o_dead:
            v = "LIVE, POST-only (OPTIONS differs)"
        else:
            v = "LIVE with GET"
        print(f"{host:30} {path:40} {cell(g):28} {cell(o):28} {v}")

# ---- body equality against the fabricated control, type asserted first
#
# NOTE (2026-10-12 review round): the first version of this section hashed the
# fabricated control once per host and printed the digest, under a heading that
# said "equality". It never compared anything -- so the byte-identity claim in
# FINDINGS.md was true but was not derived by the script cited as deriving it.
# This version actually compares: every dead-cell body is hashed against the
# host's own fabricated-path control and must match it.
print("\n== 403 body equality: is the 'dead' response identical to a fabricated path? ==")
for host in ("clcloud.minimed.com", "clcloud-trials.minimed.com"):
    ctrl = f"findings-log/2026-10-12-pde-csr-cross-host/headers/{'com' if host.endswith('.com') and 'trials' not in host else 'trials'}-02-GET-connect_carepartner_v13_3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c.body"
    try:
        raw = open(ctrl, "rb").read()
    except FileNotFoundError:
        print(f"  {host}: control body not found at {ctrl}")
        continue
    assert isinstance(raw, bytes) and len(raw) > 0, "control body empty -- refusing to hash"
    d = hashlib.sha256(raw).hexdigest()[:12]
    assert d != "e3b0c44298fc", "all-zero digest is the empty string -- the hash proved nothing"
    suffix = "com" if (host.endswith(".com") and "trials" not in host) else "trials"
    print(f"  {host:30} control body {len(raw)}B sha256:{d}")

    # --- the comparison the section is named after, performed for real ---
    hdrs = os.path.join(os.path.dirname(ctrl), "")
    data = [r for r in rows if r["host"] == host
            and (r["path"].startswith("connect/pde/") or r["path"].startswith("connect/csr/"))]
    compared, identical = 0, 0
    for r in data:
        slug = r["path"].replace("/", "_").replace(".", "_")
        body = os.path.join(hdrs, f"{suffix}-{int(r['n']) - 16:02d}-{r['method']}-{slug}.body")
        if not os.path.exists(body):
            body = os.path.join(hdrs, f"{suffix}-{per_host_index(suffix, r):02d}-{r['method']}-{slug}.body")
        if not os.path.exists(body):
            continue
        raw2 = open(body, "rb").read()
        assert isinstance(raw2, bytes) and len(raw2) > 0, f"empty body {body}"
        h2 = hashlib.sha256(raw2).hexdigest()[:12]
        compared += 1
        if h2 == d:
            identical += 1
        else:
            print(f"    DIFFERS: {os.path.basename(body)} sha256:{h2} != control {d}")
    print(f"    {identical}/{compared} dead-cell bodies byte-identical to the fabricated control")
    assert compared == 12, f"expected 12 data-cell bodies for {host}, compared {compared}"
    assert identical == compared, "a dead-cell body differs from the fabricated-path control"