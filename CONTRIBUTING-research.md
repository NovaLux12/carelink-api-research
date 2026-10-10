# Contributing research

Two paths in. Pick whichever matches what you have.

| You have | Go to |
|---|---|
| An **area** you want to work | [Run a research session](#run-a-research-session) |
| A **finding** already in hand | [Submit a finding](#submit-a-finding) |

Either way, the bar is the same: `./scripts/research-gate.sh` exits 0.

---

## The standard

A finding is submittable when a reader can answer four questions without
re-deriving anything:

| Question | Answered by |
|---|---|
| What did you observe? | verbatim evidence — the command and the response head |
| How do I know it's true? | the evidence label — **OBSERVED** / **PUBLISHED** / **INFERRED** |
| Where did it come from? | a `[source: findings-log/…]` path that resolves |
| Could it be wrong, and how would I know? | stated limitations, plus the control that bounds it |

A missing one of those means it isn't ready. That is the entire standard, and
it exists because this repo published five wrong claims before an audit caught
them — including a glucose-unit claim that named the wrong countries.

**A negative result is a real result.** Issue #84 was closed by proving something
does *not* exist, across 73 paths, 28 key names and four corpora. That is a
first-class contribution, not a failure to find something.

---

## Run a research session

### 1. Claim an area

Open an issue with the **Claim a research area** form. State the area, your
request cap, your delay between requests, and what "closed" means for it —
*including whether a negative counts*. Claiming first stops two people duplicating
the same afternoon.

`docs/11-suggested-research-areas.md` lists open areas with their blockers.

### 2. Probe

Or copy the whole brief from
[`docs/RESEARCH-SESSION.md`](docs/RESEARCH-SESSION.md) — it is written to be
pasted into any agent. In short:

- **GET only.** No POST, no token exchange, no authentication, no port scanning,
  no DNS brute force, no wordlist fuzzing.
- **≥2 seconds between requests** to the same host, and stay under your cap.
- Candidates must come from an **observed naming convention**, with the
  reasoning recorded. A bounded, justified list is fine. "Try some words" is not.
- **Discriminate on `Content-Type`, never on status code.** One host in this
  estate returns HTTP 200 with 5518 bytes of HTML for every path that does not
  exist.
- **Establish whether a status code is an oracle before trusting it.** Prove it
  with controls: one plausible path, one certainly-absent path.
- Anything that looks internal is **recorded and left alone**.

The traps are listed in `AGENTS.md` §7 and in
[`docs/09-methodology-and-oracles.md`](docs/09-methodology-and-oracles.md).
Read them; they have each cost time here.

### 3. Write, pin, gate, PR

Raw pass to `findings-log/<date>-<area>/` (append-only, with your request count
and negatives). Synthesised result into the relevant `docs/` page, citing the
log. Pin anything that must not rot as an assertion in `regression/hurl/`. Then:

```bash
./scripts/research-gate.sh
```

Exit 0 or don't open the PR.

---

## Submit a finding

Already have it? Skip the session and go straight to the evidence.

1. **Check it isn't already recorded.** Grep `docs/` and `findings-log/`. A
   re-derivation is welcome if you say so and add what changed.
2. **Label the evidence honestly.** OBSERVED = saw it live. PUBLISHED = it's in a
   vendor document served without a login. INFERRED = reasoned, assumptions shown.
3. **Never write a credential, internal hostname, machine path, or live session
   value into the diff** — even to describe one. Describe it without the value.
4. Raw pass → `findings-log/`. Synthesised → `docs/`, citing the log. Pin it if
   it's a value someone will rely on.
5. Gate, then PR using the template.

If you can't classify something as OBSERVED, it is INFERRED. If you can't point
at the line a claim came from, delete the claim.

---

## What the gate checks

`./scripts/research-gate.sh` — and the identical script runs in CI, so a red gate
blocks the merge regardless.

| Check | Catches |
|---|---|
| credential material | the vendor key, reports-broker key fragments, reCAPTCHA keys, long base64 |
| internal hostnames | Grafana / K8s / GitLab / DB / Prometheus hosts, `.corp` hosts |
| machine paths | absolute home-directory paths and Windows user profiles |
| live session values | `jsessionid_*`, `sessionData` JWS/JWE from archive captures |
| citation integrity | any `[source: …]` path that does not resolve |
| assertion suite | re-runs `regression/hurl/` — a failed assertion means the vendor surface moved |

It deliberately does **not** check whether a claim is true. That needs a human or
a second pass. The gate stops the irreversible mistakes; the review catches the
subtle ones.

Flags it needs help with:

```bash
brew install hurl jq     # macOS
apt-get install curl jq  # Debian/Ubuntu
```

---

## House rules worth knowing before you start

- **Never publish a credential.** Record *that* one exists and *where*, never the
  value. Full list in `AGENTS.md` §7.
- **Never delete a retraction.** Corrections are kept visible with the correction
  attached. That history is the evidence — several claims here are only
  trustworthy because we can see what they used to say.
- **If a finding is better held back for a disclosure decision, say so** and say
  why, rather than publishing it and hoping. One finding in this repo is
  deliberately unpublished for exactly that reason.
- **Diagrams are Mermaid**, GitHub renders it natively, and **every branch must
  be labelled** — an unlabelled branch is an INFERRED claim in disguise.