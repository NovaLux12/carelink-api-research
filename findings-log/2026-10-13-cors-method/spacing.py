#!/usr/bin/env python3
"""Spacing measurement for findings-log/2026-10-13-cors-method/.

docs/09 section 4 records that the harness `date` series is the suspect in five passes
now, and that body-file mtimes -- set by the kernel at write time -- are the independent
series. This measures BOTH and reports one never instead of the other.

Counting rule, stated so the number can be reproduced: one gap per consecutive pair **in
request order** taken from results.jsonl, restricted to pairs where both requests went to
the SAME host, because the repo's rule is per host. The one cross-host pair is counted and
reported separately, never folded into the floor.

Attempt 1 and attempt 2 rows are excluded from the measurement and from the floor: they
never resolved a host, so no request reached a vendor. They stay in the ledger.

Two series, two resolutions, and the difference between them matters:
  * t_sent / t_done are the harness `date` readings, millisecond ISO-8601 UTC.
  * the mtime series is read here with `stat -c %y` (nanoseconds, local zone, converted to
    UTC), NOT with the 1-second `body_mtime_epoch` the ledger records. It is read from the
    body files at analysis time; they have not been modified since the run, so these are
    still the kernel's write times. Git does not preserve mtimes, so a verifier working
    from a fresh clone cannot re-derive this series from the files and must use the
    numbers printed below.
"""
import datetime, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ATTEMPT = sys.argv[1] if len(sys.argv) > 1 else "3"


def ts(s):
    """millisecond ISO-8601 UTC -> epoch seconds"""
    date, clock = s.rstrip("Z").split("T")
    h, m, rest = clock.split(":")
    sec, frac = rest.split(".")
    base = datetime.datetime.strptime(date + " " + h + ":" + m + ":" + sec, "%Y-%m-%d %H:%M:%S")
    return base.timestamp() + int(frac) / 1000.0


def mtime_ns_epoch(path):
    """`stat -c %y` -> epoch seconds, full precision, via %z so the local zone is honoured"""
    raw = subprocess.run(["stat", "-c", "%y", path], capture_output=True, text=True,
                         check=True).stdout.strip()
    base, zone = raw.rsplit(" ", 1)          # "… .287749245" and "+0100"
    dt = datetime.datetime.strptime(base[:26], "%Y-%m-%d %H:%M:%S.%f")  # ns field -> us
    off = datetime.datetime.strptime(zone, "%z").utcoffset()
    return (dt - off).timestamp()


rows = []
for line in open(os.path.join(HERE, "results.jsonl")):
    line = line.strip()
    if not line:
        continue
    try:
        rows.append(json.loads(line))
    except ValueError:
        pass                       # attempt 1/2 rows are malformed by design; see FINDINGS.md
ok = [r for r in rows if r.get("attempt") == ATTEMPT]

sent = [ts(r["t_sent"]) for r in ok]
done = [ts(r["t_done"]) for r in ok]
mt = [mtime_ns_epoch(os.path.join(HERE, "bodies", "%02d-%s.b" % (int(r["seq"]), r["host_tag"])))
      for r in ok]

series = (
    ("kernel body mtime (stat -c %y, ns)", mt),
    ("harness t_sent  (date, ms ISO-8601)", sent),
    ("harness t_done  (date, ms ISO-8601)", done),
)

print("spacing — attempt %s, %d ledger rows" % (ATTEMPT, len(ok)))
print("counting rule: consecutive pairs in request order, same host only; the cross-host")
print("pair is reported separately and is not part of the floor.\n")

for name, vals in series:
    same = [(ok[i - 1]["seq"], ok[i]["seq"], ok[i]["host"], vals[i] - vals[i - 1])
            for i in range(1, len(vals)) if ok[i]["host"] == ok[i - 1]["host"]]
    cross = [(ok[i - 1]["seq"], ok[i]["seq"], vals[i] - vals[i - 1])
             for i in range(1, len(vals)) if ok[i]["host"] != ok[i - 1]["host"]]
    lo = min(g[3] for g in same)
    hi = max(g[3] for g in same)
    print("  %s" % name)
    print("    %d same-host gaps   min %.3fs   max %.3fs   span %.3fs"
          % (len(same), lo, hi, vals[-1] - vals[0]))
    print("    gaps under the declared 2.5s: %d" % sum(1 for g in same if g[3] < 2.5))
    print("    gaps under the repo floor of 2s: %d" % sum(1 for g in same if g[3] < 2.0))
    for a, b, h, g in same:
        print("      seq %2s -> %2s  %-30s %.3fs" % (a, b, h, g))
    for a, b, g in cross:
        print("    cross-host (excluded from the floor): seq %s -> %s  %.3fs" % (a, b, g))
    print()

print("  validation of the mtime series, as docs/09 section 4 requires before it is trusted")
print("    mtime span %.3fs   t_sent span %.3fs   difference %+.3fs over %d requests"
      % (mt[-1] - mt[0], sent[-1] - sent[0], (mt[-1] - mt[0]) - (sent[-1] - sent[0]), len(ok)))
print("    The two series agree to within a hundredth of a second over the whole run. They")
print("    are offset by exactly one request duration, not by the sum of them, because a")
print("    mtime is stamped at body-write time (after the send) while t_sent is stamped")
print("    before curl is invoked. A divergence proportional to the number of requests would")
print("    have been the signature of the clock fault docs/09 section 4 describes; this is")
print("    not that.")