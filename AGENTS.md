# AGENTS.md — how to contribute research here

This repo is a **research artefact**, not a codebase. Contributions are findings,
corrections, and diagrams — not features. Read this before your first PR.

If you are an AI agent: this file is your operating instruction. The rules below
are load-bearing, not suggestions.

---

## 1. The one rule that outranks everything else

> [!IMPORTANT]
> **Every factual statement must be traceable to a source file.** If you cannot
> point at the line it came from, **delete the sentence** — do not soften it, do
> not hedge it, delete it.

This repo already contains a correction to a false claim made *in good faith*
about source maps. A grep that hits is not a grep that proves what you said it
proved. See [§6](#6-the-four-ways-this-project-has-been-wrong).

---

## 2. Evidence classes — label every claim

| Label | Means | Test |
|---|---|---|
| **OBSERVED** | Seen in a live response | You can paste the response head |
| **PUBLISHED** | In a vendor document served without a login | You can paste the document fetch |
| **INFERRED** | Reasoned, not seen | You can show the reasoning **and** its assumptions |

**Never let INFERRED read as OBSERVED.** The single most valuable thing in this
repo is that Jeff — or anyone — can tell *which claims are still guesses*. That
property is destroyed by one unlabelled inference.

Where sources disagree, **give both**. Never pick one silently.

---

## 3. Where findings go

```
findings-log/<date-pass>/          append-only, dated, verbatim
docs/                              canonical, synthesised, cites the log
regression/hurl/                   the pinned assertion suite
```

- **New raw finding** → append a dated doc to `findings-log/`. Do not edit an
  existing dated doc — add a new one, or a `## Correction (YYYY-MM-DD)` section
  inside it. Append-only is deliberate: the retraction history *is* evidence.
- **A claim that changes what `docs/` says** → update `docs/` **and** leave the log
  in place. `docs/` supersedes; it does not erase.
- **A claim that should never silently rot** → add it to
  `regression/hurl/05-public-config.check.sh` as a `check`. See §5.

---

## 4. Structured issue logging

Use the issue forms. They exist because a finding logged without an evidence class
and a source cite is unusable.

If you are an agent opening an issue, the form data maps to flags:

```bash
gh issue create --repo <owner>/carelink-api-research \
  --title "finding: <one line>" \
  --label finding,needs-verification \
  --template 01-new-finding
```

**Issue rules:**

- **One finding per issue.** Two findings in one issue is how one of them gets
  dropped.
- **Title format:** `finding: <subject>` · `correction: <subject>` ·
  `question: <subject>` · `security: <subject>`.
- **Never put a credential, a real patient identifier, or an unredacted internal
  hostname in an issue body.** Redact to `<service>.<internal>` or
  `<REDACTED>` and state that it exists.
- **If the finding is from a live authenticated response**, say so explicitly, and
  confirm the response was yours to see.

---

## 5. PR requirements

A PR is mergeable when **all** of these hold:

- [ ] Every claim has an evidence label and a source cite
- [ ] No credential, session value, or internal hostname appears anywhere in the diff
      (`grep` for them — see §7)
- [ ] Corrections and retractions in the sources are preserved, not smoothed over
- [ ] If the diff changes a claim the regression suite pins, **the suite has been
      updated in the same PR** and still exits 0
- [ ] New diagrams are Mermaid (GitHub renders them natively, no build step)
- [ ] `README.md` and `docs/00-summary-the-map.md` updated if the finding changes
      what a newcomer would need to know first

**Run the gate before pushing:**

```bash
cd regression/hurl && ./run.sh          # exit 0 = no drift
grep -rIE '<forbidden string>' .        # must be zero — see §7
```

---

## 6. The four ways this project has been wrong

Reviewers: check for these. They are the recurring failure modes here, and each
produced a real correction.

1. **A claim stated without evidence.** Nothing to point at. → *Delete the claim.*
2. **A grep that hit without proving.** `grep sourceMappingURL` returned a hit, so
   a note said "no source-map directive exists" — the hit was a `worker-loader`
   string literal. → *A hit proves the token exists, not that it means what you
   assumed.*
3. **A hash comparison over a lookup that silently returned `null`.** Two
   different values hashed to the same digest and looked like agreement. → *Assert
   the resolved type before comparing.*
4. **A verification that only reads back the intended target.** A `gh api` PATCH
   went to the wrong repo, exited 0, and the read-back from the correct repo looked
   like "it didn't apply". → *Verify the target you wrote to, and name both repos
   in the command.*

---

## 7. Traps — each one has already cost time

> [!WARNING]
> `*.carelink.eu`, `*.carelink.com`, `*.clcloud.eu` — **wildcard parking DNS**. A
> random string resolves. ~50 collected names are false positives. Never report one
> as a vendor asset.

> [!CAUTION]
> `carelinkhp.minimed.eu` returns **HTTP 200 + `text/html` (5518 bytes)** for every
> path that does not exist. Discriminate on `Content-Type`, never on status.

> [!NOTE]
> `carelink.minimed.eu` serves **gzip unconditionally**, ignoring `Accept-Encoding`.
> Use `curl --compressed` or every parse fails on `0x8b`.

> [!NOTE]
> `index.commoncrawl.org` is unreachable from some hosts (TLS `unexpected eof`).
> Use the `cluster.idx` bulk path instead.

Scrub list — grep for these and the count must be **zero** in any diff:

```
<VENDOR-API-KEY>          # known-published, redacted on purpose
<VENDOR-API-KEY-placeholder>
grafana.<internal>        k8s.<internal>      gitlab.<internal>
db.<internal>            prometheus.<internal>
*.corp hostnames
/home/<user>              /home/jack
jsessionid_               sessionData
```

**Never publish raw archive captures.** Common Crawl/Wayback records contain live
`jsessionid_*` values and pre-Auth0 authorize URLs whose `sessionData` is a
plaintext-base64 JWS. Facts only, captures never.

---

## 8. Probing discipline

If your contribution adds a probe:

- **GET only.** No POST unless the route is *known* to be POST-only and you are
  documenting that fact. No token exchange, ever.
- **Sleep ≥2s between requests to the same host.** State the request count and the
  cap you set.
- **Bounded, justified candidate lists only** — derived from observed naming
  conventions, with the reasoning recorded. No wordlist fuzzing, no DNS brute
  force.
- **Establish whether the status code is an oracle before trusting it.** On
  `clcloud.*`, the 403 line is uniform and useless; `x-amzn-errortype` is the
  signal. On `carelinkhp.*`, the 200/412/401/404/405 set *is* reliable. Controls
  are mandatory: one plausible path, one certainly-absent path.
- **Hosts that look internal are recorded and left alone.**

---

## 9. Diagrams

Mermaid only — GitHub renders it natively, no build step.

- Use `flowchart TD` for decision logic (why a device fails detection),
  `flowchart TB`/`LR` for topology, `sequenceDiagram` for auth flows.
- Label every branch. An unlabelled branch is an INFERRED claim in disguise.
- Keep a diagram to the one question it answers. If it needs two questions, it
  needs two diagrams.

---

## 10. What good looks like

The bar for "mergeable" is the same as the bar for "publishable": a stranger can
read the page, tell exactly which claims are confirmed and which are guesses, and
re-run your probe from what you wrote down.

If a paragraph doesn't carry information, delete it. This repo has no filler.

---

## 11. What automation may and may not do

Scheduled and CI jobs are guests here. They exist to **notice** drift, never to
**decide** truth, and never to write to the record.

| A scheduled/CI job MAY | A scheduled/CI job MAY NEVER |
|---|---|
| Run `regression/hurl/` exactly as the PR gate runs it — same suites, same runner, same pinned hurl version. Budget: ~62 requests per sweep. | Push to any branch, or open a PR. Merges and pushes are the human's job. The single exception is the badge-counts job below: it writes nothing but one generated JSON to the `counts` branch. |
| Open issues (`correction:`/`finding:` titles per §4), comment on issues, and add or remove the labels `drift`, `automation`, `stale-claim`, `verified`, `needs-verification`, `pinned`. | Edit any file — `docs/`, `README.md`, `findings-log/`, `regression/`, this file. If a claim needs changing, a human PR changes it. |
| Read anything; run any read-only local check (grep, python, the assertion inventory). | POST, authenticate, or exchange a token against any vendor host. The single standing exception is the two POSTs already pinned and documented in `04-deep-surface.hurl` — public client_ids, rejected 403 server-side, asserted as failures. No automation may extend that exception; no third POST may be added. |
| Probe only patterns already in `regression/hurl/`. A new host, path, or candidate list enters a workflow **only** after a human added it to the suite (§8: bounded, justified lists). | Close an issue, or edit an issue's body. A stale claim gets a comment and a `stale-claim` label; the claimant closes it. |
| Generate vendor traffic only by re-running the existing suites. No new targets, ever. | Delete or rewrite anything in `findings-log/`. Append-only is deliberate (§3) — the retraction history *is* the evidence. |
| Publish exactly one generated artefact: `counts.json` on the `counts` branch, written by the drift sweep's badge-counts job after each sweep, from `scripts/measure_assertions.py`. That branch is generated data — never hand-edit it. | Any other push. If a badge, a count, or a page is wrong, the fix is a human PR. |

Every automated issue and comment carries the `automation` label so bot output
filters to one click. An automated issue that fails a scrub check (§7) is
dropped unsent — the sweep would rather stay silent than leak.

Rationale: the gate stops the irreversible mistakes and review catches the
subtle ones (`CONTRIBUTING-research.md` §What the gate checks). Automation
extends the first half of that sentence to the calendar — drift, silence, and
rot are noticed weekly instead of never — and leaves the second half exactly
where it is.
