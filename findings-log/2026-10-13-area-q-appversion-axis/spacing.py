#!/usr/bin/env python3
"""Area Q — spacing oracle. ZERO requests.

Two independent series, because docs/09 section 4 records that the harness's own
`date` series is the suspect instrument (four passes recorded impossible negative
durations):

  A. t_sent / t_done from results.jsonl  - what the harness wrote
  B. body-file mtimes                     - set by the KERNEL at write time,
                                            independent of the harness clock

Series B is only usable if it is the run's own: git does not preserve mtimes, so
on a fresh clone every body carries the checkout time and the spread collapses to
0.0 s. Validation: B's span must equal A's span. Both are reported; neither is
reported instead of the other.

Counting rule (stated so it is reproducible, from docs/09 section 4): one gap per
consecutive pair in REQUEST ORDER from results.jsonl, per host. N bodies -> N-1
gaps per host.
"""
import datetime
import json
import pathlib
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
rows = [json.loads(l) for l in (HERE / "results.jsonl").read_text().splitlines() if l.strip()]


def parse(ts):
    return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")


print("=" * 78)
print("LEDGER")
print("=" * 78)
print(f"rows in results.jsonl            : {len(rows)}")
print(f"distinct hosts                   : {sorted({r['host'] for r in rows})}")
print(f"methods                          : {sorted({r['method'] for r in rows})}")
by_seq = defaultdict(list)
for r in rows:
    by_seq[r["seq"]].append(r)
dupe = {s: v for s, v in by_seq.items() if len(v) > 1}
print(f"repeated seq values              : {sorted(dupe)}")
for s, v in sorted(dupe.items()):
    print(f"   seq={s} issued {len(v)} times, t_sent {v[0]['t_sent']} and {v[1]['t_sent']}")

print()
print("=" * 78)
print("ORACLE A — harness t_sent series")
print("=" * 78)
per_host = defaultdict(list)
for r in rows:
    per_host[r["host"]].append(r)
gaps_a, dur_bad = [], []
for host, rs in per_host.items():
    rs = sorted(rs, key=lambda r: r["seq"])
    for x, y in zip(rs, rs[1:]):
        g = (parse(y["t_sent"]) - parse(x["t_sent"])).total_seconds()
        gaps_a.append((host, x["seq"], y["seq"], g))
    for r in rs:
        d = (parse(r["t_done"]) - parse(r["t_sent"])).total_seconds()
        if d < 0:
            dur_bad.append((r["seq"], d))
    span = (parse(rs[-1]["t_sent"]) - parse(rs[0]["t_sent"])).total_seconds()
    print(f"{host:26} {len(rs)} rows, {len(rs)-1} gaps, t_sent span {span:8.3f} s")
for host, a, b, g in gaps_a:
    flag = "  <-- UNDER 2 s" if g < 2.0 else ("  <-- under declared 2.5" if g < 2.5 else "")
    print(f"   {host:26} seq {a:>2} -> {b:>2}  {g:8.3f} s{flag}")
print(f"minimum same-host t_sent gap     : {min(g[3] for g in gaps_a):.3f} s")
print(f"negative durations (impossible)  : {dur_bad if dur_bad else 'none'}")

print()
print("=" * 78)
print("ORACLE B — kernel body-mtime series (independent of the harness clock)")
print("=" * 78)
# The harness reuses bodies/<host_tag>.b. Two ledger rows sharing a host_tag
# share ONE body file, so the second write overwrote the first and N bodies !=
# N requests. That is a harness defect, it is disclosed here rather than
# smoothed over, and it means those rows contribute no measurable gap. Rows are
# therefore walked in LEDGER ORDER (not sorted by seq, which would collapse the
# duplicate) and each distinct body file contributes exactly one measurement.
gaps_b, tagrows = [], defaultdict(list)
for i, r in enumerate(rows):
    tagrows[r["host_tag"]].append(i)
reused = {t: ix for t, ix in tagrows.items() if len(ix) > 1}
seen, walked = set(), []
for r in rows:
    if r["host_tag"] not in seen:
        seen.add(r["host_tag"])
        walked.append(r)
print(f"ledger rows                       : {len(rows)}")
print(f"distinct body files written       : {len(walked)}")
print(f"host_tags reused by >1 row        : { {t: ix for t, ix in reused.items()} }")
for t, ix in reused.items():
    print(f"   host_tag {t!r} was written by ledger rows {ix} "
          f"(indexes); only the LAST write's mtime survives, so")
    print(f"   the gap between those rows is NOT measurable from the mtime series.")
prev_by_host = {}
for r in walked:
    m = (HERE / "bodies" / f"{r['host_tag']}.b").stat().st_mtime
    if r["host"] in prev_by_host:
        ps, pm = prev_by_host[r["host"]]
        gaps_b.append((r["host"], ps, r["seq"], m - pm))
    prev_by_host[r["host"]] = (r["seq"], m)
for host, rs in per_host.items():
    seqs = [r["seq"] for r in sorted(rs, key=lambda r: r["seq"])]
    span = None
    print(f"{host:26} {len(seqs)} rows {seqs} -> "
          f"{sum(1 for g in gaps_b if g[0] == host)} measurable gaps")
for host, a, b, g in gaps_b:
    flag = "  <-- UNDER 2 s" if g < 2.0 else ("  <-- under declared 2.5" if g < 2.5 else "")
    print(f"   {host:26} seq {a:>2} -> {b:>2}  {g:8.3f} s{flag}")
print(f"minimum same-host mtime gap      : {min(g[3] for g in gaps_b):.3f} s")
print(f"gaps under 2.5 s                 : {sum(1 for g in gaps_b if g[3] < 2.5)} of {len(gaps_b)}")
print(f"gaps under the 2 s floor         : {sum(1 for g in gaps_b if g[3] < 2.0)} of {len(gaps_b)}")

print()
print("=" * 78)
print("SERIES VALIDATION — is oracle B the run's own?")
print("=" * 78)
span_a = (parse(rows[-1]["t_sent"]) - parse(rows[0]["t_sent"])).total_seconds()
mt_all = [(HERE / "bodies" / f"{r['host_tag']}.b").stat().st_mtime for r in rows]
span_b = max(mt_all) - min(mt_all)
print(f"harness t_sent span (seq 1 -> last) : {span_a:8.3f} s")
print(f"kernel mtime span                    : {span_b:8.3f} s")
print(f"difference                           : {abs(span_a - span_b):8.3f} s")
print("verdict: " + ("SERIES B IS THIS RUN'S OWN - trustworthy"
                     if abs(span_a - span_b) < 60 else
                     "SERIES B COLLAPSED - not this run's, do not trust it"))
print()
print("NOTE: git does not preserve mtimes. Oracle B is valid on the machine that")
print("ran the probe and is NOT re-derivable from a clean clone.")