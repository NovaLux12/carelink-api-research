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
internal hostnames, validates every citation path, and re-runs the vendor
assertion suite. CI runs the identical script, so a red gate blocks the merge
regardless. If it fails, fix it — don't work around it.

### 6. Open the PR

Use `.github/PULL_REQUEST_TEMPLATE.md`. Fill the evidence table honestly,
including the request count.

If your finding corrects something already published, say so plainly and keep the
original claim visible with the correction attached — **never delete a
retraction**. That history is the evidence.

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
five wrong claims before an audit caught them — including a glucose-unit claim
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
| assertion suite | re-runs `regression/hurl/` — a failure means the vendor surface moved |

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