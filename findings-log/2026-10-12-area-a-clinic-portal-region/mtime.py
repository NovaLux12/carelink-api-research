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

EXIT CODE — READ THIS BEFORE TRUSTING THE OUTPUT
------------------------------------------------
    0  the series VALIDATED and no negative gap: the oracle was available and the
       reported result is derived from the measured values
    1  the series could NOT be validated, or a negative gap was found: NO RESULT

**A clean clone is EXPECTED TO EXIT 1.** git does not preserve mtimes, so
`git archive` / a fresh clone hands every body the same mtime and the oracle has
nothing to measure. That run correctly reports "not trustworthy" instead of
asserting a result. An earlier revision of this file printed a hardcoded
CONCLUSION on exactly that input — claiming "no gap below the declared 2.5 s"
while its own table showed 0 of 10 — and still exited 0. That is the AGENTS.md
section 1 failure (a sentence that cannot be traced to a source) wearing the
section 6.5 shape (prose contradicting its own table). Every sentence below is now
computed from the measurements.

VALIDITY TESTS — each one CAN fail, and each has failed in practice
--------------------------------------------------------------------
  V1 collapse      the usable bodies must not all share one mtime
  V2 span          mtime gaps and run.log gaps must agree to within 1 s per pair
  V3 alignment     the denominator enumerated from results.jsonl must equal the one
                   derived independently from run.log, and the two seq sets must match

WHAT IT STILL CANNOT DO
-----------------------
1. Only rows with a committed body carry an mtime, and the four 3.3-3.4 MB asset
   bodies were deliberately NOT committed, so some gaps are uncheckable and the
   denominator below counts them.
2. **git does not preserve mtimes**, so this is reproducible only on the machine
   that ran the pass. Hence V1/V2 and the non-zero exit above.
3. An mtime marks when curl finished writing the body, so
   gap = 2.5 s sleep + overhead + dur[n+1] - dur[n]: a faster later request can
   shrink a measured gap below the sleep. A gap >= 2.5 s is therefore the
   meaningful direction; a gap < 2.5 s would not be conclusive on its own.

Usage: python3 mtime.py
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECLARED_SLEEP = 2.5
FLOOR = 2.0          # the repo's real rule, docs/09 s4
TOLERANCE = 1.0      # s, per pair, for the span test (V2)

rows = [json.loads(l) for l in open(os.path.join(HERE, 'results.jsonl'))]

t0 = {}
rl_seq_host = []
for line in open(os.path.join(HERE, 'run.log')):
    if not line.startswith('2026-'):
        continue
    ts, rest = line.split(' ', 1)
    m = re.search(r'seq=(\d+)', rest)
    if m:
        seq = int(m.group(1))
        t0[seq] = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ')
        h = re.search(r'host=(\S+)', rest)
        if h:
            rl_seq_host.append((seq, h.group(1)))

# the ledger's body_bytes must equal the file on disk, so a stale or truncated
# file cannot pose as an oracle
#
# TIMEZONE, and why the conversion is not optional: run.log is written by `date -u`,
# so its timestamps are UTC. A filesystem mtime is an epoch instant, and
# fromtimestamp() renders it in LOCAL time. Comparing local wall time against UTC
# logs silently shifts every reading by the machine's UTC offset. That offset is
# constant across a run, so it cancels out of every DIFFERENCE and the bug stays
# invisible for this pass — it would surface on a machine in another timezone, or
# across a DST boundary mid-run. Convert explicitly rather than relying on the
# offset cancelling.
bodies = {}
for r in rows:
    p = os.path.join(HERE, 'headers', r['host_tag'] + '.b')
    if os.path.exists(p) and os.stat(p).st_size == r['body_bytes']:
        bodies[r['seq']] = datetime.datetime.fromtimestamp(
            os.stat(p).st_mtime, datetime.timezone.utc).replace(tzinfo=None)

hosts = list(dict.fromkeys(r['host'] for r in rows))
print(f"rows: {len(rows)}   distinct hosts: {len(hosts)}   usable committed bodies: {len(bodies)}")
print(f"declared sleep: {DECLARED_SLEEP}s   repo floor: {FLOOR}s   V2 tolerance: +-{TOLERANCE}s\n")

print(f"{'pair':<10} {'host':<32} {'run.log':>8} {'mtime':>10}  verdict")
pairs = []
for host in hosts:
    seqs = [r['seq'] for r in sorted((r for r in rows if r['host'] == host), key=lambda r: r['seq'])]
    for a, b in zip(seqs, seqs[1:]):
        lg = (t0[b] - t0[a]).total_seconds()
        if a in bodies and b in bodies:
            mg = (bodies[b] - bodies[a]).total_seconds()
            pairs.append((a, b, lg, mg))
            print(f"  {a:>3}->{b:<3}  {host:<32} {lg:>6.0f}s {mg:>9.3f}s")
        else:
            pairs.append((a, b, lg, None))
            print(f"  {a:>3}->{b:<3}  {host:<32} {lg:>6.0f}s {'n/a':>10}  asset body not committed")

checked = [p for p in pairs if p[3] is not None]
total = len(pairs)
neg = [p for p in checked if p[3] < 0]

# ---- V3 alignment: derive the denominator from run.log, not from results.jsonl ----
# Two earlier attempts at this test were tautologies and are recorded so nobody
# rebuilds them:
#   (a) comparing the enumerated total to len(rows) - n_hosts — algebraically equal
#       by construction, so it can never fail;
#   (b) counting only ADJACENT-IN-TIME same-host pairs from run.log — that is a
#       DIFFERENT quantity (14 here, not 15), because seq 12 and seq 20 both go to
#       carelink-support.medtronic.com but seq 13-19 sit between them. The rule this
#       file checks is "no two requests to the same host closer than 2 s", which is
#       the PER-HOST grouping; the adjacent-in-time count answers a different
#       question. Comparing the two is not a validity test, it is a category error.
# run.log is an INDEPENDENT record of the same run: it carries its own (seq, host)
# stream. Grouping THAT by host must reproduce the same denominator, and the two seq
# sets must match, or one of the ledgers has drifted.
rl_by_host = {}
for seq, host in rl_seq_host:
    rl_by_host.setdefault(host, []).append(seq)
rl_gaps = sum(len(v) - 1 for v in rl_by_host.values())
rl_seqs = {s for s, _ in rl_seq_host}
jl_seqs = {r['seq'] for r in rows}
v3_total_ok = (total == rl_gaps)
v3_seq_ok = (rl_seqs == jl_seqs)
v3_ok = v3_total_ok and v3_seq_ok
if v3_ok:
    v3_why = ""
elif not v3_total_ok:
    v3_why = f"  (results.jsonl enumerates {total} gaps, run.log grouped by host yields {rl_gaps})"
else:
    only_rl = sorted(rl_seqs - jl_seqs)
    only_jl = sorted(jl_seqs - rl_seqs)
    v3_why = (f"  (per-host gap totals agree at {total}, but the seq sets differ: "
              f"run.log-only {only_rl}, results.jsonl-only {only_jl})")

# ---- V1 collapse -----------------------------------------------------------
distinct_mtimes = len({bodies[p[0]] for p in checked} | {bodies[p[1]] for p in checked})
v1_ok = bool(checked) and distinct_mtimes > 1

# ---- V2 span ---------------------------------------------------------------
# On a valid run each checkable pair's mtime gap tracks its run.log gap to within
# TOLERANCE. A collapsed series has mtime gaps of 0.000 against logged gaps of 2-84s.
v2_bad = [(a, b, lg, mg) for a, b, lg, mg in checked if abs(mg - lg) > TOLERANCE]
v2_ok = bool(checked) and not v2_bad

valid = v1_ok and v2_ok and v3_ok and not neg

print()
print(f"same-host gaps:            {total}   (run.log derives {rl_gaps} independently)")
print(f"checkable (mtime oracle):  {len(checked)} of {total}")
print(f"negative mtime gaps:       {len(neg)}")
print(f"run.log gaps below {DECLARED_SLEEP}s:   {sum(1 for p in pairs if p[2] < DECLARED_SLEEP)} of {total}")
print(f"run.log gaps below {FLOOR}s:  {sum(1 for p in pairs if p[2] < FLOOR)} of {total}")
if checked:
    mgs = [p[3] for p in checked]
    print(f"mtime gaps >= {DECLARED_SLEEP}s:      {sum(1 for g in mgs if g >= DECLARED_SLEEP)} of {len(checked)}")
    print(f"minimum mtime gap:          {min(mgs):.3f}s")
    print(f"distinct mtimes (V1):       {distinct_mtimes} of {2 * len(checked)} endpoints")

print()
print("VALIDITY")
print(f"  V1 mtimes not collapsed          {'PASS' if v1_ok else 'FAIL'}"
      f"{'' if v1_ok else f'  ({distinct_mtimes} distinct mtime across {len(checked)} checkable pairs)'}")
print(f"  V2 mtime gaps track run.log      {'PASS' if v2_ok else 'FAIL'}"
      f"{'' if v2_ok else f'  ({len(v2_bad)} of {len(checked)} pairs differ by more than {TOLERANCE}s)'}")
print(f"  V3 denominator agrees            {'PASS' if v3_ok else 'FAIL'}"
      f"{v3_why}")
print(f"  no negative mtime gap            {'PASS' if not neg else 'FAIL'}")

print()
if not valid:
    print("RESULT: NO RESULT — this mtime series is NOT trustworthy, so no claim is made")
    print("about the true intervals. Most likely cause: git did not preserve mtimes,")
    print("which collapses every body to the same timestamp. Re-run on the machine")
    print("that performed the probe. See this file's docstring.")
    sys.exit(1)

# ---- everything below is DERIVED from the measurements above ----------------
short = [p for p in checked if p[2] < DECLARED_SLEEP]
short_ge = [p for p in short if p[3] >= DECLARED_SLEEP]
min_mg = min(p[3] for p in checked)
n_ge = sum(1 for p in checked if p[3] >= DECLARED_SLEEP)

print("RESULT (bounded, this pass only). Derived from the table above:")
print(f"  {len(checked)} of {total} same-host gaps were checkable by the mtime oracle.")
print(f"  Of those, {n_ge} measure >= the declared {DECLARED_SLEEP}s; minimum {min_mg:.3f}s.")
print(f"  {len(neg)} negative gaps, so no corrupt-t0 signature.")
if short:
    verdict = ("all" if len(short_ge) == len(short) else
               f"{len(short_ge)} of {len(short)}")
    print(f"  Of the {len(short)} pairs run.log logged below {DECLARED_SLEEP}s, {verdict} measure "
          f">= {DECLARED_SLEEP}s by mtime:")
    for a, b, lg, mg in short:
        print(f"    seq {a}->{b} ({lg:.0f}s logged) -> {mg:.3f}s measured")
    if len(short_ge) == len(short):
        print(f"  => no gap in THIS PASS was actually shorter than the declared {DECLARED_SLEEP}s.")
    else:
        print(f"  => {len(short) - len(short_ge)} pair(s) were genuinely shorter; not explained here.")
else:
    print("  No pair was logged below the declared sleep, so this cross-check adds nothing.")
print()
print("This does NOT establish a cause for docs/09's open question, which concerns")
print("areas B, X and Z, and it is NOT re-derivable from a clean clone (git does not")
print("preserve mtimes — hence the non-zero exit on such a run). See this docstring.")
sys.exit(0)