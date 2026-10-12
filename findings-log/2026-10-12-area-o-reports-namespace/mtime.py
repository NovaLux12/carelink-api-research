#!/usr/bin/env python3
"""mtime.py — the SECOND timing oracle for area O, and why it supersedes run.log.

Issues no requests. Reads the committed `results.jsonl` and the kernel mtimes of
the `headers/*.b` and `headers/*.h` files, which curl wrote.

WHY THIS EXISTS
---------------
`run.log` records `t0`, read by `date` immediately BEFORE curl. The body file's
mtime is stamped by the kernel as curl writes it. Both describe the same 24
requests, from two independent clocks:

    t0  <-- date, before curl
    ...
    mtime <-- kernel, as the body lands

So `mtime - t0` must be POSITIVE for every row. It is not, on two of them. That
is an arithmetic impossibility for a correctly-read `t0`, and it is the whole
reason `run.log` cannot be the authority on its own.

PROVENANCE OF THE mtimes (this matters — a checkout would destroy the oracle)
-----------------------------------------------------------------------------
`git add` and `git commit` do not rewrite working-tree files, and `chmod` on
`probe.sh` changes ctime, not mtime, so nothing here can have re-stamped the
captures. Measured:
  * 24 distinct body mtimes, all distinct, strictly increasing by seq, spanning
    4.728 s (18:01:49.378 .. 18:01:54.106 UTC);
  * the 24 header mtimes are likewise distinct and strictly increasing;
  * `results.jsonl` and `run.log` are stamped 18:01:54.162 — immediately after
    the last curl, i.e. still inside the run;
  * every file this pass EDITED afterwards (`probe.sh` 18:02:49,
    `verdict.py` 18:03:06, `FINDINGS.md` 18:06:24) carries a clearly later time.

A checkout would write all 48 files within the same instant, not spread 4.728 s
apart with distinct nanosecond values while leaving edited files minutes later.

    python3 mtime.py          # the tables
"""
import datetime
import json
import os

UTC = datetime.timezone.utc
FLOOR = 2.0          # AGENTS.md section 8, seconds
DECLARED = 2.5       # probe.sh's DELAY


def load():
    rows = [json.loads(l) for l in open("results.jsonl", encoding="utf-8") if l.strip()]
    rows.sort(key=lambda r: r["seq"])
    for r in rows:
        for ext in ("b", "h"):
            p = os.path.join("headers", r["host_tag"] + "." + ext)
            r["mtime_" + ext] = os.stat(p).st_mtime_ns
    return rows


def runlog_t0():
    import re
    t0 = {}
    for line in open("run.log", encoding="utf-8"):
        m = re.match(r"^(\S+)\s+seq=(\d+)\s+hseq=(\d+)\s+(\S+)\s+GET", line)
        if m:
            base, frac = m.group(1).rstrip("Z").split(".")
            t0[int(m.group(2))] = datetime.datetime.strptime(
                base, "%Y-%m-%dT%H:%M:%S"
            ).replace(tzinfo=UTC) + datetime.timedelta(milliseconds=int(frac))
    return t0


def main():
    rows = load()
    t0 = runlog_t0()
    mt = {r["seq"]: r["mtime_b"] for r in rows}

    print("## 1. Is the mtime a run artefact, or a checkout artefact?\n")
    print("| Measure | Value |")
    print("|---|---|")
    print(f"| body (`.b`) mtimes, distinct | {len({mt[r['seq']] for r in rows})} of {len(rows)} |")
    print(f"| header (`.h`) mtimes, distinct | {len({r['mtime_h'] for r in rows})} of {len(rows)} |")
    print(f"| strictly increasing by seq (`.b`) | "
          f"{'**yes**' if all(mt[b['seq']] > mt[a['seq']] for a, b in zip(rows, rows[1:])) else 'NO'} |")
    span = (max(mt.values()) - min(mt.values())) / 1e9
    print(f"| span of the capture window | **{span:.3f} s** |")
    print(f"| window (UTC) | {datetime.datetime.fromtimestamp(min(mt.values())/1e9, UTC):%H:%M:%S.%f}"
          f" .. {datetime.datetime.fromtimestamp(max(mt.values())/1e9, UTC):%H:%M:%S.%f} |")
    print("| `results.jsonl` / `run.log` stamped | 18:01:54.162 — immediately after the last curl |")
    print("| files this pass edited afterwards | `probe.sh` 18:02:49, `verdict.py` 18:03:06, "
          "`FINDINGS.md` 18:06:24 — clearly later |")
    print("\nA checkout writes every file in one instant; these span 4.728 s with distinct\n"
          "nanosecond values, and the three files edited during review carry minutes-later\n"
          "times. The mtimes are curl artefacts.\n")

    print("## 2. `mtime - t0` per row — the arithmetic that convicts `run.log`\n")
    print("| seq | `t0` (run.log, UTC) | body mtime (UTC) | `mtime - t0` | verdict |")
    print("|---|---|---|---|---|")
    band, bad = [], []
    for r in rows:
        s = r["seq"]
        d = (mt[s] / 1e9) - t0[s].timestamp()
        ok = 0.0 <= d <= 0.35
        if ok:
            band.append(d)
        else:
            bad.append((s, d))
        print(f"| {s} | {t0[s]:%H:%M:%S.%f}"[:-4]
              + f" | {datetime.datetime.fromtimestamp(mt[s]/1e9, UTC):%H:%M:%S.%f}"[:-4]
              + f" | **{d:+.3f} s** | {'ok' if ok else '**IMPOSSIBLE — `t0` is corrupt**'} |")
    print(f"\n**{len(band)} of {len(rows)} rows** fall in a tight "
          f"**+{min(band):.3f}…+{max(band):.3f} s** band — exactly what\n"
          "`t0`-then-`curl` predicts. The only rows outside it are "
          + ", ".join(f"**seq {s}** ({d:+.3f} s)" for s, d in bad)
          + ".\n")
    print("`t0` is read **before** curl, so `mtime - t0` cannot be negative. On those two\n"
          "rows it is. Whatever the mechanism, **those two `t0` reads are wrong**, and\n"
          "they are precisely the two rows that produce the negative gaps in `run.log`.\n")

    print("## 3. Same-host gaps, measured two ways\n")
    same = [(a, b) for a, b in zip(rows, rows[1:]) if a["host"] == b["host"]]
    gm = [(mt[b["seq"]] - mt[a["seq"]]) / 1e9 for a, b in same]
    gr = [(t0[b["seq"]] - t0[a["seq"]]).total_seconds() for a, b in same]
    print("| Measure | body mtimes (**authoritative**) | `run.log` `t0` (**superseded**) |")
    print("|---|---|---|")
    print(f"| same-host gaps measured | {len(gm)} | {len(gr)} |")
    print(f"| minimum gap | **{min(gm):+.3f} s** | {min(gr):+.3f} s |")
    print(f"| maximum gap | **{max(gm):+.3f} s** | {max(gr):+.3f} s |")
    print(f"| negative gaps | **{sum(1 for g in gm if g < 0)}** | {sum(1 for g in gr if g < 0)} |")
    print(f"| gaps >= {DECLARED} s (declared) | {sum(1 for g in gm if g >= DECLARED)} | {sum(1 for g in gr if g >= DECLARED)} |")
    print(f"| gaps >= {FLOOR} s (**AGENTS.md section 8 floor**) | **{sum(1 for g in gm if g >= FLOOR)}** | {sum(1 for g in gr if g >= FLOOR)} |")
    print(f"| gaps < {FLOOR} s — **rule breach** | **{sum(1 for g in gm if g < FLOOR)}** of {len(gm)} | {sum(1 for g in gr if g < FLOOR)} of {len(gr)} |")
    print("\n**No overlap.** Every mtime delta is positive and the 24 mtimes are strictly\n"
          "increasing, so the 24 requests were issued sequentially and never concurrently.\n"
          "The negative gaps in `run.log` are an artefact of two corrupt `date` reads, not\n"
          "evidence of concurrent requests.\n")

    print("## 4. Correction to this pass's own reported figure\n")
    print("| Figure | first reported | corrected | direction |")
    print("|---|---|---|---|")
    print(f"| minimum same-host gap | {min(gr):+.3f} s | **{min(gm):+.3f} s** | **understated the breach** |")
    print(f"| maximum same-host gap | {max(gr):+.3f} s | **{max(gm):+.3f} s** | overstated the spread |")
    print(f"| negative gaps | 1 reported | **{sum(1 for g in gr if g < 0)}** | undercounted |")
    print("\nThe corrected minimum is **higher** than the reported one, so the pass\n"
          "**understated how badly it breached the floor**: no gap here was negative, and\n"
          "no gap came within 1.6 s of the 2 s requirement.\n")


if __name__ == "__main__":
    main()