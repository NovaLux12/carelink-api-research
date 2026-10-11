#!/usr/bin/env bash
# research-loop.sh — loop a coding agent until the research work runs out.
#
# WHY THIS EXISTS
# None of opencode, Claude Code, or Codex CLI has a native "loop until a goal
# is met" mode. Each gives you one non-interactive run, a way to resume a
# session, and a way to cap cost. So the loop is this file: a goal file, a
# state file, three stop conditions, and a log per iteration.
#
# The goal is NOT a prompt. The goal is a WORKLIST — a file of `- [ ] <area>`
# lines. An agent flips a line to `- [x]` only when the area is closed with
# evidence. The loop stops when no `- [ ]` line remains.
#
# STATE LIVES IN FILES, NOT IN THE SESSION. A resumed session is a liability:
# it grows, it gets compacted, and (for Claude Code) --continue skips -p
# sessions anyway. Each iteration starts fresh and reads its marching orders
# off disk.
#
# USAGE
#   ./scripts/research-loop.sh                    # opencode, 5 iterations
#   AGENT_CLI=claude ./scripts/research-loop.sh
#   AGENT_CLI=codex   ./scripts/research-loop.sh
#   MAX_ITERATIONS=1 ./scripts/research-loop.sh   # dry run
#
# ENV
#   AGENT_CLI        opencode | claude | codex     (default: opencode)
#   AGENT_BIN        absolute path to that binary. Set this (or DRY_RUN=1) when
#                    testing — the PATH below deliberately puts the known
#                    install locations FIRST, so a stub passed via PATH will be
#                    shadowed by a real CLI and the loop will launch a real
#                    research session.
#   DRY_RUN          1 = build and print each iteration's prompt, invoke nothing
#   MAX_ITERATIONS   hard stop on iteration count  (default: 5)
#   REQUEST_BUDGET   stop when cumulative requests reach this (default: 0 = off)
#   WORKLIST         file of `- [ ] <area>` lines   (default: .loop/worklist.md)
#   MODEL            optional model override
#
# EXIT
#   0  stopped on a goal condition (no unclaimed areas, or budget exhausted)
#   1  environment failure, or an iteration failed and retries ran out
#   2  stopped on MAX_ITERATIONS

set -uo pipefail

# ---------------------------------------------------------------------------
# 0. Environment. cron runs with PATH=/usr/bin:/bin, PWD=$HOME and a non-login
#    /bin/sh, so a CLI installed by nvm/pnpm/the vendor installer is simply
#    "command not found". Put the real locations first, then verify.
# ---------------------------------------------------------------------------
export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$HOME/.local/share/pnpm:\
$HOME/.nvm/current/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"

# The repo must be the CWD: opencode discovers AGENTS.md by walking up from the
# launch directory, so a loop started in $HOME silently loses the whole
# instruction file.
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || REPO=$PWD
cd "$REPO" || { echo "!! cannot enter $REPO"; exit 1; }
[ -f AGENTS.md ] || echo ".. warning: no AGENTS.md in $REPO — the agent will not see the house rules"

AGENT_CLI=${AGENT_CLI:-opencode}
AGENT_BIN=${AGENT_BIN:-}
DRY_RUN=${DRY_RUN:-0}
MAX_ITERATIONS=${MAX_ITERATIONS:-5}
REQUEST_BUDGET=${REQUEST_BUDGET:-0}
WORKLIST=${WORKLIST:-.loop/worklist.md}
MODEL=${MODEL:-}

LOOPDIR=.loop
LOGDIR=$LOOPDIR/logs
STATE=$LOOPDIR/state.tsv
REPORT=$LOOPDIR/last-report.md
mkdir -p "$LOGDIR"

if [ "$DRY_RUN" -eq 0 ]; then
  if [ -n "$AGENT_BIN" ]; then
    [ -x "$AGENT_BIN" ] || { echo "!! AGENT_BIN '$AGENT_BIN' is not executable"; exit 1; }
  else
    command -v "$AGENT_CLI" >/dev/null 2>&1 || {
      echo "!! '$AGENT_CLI' not on PATH. Current PATH: $PATH"; exit 1; }
  fi
else
  echo "== DRY RUN: no agent will be invoked, no request will be made =="
fi

# One loop at a time. Two loops mean two sessions probing the same afternoon.
exec 9>"$LOOPDIR/lock"
if command -v flock >/dev/null 2>&1; then
  flock -n 9 || { echo "!! another research-loop.sh is running here"; exit 1; }
fi

[ -s "$STATE" ] || printf 'iteration\tstarted_utc\texit\trequests_used\tareas_open\tstop_reason\n' >"$STATE"

# ---------------------------------------------------------------------------
# 1. Goal file. Pre-seed it from docs/11 if it does not exist yet: every
#    `### X. Name` heading becomes a work item.
# ---------------------------------------------------------------------------
if [ ! -s "$WORKLIST" ]; then
  if [ -f docs/11-suggested-research-areas.md ]; then
    grep '^### [A-Z]\.' docs/11-suggested-research-areas.md \
      | sed 's/^### /- [ ] /' >"$WORKLIST"
    echo ".. seeded $WORKLIST with $(grep -c '^- \[ \]' "$WORKLIST") areas"
  else
    echo "!! no worklist and no docs/11 — create $WORKLIST with '- [ ] <area>' lines"
    exit 1
  fi
fi

open_areas() { grep -c '^\- \[ \]' "$WORKLIST" 2>/dev/null || echo 0; }
total_requests() { awk -F'\t' 'NR>1{s+=$4} END{print s+0}' "$STATE"; }

# ---------------------------------------------------------------------------
# 2. The iteration prompt. Written to disk and passed as one argv element;
#    it is deliberately self-contained because opencode's non-interactive mode
#    denies the question tool and plan mode — the agent cannot ask you anything.
# ---------------------------------------------------------------------------
build_prompt() {
  local iter=$1
  cat >"$LOOPDIR/prompt-$iter.md" <<PROMPT
You are iteration $iter of a bounded research loop on this repository, a public
read-only map of Medtronic's undocumented CareLink API.

Read, before anything else:
  AGENTS.md
  CONTRIBUTING-research.md   (follow "Run a research session", steps 1 to 7)
  docs/11-suggested-research-areas.md
  docs/09-methodology-and-oracles.md
  docs/10-open-questions.md
  $WORKLIST

Your goal for this iteration: **close the single highest-value area in
$WORKLIST that is still marked \`- [ ]\`, or prove it blocked.**

Invariants, non-negotiable:
- GET only. No POST, no token exchange, no authentication, no port scanning,
  no DNS brute force, no wordlist fuzzing. OPTIONS with an empty body is
  allowed and is how POST-only routes are found.
- >=2 seconds between requests to the same host, under a stated cap. State the
  cap and the request count in your write-up.
- Candidate paths derived from an observed naming convention, reasoning
  recorded. "Try some words" is not a method.
- Discriminate on Content-Type, never on status code. carelinkhp.minimed.eu
  returns HTTP 200 + 5518 bytes of text/html for paths that do not exist.
- carelink.minimed.eu serves gzip unconditionally. Use \`curl --compressed\`.
- *.carelink.eu, *.carelink.com, *.clcloud.eu are wildcard parking DNS. Never
  report a name from those spaces as a vendor asset.
- Establish whether a status code is an oracle before trusting it. Controls
  first: one plausible path, one certainly-absent path.
- Anything that looks internal is recorded and left alone.
- Evidence labels: OBSERVED / PUBLISHED / INFERRED. An INFERRED claim that
  reads as OBSERVED is the worst thing you can do here. If you cannot point at
  the line a claim came from, delete the claim.
- Never write a credential, internal hostname, machine path, or live session
  value into any file or diff. Never publish raw archive captures.

Then:
1. Claim the area in an issue with the cap, the delay, and what "closed" means.
2. Probe. Controls first.
3. Raw pass -> findings-log/<YYYY-MM-DD>-<area>/. Synthesised -> docs/, citing
   the log. Pin any value someone will rely on -> regression/hurl/.
4. **Refill the priority page** (CONTRIBUTING-research.md step 7): move the
   closed area into the dated Closed table with its evidence, and add at least
   ONE successor area with a stated blocker, a definition of done, and INFERRED
   labels on any assumption behind it. If you genuinely cannot name one, write
   the reason in the PR.
5. Run \`./scripts/research-gate.sh\`. It must exit 0. Then open the PR.
6. Flip your area's line in $WORKLIST from \`- [ ]\` to \`- [x]\`.
7. Append this to $REPORT:

## Loop report
ITERATION: $iter
REQUESTS_USED: <requests you made this iteration, not the running total>
AREAS_OPEN: <number of \`- [ ]\` lines left in $WORKLIST>
STOP: no-unclaimed-areas | budget-exhausted | needs-human | none
NOTES: <one line>

Stop when the gate exits 0 and the PR is open, or when you hit your request
cap, or when you can name a precise blocker. Do not silently exceed the cap.
Do not open a PR if the gate is red.
PROMPT
}

# ---------------------------------------------------------------------------
# 3. One run, per harness. Each writes a machine-readable log to
#    $LOGDIR/iter-<n>.* so the iteration is auditable afterwards.
#
#    Permissions, per harness — the loop needs to WRITE the findings log, so
#    every one of these is the least-privilege form that can still edit:
#      opencode --auto        auto-approve "ask" rules; explicit denies still fire
#      claude --permission-mode acceptEdits   edits in-cwd, no execution of
#                            everything else without a prompt
#      codex --sandbox workspace-write         (exec defaults to READ-ONLY)
# ---------------------------------------------------------------------------
run_iteration() {
  local iter=$1 pf="$LOOPDIR/prompt-$iter.md" prompt
  prompt=$(cat "$pf")

  if [ "$DRY_RUN" -eq 1 ]; then
    printf '%s\n' "$prompt" >"$LOGDIR/iter-$iter.dryrun.md"
    echo "    (dry run) prompt written to $LOGDIR/iter-$iter.dryrun.md"
    return 0
  fi

  case "$AGENT_CLI" in
    opencode)
      # --auto is NOT optional: `opencode run` auto-rejects permission.asked
      # events when it is absent, and the session gives up after a few errors.
      # --title makes the session findable afterwards; --format json gives an
      # auditable event stream. A fresh session per iteration on purpose: state
      # lives in files, not in the conversation.
      "${AGENT_BIN:-opencode}" run --auto ${MODEL:+--model "$MODEL"} \
                 --title "carelink-research-loop-$iter" \
                 --format json "$prompt" \
                 >"$LOGDIR/iter-$iter.json" 2>"$LOGDIR/iter-$iter.err"
      ;;
    claude)
      # acceptEdits, not bypassPermissions: the loop writes files, it does not
      # need to run arbitrary commands without a prompt. --max-turns bounds a
      # runaway iteration; --max-budget-usd bounds spend for THIS invocation.
      "${AGENT_BIN:-claude}" -p --permission-mode acceptEdits \
                 --max-turns 80 ${MODEL:+--model "$MODEL"} \
                 --output-format json "$prompt" \
                 >"$LOGDIR/iter-$iter.json" 2>"$LOGDIR/iter-$iter.err"
      ;;
    codex)
      # exec defaults to a READ-ONLY sandbox, which cannot write the findings
      # log. workspace-write is the least privilege that can. --json plus
      # --output-last-message gives both the event stream and a summary.
      "${AGENT_BIN:-codex}" exec --sandbox workspace-write --json ${MODEL:+--model "$MODEL"} \
                 --output-last-message "$LOGDIR/iter-$iter.last.md" \
                 "$prompt" \
                 >"$LOGDIR/iter-$iter.json" 2>"$LOGDIR/iter-$iter.err"
      ;;
    *) echo "!! unknown AGENT_CLI '$AGENT_CLI'"; exit 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# 4. Stop decision. Three conditions, checked before each iteration.
# ---------------------------------------------------------------------------
decide_stop() {
  STOP_REASON=""
  if [ "$(open_areas)" -eq 0 ]; then
    STOP_REASON="no-unclaimed-areas"; return 0
  fi
  if [ "$REQUEST_BUDGET" -gt 0 ] && [ "$(total_requests)" -ge "$REQUEST_BUDGET" ]; then
    STOP_REASON="request-budget-exhausted"; return 0
  fi
  # An iteration can also ask to stop: STOP: needs-human in its report.
  if [ -f "$REPORT" ] && grep -q '^STOP: needs-human' "$REPORT"; then
    STOP_REASON="needs-human"; return 0
  fi
  return 1
}

# ---------------------------------------------------------------------------
# 5. The loop.
# ---------------------------------------------------------------------------
echo "=== research-loop: cli=$AGENT_CLI repo=$REPO max=$MAX_ITERATIONS budget=${REQUEST_BUDGET:-off} ==="
echo "    worklist=$WORKLIST  open=$(open_areas)"

iter=0
RETRIES=2
final=2

while [ "$iter" -lt "$MAX_ITERATIONS" ]; do
  if decide_stop; then
    echo "--- stop: $STOP_REASON (iteration $iter, $(open_areas) areas open)"
    final=0
    break
  fi

  iter=$((iter+1))
  started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo
  echo "--- iteration $iter / $MAX_ITERATIONS   open=$(open_areas)   requests_so_far=$(total_requests)"
  build_prompt "$iter"
  run_iteration "$iter"
  rc=$?

  # An iteration that made no progress is retried once, then the loop stops
  # rather than burning the rest of the budget on the same failure.
  if [ "$rc" -ne 0 ] && [ "$RETRIES" -gt 0 ]; then
    echo "    iteration exited $rc; retrying"
    RETRIES=$((RETRIES-1))
    iter=$((iter-1))
    continue
  fi

  reqs=0
  areas=$(open_areas)
  if [ -f "$REPORT" ]; then
    r=$(sed -n 's/^REQUESTS_USED: *//p' "$REPORT" | tail -1)
    a=$(sed -n 's/^AREAS_OPEN: *//p'      "$REPORT" | tail -1)
    [[ "$r" =~ ^[0-9]+$ ]] && reqs=$r
    [[ "$a" =~ ^[0-9]+$ ]] && areas=$a
  fi

  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$iter" "$started" "$rc" "$reqs" "$areas" "${STOP_REASON:-}" >>"$STATE"

  echo "    exit=$rc requests=$reqs areas_open=$areas"
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "    logs: $LOGDIR/iter-$iter.dryrun.md"
  else
    echo "    logs: $LOGDIR/iter-$iter.json, $LOGDIR/iter-$iter.err"
  fi

  if [ "$rc" -ne 0 ]; then
    echo "!! iteration $iter failed twice; stopping rather than burning budget"
    final=1
    break
  fi
done

echo
echo "=== summary ==="
cat "$STATE"
echo "iterations run: $iter   areas still open: $(open_areas)"
[ -n "${STOP_REASON:-}" ] && echo "stop reason: $STOP_REASON"
echo "per-iteration logs: $LOGDIR/iter-*.{json,err}"
exit "$final"
