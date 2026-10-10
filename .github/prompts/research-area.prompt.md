---
mode: agent
description: Run a bounded read-only research session and submit findings as a PR
---

I want to run a **read-only research session** on the Medtronic CareLink API surface, then submit what I find as a pull request to this repo.

**First, read these three files. Do not skip them.**

1. `AGENTS.md` — the operating rules. Evidence classes, the never-publish list, the traps, and the four ways this project has been wrong.
2. `docs/00-summary-the-map.md` — the map, so you do not re-derive what is already known.
3. `docs/11-suggested-research-areas.md` — the open areas.

Then follow this sequence exactly.

---

### 1. Claim an area

Pick **one** area from `docs/11-suggested-research-areas.md`. Before you probe anything, state:

- which area, and why it's the highest-value one you can do
- the exact request cap you will not exceed, and the delay you'll hold between requests to the same host
- what "closed" means for this area — **including whether a negative result counts**

Claim it as an issue before starting, so two people don't duplicate the work. Use the *Claim a research area* form.

### 2. Probe — hard rules that are not negotiable

- **GET only.** No POST, no token exchange, no authentication, no port scanning, no DNS brute force, no wordlist fuzzing.
- **≥2 seconds between requests to the same host.** Stay under your stated cap.
- Candidates must be **derived from an observed naming convention**, with the reasoning recorded. A bounded, justified list is fine. "Try some words" is not.
- **Discriminate on `Content-Type`, never on status code.** `carelinkhp.minimed.eu` returns HTTP 200 with 5518 bytes of HTML for every path that does not exist.
- **`carelink.minimed.eu` serves gzip unconditionally**, ignoring `Accept-Encoding`. Use `curl --compressed`.
- **`*.carelink.eu`, `*.carelink.com`, `*.clcloud.eu` are wildcard DNS on a parking operator.** A random string resolves there. Never report a name from those spaces as a vendor asset.
- **Establish whether the status code is an oracle before trusting it.** On `clcloud.*` the 403 line is uniform and useless; `x-amzn-errortype` is the signal. Prove it with controls — one plausible path, one certainly-absent path.
- Anything that looks internal is **recorded and left alone**.

### 3. Write it up

**Every claim gets an evidence label and a source cite.** This is the rule this repo enforces hardest:

- **OBSERVED** — you saw it in a live response
- **PUBLISHED** — it's in a vendor document served without a login
- **INFERRED** — you reasoned it; show the reasoning *and* its assumptions

An INFERRED claim that reads as OBSERVED is the worst thing you can do here.

Put the raw pass in `findings-log/<date>-<area>/`. Put the synthesised result in the relevant `docs/` page, citing the log. **A negative result is a first-class contribution** — issue #84 was closed by proving something doesn't exist across 73 paths and four corpora.

### 4. Pin anything that must not rot

If your finding is a specific value someone will later rely on, add an assertion to `regression/hurl/`. A claim that isn't pinned will quietly go stale; that has happened here.

### 5. Gate it

```bash
./scripts/research-gate.sh
```

**Do not open a PR until this exits 0.** It scans the diff for credentials and internal hostnames, validates every citation path, and re-runs the vendor suite. If it fails, fix it — do not bypass it. A PR that fails the gate cannot merge anyway, because CI runs the same script.

### 6. Open the PR

Use the PR template. Fill in the evidence table honestly, including the request count. If your finding corrects something already published, say so plainly and keep the original claim visible with the correction attached — **never delete a retraction**. That history is the evidence.

---

**Remember:** a wrong claim here misleads someone building a medical-data integration. If you are not sure whether something is OBSERVED or INFERRED, it is INFERRED. If you cannot point at the line a claim came from, delete the claim.