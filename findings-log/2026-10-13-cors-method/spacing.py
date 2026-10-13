#!/usr/bin/env python3
"""Spacing measurement for findings-log/2026-10-13-cors-method/.

CORRECTED 2026-10-13 after the verification round. The first version of this file
validated the mtime series against `t_sent`, and that check was worthless: the span
difference `mtime_span - t_sent_span` is arithmetically identical to `dur[n] - dur[1]`,
i.e. it is computed entirely from `t_sent` and `t_done` and never touches the mtime
series, so it cannot discriminate a sound mtime series from an unsound one. It is
reproduced below anyway, labelled as what it is, so the retraction stays visible.

The right counterpart to a body-write mtime is `t_done` -- the stamp taken when curl
returns, immediately after the body is written. Against that series this run validates to
**0.000294 s over a 19.651 s span**, and per row to about -4 ms on the six clean rows.

Counting rule, stated so the number can be reproduced: one gap per consecutive pair **in
request order** taken from results.jsonl, restricted to pairs where both requests went to
the SAME host, because the repo's rule is per host. The one cross-host pair is counted and
reported separately, never folded into the floor.

Attempt 1 and attempt 2 rows are excluded from the measurement and from the floor: they
never resolved a host, so no request reached a vendor. They stay in the ledger.

Series and resolutions:
  * t_sent / t_done -- harness `date`, millisecond ISO-8601 UTC. docs/09 section 4 records
    this series as the suspect, and this run gives it two bad readings (see below).
  * mtime -- `stat -c %y` on the body files, microsecond resolution after strptime's
    truncation of stat's nanosecond field. Read at analysis time; the bodies have not been
    modified since the run, so these are still the kernel's write times. **The series is
    printed in full below at the resolution it was measured at**, because git does not
    preserve mtimes and a verifier working from a fresh clone cannot re-derive it from the
    files. Note that results.jsonl's own `body_mtime_epoch` is integer seconds and cannot
    separate 2.737 from 2.744.
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


def mtime_epoch(path):
    """`stat -c %y` -> epoch seconds, microsecond resolution, via %z so the local zone is honoured"""
    raw = subprocess.run(["stat", "-c", "%y", path], capture_output=True, text=True,
                         check=True).stdout.strip()
    base, zone = raw.rsplit(" ", 1)          # "… .287749245" and "+0100"
    dt = datetime.datetime.strptime(base[:26], "%Y-%m-%d %H:%M:%S.%f")   # ns field -> us
    return (dt - datetime.datetime.strptime(zone, "%z").utcoffset()).timestamp()


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
mt = [mtime_epoch(os.path.join(HERE, "bodies", "%02d-%s.b" % (int(r["seq"]), r["host_tag"])))
      for r in ok]

print("spacing — attempt %s, %d ledger rows" % (ATTEMPT, len(ok)))
print("counting rule: consecutive pairs in request order, same host only; the cross-host")
print("pair is reported separately and is not part of the floor.\n")

print("  1. the mtime series in full, microsecond resolution, as re-derivable evidence")
print("     (results.jsonl's own body_mtime_epoch is integer seconds and cannot separate")
print("     sub-second gaps; git does not preserve mtimes, so these numbers are the copy)")
for r, v in zip(ok, mt):
    print("      seq %2s  %s  %.6f" % (r["seq"], r["host_tag"], v))
print()

print("  2. the floor, measured from the mtime series")
same = [(ok[i - 1]["seq"], ok[i]["seq"], ok[i]["host"], mt[i] - mt[i - 1])
        for i in range(1, len(mt)) if ok[i]["host"] == ok[i - 1]["host"]]
lo = min(g[3] for g in same)
print("     %d same-host gaps   min %.3fs   max %.3fs   span %.3fs"
      % (len(same), lo, max(g[3] for g in same), mt[-1] - mt[0]))
print("     gaps under the declared 2.5s: %d" % sum(1 for g in same if g[3] < 2.5))
print("     gaps under the repo floor of 2s: %d" % sum(1 for g in same if g[3] < 2.0))
for a, b, h, g in same:
    print("       seq %2s -> %2s  %-30s %.3fs" % (a, b, h, g))
for i in range(1, len(mt)):
    if ok[i]["host"] != ok[i - 1]["host"]:
        print("     cross-host (excluded from the floor): seq %s -> %s  %.3fs"
              % (ok[i - 1]["seq"], ok[i]["seq"], mt[i] - mt[i - 1]))
print()

print("  3. VALIDATION against t_done, the series a body-write mtime physically corresponds to")
for r, v, d in zip(ok, mt, done):
    print("      seq %2s  mtime - t_done = %+.6f" % (r["seq"], v - d))
print("     mtime span %.6f   t_done span %.6f   difference %+.6f s over %d requests"
      % (mt[-1] - mt[0], done[-1] - done[0], (mt[-1] - mt[0]) - (done[-1] - done[0]), len(ok)))
print("     Seven of the eight rows sit within -0.0035..-0.0045 s, which is what the pair is")
print("     supposed to look like: the kernel stamps the body, curl exits, `date` runs. The")
print("     span agrees to 0.000294 s. The eighth row is seq 18 and is discussed below.")
print()

print("  4. the suspect series, and why it is the suspect here")
for r, v, s_, d in zip(ok, mt, sent, done):
    print("      seq %2s  dur %+.3fs   mtime - t_sent %+.6f" % (r["seq"], d - s_, v - s_))
neg = [(r["seq"], d - s_) for r, s_, d in zip(ok, sent, done) if d < s_]
print("     impossible durations (t_done earlier than t_sent): %s"
      % (["seq %s: %+.3fs" % (a, b) for a, b in neg] or "none"))
print("     seq 23's reading is the one that manufactures the apparent 2.273 s gap in the")
print("     t_sent series; seq 18's is late by 0.42 s against its own body write. Both are")
print("     readings of one clock, not requests that fired early. No cause is asserted.")
print()

print("  5. RETRACTED CHECK, kept so the retraction stays visible")
print("     mtime span %.6f   t_sent span %.6f   difference %+.6f s"
      % (mt[-1] - mt[0], sent[-1] - sent[0], (mt[-1] - mt[0]) - (sent[-1] - sent[0])))
print("     This was published as the validation. It is arithmetically identical to")
print("     `dur[n] - dur[1]` -- computed from t_sent and t_done alone, never from mtimes --")
print("     so it cannot discriminate a sound mtime series from an unsound one. It happens")
print("     to be small here, and that is a coincidence of how long the last request took,")
print("     not evidence about the mtime series.")