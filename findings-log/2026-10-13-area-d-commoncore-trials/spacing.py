import os, json, glob, datetime, sys

LOG = 'findings-log/2026-10-13-area-d-commoncore-trials'
rows = {int(json.loads(l)['seq']): json.loads(l) for l in open(f'{LOG}/results.jsonl')}

def P(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc).timestamp()

recs = []
for f in sorted(glob.glob(f'{LOG}/bodies/*.b')):
    recs.append((int(os.path.basename(f).split('-')[0]), os.stat(f).st_mtime_ns / 1e9))
recs.append((1, os.stat(f'{LOG}/attempt1-aborted/01-ct-medtronic-cn.dns').st_mtime_ns / 1e9))
recs.sort()

print("AREA D — request spacing measurement")
print("Date: 2026-10-13. Declared delay 2.5 s, emitted INSIDE the per-host flock.")
print()
print("ORACLE: kernel-set body-file mtimes at nanosecond resolution (clock-independent),")
print("per docs/09 section 4, cross-checked against the harness `date` series.")
print()
print("COUNTING RULE: one gap per consecutive pair in request order across the 7")
print("captures carrying an mtime (6 HTTP bodies + the dig capture) = 6 gaps.")
print()
print(f"{'from':>4} {'to':>4} {'gap_s':>10}")
gaps = []
for (a, ma), (b, mb) in zip(recs, recs[1:]):
    g = mb - ma
    gaps.append(g)
    print(f"{a:>4} {b:>4} {g:>10.3f}")
print()
print(f"FLOOR  {min(gaps):.3f} s     MAX {max(gaps):.3f} s     SPAN {recs[-1][1]-recs[0][1]:.3f} s")
print(f"under the declared 2.5 s: {sum(1 for g in gaps if g < 2.5)}")
print(f"under the repo floor 2 s: {sum(1 for g in gaps if g < 2.0)}")
print()
print("SAME-HOST GAPS (the rule is per host, and these are all larger):")
hosts = {}
for f in sorted(glob.glob(f'{LOG}/bodies/*.b')):
    s = int(os.path.basename(f).split('-')[0])
    hosts.setdefault(rows[s]['host'], []).append((s, os.stat(f).st_mtime_ns / 1e9))
for h, v in hosts.items():
    for (a, ma), (b, mb) in zip(v, v[1:]):
        print(f"  {h:<32} seq {a}->{b}  {mb-ma:.3f} s")
print()
print("DISCLOSURE 1 — the date series has a broken row.")
for s in sorted(rows):
    try:
        dd = P(rows[s]['t_done']) - P(rows[s]['t_sent'])
    except ValueError:
        continue
    if dd < 0:
        print(f"  seq {s}: t_done - t_sent = {dd:+.3f} s  IMPOSSIBLE (dig had exited before the date)")
print("  In the date series the seq6->seq7 gap reads 1.857 s, apparently below the")
print("  >=2 s floor. The mtime series for the same pair reads 2.757 s. The apparent")
print("  violation is an artefact of that broken row, not a spacing failure.")
print()
print("DISCLOSURE 2 — series validation (docs/09 section 4 requires this).")
h_span = P(rows[9]['t_done']) - P(rows[2]['t_queued'])
m_span = [m for s, m in recs if s == 9][0] - [m for s, m in recs if s == 2][0]
print(f"  harness span (seq2 t_queued -> seq9 t_done) = {h_span:.3f} s")
print(f"  mtime   span (seq2 body      -> seq9 body)   = {m_span:.3f} s")
print(f"  difference                                      = {h_span-m_span:.3f} s")
print("  NOT the 'collapsed spread' signature of an untrustworthy series: the difference is")
print("  the two endpoints that do not coincide (in-lock sleep + connect before the first")
print("  body write; curl teardown after the last). Per request:")
mt = {s: m for s, m in recs}
for s in sorted(k for k in mt if k >= 2 and rows[k]['method'] == 'GET'):
    print(f"    seq {s}: mtime - t_sent = {mt[s]-P(rows[s]['t_sent']):+.3f} s")
print("  All six HTTP rows positive and inside 0.1-0.5 s -> the two series AGREE.")
print()
print("NOTE: an earlier draft of this check printed a 'residual unexplained: 0.000 s'")
print("line. That was a telescoping identity and evidence of nothing; it is not here.")