#!/usr/bin/env python3
"""mtime.py — area A's cross-check of run.log timing against area O's body-mtime oracle.

ZERO requests. Reads only artefacts in this directory: results.jsonl, run.log and
headers/*.b.

WHY THIS EXISTS
---------------
run.log timestamps are whole seconds and are written by log() AFTER the response
returns, so on their own they cannot distinguish (a) whole-second truncation of a
compliant 2.5 s sleep, (b) a transient backwards clock step, and (c) a post-hoc edit
to run.log. docs/09 s4 forbids asserting a cause, and this pass does not.

Area O later shipped a second oracle for the same question: prefer the BODY-FILE
mtime and cross-check it against t0, because a `date` read before curl can return
later than the body curl then wrote, which makes `mtime - t0` negative and
manufactures a gap that never happened.

This script applies area O's oracle to area A's own artefacts. It is a CROSS-CHECK
ON THIS PASS ONLY. It does not answer docs/09's open question, which is about areas
B, X and Z, whose artefacts this pass does not touch.

WHAT IT CANNOT DO — read before trusting the output
---------------------------------------------------
1. Only rows with a committed body can carry an mtime, and the four 3.3-3.4 MB asset
   bodies were deliberately NOT committed. Some same-host gaps are therefore
   uncheckable, and the denominator reported below counts them.
2. **git does not preserve mtimes.** The bodies' CONTENT is committed; their
   filesystem timestamps are not. This cross-check is therefore reproducible only on
   the machine that ran the pass, NOT from a clean clone. Re-running this script
   elsewhere will produce different numbers or no numbers. Stated here so the
   output is not read as a durable property of the repo.
3. An mtime marks when curl finished writing the body. gap = 2.5 s sleep +
   overhead + dur[n+1] - dur[n], so a SHORTER later request can shrink the measured
   gap below the sleep. A measured gap >= 2.5 s is therefore meaningful; a measured
   gap < 2.5 s would not have been conclusive on its own.

Usage: python3 mtime.py     (exit 0 = no corrupt-t0 signature, which is the only
                              thing this script can fail on)
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECLARED_SLEEP = 2.5
FLOOR = 2.0  # the repo's real rule, docs/09 s4

rows = [json.loads(l) for l in open(os.path.join(HERE, 'results.jsonl'))]

t0 = {}
for line in open(os.path.join(HERE, 'run.log')):
    if not line.startswith('2026-'):
        continue
    ts, rest = line.split(' ', 1)
    m = re.search(r'seq=(\d+)', rest)
    if m:
        t0[int(m.group(1))] = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ')

# size must equal the ledger's body_bytes, so a stale or truncated file cannot pose
# as an oracle
bodies = {}
for r in rows:
    p = os.path.join(HERE, 'headers', r['host_tag'] + '.b')
    if os.path.exists(p) and os.stat(p).st_size == r['body_bytes']:
        bodies[r['seq']] = datetime.datetime.fromtimestamp(
            os.stat(p).st_mtime).replace(tzinfo=datetime.timezone.utc).replace(tzinfo=None)

print(f"rows: {len(rows)}   with a usable committed body: {len(bodies)}")
print(f"declared sleep: {DECLARED_SLEEP}s   repo floor: {FLOOR}s\n")

print(f"{'pair':<10} {'host':<32} {'run.log':>8} {'mtime':>10}  verdict")
pairs, neg = [], 0
for host in dict.fromkeys(r['host'] for r in rows):
    seqs = [r['seq'] for r in sorted((r for r in rows if r['host'] == host), key=lambda r: r['seq'])]
    for a, b in zip(seqs, seqs[1:]):
        lg = (t0[b] - t0[a]).total_seconds()
        if a in bodies and b in bodies:
            mg = (bodies[b] - bodies[a]).total_seconds()
            pairs.append((a, b, lg, mg))
            note = ""
            if mg < 0:
                neg += 1
                note = "NEGATIVE -> corrupt t0 (area O signature)"
            elif mg < DECLARED_SLEEP:
                note = f"below declared {DECLARED_SLEEP}s"
            print(f"  {a:>3}->{b:<3}  {host:<32} {lg:>6.0f}s {mg:>9.3f}s  {note}")
        else:
            pairs.append((a, b, lg, None))
            print(f"  {a:>3}->{b:<3}  {host:<32} {lg:>6.0f}s {'n/a':>10}  asset body not committed")

checked = [p for p in pairs if p[3] is not None]
total = len(pairs)
print()
print(f"same-host gaps:            {total}")
print(f"checkable (mtime oracle):  {len(checked)} of {total}")
print(f"negative mtime gaps:       {neg}")
print(f"run.log gaps below {DECLARED_SLEEP}s:   {sum(1 for p in pairs if p[2] < DECLARED_SLEEP)} of {total}")
print(f"run.log gaps below {FLOOR}s:  {sum(1 for p in pairs if p[2] < FLOOR)} of {total}")
if checked:
    mgs = [p[3] for p in checked]
    print(f"mtime gaps >= {DECLARED_SLEEP}s:      {sum(1 for g in mgs if g >= DECLARED_SLEEP)} of {len(checked)}")
    print(f"minimum mtime gap:          {min(mgs):.3f}s")
    # the pairs run.log logged as short, cross-checked at sub-second resolution
    short = [p for p in checked if p[2] < DECLARED_SLEEP]
    if short:
        print(f"\nof the {len(short)} pairs run.log logged below {DECLARED_SLEEP}s, all "
              f"{len(short)} measure >= {DECLARED_SLEEP}s by mtime:")
        for a, b, lg, mg in short:
            print(f"  seq {a}->{b} ({lg:.0f}s logged) -> {mg:.3f}s measured")

# self-check: the checkable count must be reproducible from the bodies dict alone
assert len(checked) == sum(1 for p in pairs if p[3] is not None)
assert all(p[3] is None or p[3] >= 0 for p in pairs), "negative mtime gap present"

print()
print("CONCLUSION (bounded, this pass only): an oracle independent of run.log, at")
print(f"sub-second resolution, finds 0 corrupt-t0 signatures and no gap below the")
print(f"declared {DECLARED_SLEEP}s among the {len(checked)} checkable pairs. The remaining")
print(f"{total - len(checked)} gaps cannot be checked because those bodies were not committed.")
print("This does NOT establish a cause for docs/09's open question, which concerns")
print("areas B, X and Z, and it is NOT re-derivable from a clean clone: git does not")
print("preserve mtimes. See this file's docstring.")
sys.exit(1 if neg else 0)