#!/usr/bin/env bash
# research-gate.sh — the gate this repo's claims must pass.
#
# Run it before opening a PR, and it runs again in CI on every PR. Exit 0 =
# publishable. Exit 1 = something in the diff must not ship.
#
# Usage:
#   ./scripts/research-gate.sh            # check the diff vs origin/main
#   ./scripts/research-gate.sh --staged   # check staged changes
#   ./scripts/research-gate.sh --all      # check every tracked file
#   ./scripts/research-gate.sh --suite    # only the live assertion suite
#
# What it enforces, and why:
#   1. no credential material, ever
#   2. no internal hostnames, ever
#   3. no machine-specific paths
#   4. no live session values from archive captures
#   5. every [source: …] citation resolves to a real file
#   6. the vendor assertion suite still exits 0
#
# Deliberately NOT enforced: whether a claim is TRUE. That needs a human or a
# second pass. This gate stops the irreversible mistakes, not the subtle ones.

set -uo pipefail
cd "$(dirname "$0")/.."

MODE="diff"
SUITE_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --staged) MODE="staged" ;;
    --all)    MODE="all" ;;
    --suite)  SUITE_ONLY=1 ;;
    --help|-h) sed -n '2,20p' "$0"; exit 0 ;;
  esac
done

FAIL=0
note() { printf '  %-8s %s\n' "$1" "$2"; }

# ---------------------------------------------------------------- 1-4: leak scan
# Built from the repo's own history: every one of these has been in a file at
# some point. Matched on the DIFF so that AGENTS.md and README can *name* the
# patterns without tripping them.
if [ "$SUITE_ONLY" -eq 0 ]; then
  echo "--- leak scan (mode: $MODE) ---"

  # Gather the text under test.
  if [ "$MODE" = "all" ]; then
    SUBJECT=$(git ls-files '*.md' '*.yml' '*.yaml' '*.sh' '*.hurl' 2>/dev/null)
  elif [ "$MODE" = "staged" ]; then
    SUBJECT=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(md|yml|yaml|sh|hurl)$' || true)
  else
    BASE=$(git rev-parse --verify origin/main 2>/dev/null || echo HEAD)
    SUBJECT=$(git diff --name-only --diff-filter=ACM "$BASE" | grep -E '\.(md|yml|yaml|sh|hurl)$' || true)
  fi

  if [ -z "$SUBJECT" ]; then
    note ok "no changed files to scan"
  else
    # ADDED lines only — a pre-existing line in a touched file is not this PR's
    # doing, and flagging it would make the gate unusable.
    case "$MODE" in
      all)    ADDED=$(printf '%s\n' "$SUBJECT" | xargs -r cat 2>/dev/null) ;;
      staged) ADDED=$(git diff --cached --diff-filter=ACM -U0 | grep '^+' | grep -v '^+++') ;;
      *)      BASE=$(git rev-parse --verify origin/main 2>/dev/null || echo HEAD)
              ADDED=$(git diff --diff-filter=ACM -U0 "$BASE" | grep '^+' | grep -v '^+++') ;;
    esac

    # Each pattern is: name | extended-regex. Deliberately specific — a loose
    # pattern would make people disable the gate, which is worse than no gate.
    while IFS='|' read -r name pat; do
      [ -z "$name" ] && continue
      hits=$(printf '%s' "$ADDED" | grep -cEi "$pat" || true)
      if [ "${hits:-0}" -gt 0 ]; then
        note "!!" "$name — $hits hit(s). DO NOT COMMIT."
        printf '%s' "$ADDED" | grep -nEi "$pat" | head -3 | cut -c1-150 | sed 's/^/           /'
        FAIL=1
      else
        note ok "$name"
      fi
    done <<'PATTERNS'
vendor API key literal|11IQOmW1Yr4z8T4kkeZJD5YbN4FSaWAQ4J5JpWi1
reports-broker key fragments|(0vJJl02[0-9A-Za-z]{8,}|GIFQiM3[0-9A-Za-z]{8,})
reCAPTCHA site keys|6Lf?buorAAAA[0-9A-Za-z_-]{10,}
internal Grafana/K8s/GitLab/DB/Prometheus host|(grafana|k8s|gitlab|prometheus|db)\.[a-z0-9-]+\.(minimed|medtronic)\.
internal *.corp host|[a-z0-9-]+\.corp\b
other internal-looking hosts|(titan-internal|mmd|ols)\.
machine-specific paths|/home/[a-z]|/Users/[a-z]|C:\\Users\\
live jsession values|;jsessionid_[A-Z0-9]{6,}=
live sessionData values|sessionData=[A-Za-z0-9_-]{20,}
long base64 secrets|\b[A-Za-z0-9+/]{40,}={0,2}\b
PATTERNS
  fi
fi

# ---------------------------------------------------------------- 5: citations
if [ "$SUITE_ONLY" -eq 0 ]; then
  echo "--- citation integrity ---"
  BROKEN=$(python3 - <<'PY'
import re, glob, os
real = set(glob.glob('findings-log/**/*.md', recursive=True))
bad = 0
targets = glob.glob('docs/*.md') + ['README.md', 'AGENTS.md']
for page in targets:
    if not os.path.exists(page):
        continue
    t = open(page, encoding='utf-8', errors='replace').read()
    for m in re.findall(r'findings-log/[A-Za-z0-9._/-]+\.md', t):
        if '<' in m:
            continue
        if m not in real:
            print(f'    {page}: {m}')
            bad += 1
    for m in re.findall(r'(?<![\w./-])recon/[A-Za-z0-9._-]+\.md', t):
        if f'findings-log/probe-2026-10-08/{m}' not in real:
            print(f'    {page}: recon/{m}')
            bad += 1
print(f'BROKEN={bad}')
PY
)
  N=$(printf '%s' "$BROKEN" | sed -n 's/^BROKEN=//p')
  printf '%s\n' "$BROKEN" | grep -v '^BROKEN=' | sed 's/^/    /' || true
  if [ "${N:-0}" -gt 0 ]; then note "!!" "$N broken citation path(s)"; FAIL=1
  else note ok "all citation paths resolve"; fi
fi

# ---------------------------------------------------------------- 6: suite
echo "--- vendor assertion suite ---"
if command -v hurl >/dev/null 2>&1 && [ -x regression/hurl/05-public-config.check.sh ]; then
  if ( cd regression/hurl && bash ./05-public-config.check.sh >/tmp/_gate_suite.log 2>&1 ); then
    note ok "$(tail -2 /tmp/_gate_suite.log | grep -oE '[0-9]+ passed.*' || echo 'suite green')"
  else
    note "!!" "assertion suite failed — read regression/hurl output"
    tail -6 /tmp/_gate_suite.log | sed 's/^/    /'
    FAIL=1
  fi
else
  note "~~" "hurl not installed — suite skipped. Install: brew install hurl"
fi

echo
if [ "$FAIL" -eq 0 ]; then
  echo "GATE PASS — safe to open a PR."
  exit 0
fi
echo "GATE FAIL — fix the above, then re-run. See AGENTS.md §7 for the scrub list."
exit 1