#!/usr/bin/env python3
"""redact.py — lane l2. Zero vendor requests.

WHAT IT IS FOR. `pow.nutrino.cc.broker.service.config` and
`pow.nutrino.cc.metadata.service.config` returned a **non-placeholder**
`security_headers."x-api-key"` on the `.com` deployments in this pass. That is
the same key material this repository already documents as F2 /
SECURITY-FINDINGS §S3 and redacts everywhere — so it is an already-known
published value, not a new disclosure. It is still a credential, and
`SECURITY.md` is unambiguous: the value does not go into this repository, not
into a finding, not into `plan.md`, not into a PR body, not into an issue.

This script is the mechanical guarantee, not a promise. It reads the scrub
patterns from `scripts/scrub-patterns.txt` — the same list the PR gate scans
the diff with — so the net it applies here is the gate's net, not a hand-typed
subset of it.

It rewrites the committed response bodies in place, replacing each match with
the repository's own redaction token, and records every substitution. It does
NOT touch `results.jsonl`: that file's `body_bytes` and `body_sha256` describe
the body **as received**, which is the value that matters for reproducibility,
and the redacted file's size differs from it by design. `REDACTIONS.md` states
that so a re-deriver is not confused by the mismatch.
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Resolved with git, not by counting parent directories: this pass was written
# in .loop/worktrees/<name>/, where a five-level walk happens to land on the
# main checkout, and that accidental success would have broken the script the
# moment the branch was merged into a normal checkout (five levels up from
# <repo>/findings-log/<pass>/ is not the repo). `git rev-parse --show-toplevel`
# is the convention in scripts/research-loop.sh and six other files here.
_top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
# Loud and early, and specifically NOT a bare os.path.exists check: from the
# merged checkout the old five-level walk resolved several levels ABOVE the
# repository — to a directory that exists — so an existence test would pass and
# the script would then die at open(PATTERNS) with a traceback pointing at the
# scrub-patterns file rather than at the path resolution three lines above it.
# (The concrete wrong root is not written here on purpose: it is a machine-
# specific path, which this script's own patterns scrub — it redacted this
# comment the first time it ran.)
if not _top or not os.path.isfile(os.path.join(_top, "scripts", "scrub-patterns.txt")):
    sys.exit("STOP: could not locate the repository root from "
             f"{HERE}. Searched via `git rev-parse --show-toplevel`, which returned "
             f"{_top!r}; expected scripts/scrub-patterns.txt beneath it. Running this "
             "outside a git worktree is not supported — run it from the checkout.")
REPO = _top
PATTERNS = os.path.join(REPO, "scripts", "scrub-patterns.txt")
TOKEN = "<VENDOR-API-KEY-REDACTED>"   # the repo's own token, SECURITY-FINDINGS §S3

# Scanned extensions only. Binary-ish and >1MiB files are not text and are
# excluded by research-checks.py's hygiene rule anyway.
SUFFIXES = (".b", ".h", ".md", ".json", ".jsonl", ".sh", ".py", ".txt", ".log")
# `redact.py` skips itself: this script was rewritten mid-pass, and the one
# machine-specific path its own comment carried made the next run match the
# comment and rewrite this file and REDACTIONS.md. A tool that edits its own
# source is not a redaction tool.
SKIP = {"results.jsonl", "plan.json", "REDACTIONS.md", "redact.py"}

pats = []
for line in open(PATTERNS, encoding="utf-8"):
    line = line.rstrip("\n")
    if not line or line.lstrip().startswith("#") or "|" not in line:
        continue
    name, _, pat = line.partition("|")
    pats.append((name.strip(), pat.strip()))

changed = []
scanned = 0
for root, _dirs, files in os.walk(HERE):
    for fn in files:
        if fn in SKIP or not fn.endswith(SUFFIXES):
            continue
        p = os.path.join(root, fn)
        try:
            t = open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        hits, new = 0, t
        for name, pat in pats:
            try:
                new, n = re.subn(pat, TOKEN, new)
            except re.error:
                continue
            hits += n
        if hits:
            open(p, "w", encoding="utf-8").write(new)
            changed.append((os.path.relpath(p, HERE), hits,
                            hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]))

if not changed:
    print("redact.py: no matches — nothing to redact")
    sys.exit(0)

lines = ["# REDACTIONS.md — lane l2, applied mechanically before any write-up\n",
         "`pow.nutrino.cc.broker.service.config` and "
         "`pow.nutrino.cc.metadata.service.config` returned a **non-placeholder** "
         "`security_headers.\"x-api-key\"` on the `.com` deployments. This is the "
         "key material `docs/08` F2 / `findings-log/probe-2026-10-08/"
         "SECURITY-FINDINGS.md` §S3 already document and already redact — an "
         "already-published vendor value, not a new disclosure. It is still a "
         "credential and `SECURITY.md` does not permit it in this repository.\n",
         "`redact.py` applied the **gate's own pattern list** "
         "(`scripts/scrub-patterns.txt`), not a hand-typed subset, and the "
         "replacement is the repository's existing token.\n",
         "| file | substitutions | sha256 of the redacted file (16) |",
         "|---|---:|---|"]
for f, n, h in changed:
    lines.append(f"| `{f}` | {n} | `{h}` |")
lines += ["",
          "**`results.jsonl` is deliberately untouched.** Its `body_bytes` and "
          "`body_sha256` are the **as-received** values — 329 / 314 on the two "
          "`.com` hosts and 309 / 288 on `carelink.medtronic.eu` — and they are "
          "what makes the finding reproducible. The redacted file in `headers/` "
          "is therefore *not* byte-identical to the body those two fields "
          "describe; the difference is exactly the substitution count above. "
          "Comparing the two is a way to confirm the redaction happened, not a "
          "way to check a finding.\n",
          "**What may and may not be said about the value.** Its *shape* — a "
          "40-character base62 string, identical in both services, present on the "
          "`.com` deployments and replaced by a 17-character placeholder on "
          "`carelink.medtronic.eu` — is recorded, because the shape is the finding. "
          "The value itself is not recorded anywhere in this repository, and "
          "`SECURITY.md` says so in advance.\n"]
open(os.path.join(HERE, "REDACTIONS.md"), "w", encoding="utf-8").write("\n".join(lines))
print(f"redact.py: scanned {scanned} file(s), rewrote {len(changed)}")
for f, n, h in changed:
    print(f"  {n} substitution(s)  {h}  {f}")