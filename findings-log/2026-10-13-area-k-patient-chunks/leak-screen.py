#!/usr/bin/env python3
"""Area K — hand-equivalent screen of THIS PASS's non-md artefacts against
`scripts/scrub-patterns.txt`. ZERO requests.

WHY THIS EXISTS, and why it is a committed script rather than a claim in the PR.
`docs/09` section 4 records that the repository's own leak scan chooses its subjects
by FILE EXTENSION — `md`/`yml`/`yaml`/`sh`/`hurl` — so it reads **no `.txt`, no `.tsv`
and no `.h`** in any mode, `--all` included. This pass alone commits eleven artefacts
of exactly those kinds (`runtime-map.txt`, `grep-out.txt`, `tables.txt`, `spacing.txt`,
`resolve.txt`, `resolve-mutants.txt`, `patient-csr.txt`, `verdicts.tsv`,
`chunks-swept.txt`, and 215 `headers/*.h`). Nothing in CI or in the gate reads them.

So they are screened here, by the same pattern file the gate uses, and the RESULT is
committed so a reader does not have to take the PR's word for it.

TWO THINGS THIS SCRIPT DELIBERATELY DOES NOT DO:

  1. It does not echo pattern VALUES. `scripts/scrub-patterns.txt` necessarily
     contains the literal secrets it searches for; a screen report that reprinted
     them would leak them into a new file. Only the pattern NAME and a count are
     printed.
  2. It does not scan `scripts/scrub-patterns.txt` or `scripts/research-gate.sh`
     against themselves, for the reason the pattern file's own header gives: without
     that exclusion the scan always fails on itself, and a gate that always fails is
     a gate that gets switched off.

Exits non-zero if any pattern fires on any subject, so this is a check and not a
report.
"""
import os
import re
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "."
LOGDIR = os.path.join(REPO, "findings-log", "2026-10-13-area-k-patient-chunks")
PATTERNS = os.path.join(REPO, "scripts", "scrub-patterns.txt")

# The extensions the gate's leak scan does NOT read, plus every artefact this pass
# commits that falls in them.
SUBJECT_EXT = (".txt", ".tsv", ".h")

SELF_EXCLUDED = {"scripts/scrub-patterns.txt", "scripts/research-gate.sh"}

patterns = []
for line in open(PATTERNS):
    line = line.rstrip("\n")
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    if "|" not in line:
        continue
    name, pat = line.split("|", 1)
    try:
        patterns.append((name.strip(), re.compile(pat)))
    except re.error as e:
        print("FATAL: pattern %r does not compile: %s" % (name, e), file=sys.stderr)
        raise SystemExit(2)

subjects = []
for root, _dirs, files in os.walk(REPO):
    for f in files:
        if not f.endswith(SUBJECT_EXT):
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, REPO)
        if rel in SELF_EXCLUDED:
            continue
        subjects.append((rel, p))
subjects.sort()

hits = []
by_name = {}
for name, rx in patterns:
    n = 0
    for rel, p in subjects:
        try:
            body = open(p, "rb").read().decode("utf-8", errors="replace")
        except OSError:
            continue
        for m in rx.finditer(body):
            n += 1
            line = body.count("\n", 0, m.start()) + 1
            hits.append((name, rel, line))
    by_name[name] = n

o = []
w = o.append
w("=" * 96)
w("LEAK SCREEN — this pass's .txt / .tsv / .h artefacts against scripts/scrub-patterns.txt")
w("Committed because docs/09 section 4 records the gate's leak scan reads NO file of")
w("these extensions, in any mode, --all included. Pattern VALUES are not reprinted.")
w("=" * 96)
w("")
w("patterns loaded        : %d" % len(patterns))
w("subjects screened      : %d" % len(subjects))
w("subject extensions     : %s   (none of which the gate's leak scan reads)"
  % ", ".join(SUBJECT_EXT))
w("self-excluded          : %s" % ", ".join(sorted(SELF_EXCLUDED)))
w("")
w("-" * 96)
w("HITS PER PATTERN — the value is never printed")
w("-" * 96)
w("%-46s %s" % ("pattern", "hits"))
for name in sorted(by_name):
    w("%-46s %d" % (name, by_name[name]))
w("")
# --- SELF-TEST -----------------------------------------------------------------
# scripts/scrub-patterns.txt states the rule itself: "a scan proves nothing about a
# pattern until the pattern has been shown to fire." A screen that has never been
# seen to fail is indistinguishable from a screen that cannot fail — which is the
# defect this pass was just corrected for twice. So the screen is given a known-bad
# string and must report it.
#
# The strings are BUILT AT RUNTIME from fragments. Writing them out literally would
# put the very material being screened into a new committed file, which is the one
# thing this script exists to prevent.
SELFTEST_OK = True
w("-" * 96)
w("SELF-TEST — a known-bad string must be caught, or this screen cannot be trusted")
w("-" * 96)
probes = [
    ("machine-specific paths", "/" + "home" + "/" + "zzprobe" + "/x"),
    ("live jsession values", ";jsessionid_" + "ZZPROBE1" + "="),
    # NOTE the trailing DOT, not a letter: the pattern ends in `\b`, and "corpx" is
    # a single word, so a probe written as `.corpx` fails for the wrong reason and
    # would have had me "fix" a pattern that was never broken.
    ("internal .corp host", "zzprobe" + ".corp" + "."),
    ("internal Grafana/K8s/GitLab/DB/Prometheus host",
     "grafana" + "." + "zzprobe" + "." + "minimed" + ".x"),
]
for pname, probe in probes:
    rx = dict(patterns).get(pname)
    fired = bool(rx and rx.search(probe))
    if not fired:
        SELFTEST_OK = False
    w("%-4s %-48s probe %r"
      % ("ok" if fired else "BAD", pname, probe[:34]))
if not SELFTEST_OK:
    w("  -> *** at least one pattern did not fire on its own target: the screen is")
    w("     either mis-specified or the pattern is dead, exactly as the pattern file")
    w("     warns. Do not read the zero-hit verdict above as evidence. ***")
else:
    w("  -> every probed pattern fires on its own target, so the zero-hit verdict")
    w("     above is a measurement rather than a silence.")
w("")
if hits or not SELFTEST_OK:
    w("-" * 96)
    w("FAILURES — every hit, by pattern name, file and line")
    w("-" * 96)
    for name, rel, line in hits:
        w("  %s  %s:%d" % (name, rel, line))
    w("")
    w("VERDICT: %d HIT(S). The diff must not be pushed until these are gone." % len(hits))
    if not SELFTEST_OK:
        w("VERDICT: and the SELF-TEST failed, so this screen cannot be trusted at all.")
elif not SELFTEST_OK:
    w("-" * 96)
    w("VERDICT: ZERO raw hits, but the SELF-TEST FAILED — this is a silence, not a result.")
else:
    w("-" * 96)
    w("VERDICT: ZERO hits on all %d patterns across all %d subjects." % (len(patterns), len(subjects)))
    w("")
    w("Note what this does and does not establish: it establishes that the scrub list")
    w("does not fire on these files. It does not establish that the list is complete,")
    w("and it cannot — the pattern file itself warns that a pattern which never fires")
    w("is silent, and that a scan proves nothing about a pattern until the pattern has")
    w("been shown to fire on its own target.")
w("=" * 96)
print("\n".join(o))
sys.exit(1 if (hits or not SELFTEST_OK) else 0)