# Contributing research

**You want to help reverse-engineer Medtronic's CareLink API.** This file is the
whole instruction set. Follow it in order.

You have one of two starting points:

- **You have an area you want to work** → [Run a research session](#run-a-research-session)
- **You already have a finding** → [Submit a finding](#submit-a-finding)

Either way the gate is the same: `./scripts/research-gate.sh` must exit 0.

---

## Read these before you touch the network

| File | Why |
|---|---|
| `AGENTS.md` | the operating rules — evidence classes, never-publish list, the four ways this project has been wrong |
| `docs/00-summary-the-map.md` | what is already known, so you do not re-derive it |
| `docs/11-suggested-research-areas.md` | the open areas and their blockers |
| `docs/09-methodology-and-oracles.md` | the traps and the existence oracles |

Fetch them over HTTPS rather than assuming you have them:

```bash
gh api repos/NovaLux12/carelink-api-research/contents/AGENTS.md --jq .content | base64 -d
# or, to get the whole repo:
git clone https://github.com/NovaLux12/carelink-api-research
```

---

## Run a research session

### 1. Claim an area first

Open an issue using the **Claim a research area** form. Before you probe anything,
state:

- which area from `docs/11-suggested-research-areas.md`, and why it's the
  highest-value one you can do
- the exact request cap you will not exceed
- the delay you'll hold between requests to the same host
- what "closed" means — **including whether a negative result counts**

Claiming first stops two people duplicating the same afternoon.

### 2. Probe

These are not negotiable:

- **GET only.** No POST, no token exchange, no authentication, no port scanning,
  no DNS brute force, no wordlist fuzzing.
- **≥2 seconds between requests to the same host.** Stay under your cap.
- Candidates must be **derived from an observed naming convention**, with the
  reasoning recorded. A bounded, justified list is fine. "Try some words" is not.
- **Discriminate on `Content-Type`, never on status code.** `carelinkhp.minimed.eu`
  returns HTTP 200 with 5518 bytes of HTML for every path that does not exist —
  a status-code check reads that as a hit.
- **`carelink.minimed.eu` serves gzip unconditionally**, ignoring
  `Accept-Encoding`. Use `curl --compressed`, or every parse fails.
- **`*.carelink.eu`, `*.carelink.com`, `*.clcloud.eu` are wildcard DNS on a
  parking operator.** A random unregistered string resolves there. Never report a
  name from those spaces as a vendor asset — that is how a false positive
  reaches a disclosure.
- **Establish whether a status code is an oracle before trusting it.** On
  `clcloud.*` the 403 line is uniform and useless; `x-amzn-errortype` is the
  signal. Prove it with controls: one plausible path, one certainly-absent path.
- Anything that looks internal is **recorded and left alone.**

### 3. Write it up

**Every claim gets an evidence label and a source cite.** This is the rule the
repo enforces hardest:

- **OBSERVED** — you saw it in a live response
- **PUBLISHED** — it is in a vendor document served without a login
- **INFERRED** — you reasoned it; show the reasoning *and* its assumptions

An INFERRED claim that reads as OBSERVED is the worst thing you can do here. If
you are not sure, it is INFERRED.

- Raw pass → `findings-log/<YYYY-MM-DD>-<area>/`. Append-only. Include your
  request count, your cap, your delay, and any negative results.
- Synthesised finding → the relevant `docs/` page, citing the log with a
  `[source: findings-log/…]` path. Don't duplicate the log; link it.

**A negative result is a first-class contribution.** Issue #84 was closed by
proving something does *not* exist, across 73 paths, 28 key names and four
corpora. That is one of the most useful things anyone can contribute here.

### 4. Pin anything that must not rot

If your finding is a specific value someone will later rely on, add an assertion
to `regression/hurl/`. Unpinned claims have quietly gone stale here repeatedly.

### 5. Gate it

```bash
./scripts/research-gate.sh
```

**Do not open a PR until this exits 0.** It scans the diff for credentials and
internal hostnames, validates every citation path, checks numbers / hygiene /
priorities / prompt parity / append-only, and re-runs the 05-public-config
vendor suite (the PR gate runs 05 only by design — cheap, no vendor storm per
PR; the full five-suite probe runs in the weekly drift sweep). CI runs the
identical script, so a red gate blocks the merge regardless. If it fails, fix
it — don't work around it.

### 6. Open the PR

Use `.github/PULL_REQUEST_TEMPLATE.md`. Fill the evidence table honestly,
including the request count.

If your finding corrects something already published, say so plainly and keep the
original claim visible with the correction attached — **never delete a
retraction**. That history is the evidence.

### 7. Leave the priorities page fuller than you found it

`docs/11-suggested-research-areas.md` is the page a newcomer reads to find work.
Every area you close makes it shorter. Unless you put back at least what you
took, it eventually says nothing and the repo loses its front door. **This step
is mandatory and it lands in the same PR as your finding** — amend, or add a
second commit, before you ask for review.

**(a) Close what you closed.** Move the area out of the live tiers into the dated
`## Closed areas` table at the bottom of the page. One row per area, with the
verdict, the evidence path, and the issue that claimed it:

```
| Area | Closed | Verdict | Evidence | Closed by |
|---|---|---|---|---|
| C — extend the oracle set to `pde/v3` and `csr` | 2026-10-11 | PDE dead on GET **and** OPTIONS; `csr/v2` and `connect/v2` **live, POST-only** | findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md | #2 |
```

Say plainly whether it was positive or negative. **A negative result closes an
area just as firmly** — #84 was closed by proving something does not exist
across 73 paths and four corpora.

The evidence path is validated by the gate, which fails any `[source:
findings-log/…]` path that does not resolve — so a closed row citing a log you
did not write fails the gate. Do not try to make it pass by deleting the cite.

**(b) Add at least one successor area**, derived from what you actually saw this
session — the thing you now know that you did not know when you started,
twisted into a question. One is the minimum. Two or three is better. Use the
template below.

**(c) Label the assumptions behind any successor that is INFERRED.** If any line
of it rests on reasoning rather than observation, mark it INFERRED and state the
assumption. An unlabelled INFERRED successor is the same failure as an
unlabelled INFERRED claim — and it sends the next person probing for something
you never saw.

**(d) If you genuinely cannot name a successor, say why** — in the PR, under a
`## Priorities` heading. Accepted reasons:

- **The session closed a whole class.** The discovery version axis provably
  serves two documents past 3.8 (`docs/10-open-questions.md` §2), so no
  "probe version N" successor exists any more. Say which class died.
- **Every follow-up needs a token.** Name them, and move them into the
  already-blocked table at the top of `docs/11`.
- **The finding was a correction**, so the honest successor is re-verifying the
  corrected claim. Name the claim and what would settle it.

Not accepted: *"there is plenty left on the page."* That is exactly the state
this step exists to prevent. The alarm in `.github/workflows/priorities-alarm.yml`
files an issue when the page falls below three open areas.

### Successor-area template

```markdown
### <Letter>. <Name — a question, not a topic>

<What is known, with evidence labels and [source: findings-log/…] cites.>

<What is missing, and why it matters.>

**Blocker:** <the one specific thing that stops this now — a token, an OPTIONS
probe nobody has run, an artefact nobody has read, a request budget. Not "more
research", and not "time".>

**Closes when:** <the specific, checkable result — including whether a negative
counts. If a negative counts, say so here.>

**Assumptions (INFERRED):** <every line above that is reasoned rather than
observed, with its assumption stated. Omit only if nothing above is inferred.>
```

### The quality bar for a successor

| Test | It fails when |
|---|---|
| **Derived** | it could have been written before your session ran |
| **Bounded** | the blocker is "a token" but it sits in Tier 1 rather than the blocked table; or "closes when" is not checkable by a stranger |
| **Non-duplicate** | it is already in `docs/10-open-questions.md` §1, already in the Closed table, or already on the page — grep both first |
| **Labelled** | reasoning reads as observation, or two sources disagree and only one is given |

A successor that fails one of these is worse than an empty page. Write the
empty-page reason under (d) instead.

---

## Submit a finding

Already have it? Skip the session.

1. **Check it isn't already recorded.** Grep `docs/` and `findings-log/`. A
   re-derivation is welcome if you say so and add what changed.
2. **Label the evidence honestly** (OBSERVED / PUBLISHED / INFERRED).
3. **Never write a credential, internal hostname, machine path, or live session
   value into the diff** — even to describe one. Describe it without the value.
4. Raw pass → `findings-log/`. Synthesised → `docs/`, citing the log. Pin it if
   it's a value someone will rely on.
5. Gate, then PR.

If you can't classify something as OBSERVED, it's INFERRED. If you can't point
at the line a claim came from, delete the claim.

---

## Looping an agent

Five ready-to-paste prompts, and the anatomy of running them in a loop. Each
prompt is self-contained — an agent that receives only the prompt and the repo's
instruction files acts correctly. `scripts/research-loop.sh` is a reference
controller that runs the loop prompt until the work runs out.

### The invariants every prompt below carries

```
- GET only. No POST, no token exchange, no authentication, no port scanning,
  no DNS brute force, no wordlist fuzzing. OPTIONS with an empty body is
  allowed and is how POST-only routes are found.
- >=2 seconds between requests to the same host, under a stated cap. State the
  cap and the request count in the write-up.
- Candidate paths must be derived from an observed naming convention, with the
  reasoning recorded. A bounded, justified list is fine. "Try some words" is not.
- Discriminate on Content-Type, never on status code. carelinkhp.minimed.eu
  returns HTTP 200 + 5518 bytes of HTML for every path that does not exist.
- carelink.minimed.eu serves gzip unconditionally, ignoring Accept-Encoding. Use
  `curl --compressed`, or every parse fails on 0x8b.
- *.carelink.eu, *.carelink.com, *.clcloud.eu are wildcard parking DNS. A random
  unregistered string resolves there. Never report a name from those spaces as a
  vendor asset — that is how a false positive reaches a disclosure.
- Establish whether a status code is an oracle before trusting it. On clcloud.*
  the 403 line is uniform and useless; x-amzn-errortype is the signal. Prove it
  with controls: one plausible path, one certainly-absent path.
- Anything that looks internal is recorded and left alone.
- Evidence labels: OBSERVED / PUBLISHED / INFERRED. An INFERRED claim that
  reads as OBSERVED is the worst thing you can do here. If you cannot point at
  the line a claim came from, delete the claim.
- Never write a credential, internal hostname, machine path, or live session
  value into any file, issue, or diff — even to describe one. Never publish raw
  archive captures.
- Run ./scripts/research-gate.sh before opening a PR. It must exit 0. CI runs
  the identical script. If it fails, fix it — do not work around it.
- Never delete a retraction. Corrections stay visible with the correction
  attached. That history is the evidence.
```

### Prompt A — one research session

```
You are contributing to https://github.com/NovaLux12/carelink-api-research — a
public, read-only map of Medtronic's undocumented CareLink API. A wrong claim
here misleads someone building a medical-data integration, so accuracy is worth
more than coverage.

Read these first, over HTTPS, before you touch the network (clone the repo if you
can — prefer that):
  AGENTS.md · CONTRIBUTING-research.md · docs/00-summary-the-map.md
  docs/11-suggested-research-areas.md · docs/09-methodology-and-oracles.md
  docs/10-open-questions.md

Then follow CONTRIBUTING-research.md "Run a research session" in order, ending at
step 7.

1. Pick ONE area from docs/11 that is not already claimed in an open issue. State
   why it is the highest-value one you can do, your request cap, your delay, and
   what "closed" means — including whether a negative counts.
2. Probe. Controls first: one plausible path, one certainly-absent path.
3. Raw pass → findings-log/<YYYY-MM-DD>-<area>/. Synthesised → docs/, citing the
   log. Pin anything someone will rely on into regression/hurl/.
4. Refill the priority page (step 7): close the area into the dated Closed
   table, and add at least one successor area with a blocker, a definition of
   done, and INFERRED labels where they belong.
5. Run the gate. Then open the PR.

Stop when the gate exits 0 and the PR is open, OR when you hit your stated
request cap, OR when you can state a specific blocker that stops the session — in
which case record it as the area's blocker and still write up what you have.
Do not silently exceed the cap.

Final output, in this order: one line per request (method, path, status,
discriminating header) · the evidence table (claim | class | source file:line) ·
the paths you changed · the gate exit code · the successor area(s) you added, or
the reason you could not.
```

### Prompt B — area-closing loop (one iteration)

```
You are one iteration of a research loop on
https://github.com/NovaLux12/carelink-api-research — a public read-only map of
Medtronic's undocumented CareLink API.

Read first: AGENTS.md · CONTRIBUTING-research.md · docs/00-summary-the-map.md
docs/11-suggested-research-areas.md · docs/09-methodology-and-oracles.md
docs/10-open-questions.md

Your goal for this iteration: close the single highest-value still-open area in
docs/11, or prove it blocked. "Highest value" = cheapest-and-highest-value
first, per the page's own ordering; token-gated areas are at the bottom and are
not yours to start.

1. Read docs/11. Choose one area. Check it is not claimed in an open issue.
2. Claim it in an issue with the exact request cap, the delay, and the specific
   result that would let you file it as done — including whether a negative
   counts. A vague bound is a failed iteration.
3. Probe. Controls first, so the oracle verdict is not contaminated by the data
   it judges.
4. Write it up: raw pass → findings-log/<date>-<area>/; synthesised → docs/; pin
   any value someone will rely on → regression/hurl/.
5. Refill the priority page (step 7): move the closed area into the dated Closed
   table with its evidence, and add at least one successor area with a stated
   blocker, a definition of done, and INFERRED labels on any assumption behind
   it. If you genuinely cannot name one, write the reason in the PR.
6. Run the gate. Open the PR.
7. Flip your area's line in .loop/worklist.md from - [ ] to - [x], and append
   this to .loop/last-report.md:

   ## Loop report
   ITERATION: <n>
   REQUESTS_USED: <cumulative requests this run>
   AREAS_OPEN: <count of - [ ] lines still in .loop/worklist.md>
   STOP: no-unclaimed-areas | budget-exhausted | needs-human | none
   NOTES: <one line>

Stop when any of: the gate exits 0 and the PR is open; your request cap is
reached; you hit a blocker you can name precisely (then record it as the area's
blocker and still submit what you have); or the area is already claimed.

Final output: area letter and one-line verdict · requests used, of what cap, at
what spacing · the evidence table · paths changed and the gate exit code · the
successor area(s) added · the Loop report block verbatim.
```

### Prompt C — priorities regeneration

```
You are refilling the priority page of
https://github.com/NovaLux12/carelink-api-research. You are NOT probing
anything in this task. This is a synthesis pass over what is already on disk.

Read first: AGENTS.md · docs/00-summary-the-map.md ·
docs/11-suggested-research-areas.md · docs/10-open-questions.md ·
docs/09-methodology-and-oracles.md · every findings-log/ directory whose date is
in the last 14 days · the Closed areas table at the bottom of docs/11.

1. List the newest findings — what each pass learned that was not known before.
2. For each new fact, ask: what does this now make askable that was not askable
   before? Derive candidate areas from that, not from a general wish list.
3. Check each candidate against docs/10 section 1 and the Closed table. Drop
   duplicates. Downgrade anything that needs a token into the already-blocked
   table.
4. Write TWO OR THREE new areas into docs/11 using the successor-area template in
   step 7, each with: what is known (labelled, cited), what is missing, a
   specific blocker, a checkable "closes when" that states whether a negative
   counts, and an Assumptions (INFERRED) line for anything reasoned rather than
   observed.

The bar: Derived (it could not have been written before the newest findings) ·
Bounded (the blocker is specific; "closes when" is checkable) · Non-duplicate ·
Labelled (reasoning does not read as observation). If you cannot name two areas
that pass, say so and say why — an honest short page beats a padded one.

Stop when you have 2-3 areas that pass the bar and are committed, or a written
explanation of why fewer exist. Final output: the log dirs you read with dates ·
each area in full template form · which candidates you dropped and which bar
they failed · anything moved to the token-blocked table · git diff --stat.
```

### Prompt D — independent verification of one claim

```
You are independently verifying ONE claim in
https://github.com/NovaLux12/carelink-api-research. Your job is to try to break
it, not to agree with it. A verification that only reads back the intended
target is worth nothing; that failure is on the record here.

Read first: AGENTS.md · CONTRIBUTING-research.md ·
docs/09-methodology-and-oracles.md · the docs page carrying the claim · the
findings-log file it cites.

1. Take the claim's cited source and open it. Assert you resolved the right
   thing — the file exists and the line says what the claim says it says. A
   lookup that silently returned null is how two different values once hashed to
   the same digest and looked like agreement.
2. Re-derive it from the artefact or the live surface, not from a prose summary
   of it. Values quoted in prose notes are not evidence; the pinned assertion
   and the raw log are.
3. If the claim rests on a hash, assert the resolved type before comparing, and
   treat an all-zero digest as a failure, not a comparison.
4. If it rests on a status code, re-establish the oracle with controls first.

Verdict, exactly one: CONFIRMS (you re-derived the same value by a route that
does not pass through the claim's own wording) · CONTRADICTS (paste both values
and the command that produced yours) · INCONCLUSIVE (say precisely what is
missing and what would settle it). If the sources disagree with each other, give
both. Never pick one silently.

Stop at the verdict. One claim per run. Do not exceed 10 requests; if you cannot
settle it inside 10, the verdict is inconclusive and the missing request is the
finding.

Final output: the claim verbatim and where it lives (file:line) · the verdict ·
the evidence (command and response head, or document and line) · if it
contradicts, the original claim kept visible with the correction attached, never
deleted · whether the suite pins this value and whether it agrees.
```

### Prompt E — drift sweep

```
You are running the drift sweep on
https://github.com/NovaLux12/carelink-api-research. The pinned assertions are
how this repo notices that the vendor surface moved. (The scheduled job at
.github/workflows/drift-sweep.yml does this weekly; this prompt is the manual
version, or the pass to run when it files a drift issue.)

Read first: AGENTS.md · CONTRIBUTING-research.md ·
docs/09-methodology-and-oracles.md · regression/hurl/ in full, including
05-public-config.check.sh's header.

1. cd regression/hurl && DELAY_MS=2000 ./run.sh — read the exit code and the
   full output, not just the summary line. Exit 0 = no drift.
2. For every failure, capture: suite, assertion label, expected, actual, and the
   response head that produced the actual.
3. Establish whether the failure is drift or a broken assertion. Re-probe the
   failing cell with controls. A suite that fails because of a proxy, a gzip
   mishandling, or a wrong expected value is not vendor drift; on
   carelink.minimed.eu gzip is sent unconditionally and hurl only decodes what
   it asked for, which is why the config suite is a shell script.
4. Write the result as a correction-ready finding: raw pass →
   findings-log/<date>-drift-sweep/; synthesised → the affected docs page, citing
   the log; and if a pinned value changed, update the assertion and the prose in
   the same change. The suite has caught a wrong prose hash before by being
   right when the note was wrong.
5. If nothing drifted, say so, with the exit code and the date. A clean sweep is
   a result.

Stop when every failing assertion is explained as drift (with evidence) or as a
harness artefact (with the control that proves it). Do not open a PR that
changes a claim the suite pins without updating the suite.

Final output: the run.sh exit code and timestamp · a table of assertion |
expected | actual | verdict · what would settle anything unknown · paths changed ·
the research-gate.sh exit code.
```

### Running the loop

**No harness has a native "loop until the goal is met" mode.** opencode,
Claude Code and Codex each give you one non-interactive run, a resume flag and
a cost cap; the loop is the wrapper around them. That is fine here: this repo's
protocol already has a goal state (the open areas in `docs/11`) and natural
stop conditions.

```bash
./scripts/research-loop.sh                    # opencode, up to 5 iterations
AGENT_CLI=claude ./scripts/research-loop.sh
AGENT_CLI=codex   ./scripts/research-loop.sh
MAX_ITERATIONS=1  REQUEST_BUDGET=60 ./scripts/research-loop.sh   # one, bounded
```

The controller seeds `.loop/worklist.md` from the `### X.` headings in
docs/11, runs one fresh session per iteration (state lives in files, not in the
conversation), records each iteration in `.loop/state.tsv`, and stops when the
open areas run out, the request budget is exhausted, an iteration reports
`needs-human`, or MAX_ITERATIONS is reached. It holds a lock, so two loops
cannot probe the same afternoon.

What each harness needs, and the pitfalls that cost someone an afternoon
(verified against vendor docs, 2026-10-11):

| | opencode | Claude Code | Codex CLI |
|---|---|---|---|
| Run | `opencode run "<prompt>"` | `claude -p "<prompt>"` | `codex exec "<prompt>"` |
| Resume | `--continue`/`-c`; `--session`/`-s` <id>; `--fork` | `--continue`/`-c`; `--resume`/`-r` <id>; `--fork-session` | `codex exec resume <id>` |
| Machine-readable | `--format json` | `--output-format json` | `--json`, `--output-last-message <path>` |
| Cap the run | none — cap in the wrapper | `--max-turns N`; `--max-budget-usd N` (print mode only) | none — cap in the wrapper |
| Permissions | `--auto` (approves anything not explicitly denied) | `--permission-mode acceptEdits` | default sandbox is read-only; `--sandbox workspace-write` |
| Restrict tools | `opencode agent create --permissions …` (allow-list; omitted = denied) | `--allowedTools`/`--disallowedTools` | `--sandbox`, `--add-dir` |
| Target directory | cwd — `cd` into the repo, don't rely on `--dir` | cwd (or `--add-dir`) | `--cd`/`-C` |

- **opencode `run` auto-rejects every permission request without `--auto`**, and
  the session gives up after a few errors. `--auto` is required; explicit deny
  rules still fire.
- **opencode's non-interactive mode denies the question tool and plan mode at
  session bootstrap** — which is why every prompt above states its own stop
  condition instead of asking you anything.
- **The repo must be the working directory.** opencode walks up from the launch
  directory to find `AGENTS.md`; a loop started in `$HOME` silently loses the
  house rules. `cd` into the repo.
- **Codex refuses to run outside a git repository** without
  `--skip-git-repo-check`, and `codex exec --full-auto` is deprecated — use
  `--sandbox workspace-write`.
- **Claude Code's `--max-budget-usd` is a client-side estimate** and resumed
  session totals do not carry over — budget per invocation, not per loop. Its
  `--continue` also skips `-p` sessions unless it is itself `claude -p
  --continue`; a resume that looks silent has quietly started a new
  conversation.
- **cron runs with `PATH=/usr/bin:/bin`** — a CLI installed by nvm or a vendor
  installer is simply `command not found`. `research-loop.sh` sets an explicit
  PATH.

The loop may not do two things: assign its own evidence label (OBSERVED needs a
response head, and a loop cannot see one), and merge its own PR. Merging is the
human's — AGENTS.md §11.

---

## The standard

A finding is submittable when a reader can answer four questions without
re-deriving anything:

| Question | Answered by |
|---|---|
| What did you observe? | verbatim evidence — the command and the response head |
| How do I know it's true? | the evidence label |
| Where did it come from? | a `[source: findings-log/…]` path that resolves |
| Could it be wrong, and how would I know? | stated limits, plus the control that bounds it |

A missing one means it isn't ready. This bar exists because the repo published
fourteen wrong claims before audits caught them — including a glucose-unit claim
that named the wrong countries.

---

## What the gate checks

| Check | Catches |
|---|---|
| credential material | the vendor key, reports-broker key fragments, reCAPTCHA keys, long base64 |
| internal hostnames | Grafana / K8s / GitLab / DB / Prometheus hosts, `.corp` hosts |
| machine paths | absolute home directories and Windows user profiles |
| live session values | `jsessionid_*`, `sessionData` JWS/JWE from archive captures |
| citation integrity | any `[source: …]` path that does not resolve |
| assertion suite (05 on PRs) | re-runs `05-public-config.check.sh` — a failure means the pinned config drifted; the full five-suite probe runs in the weekly drift sweep |
| numbers | every prose count matches `scripts/measure_assertions.py`; the counts-branch comparison is warning-only so pin-adding PRs don't deadlock |
| findings-log hygiene | missing accounting, oversized or banned captures |
| priorities sync | a log declaring an area closed while docs/11 still lists it open |
| prompt parity | one of the three prompt sources dropping a load-bearing rule |
| append-only | a findings-log deletion, or a rewrite without a dated Correction section |

It deliberately does **not** check whether a claim is true. That needs a human
or a second pass. The gate stops the irreversible mistakes; review catches the
subtle ones.

Flags:

```bash
brew install hurl jq     # macOS
apt-get install curl jq  # Debian/Ubuntu
```

---

## House rules

- **Never publish a credential.** Record *that* one exists and *where*, never the
  value. Full list in `AGENTS.md` §7.
- **Never delete a retraction.** Corrections stay visible with the correction
  attached. Several claims here are only trustworthy because you can see what
  they used to say.
- **If a finding is better held back for a disclosure decision, say so and say
  why**, rather than publishing it and hoping. One finding in this repo is
  deliberately unpublished for exactly that reason.
- **Diagrams are Mermaid**, GitHub renders it natively, and **every branch must
  be labelled** — an unlabelled branch is an INFERRED claim in disguise.