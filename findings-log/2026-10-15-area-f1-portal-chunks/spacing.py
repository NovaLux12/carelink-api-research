#!/usr/bin/env python3
"""spacing.py — recompute this pass's same-host request spacing from the
ledger. Zero requests.

TWO SERIES, BOTH REPORTED, because docs/09 §4 records that they have disagreed
in five passes in this repository:

  * `t_sent`   — the harness clock, stamped INSIDE the flock immediately before
                 curl execs. This is the series the declared delay is about.
  * `body_mtime` — the kernel's own body-write time. `curl -o` makes the kernel
                 set it, so it is independent of the harness's clock. It is at
                 1-second resolution, so it can bound a gap but cannot resolve
                 2.5 s; that limit is stated with the number, never omitted.

Counting rule: one gap per consecutive pair IN REQUEST ORDER within one host,
measured as the difference of the two timestamps. A gap is "under 2.5 s" if it
is < 2.5 and "under the floor" if it is < 2.0. Negative durations (t_done
earlier than t_sent) are counted and reported separately, because they are
impossible and mean the series is not faithful — never silently dropped.

Usage: spacing.py [ledger]
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
LEDGER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results.jsonl"
DECLARED, FLOOR = 2.5, 2.0


def ms(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1000.0


def secs(s):
    # The body mtime is recorded at 1-second resolution (`stat -c%Y` converted
    # to an ISO stamp with a .000 fraction), so the fractional part is always
    # zero and is stripped rather than mis-parsed.
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(
        tzinfo=timezone.utc).timestamp()


def report(series_name, getter, note):
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    rows.sort(key=lambda r: r["seq"])
    per_host, out = {}, []
    for r in rows:
        per_host.setdefault(r["host"], []).append(r)
    for host, rs in sorted(per_host.items()):
        gaps = []
        for a, b in zip(rs, rs[1:]):
            va, vb = getter(a), getter(b)
            if va is None or vb is None:
                gaps.append(None)
                continue
            gaps.append((round((vb - va) / 1000.0, 3), a["seq"], b["seq"]))
        good = [g for g in gaps if g is not None]
        if not good:
            continue
        vals = [g[0] for g in good]
        out.append({
            "host": host, "requests": len(rs), "gaps": len(good),
            "min_gap_s": min(vals), "max_gap_s": max(vals),
            "under_declared_2_5s": sum(1 for v in vals if v < DECLARED),
            "under_floor_2_0s": sum(1 for v in vals if v < FLOOR),
            "shortest": sorted(good)[:6],
        })
    print(f"== {series_name} == {note}")
    for o in out:
        print(f"  {o['host']}: {o['requests']} requests, {o['gaps']} gaps, "
              f"min {o['min_gap_s']}s max {o['max_gap_s']}s, "
              f"under 2.5s: {o['under_declared_2_5s']}, under 2.0s: {o['under_floor_2_0s']}")
        print(f"     shortest: {o['shortest']}")
    return out


def main():
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    rows.sort(key=lambda r: r["seq"])

    # Negative durations: t_done before t_sent is impossible.
    neg = [(r["seq"], round((ms(r["t_done"]) - ms(r["t_sent"])) / 1000.0, 3))
           for r in rows
           if ms(r["t_done"]) < ms(r["t_sent"])]

    # Faithfulness of the send series, stated rather than assumed.
    missing_sent = [r["seq"] for r in rows if not r.get("t_sent")]
    missing_mtime = [r["seq"] for r in rows if not r.get("body_mtime")]

    a = report("t_sent (harness clock)", lambda r: ms(r["t_sent"]),
               "(millisecond resolution, stamped inside the host lock)")
    b = report("body_mtime (kernel clock)",
               lambda r: int(secs(r["body_mtime"]) * 1000) if r.get("body_mtime") else None,
               "(1-second resolution — bounds a gap, cannot resolve 2.5 s)")

    print(f"\nnegative durations (t_done < t_sent): {len(neg)} {neg if neg else ''}")
    print(f"rows missing t_sent: {len(missing_sent)} {missing_sent if missing_sent else ''}")
    print(f"rows missing body_mtime: {len(missing_mtime)} "
          f"{missing_mtime[:10] if missing_mtime else ''}")
    (HERE / "spacing.json").write_text(json.dumps(
        {"t_sent": a, "body_mtime": b, "negative_durations": neg,
         "missing_t_sent": missing_sent, "missing_body_mtime": missing_mtime},
        indent=2) + "\n")


if __name__ == "__main__":
    main()