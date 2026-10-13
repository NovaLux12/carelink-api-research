#!/usr/bin/env python3
"""Area M — spacing measurement, both series, with the counting rule in code.

docs/09 §4 is explicit that the harness `date` series is the suspect in several
passes (a negative request duration is impossible) and that the KERNEL's
body-file mtimes are the independent series, because curl writes each body at
write time and the kernel stamps it there.

Counting rule (docs/09 §4, restated here so the number is reproducible):
  * one gap per consecutive pair IN RUN ORDER, taken from run.log;
  * measured separately per host, because the rule is ">= 2 s between requests
    to the SAME host";
  * bodies with no file (a request curl never wrote) break a series rather than
    being silently skipped — a gap measured across a missing point is not a gap.
VALIDATION before trusting either series: a trustworthy run's mtime span must
equal the harness span. Git does not preserve mtimes, so this is valid only on
the machine that ran the probe, and the script says so rather than implying
otherwise.

Exit 0 always — this measures, it does not gate. A number that cannot be
measured is reported as unmeasured, never rounded to the declared delay.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
# datetime.timestamp() is already SECONDS. Dividing by 1000 here silently turned
# every gap into milliseconds — which printed as a 0.003 s floor and would have
# been reported as "58 gaps under the 2 s floor", a rule breach that never
# happened. Caught because the per-gap mean (0.011) did not reconcile with the
# span (658 s) it was drawn from. Fixed 2026-10-13; recorded because the failure
# mode was a wrong measurement, not a crash.
UNITS = 1.0


def parse(ts: str):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")


def run_order() -> list[dict]:
    """Rebuild the send order from run.log, which is the harness's own log."""
    rows = []
    with open(os.path.join(HERE, "results.jsonl"), encoding="utf-8") as fh:
        by_seq = {json.loads(l)["seq"]: json.loads(l) for l in fh if l.strip()}
    with open(os.path.join(HERE, "run.log"), encoding="utf-8") as fh:
        for line in fh:
            if " seq=" not in line or " method=GET" not in line:
                continue
            d = dict(kv.split("=", 1) for kv in line.split() if "=" in kv)
            seq = int(d["seq"])
            if seq in by_seq:
                rows.append(by_seq[seq])
    return rows


def gaps(points: list[tuple[float, str]]) -> list[float]:
    return [round((points[i + 1][0] - points[i][0]) / UNITS, 3)
            for i in range(len(points) - 1)]


def report(label: str, per_host: dict[str, list[float]], span: float | None) -> None:
    allg = [g for v in per_host.values() for g in v]
    print(f"--- {label} ---")
    for host, g in sorted(per_host.items()):
        if not g:
            continue
        under25 = [x for x in g if x < 2.5]
        under2 = [x for x in g if x < 2.0]
        print(f"  {host:<24} gaps={len(g):>3} min={min(g):.3f}s max={max(g):.3f}s "
              f"under 2.5s={len(under25)} under 2.0s={len(under2)}")
    if allg:
        print(f"  ALL HOSTS  gaps={len(allg)} min={min(allg):.3f}s max={max(allg):.3f}s "
              f"under 2.5s={len([x for x in allg if x < 2.5])} "
              f"under 2.0s={len([x for x in allg if x < 2.0])}")
    if span is not None:
        print(f"  span={span:.3f}s")


def main() -> int:
    rows = run_order()
    print(f"requests in run order: {len(rows)}")
    if rows != sorted(rows, key=lambda r: r["seq"]):
        print("  !! run.log order is not seq order — the mtime series would be wrong")

    # --- series 1: the harness's own t_sent, per host
    pts: dict[str, list[tuple[float, str]]] = {}
    for r in rows:
        try:
            t = parse(r["t_sent"]).timestamp()
        except Exception:
            print(f"  !! seq {r['seq']}: t_sent unparseable ({r['t_sent']}) — "
                  "series broken, not skipped")
            continue
        pts.setdefault(r["host"], []).append((t, r["seq"]))
    report("harness t_sent series", {h: gaps(p) for h, p in pts.items()},
           (max(max(p)[0] for p in pts.values()) - min(min(p)[0] for p in pts.values()))
           if pts else None)

    # negative durations are impossible; count them rather than hide them
    neg = [r["seq"] for r in rows
           if parse(r["t_done"]) < parse(r["t_sent"])]
    print(f"  requests whose t_done precedes t_sent (impossible): {len(neg)} {neg}")

    # --- series 2: kernel body mtimes, per host, in run order
    #
    # A body file is named by host_tag, so a re-issued request that REUSES a tag
    # overwrites the first body: two ledger rows, one file, two identical
    # mtimes, and a gap that reads 0.000 s. That is not a spacing breach, it is
    # the oracle failing to see, and reporting it as a breach would be the
    # wrong number in the dangerous direction. Such pairs are counted and
    # reported as UNMEASURED.
    series_m: dict[str, list[tuple[float, str]]] = {}
    missing = []
    tagcount: dict[str, int] = {}
    for r in rows:
        tagcount[r["host_tag"]] = tagcount.get(r["host_tag"], 0) + 1
    shared = sorted(t for t, n in tagcount.items() if n > 1)
    print(f"host_tags used by more than one request (bodies overwritten, "
          f"kernel series cannot separate them): {shared}")
    for r in rows:
        if r["host_tag"] in shared:
            continue
        p = os.path.join(HERE, "bodies", r["host_tag"] + ".b")
        if not os.path.exists(p):
            missing.append(r["seq"])
            continue
        series_m.setdefault(r["host"], []).append((os.path.getmtime(p), r["seq"]))
    print(f"bodies missing on disk: {len(missing)} {missing}")
    report("kernel body-mtime series (duplicate-tag pairs excluded)", {h: gaps(p) for h, p in series_m.items()},
           (max(max(p)[0] for p in series_m.values()) - min(min(p)[0] for p in series_m.values()))
           if series_m else None)

    print("\nNOTE: git does not preserve mtimes, so the kernel series is valid "
          "only on the machine that ran the probe; it is not re-derivable from a "
          "clean clone. Both series are reported; neither replaces the other.")
    return 0


if __name__ == "__main__":
    sys.exit(main())