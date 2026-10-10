# Run a research session

**Copy everything below this line into any agent** — Claude Code, opencode,
Copilot Chat, Cursor, or the GitHub prompts panel. It is written to be pasted
verbatim.

---

> I want to run a **read-only research session** on the Medtronic CareLink API
> surface, then submit what I find as a pull request to this repo.
>
> **First, read these three files. Do not skip them.**
>
> 1. `AGENTS.md` — the operating rules: evidence classes, the never-publish list,
>    the traps, and the four ways this project has been wrong.
> 2. `docs/00-summary-the-map.md` — the map, so you do not re-derive what is
>    already known.
> 3. `docs/11-suggested-research-areas.md` — the open areas.
>
> Then follow this sequence exactly.
>
> **1. Claim an area.** Pick **one** area from `docs/11-suggested-research-areas.md`.
> Before probing anything, state which area and why it is the highest-value one
> you can do, the exact request cap you will not exceed, the delay you'll hold
> between requests to the same host, and what "closed" means — **including
> whether a negative result counts**. Claim it as an issue first, so two people
> don't duplicate the work.
>
> **2. Probe.** These are not negotiable:
> - **GET only.** No POST, no token exchange, no authentication, no port
>   scanning, no DNS brute force, no wordlist fuzzing.
> - **≥2 seconds between requests to the same host.** Stay under your cap.
> - Candidates must be **derived from an observed naming convention**, with the
>   reasoning recorded. A bounded, justified list is fine. "Try some words" is not.
> - **Discriminate on `Content-Type`, never on status code.** `carelinkhp.minimed.eu`
>   returns HTTP 200 with 5518 bytes of HTML for every path that does not exist.
> - **`carelink.minimed.eu` serves gzip unconditionally**, ignoring
>   `Accept-Encoding`. Use `curl --compressed`.
> - **`*.carelink.eu`, `*.carelink.com`, `*.clcloud.eu` are wildcard DNS on a
>   parking operator.** A random string resolves there. Never report a name from
>   those spaces as a vendor asset.
> - **Establish whether the status code is an oracle before trusting it.** On
>   `clcloud.*` the 403 line is uniform and useless; `x-amzn-errortype` is the
>   signal. Prove it with controls — one plausible path, one certainly-absent path.
> - Anything that looks internal is **recorded and left alone.**
>
> **3. Write it up.** Every claim gets an evidence label and a source cite:
> **OBSERVED** (saw it live) / **PUBLISHED** (in a vendor document served without
> a login) / **INFERRED** (reasoned — show the reasoning *and* its assumptions).
> An INFERRED claim that reads as OBSERVED is the worst thing you can do here.
> Raw pass goes in `findings-log/<date>-<area>/`; the synthesised result goes in
> the relevant `docs/` page citing the log. **A negative result is a first-class
> contribution.**
>
> **4. Pin anything that must not rot.** If your finding is a value someone will
> later rely on, add an assertion to `regression/hurl/`. Unpinned claims have
> gone stale here repeatedly.
>
> **5. Gate it.**
> ```bash
> ./scripts/research-gate.sh
> ```
> **Do not open a PR until this exits 0.** It scans the diff for credentials and
> internal hostnames, validates every citation path, and re-runs the vendor
> suite. If it fails, fix it — do not bypass it. CI runs the identical script, so
> a red gate blocks the merge anyway.
>
> **6. Open the PR** using the template. Fill the evidence table honestly,
> including the request count. If your finding corrects something already
> published, say so plainly and keep the original claim visible with the
> correction attached — **never delete a retraction**. That history is the
> evidence.
>
> **Remember:** a wrong claim here misleads someone building a medical-data
> integration. If you are not sure whether something is OBSERVED or INFERRED, it
> is INFERRED. If you cannot point at the line a claim came from, delete the
> claim.

---

## Where things live

| You want to | Go to |
|---|---|
| See what is already known | [`docs/00-summary-the-map.md`](00-summary-the-map.md) |
| Pick something to work on | [`docs/11-suggested-research-areas.md`](11-suggested-research-areas.md) |
| Read the rules before probing | [`AGENTS.md`](../AGENTS.md) §7, and [`docs/09-methodology-and-oracles.md`](09-methodology-and-oracles.md) |
| Learn the oracles and traps | [`docs/09-methodology-and-oracles.md`](09-methodology-and-oracles.md) |
| Claim an area | the *Claim a research area* issue form |
| Submit an existing finding | [`CONTRIBUTING-research.md`](../CONTRIBUTING-research.md) |

The same brief is available as a copy-paste prompt in GitHub's **prompts panel**
on any issue or PR comment: *research-area*.