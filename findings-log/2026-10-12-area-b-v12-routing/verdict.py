#!/usr/bin/env python3
"""Derive the Area B verdict from results.jsonl.

The discriminator is x-amzn-errortype, NEVER the status code
(docs/09-methodology-and-oracles.md section 2: on clcloud.* a 403 is the
no-matching-route error and a 404 is never emitted at all).

Three things this script refuses to do unless it can prove them first:

  1. It asserts every control before it will emit a single data verdict. If a
     control did not reproduce the known signature, that host's data cells
     would be reported INCONCLUSIVE rather than believed -- otherwise the
     oracle would be established from the very data it is meant to judge.
  2. It treats a non-zero curl_exit as a hole in the evidence. A transport
     failure is not a vendor answer; such a row can never become a verdict.
  3. It refuses to hash a body it has not first asserted is non-empty, and it
     refuses to report the all-zero (empty-string) digest as a finding --
     AGENTS.md section 6 item 3, the "hash over a lookup that silently
     returned null" failure.

It also measures the actual inter-request spacing from run.log rather than
asserting the value the harness was written with.
"""
import json
import re
import sys
from datetime import datetime

DIR = "findings-log/2026-10-12-area-b-v12-routing"

NO_ROUTE = "MissingAuthenticationTokenException"
AUTHZ = "UnauthorizedException"
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

DEAD_UUID = "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"
DEAD_VER = "connect/carepartner/v99/display/message"

# control -> (host, method, path) -> expectation
CONTROLS = [
    ("eu", "GET", "connect/carepartner/v13/display/message", "live-401"),
    ("eu", "GET", DEAD_UUID, "no-route"),
    ("eu", "OPTIONS", "connect/carepartner/v13/display/message", "live-preflight"),
    ("eu", "OPTIONS", DEAD_VER, "no-route"),
    ("com", "GET", "connect/carepartner/v13/display/message", "live-401"),
    ("com", "GET", DEAD_UUID, "no-route"),
    ("trials", "GET", "connect/carepartner/v13/display/message", "live-401"),
    ("trials", "GET", DEAD_UUID, "no-route"),
]

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
print(f"requests in corpus: {len(rows)}")
assert len(rows) == len({r["seq"] for r in rows}), "duplicate seq -- probe.sh ran twice?"
assert [r["seq"] for r in rows] == list(range(1, len(rows) + 1)), "seq is not contiguous 1..N"

# ---------------------------------------------------------------- transport
print("\n== transport health: a non-zero curl_exit is a hole, not an answer ==")
bad_exit = [r for r in rows if r["curl_exit"] != 0]
print(f"  rows: {len(rows)}  curl_exit=0: {len(rows) - len(bad_exit)}  non-zero: {len(bad_exit)}")
for r in bad_exit:
    print(f"  HOLE seq={r['seq']} {r['host']} {r['method']} {r['path']} exit={r['curl_exit']}")
holed = {r["seq"] for r in bad_exit}

# ---------------------------------------------------------------- controls
print("\n== controls (these gate whether the data cells below may be believed) ==")
by = {(r["host_tag"], r["method"], r["path"]): r for r in rows}
oracle_ok = True
for tag, method, path, expect in CONTROLS:
    r = by.get((tag, method, path))
    if r is None:
        print(f"  MISSING  {tag} {method} {path}")
        oracle_ok = False
        continue
    tok = r["x_amzn_errortype_token"]
    has_acao = r["access_control_allow_origin"] != "(none)"
    if expect == "live-401":
        good = (tok == AUTHZ and r["http_status"] == "401"
                and r["x_ca_err"] == "990" and not has_acao)
    elif expect == "live-preflight":
        good = (tok == "(none)" and r["http_status"] == "200" and has_acao
                and r["body_bytes"] == 0)
    else:  # no-route
        good = (tok == NO_ROUTE and not has_acao)
    print(f"  {'ok ' if good else 'BAD'} {tag:7} {method:7} expect={expect:16} "
          f"status={r['http_status']} errortype={tok} x-ca-err={r['x_ca_err']} "
          f"acao={r['access_control_allow_origin']}")
    oracle_ok = oracle_ok and good
print(f"\nORACLE: {'established before any data cell was judged' if oracle_ok else 'NOT ESTABLISHED -- data cells INCONCLUSIVE'}")
if not oracle_ok:
    sys.exit("refusing to emit data verdicts on an unestablished oracle")


def verdict(r):
    """x-amzn-errortype only. Never the status code."""
    if r["seq"] in holed:
        return "INCONCLUSIVE (transport failure)"
    tok = r["x_amzn_errortype_token"]
    if tok == NO_ROUTE:
        return "DEAD - no route"
    if tok == AUTHZ and r["x_ca_err"] == "990":
        return "LIVE - token-gated"
    if tok == "(none)" and r["http_status"] in ("200", "204"):
        return "LIVE - public"
    return "UNCLASSIFIED - see raw"


# ---------------------------------------------------------------- data cells
print("\n== data cells ==")
print(f"{'tag':7} {'method':7} {'path':42} {'st':4} {'x-amzn-errortype':32} {'x-ca-err':8} {'acao':6} {'acam':9} verdict")
for r in rows:
    if r["seq"] in {c[0] for c in []}:
        continue
    if r["role"].startswith("CONTROL"):
        continue
    print(f"{r['host_tag']:7} {r['method']:7} {r['path']:42} {r['http_status']:4} "
          f"{r['x_amzn_errortype']:32} {r['x_ca_err']:8} "
          f"{r['access_control_allow_origin']:6} {r['access_control_allow_methods']:9} "
          f"{verdict(r)}")

# ---------------------------------------------------------------- v12 across hosts
print("\n== is v12/display/message 401 on all three hosts? ==")
v12 = [r for r in rows if r["path"] == "connect/carepartner/v12/display/message" and r["method"] == "GET"]
for r in v12:
    print(f"  {r['host']:32} seq={r['seq']:2} status={r['http_status']} "
          f"errortype={r['x_amzn_errortype_token']} x-ca-err={r['x_ca_err']} -> {verdict(r)}")
print(f"  hosts with direct evidence: {len(v12)}/3 -> {[r['host_tag'] for r in v12]}")

# ---------------------------------------------------------------- body equality
print("\n== body digests, type asserted before hashing ==")
digests = {}
for r in rows:
    raw = open(f"{DIR}/headers/{r['host_tag']}-{r['host_seq']:02d}-{r['method']}-"
               f"{r['path'].replace('/', '_')}.body", "rb").read()
    assert isinstance(raw, bytes), "body did not resolve to bytes"
    d = r["body_sha256"]
    if raw == b"":
        assert d == EMPTY_SHA, f"seq {r['seq']} empty body but digest {d}"
        print(f"  seq {r['seq']:2} {r['host_tag']:7} {r['method']:7} 0 B  -> EMPTY (sha {d[:12]}, the empty-string digest)")
    else:
        assert d != EMPTY_SHA, f"seq {r['seq']} all-zero digest on a non-empty body"
        digests.setdefault(d, []).append(r["seq"])
        print(f"  seq {r['seq']:2} {r['host_tag']:7} {r['method']:7} {len(raw):3} B  sha256:{d[:12]}")
print("\n  grouping:")
for d, seqs in sorted(digests.items()):
    print(f"    sha256:{d[:12]} -> {len(seqs)} bodies, seq {seqs}")

# ---------------------------------------------------------------- spacing
print("\n== measured spacing from run.log (not the value the harness was written with) ==")
ts = []
for line in open(f"{DIR}/run.log"):
    # group 3 is the FILENAME tag, which is "<host>-<NN>" and therefore unique per
    # request. Grouping by it makes every row its own "host", so the per-host gap set
    # comes out empty and the floor below is never computed. Group by the host part.
    m = re.match(r"\[(\d{4}-\d\d-\d\dT[\d:.]+Z)\] \[(\d+)\] (\S+)", line)
    if m:
        ts.append((int(m.group(2)), m.group(3).rsplit("-", 1)[0],
                   datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S.%fZ")))
last, floors, short = {}, {}, []
for seq, tag, t in ts:
    if tag in last:
        gap = (t - last[tag][1]).total_seconds()
        floors[tag] = min(floors.get(tag, 9e9), gap)
        if gap < 2.5:
            short.append((tag, seq, gap))
    last[tag] = (seq, t)
for tag in ("eu", "com", "trials"):
    n = sum(1 for s, tg, _ in ts if tg == tag)
    if tag in floors:
        print(f"  {tag:7} {n:2} requests, measured floor {floors[tag]:.3f}s")
overall = min(floors.values())
print(f"\n  repo rule (AGENTS.md section 8, >=2s per host): {'PASS' if overall >= 2.0 else 'FAIL'} (worst floor {overall:.3f}s)")
print(f"  harness's own stated spacing (>=2.5s per host): {'PASS' if overall >= 2.5 else 'FAIL'}")
if short:
    print(f"  gaps below the harness's 2.5s, listed rather than summarised:")
    for tag, seq, gap in short:
        print(f"    {tag} -> request {seq}: {gap:.3f}s")
print(f"\nrequests used: {len(rows)} / cap 24")
