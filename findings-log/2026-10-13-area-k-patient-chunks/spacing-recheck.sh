#!/bin/bash
# Area K — INDEPENDENT re-derivation of spacing.txt, run after the merge into
# origin/main (PR #65). Not a re-run of the probe: it reads results.jsonl, which
# is already committed, and sends ZERO requests.
#
# WHY THIS FILE EXISTS. spacing.txt is an artefact produced by spacing.sh. Reading
# an artefact and believing it is the "A claim stated without evidence" failure
# (AGENTS.md section 6, item 1). This re-derives every figure docs/09 section 4
# will quote, from the ledger, by a second implementation.
#
# It also records the ONE defect found: the timezone handling. A first attempt at
# this script omitted `.replace(tzinfo=timezone.utc)` from its parser and reported
# "0 bodies written before their own t_sent" against the artefact's 22. The
# artefact was right and the re-derivation was wrong — spacing.sh:47 pins the
# timezone and this file must too. That mistake is the reason the parse line here
# is marked, and it is published rather than deleted because a reader re-deriving
# this will make it too.
#
# COUNTING RULE, stated so every number below is reproducible (docs/09 section 4):
#   - rows are sorted by `seq`; gaps are one per CONSECUTIVE PAIR in request order,
#     restricted to pairs on the SAME host; N rows give N-1 gaps.
#   - "negative duration" is t_done < t_sent, which is impossible.
#   - "body written before its own t_sent" is body_mtime_ns/1e9 < t_sent. This is a
#     DIFFERENT set from the negative durations and the two are not interchangeable:
#     16 of the 22 appear in both.
set -u
LEDGER=${1:?usage: spacing-recheck.sh <results.jsonl>}
python3 - "$LEDGER" <<'EOF'
import json, statistics, sys
from datetime import datetime, timezone

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
rows.sort(key=lambda r: r["seq"])

def t(s):
    # The `Z` suffix is UTC. Without tzinfo=timezone.utc, .timestamp() reads the
    # naive datetime as LOCAL time; this box is UTC+1 (BST), which shifts every
    # timestamp by 3600 s and silently turns the check below into a tautology.
    if not s or s.startswith("("):
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=timezone.utc).timestamp()

def mt(r):
    ns = r.get("body_mtime_ns", "")
    return int(ns) / 1e9 if ns and ns != "(none)" else None

fails = []          # every printed FAIL must append here — see the self-check
def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {label}: re-derived {got}, artefact says {want}")
    if not ok:
        fails.append(label)

print("AREA K — independent re-derivation of spacing.txt (zero requests)")
print(f"rows={len(rows)}  hosts={sorted({r['host'] for r in rows})}  "
      f"declared={sorted({r['delay_declared_s'] for r in rows})}")

print("\nimpossible durations (t_done < t_sent):")
neg = [r["seq"] for r in rows if t(r["t_done"]) < t(r["t_sent"])]
check("negative durations", len(neg), 16)

early = [r["seq"] for r in rows if mt(r) is not None and mt(r) < t(r["t_sent"])]
check("bodies written before own t_sent", len(early), 22)
print(f"  note: the {len(early)}-set contains the {len(neg)}-set plus "
      f"{sorted(set(early) - set(neg))} — they are different questions")

send, mm = [], []
for a, b in zip(rows, rows[1:]):
    if a["host"] != b["host"]:
        continue
    send.append(t(b["t_sent"]) - t(a["t_sent"]))
    mm.append(mt(b) - mt(a))
check("same-host gaps", len(send), 214)

sg, mg = sorted(send), sorted(mm)
check("send: gaps under declared 2.5 s", sum(1 for v in sg if v < 2.5), 22)
check("send: gaps under 2 s floor", sum(1 for v in sg if v < 2.0), 7)
check("mtime: gaps under declared 2.5 s", sum(1 for v in mg if v < 2.5), 0)
check("mtime: gaps under 2 s floor", sum(1 for v in mg if v < 2.0), 0)
check("mtime: negative gaps", sum(1 for v in mm if v <= 0), 0)
print(f"  min/max — send {min(send):.3f}/{max(send):.3f}  "
      f"mtime {min(mm):.3f}/{max(mm):.3f}")
check("mtime floor", f"{min(mm):.3f}", "2.636")
check("send floor", f"{min(send):.3f}", "1.835")

ad = sorted(abs(a - b) for a, b in zip(send, mm))
check("per-gap max |send-mtime|", f"{ad[-1]:.3f}", "0.873")
check("per-gap gaps disagreeing >0.5 s", sum(1 for v in ad if v > 0.5), 20)
# spacing.sh reports sorted(ad)[len//2] — the UPPER middle element of an even-length
# list, which is not the median. Both are published so the difference is visible.
print(f"  median — spacing.sh's upper-middle element ad[107] = {ad[len(ad)//2]:.4f}s; "
      f"true median (mean of ad[106],ad[107]) = {statistics.median(ad):.4f}s "
      f"(ad[106]={ad[105]:.4f}, ad[107]={ad[106]:.4f})")

hs = max(t(r["t_done"]) for r in rows) - min(t(r["t_sent"]) for r in rows)
ks = (max(mt(r) for r in rows) - min(mt(r) for r in rows))
print(f"\nspan  first t_sent->last t_done {hs:.3f}s | kernel first->last write "
      f"{ks:.3f}s | diff {hs-ks:.3f}s")
print("  (a two-endpoint check; it cannot detect interior corruption — see §4)")

print("\nSELF-CHECK")
print(f"  checks that FAILED: {len(fails)}")
if fails:
    for f in fails:
        print(f"    FAIL {f}")
print("  consistent" if not fails else "  INCONSISTENT — the two disagree")
raise SystemExit(1 if fails else 0)
EOF