# Security

This repo holds a **map of Medtronic's public CareLink surface**. It contains no
credentials, no patient data, and no working client — but research like this
occasionally turns up an exposure that belongs in Medtronic's hands, and you
should not have to decide alone whether something is one.

## Report an exposure you found

Use GitHub's [private vulnerability reporting][pvr] on this repo.

**Describe it redacted. Never paste the value.** Not in the issue, not in a
comment, not in a commit — not even a truncated or base64'd one. Say *what kind*
of secret it is, where you saw it (host, bundle path, document), how long it has
been there, and what it would grant. The maintainer with access can re-fetch and
verify; you don't need to hand over the payload to point at it.

This repo's own rules are stricter than that: a published credential, an internal
hostname, or a machine path is a **scrub gate failure** (see `AGENTS.md`), so a
report that includes one is also a repo bug worth telling us about.

[pvr]: https://github.com/NovaLux12/carelink-api-research/security/advisories/new

## What does *not* belong here

- **A vulnerability in client code.** The public client is
  [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge); report
  it through its [private advisory channel][adv], not this repo.
- **A login, upload, or crash failure.** That is a client bug, not a vendor
  exposure — use its [bug form](https://github.com/NovaLux12/carelink-bridge/issues/new?template=bug.yml).
- **A route that requires authentication.** Not a finding unless you got in without
  one; if a token is needed, it belongs in the open-questions map as a blocker.

[adv]: https://github.com/NovaLux12/carelink-bridge/security/advisories/new

## Disclosure posture

Medtronic has no published security contact this repo knows of, and no
`security.txt` on the surface (recorded as finding F10 in
[`docs/08-security-findings.md`](./docs/08-security-findings.md)). Some findings
here are held back rather than published immediately — the repo labels each one
OBSERVED / PUBLISHED / INFERRED, and an INFERRED exposure is a question, not a
disclosure. If a finding is deliberately held, that decision is the maintainer's,
and `docs/08` says which.

## Scope reminder

All probing here is **unauthenticated and read-only**. Never use a real patient
account for research without the account owner's explicit involvement, never
brute-force, never mutate. That is not just taste — it is
[`AGENTS.md`](./AGENTS.md) §1 and the gate enforces it.