#!/usr/bin/env python3
"""Area AQ — re-derive every figure in FINDINGS.md from results.jsonl. ZERO requests.

The rule (AGENTS.md §6 item 5): prose is derived from the ledger, never from
another prose summary. Every table in FINDINGS.md is printed by this script, so a
number that drifts from the ledger is visible as a diff here rather than as a
plausible-looking sentence there.

Also reports both spacing clocks, because the harness is in the repository's
recorded corrupt-`t0` class (`docs/09` §4) and one clock is not enough to say
anything about the delay.

Usage: verify.py [<scratch-dir>]   # scratch dir only enables clock B
"""
import collections
import datetime
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl")) if l.strip()]
CAP = 36


def ts(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")


print(f"== rows: {len(ROWS)}  cap: {CAP}  over cap: {len(ROWS) > CAP} ==")
print(f"== curl_exit != 0: {[r['seq'] for r in ROWS if r['curl_exit'] != 0]} ==")
print(f"== servers: {sorted({r['server'] for r in ROWS})} ==")
print(f"== acam values: {sorted({r['acam'] for r in ROWS})} ==")
print(f"== acao values: {sorted({r['acao'] for r in ROWS})} ==")

print("\n== CONTROLS (8) ==")
for r in ROWS:
    if r["role"].startswith("CONTROL"):
        print(f"  seq {r['seq']:2d} {r['host']:32s} {r['path']:46s} "
              f"{r['http_status']} {r['body_bytes']:3d}B sha={r['body_sha256'][:16] or '-'}")

print("\n== BOUNDARY — absent child under hcp/patients/ (4) ==")
for r in ROWS:
    if r["role"].startswith("BOUNDARY"):
        print(f"  seq {r['seq']:2d} {r['host']:32s} {r['http_status']} "
              f"{r['body_bytes']}B ct={r['content_type']} allow={r['allow']}")

print("\n== CANDIDATES (23) ==")
cand = [r for r in ROWS if r["role"].startswith("CANDIDATE")]
for r in cand:
    print(f"  seq {r['seq']:2d} {r['path']:56s} {r['http_status']} "
          f"{r['body_bytes']:3d}B ct={r['content_type']:24s} allow={r['allow']}")
print(f"  status histogram: {dict(collections.Counter(r['http_status'] for r in cand))}")

# The AG trap test, computed rather than asserted: does a 405 at this subtree
# discriminate presence from absence? The absent child answers one thing; a
# 405 on a candidate answers another. If the absent child ALSO answered 405 the
# 405 column would be a subtree constant and prove nothing.
boundary = [r for r in ROWS if r["role"].startswith("BOUNDARY")]
print("\n== 405-constant test ==")
print(f"  absent child statuses: {sorted({r['http_status'] for r in boundary})}, "
      f"all zero-byte: {all(r['body_bytes'] == 0 for r in boundary)}")
print(f"  candidate 405 count: {sum(1 for r in cand if r['http_status'] == '405')}")
print(f"  candidate 404 count: {sum(1 for r in cand if r['http_status'] == '404')}")
print("  VERDICT: " + ("405 is PER-ROUTE here — the absent child 404s, so a 405 on a "
                       "candidate is evidence of a registered handler"
                       if {r['http_status'] for r in boundary} == {'404'} else
                       "405 is a SUBTREE CONSTANT — the absent child reproduces it"))

# The intra-depth falsification: three single-segment candidates 404 while
# sixteen single-segment candidates 405. If a wildcard one-segment handler
# answered every child, the 404s could not exist.
single = [r for r in cand if r["path"].count("/") == 3]
print(f"\n== depth check: {len(single)} single-segment candidates ==")
print(f"  statuses at depth 1: {dict(collections.Counter(r['http_status'] for r in single))}")

print("\n== the claim's 12 names, each against this pass's cell ==")
claim = ("hcp/patients hcp/patients/archivePatient hcp/patients/checkPhoneNumber "
         "hcp/patients/getInviteToPersonalTemplate hcp/patients/getPatient "
         "hcp/patients/getPatientsMealProfilesAndDailyHabits hcp/patients/linkPatient "
         "hcp/patients/otc-linking/allowed hcp/patients/otc-linking/code/sms/send "
         "hcp/patients/sendInviteToPersonal hcp/patients/unlinkPatient "
         "hcp/patients/updatePatient").split()
by = {r["path"].lstrip("/"): r for r in cand}
for c in claim:
    r = by.get(c)
    print(f"  {c:56s} {r['http_status'] if r else 'NOT PROBED'}"
          f"{'  allow=' + r['allow'] if r and r['allow'] != '(none)' else ''}")

print("\n== spacing, clock A (t_sent, re-derivable) ==")
neg = [(r["seq"], r["host"], round((ts(r["t_done"]) - ts(r["t_sent"])).total_seconds(), 3))
       for r in ROWS if ts(r["t_done"]) < ts(r["t_sent"])]
# Gaps must be measured per host on the SEQ series, not on adjacent rows in file order.
# File order interleaves hosts (carelinkhp rows sit between the three-row host bursts), so
# `zip(ROWS, ROWS[1:])` silently skips every pair whose neighbours in the file belong to a
# different host — here it missed carelinkhp seq 4->14 and reported 31 gaps where the ledger
# holds 32. Caught by a verifier; the count is re-derived by grouping and sorting below.
_groups = {}
for _r in ROWS:
    _groups.setdefault(_r["host"], []).append(_r)
gaps = []
for _h, _rs in _groups.items():
    _rs = sorted(_rs, key=lambda r: r["seq"])
    gaps.extend(((ts(b["t_sent"]) - ts(a["t_sent"])).total_seconds(), a["seq"], b["seq"])
                for a, b in zip(_rs, _rs[1:]))
gaps.sort(key=lambda g: g[1])
vals = [g[0] for g in gaps]
print(f"  gaps {len(vals)}  min {min(vals):.3f}  median {statistics.median(vals):.3f}  "
      f"max {max(vals):.3f}")
print(f"  under 2.5 s: {[(round(v,3), a, b) for v, a, b in gaps if v < 2.5]}")
print(f"  under 2.0 s: {[(round(v,3), a, b) for v, a, b in gaps if v < 2.0]}")
print(f"  impossible negative DURATIONS: {neg}")

if len(sys.argv) > 1:
    scratch = sys.argv[1]
    print("\n== spacing, clock B (kernel body mtimes, NOT re-derivable from a clone) ==")
    stamped = []
    for r in ROWS:
        p = os.path.join(scratch, r["tag"] + ".b")
        if os.path.exists(p):
            stamped.append((r, datetime.datetime.utcfromtimestamp(os.path.getmtime(p))))
    print(f"  bodies stat-able: {len(stamped)} of {len(ROWS)}")
    g2 = [((b[1] - a[1]).total_seconds(), a[0]["seq"], b[0]["seq"])
          for a, b in zip(stamped, stamped[1:]) if a[0]["host"] == b[0]["host"]]
    v2 = [g[0] for g in g2]
    if v2:
        print(f"  gaps {len(v2)}  min {min(v2):.3f}  median {statistics.median(v2):.3f}  "
              f"max {max(v2):.3f}")
        print(f"  under 2.5 s: {[(round(v,3), a, b) for v, a, b in g2 if v < 2.5]}")
        print(f"  FLOOR ON THIS CLOCK: {min(v2):.3f} s")

print("\n== derive.txt cross-check ==")
txt = open(os.path.join(HERE, "derive.txt")).read()


def section(head):
    """The `  <literal>` lines under one heading, and nothing else.

    Scoped by heading rather than by a bare `^  hcp/patients` match: CLAIM-ONLY
    lines carry the same prefix, so an unscoped count reads 38 where the eager
    population is 21 — the "count over the wrong population" defect this repo
    has recorded (AGENTS.md §6 item 7).
    """
    body = txt.split(head, 1)[1].split("\n\n", 1)[0]
    return [l.strip() for l in body.splitlines() if l.strip().startswith("hcp/patients")]


eager = section("PROBEABLE — eager bundle")
chunk = section("PROBEABLE — chunk-only")
needs = section("NEEDS-ID")
claimonly = section("CLAIM-ONLY")
rows = [l for l in open(os.path.join(HERE, "candidates.txt")) if l.strip()]
print(f"  eager probeable: {len(eager)}   chunk-only: {len(chunk)}   "
      f"needs-id: {len(needs)}   claim-only: {len(claimonly)}")
print(f"  candidates.txt rows: {len(rows)}  "
      f"(= eager {len(eager)} + chunk {len(chunk)} + claim-only {len(claimonly)})")
print(f"  arithmetic closes: "
      f"{len(rows) == len(eager) + len(chunk) + len(claimonly)}")
print(f"  1 + 8 + 4 + {len(rows)} = {1 + 8 + 4 + len(rows)}   (cap is {CAP})")
