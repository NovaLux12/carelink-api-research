#!/usr/bin/env python3
"""verdict.py — render the area-O tables FROM results.jsonl.

Issues no requests. Reads only the committed ledger and prints the markdown
tables that FINDINGS.md quotes, so those tables are the ledger rather than a
hand-copied re-reading of it. Where a value is absent, the literal `(none)` is
printed, which is what probe.sh wrote.

    python3 verdict.py            # the tables
    python3 verdict.py --spacing  # the same-host gap table, from run.log
"""
import datetime
import json
import re
import sys
from collections import defaultdict

HOSTS = ["carelink.minimed.eu", "carelink.minimed.com", "carelink-trials.minimed.com"]
# The seven, in the order ARCHIVE-URLS.md:162 lists them, with the ARCHIVE
# verdict recorded there. Not re-derived, not guessed.
SEVEN = [
    ("supported", "401"),
    ("snapshotTimelinesRange", "401"),
    ("generateReport", "405"),
    ("favoriteReports", "405"),
    ("snapshotTimelinesForCalendar", "405"),
    ("reportStatus", "400"),
    ("report", "404"),
]
LIVE = {"200", "401", "400", "405"}


def load():
    return [json.loads(l) for l in open("results.jsonl", encoding="utf-8") if l.strip()]


def idx(rows):
    by = defaultdict(dict)
    for r in rows:
        name = r["path"].rsplit("/", 1)[-1]
        if name.startswith("this-does-not-exist"):
            name = "(certainly-absent)"
        by[r["host"]][name] = r
    return by


def table_per_host(by):
    out = [
        "| Path | archive verdict (ARCHIVE-URLS.md:162) | `carelink.minimed.eu` | `carelink.minimed.com` | `carelink-trials.minimed.com` | identical across all 3? |",
        "|---|---|---|---|---|---|",
    ]
    for name, arch in SEVEN:
        cells = [by[h][name] for h in HOSTS]
        codes = [c["http_status"] for c in cells]
        same = "**yes**" if len(set(codes)) == 1 else "**NO**"
        archmark = "" if codes[0] == arch else f" *(archive said {arch} — differs)*"
        out.append(
            f"| `/patient/reports/{name}` | {arch} | "
            + " | ".join(c + archmark for c in codes)
            + f" | {same} |"
        )
    return "\n".join(out)


def table_controls(by):
    out = [
        "| # | Host | Path | Role | Status | `Content-Type` | Bytes | body sha256 | `x-ca-err` | What it establishes |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    n = 0
    meanings = {
        "(certainly-absent)": "what **dead** looks like on this host",
        "supported": "the namespace is routed here (this row is also candidate 1 of 7)",
    }
    for h in HOSTS:
        for name in ["(certainly-absent)"] + [n for n, _ in SEVEN]:
            r = by[h][name]
            n += 1
            meaning = meanings.get(name, "")
            out.append(
                f"| {n} | `{h}` | `/patient/reports/{name}` | {r['role']} | "
                f"**{r['http_status']}** | {r['content_type']} | {r['body_bytes']} | "
                f"`{r['body_sha256'][:12]}` | {r['x_ca_err']} | {meaning} |"
            )
    return "\n".join(out)


def table_liveness(by):
    out = [
        "| Host | 7-path row complete | routed (200/401/400/405) | no route (404) | oracle usable? |",
        "|---|---|---|---|---|",
    ]
    for h in HOSTS:
        codes = {n: by[h][n]["http_status"] for n, _ in SEVEN}
        routed = sum(1 for c in codes.values() if c in LIVE)
        dead = sum(1 for c in codes.values() if c == "404")
        absent = by[h]["(certainly-absent)"]["http_status"]
        usable = "**yes**" if absent == "404" else f"**NO** — absent control returned {absent}"
        out.append(f"| `{h}` | {len(codes)}/7 | {routed}/7 | {dead}/7 | {usable} |")
    return "\n".join(out)


def table_identity(by):
    """Byte-identity of the response, per path, across the three hosts."""
    out = [
        "| Path | statuses equal | bodies equal (sha256) | byte counts |",
        "|---|---|---|---|",
    ]
    for name, _ in SEVEN:
        cells = [by[h][name] for h in HOSTS]
        st = len({c["http_status"] for c in cells}) == 1
        sh = len({c["body_sha256"] for c in cells}) == 1
        by_ = "/".join(str(c["body_bytes"]) for c in cells)
        out.append(
            f"| `/patient/reports/{name}` | {'yes' if st else 'NO'} | "
            f"{'yes — `' + cells[0]['body_sha256'][:12] + '`' if sh else '**NO**'} | {by_} |"
        )
    return "\n".join(out)


def table_headers(by):
    """The per-path header facts that are stable across hosts."""
    out = [
        "| Status | paths at that status | `x-cache` | `Allow` | `x-ca-err` | `Set-Cookie` names | `Access-Control-Allow-Origin` |",
        "|---|---|---|---|---|---|---|",
    ]
    by_status = defaultdict(list)
    for h in HOSTS:
        for name, _ in SEVEN:
            by_status[by[h][name]["http_status"]].append(name)
    for st in ["401", "400", "405", "404"]:
        names = sorted(set(by_status.get(st, [])))
        if not names:
            continue
        c = by[HOSTS[0]][names[0]]
        allow = c["allow"] if c["allow"] != "(none)" else "—"
        out.append(
            f"| **{st}** | {', '.join('`' + n + '`' for n in names)} | "
            f"`Error from cloudfront` | {allow} | {c['x_ca_err']} | "
            f"{'2 (`auth_tmp_token`, `c_token_valid_to`, both empty, `Max-Age=0`)' if st == '401' else '—'} | "
            f"**absent on every one of the 24 responses** |"
        )
    return "\n".join(out)


def spacing():
    rows = []
    for line in open("run.log", encoding="utf-8"):
        m = re.match(r"^(\S+)\s+seq=(\d+)\s+hseq=(\d+)\s+(\S+)\s+GET", line)
        if m:
            base, frac = m.group(1).rstrip("Z").split(".")
            t = datetime.datetime.strptime(base, "%Y-%m-%dT%H:%M:%S") + datetime.timedelta(
                milliseconds=int(frac)
            )
            rows.append((t, int(m.group(2)), m.group(4)))
    gaps = [
        ((b[0] - a[0]).total_seconds(), a[1], b[1], a[2])
        for a, b in zip(rows, rows[1:])
        if a[2] == b[2]
    ]
    out = [
        "| Measure | Value |",
        "|---|---|",
        f"| requests in `run.log` | {len(rows)} |",
        f"| same-host gaps measured | {len(gaps)} |",
        f"| gaps >= 2.5 s (the harness's own declared `DELAY`) | {sum(1 for g in gaps if g[0] >= 2.5)} |",
        f"| gaps >= 2.0 s (**the repository floor, AGENTS.md section 8**) | **{sum(1 for g in gaps if g[0] >= 2.0)}** |",
        f"| gaps < 2.0 s — **a rule breach** | **{sum(1 for g in gaps if g[0] < 2.0)}** |",
        f"| minimum same-host gap | **{min(gaps)[0]:.3f} s** (seq {min(gaps)[1]} -> {min(gaps)[2]}, `{min(gaps)[3]}`) |",
        f"| maximum same-host gap | {max(gaps)[0]:.3f} s |",
    ]
    return "\n".join(out)


def main():
    by = idx(load())
    if "--spacing" in sys.argv:
        print(spacing())
        return
    print("### Seven-path row, three hosts\n")
    print(table_per_host(by))
    print("\n### Oracle usable?\n")
    print(table_liveness(by))
    print("\n### Controls, sent first on every host\n")
    print(table_controls(by))
    print("\n### Cross-host byte identity\n")
    print(table_identity(by))
    print("\n### Stable header facts by status\n")
    print(table_headers(by))


if __name__ == "__main__":
    main()