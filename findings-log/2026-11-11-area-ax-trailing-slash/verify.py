#!/usr/bin/env python3
"""Area AX — re-derive every figure in FINDINGS.md from results.jsonl. ZERO requests.

Rule (AGENTS.md §6 item 5): prose is derived from the ledger, never from another
prose summary. Every table in FINDINGS.md is printed here, so a number that drifts
from the ledger shows up as a diff in this output rather than as a plausible-looking
sentence there.

Both spacing clocks are reported, because this harness is one flagged cell short of
a clean series (see the harness_note on seq 10) and one clock is not enough to say
anything about the delay (`docs/09` §4).

Usage: verify.py [<scratch-dir>]     # scratch dir only enables clock B
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "results.jsonl")
ROWS = [json.loads(l) for l in open(LEDGER) if l.strip()]
CAP = 10

# The recorded expected values, asserted rather than assumed.
C1_STATUS, C1_BYTES, C1_DIGEST_PREFIX = "200", 97, "370e3bba0d28"
C2_STATUS, C2_BYTES = "404", 0
ENTRY_DIGEST = "0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d"
ENTRY_BYTES = 5518

print(f"== rows: {len(ROWS)}   cap: {CAP}   over cap: {len(ROWS) > CAP}   rows over cap: "
      f"{max(0, len(ROWS) - CAP)} ==")
print(f"== curl_exit != 0 (FAILURES, never absences): "
      f"{[r['seq'] for r in ROWS if r['curl_exit'] != 0]} ==")
print(f"== hosts contacted: {sorted({r['host'] for r in ROWS})} ==")
print(f"== servers: {sorted({r['server'] for r in ROWS})} ==")

print("\n== CONTROLS ==")
c1 = next(r for r in ROWS if r["seq"] == 1)
c2 = next(r for r in ROWS if r["seq"] == 2)
c1_ok = (c1["http_status"] == C1_STATUS and c1["body_bytes"] == C1_BYTES
         and c1["body_sha256"].startswith(C1_DIGEST_PREFIX))
c2_ok = (c2["http_status"] == C2_STATUS and c2["body_bytes"] == C2_BYTES
         and c2["content_type"] == "(none)")
print(f"  C1 {c1['path']:50s} {c1['http_status']} {c1['body_bytes']:5d}B "
      f"sha={c1['body_sha256'][:16] or '-'}  {'PASS' if c1_ok else 'FAIL'}")
print(f"  C2 {c2['path']:50s} {c2['http_status']} {c2['body_bytes']:5d}B "
      f"ct={c2['content_type']}  {'PASS' if c2_ok else 'FAIL'}")
print(f"  controls: {'BOTH PASS' if (c1_ok and c2_ok) else 'A CONTROL FAILED — pair cells are void'}")

print("\n== THE PAIRS ==")
by = {r["seq"]: r for r in ROWS}


def v(seq):
    r = by[seq]
    return (f"{r['http_status']} / {r['body_bytes']}B / ct={r['content_type']} / "
            f"sha={(r['body_sha256'][:16] or '-')}")


for name, a, b in (("APEX   /", 3, 4), ("PAIR A /app", 5, 6), ("PAIR B /hcp/configuration", 7, 8)):
    ra, rb = by[a], by[b]
    same = (ra["body_sha256"] == rb["body_sha256"] and ra["body_bytes"] == rb["body_bytes"]
            and ra["http_status"] == rb["http_status"])
    print(f"  {name:26s} bare {ra['path']:22s} {v(a)}")
    print(f"  {'':26s} slsh {rb['path']:22s} {v(b)}")
    print(f"  {'':26s} -> {'IDENTICAL' if same else 'DIFFER'}")

print(f"\n  ANCHOR /hcp                {v(9)}")
print(f"  REFERENCE /hcp/configuration/<absent>  {v(10)} allow={by[10]['allow']}")

print("\n== ENTRY-DOCUMENT IDENTITY (cmp, not eyeball) ==")
for seq in (3, 4, 5, 6, 9):
    r = by[seq]
    is_entry = (r["body_sha256"] == ENTRY_DIGEST and r["body_bytes"] == ENTRY_BYTES)
    print(f"  seq {seq:2d} {r['path']:22s} entry-document={is_entry}")

print("\n== STATUS HISTOGRAM ==")
for s in sorted({r["http_status"] for r in ROWS}):
    print(f"  {s}: {sum(1 for r in ROWS if r['http_status'] == s)}")

CTRL_HDRS = ('content-security-policy', 'x-frame-options', 'strict-transport-security',
             'x-content-type-options', 'x-cache')
print("\n== THE CONTROL-PLANE HEADER PLANE ==")
print("  read from the RAW response headers where the scratch dir is available, because")
print("  results.jsonl's KEEP filter does not retain these names on every row.")
print(f"  {'seq':>3} {'status':>6} {'bytes':>6}  " + "  ".join(f"{h[:18]:18s}" for h in CTRL_HDRS))
for r in sorted(ROWS, key=lambda r: r["seq"]):
    names = set(h.lower() for h in r["headers"])
    if len(sys.argv) > 1:
        hp = os.path.join(sys.argv[1], r["tag"] + ".h")
        if os.path.exists(hp):
            names = set()
            for line in open(hp, "rb").read().decode("latin-1").splitlines():
                if ":" in line:
                    names.add(line.split(":", 1)[0].strip().lower())
    print(f"  {r['seq']:3d} {r['http_status']:>6} {r['body_bytes']:6d}  "
          + "  ".join(f"{('YES' if h in names else '-'):18s}" for h in CTRL_HDRS))

print("\n== CLOCK A: t_sent ==")
def ts(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")
sent = [ts(r["t_sent"]) for r in sorted(ROWS, key=lambda r: r["seq"])]
gaps = [(sent[i + 1] - sent[i]).total_seconds() for i in range(len(sent) - 1)]
if gaps:
    print(f"  rows {len(ROWS)}  same-host gaps {len(gaps)}  (expected sum(rows_per_host - 1) = "
          f"{len(ROWS) - 1} on ONE host)")
    print(f"  min {min(gaps):.3f} s  max {max(gaps):.3f} s  mean {sum(gaps)/len(gaps):.3f} s")
    print(f"  under declared 2.5 s: {sum(1 for g in gaps if g < 2.5)}")
    print(f"  under repository 2.0 s floor: {sum(1 for g in gaps if g < 2.0)}")
    for i, g in enumerate(gaps):
        if g < 2.5:
            print(f"    SHORT seq->{i+2} {g:.3f} s")
neg = [(r["seq"], (ts(r["t_done"]) - ts(r["t_sent"])).total_seconds())
       for r in ROWS if ts(r["t_done"]) < ts(r["t_sent"])]
print(f"  impossible durations (t_done < t_sent): {len(neg)} {neg}")

if len(sys.argv) > 1:
    sc = sys.argv[1]
    print("\n== CLOCK B: kernel body mtimes (NOT re-derivable from a clone) ==")
    mt = []
    for r in sorted(ROWS, key=lambda r: r["seq"]):
        p = os.path.join(sc, r["tag"] + ".b")
        mt.append((r["seq"], os.path.getmtime(p)) if os.path.exists(p) else (r["seq"], None))
    have = [(s, m) for s, m in mt if m is not None]
    print(f"  bodies stat-able {len(have)} of {len(ROWS)}")
    if len(have) > 1:
        g2 = [have[i + 1][1] - have[i][1] for i in range(len(have) - 1)]
        print(f"  same-host gaps {len(g2)}  min {min(g2):.3f} s  max {max(g2):.3f} s  "
              f"mean {sum(g2)/len(g2):.3f} s")
        print(f"  under declared 2.5 s: {sum(1 for g in g2 if g < 2.5)}")
        print(f"  under repository 2.0 s floor: {sum(1 for g in g2 if g < 2.0)}")
        # A second clock is only a clock if request-time mtimes are DISTINCT.
        distinct = len({round(m, 3) for _, m in have})
        print(f"  distinct mtimes: {distinct} of {len(have)} — second clock is "
              f"{'LIVE' if distinct == len(have) else 'NOT LIVE, report one clock only'}")
else:
    print("\n== CLOCK B: not run (pass the scratch dir to enable) ==")
