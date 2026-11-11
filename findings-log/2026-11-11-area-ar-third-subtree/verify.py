#!/usr/bin/env python3
"""Area AR — re-derive every number in FINDINGS.md from the artefacts. ZERO requests.

Checks, each one able to FAIL — a check that cannot fail is not evidence
(AGENTS.md §Method):

  1. ledger rows == CAP, and the itemisation arithmetic sums to CAP
  2. every candidates.txt name appears at both depths on both hosts, and nothing else
  3. the three controls, per host, against their recorded values
  4. the verdict matrix printed from the ledger, not from prose
  5. clock A (t_sent) spacing, disclosed as measured, gaps counted against
     sum(rows_per_host - 1)
  6. clock B (kernel body mtimes) — with a LIVENESS PROOF: the mtimes must be
     DISTINCT across requests, otherwise they are one build timestamp and are not
     a request clock at all (trap 5), and then only one clock is claimed
  7. the derivation's sum: 18 = 3 controls x 2 hosts + 3 subtrees x 2 depths x 2 hosts

Usage: verify.py <findings-dir>
Exit:  0 = every check passed; 1 = a check failed (which one is printed)
"""
import glob
import json
import os
import statistics
import sys

d = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
CAP = 18
HOSTS = ["carelink.medtronic.eu", "carelink-support.medtronic.com"]
ABSENT = "zz-ar-absent-6293"
POW = {"carelink.medtronic.eu": ("200", 96, "a977733a53ee0d5f"),
       "carelink-support.medtronic.com": ("200", 97, "370e3bba0d28c540")}

fail = []


def check(cond, msg):
    print(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        fail.append(msg)


rows = [json.loads(l) for l in open(os.path.join(d, "results.jsonl")) if l.strip()]
cands = [l.strip() for l in open(os.path.join(d, "candidates.txt")) if l.strip()]

print("== 1. request accounting ==")
check(len(rows) == CAP, f"ledger rows {len(rows)} == CAP {CAP}")
itemised = 3 * len(HOSTS) + len(cands) * 2 * len(HOSTS)
check(itemised == CAP,
      f"itemisation 3 controls x {len(HOSTS)} hosts + {len(cands)} subtrees x 2 depths x "
      f"{len(HOSTS)} hosts = {itemised}, cap is {CAP}")
check(all(r["curl_exit"] == 0 for r in rows),
      f"curl_exit 0 on {sum(r['curl_exit'] == 0 for r in rows)} of {len(rows)} rows")
check(all(r["method"] == "GET" for r in rows), "every recorded method is GET")

print("\n== 2. candidate coverage ==")
for h in HOSTS:
    got = {(r["path"], r["http_status"]) for r in rows if r["host"] == h}
    for c in cands:
        for depth, path in ((1, f"/hcp/{c}/{ABSENT}"), (2, f"/hcp/{c}/{ABSENT}/zz")):
            check(any(p == path for p, _ in got), f"{h} {path} recorded (depth {depth})")
    n = [r for r in rows if r["host"] == h]
    check(len(n) == CAP // len(HOSTS), f"{h}: {len(n)} rows == {CAP // len(HOSTS)}")

print("\n== 3. controls, per host ==")
for h in HOSTS:
    r = [x for x in rows if x["host"] == h and x["tag"].endswith("pow-crm")][0]
    st, by, sha = POW[h]
    check(r["http_status"] == st and r["body_bytes"] == by,
          f"{h} CONTROL-1 pow.crm.settings -> {r['http_status']}, {r['body_bytes']} B "
          f"(recorded {st}, {by} B)")
    check(r["body_sha256"][:16] == sha,
          f"{h} CONTROL-1 digest {r['body_sha256'][:16]} == recorded {sha}")
    c2 = [x for x in rows if x["host"] == h and x["tag"].endswith("config-absent")][0]
    check(c2["http_status"] == "405" and c2["allow"] == "POST, OPTIONS"
          and c2["body_bytes"] == 0,
          f"{h} CONTROL-2 /hcp/configuration/<absent> -> 405 + Allow: POST, OPTIONS, 0 B "
          f"(got {c2['http_status']} + {c2['allow']!r}, {c2['body_bytes']} B)")
    c3 = [x for x in rows if x["host"] == h and x["tag"].endswith("hcp-absent")][0]
    check(c3["http_status"] == "404" and c3["body_bytes"] == 0
          and c3["content_type"] == "(none)",
          f"{h} CONTROL-3 /hcp/<absent> -> 404, 0 B, no Content-Type "
          f"(got {c3['http_status']}, {c3['body_bytes']} B, {c3['content_type']!r})")

print("\n== 4. verdict matrix (read from the ledger) ==")
print(f"{'host':<32}{'subtree':<16}{'depth 1':<18}{'depth 2':<18}{'Allow'}")
matrix = {}
for h in HOSTS:
    for c in cands:
        r1 = [x for x in rows if x["host"] == h and x["path"] == f"/hcp/{c}/{ABSENT}"][0]
        r2 = [x for x in rows if x["host"] == h and x["path"] == f"/hcp/{c}/{ABSENT}/zz"][0]
        k1 = (r1["http_status"], r1["body_bytes"], r1["content_type"], r1["allow"])
        k2 = (r2["http_status"], r2["body_bytes"], r2["content_type"], r2["allow"])
        matrix[(h, c)] = (k1, k2)
        print(f"{h:<32}/hcp/{c+'/':<11}{str(k1):<18}{str(k2):<18}{r1['allow']}")
    ref = [x for x in rows if x["host"] == h and x["tag"].endswith("config-absent")][0]
    print(f"{h:<32}/hcp/configuration/ {'ref':<17}"
          f"{(ref['http_status'], ref['body_bytes'], ref['allow'])}")

same_shape = all(k1 == k2 for k1, k2 in matrix.values())
check(same_shape, "depth 1 and depth 2 agree on every (host, subtree) — no mix to report")
n405 = sum(1 for k1, _ in matrix.values() if k1[0] == "405")
n404 = sum(1 for k1, _ in matrix.values() if k1[0] == "404")
print(f"\n  cells: {n404} x 404, {n405} x 405 across {len(matrix)} (host, subtree) pairs")
check(n405 == 0 and n404 == len(matrix),
      f"all {len(matrix)} derived-subtree cells answer 404, 0 B, no Content-Type — "
      f"the constant does NOT reach them")
check(all(c[1] == 0 for pair in matrix.values() for c in pair),
      "every cell is 0 B")
check(all(c[2] == "(none)" for pair in matrix.values() for c in pair),
      "no cell carries a Content-Type (so none is the 5518 B SPA fallback, area AK)")

print("\n== 5. clock A — t_sent ==")
gaps = []
per_host = {h: sorted([r for r in rows if r["host"] == h], key=lambda r: r["seq"]) for h in HOSTS}
expected_gaps = sum(len(v) - 1 for v in per_host.values())
print(f"  grouping discipline: group by host, sort by seq, then zip.")
print(f"  expected gaps sum(rows_per_host - 1) = "
      f"{' + '.join(str(len(v) - 1) for v in per_host.values())} = {expected_gaps}")

from datetime import datetime


def parse(t):
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ")


neg = []
for h, v in per_host.items():
    for a, b in zip(v, v[1:]):
        g = (parse(b["t_sent"]) - parse(a["t_sent"])).total_seconds()
        gaps.append(g)
        dur = (parse(a["t_done"]) - parse(a["t_sent"])).total_seconds()
        if dur < 0:
            neg.append((a["seq"], round(dur, 3)))
check(len(gaps) == expected_gaps, f"gap count {len(gaps)} == {expected_gaps}")
under25 = sorted([g for g in gaps if g < 2.5])
seq_of_gap = []
for h, v in per_host.items():
    for a, b in zip(v, v[1:]):
        g = (parse(b["t_sent"]) - parse(a["t_sent"])).total_seconds()
        seq_of_gap.append((g, a["seq"], b["seq"]))
short = sorted([x for x in seq_of_gap if x[0] < 2.5])
print(f"  pairs under 2.5 s: {[(round(g,3), f'{a}->{b}') for g, a, b in short]}")
under20 = sorted([g for g in gaps if g < 2.0])
print(f"  gaps {len(gaps)}  min {min(gaps):.3f} s  median {statistics.median(gaps):.3f} s  "
      f"max {max(gaps):.3f} s")
print(f"  under 2.5 s: {len(under25)}  {[round(x,3) for x in under25]}")
print(f"  under 2.0 s: {len(under20)}  {[round(x,3) for x in under20]}")
print(f"  impossible negative DURATIONS (t_done < t_sent): {neg if neg else 'none'}")

print("\n== 6. clock B — kernel body mtimes, with a liveness proof ==")
scratch = os.environ.get("AR_SCRATCH",
                         "/home/jack/projects/carelink-api-research/.loop/ar-scratch")
bodies = []
for r in rows:
    p = os.path.join(scratch, r["tag"] + ".b")
    bodies.append((r["seq"], r["host"], os.stat(p).st_mtime if os.path.exists(p) else None))
ok = [b for b in bodies if b[2] is not None]
distinct = len({b[2] for b in ok})
print(f"  bodies stat-able {len(ok)} of {len(rows)}   DISTINCT mtimes {distinct} of {len(ok)}")
if distinct < len(ok) or not ok:
    print("  CLOCK B IS NOT LIVE — mtimes are not distinct across requests (or no body is "
          "stat-able), so they are not a request clock. ONE CLOCK ONLY is claimed; clock A "
          "above is the sole spacing record.")
    check(False,
          "clock B liveness proof: distinct request-time mtimes across requests — FAILED, so "
          "no second clock is claimed. This check is EXPECTED to fail; it is here so the "
          "absence of clock B is a recorded result, not a silent omission")
else:
    mgaps, mper = [], {h: sorted([b for b in ok if b[1] == h], key=lambda b: b[0]) for h in HOSTS}
    for h, v in mper.items():
        for a, b in zip(v, v[1:]):
            mgaps.append(b[2] - a[2])
    print(f"  clock B PROVEN LIVE by {distinct} distinct request-time mtimes.")
    print(f"  gaps {len(mgaps)}  min {min(mgaps):.3f} s  median {statistics.median(mgaps):.3f} s  "
          f"max {max(mgaps):.3f} s")
    print(f"  under 2.5 s: {len([g for g in mgaps if g < 2.5])}")
    check(len(mgaps) == expected_gaps, f"clock B gap count {len(mgaps)} == {expected_gaps}")
    check(min(mgaps) >= 2.5, f"clock B floor {min(mgaps):.3f} s >= 2.5 s")

print("\n== 7. derivation arithmetic ==")
dtxt = open(os.path.join(d, "derive.txt")).read()
check("reproduces=True" in dtxt, "derive.txt: bundle digest reproduces the value area AB pinned")
check("VERDICT: PROCEED" in dtxt, "derive.txt: derivation returned a third subtree")
check(len(cands) == 3, f"candidates.txt holds {len(cands)} subtrees (the ranked top 3)")
check(itemised == CAP, f"18 = 3 x 2 + 3 x 2 x 2 = {itemised}")

print("\n" + ("VERIFY: ALL CHECKS PASSED" if not fail else f"VERIFY: {len(fail)} CHECK(S) FAILED"))
for f in fail:
    print("  - " + f)
sys.exit(0 if not fail else 1)
