# Security policy

This repo maps a live vendor surface read-only and unauthenticated. Most
findings are safe to file publicly. Some are not — and those must **never**
go through a public issue first.

## Report privately when the finding is any of

- a credential, key, token, or session value that is **not already published**
  by the vendor (a live secret, not the known-published bundle key the repo
  already redacts);
- an internal hostname, endpoint, or infrastructure detail that is reachable
  and non-public;
- a data path that exposes patient or clinician data beyond what the repo
  already documents as unauthenticated;
- anything you would not want indexed by a search engine tomorrow.

When in doubt, report privately. A private report that turns out to be safe
for public filing costs one email. A public filing that turns out to be
sensitive cannot be un-published.

## How to report

Email the maintainer privately (see the repo owner's profile for contact).
Include:

- **what** is exposed, and **by what** endpoint or artefact — no values;
- the impact: what becomes possible, and whose data is in scope;
- how you obtained it (must be read-only and unauthenticated — see
  `AGENTS.md` §8; anything else is out of scope for this repo).

**Do not** paste the credential, key, token, session value, or a
ready-to-run reproduction. A redacted finding is a complete finding
(`.github/ISSUE_TEMPLATE/04-security.yml` states the same rule for the
public form).

## What happens next

- The maintainer confirms receipt, assesses impact, and decides: file a
  redacted public issue, hold for a disclosure decision (`CONTRIBUTING-research.md`
  §House rules — one finding in this repo is deliberately unpublished), or
  notify the vendor.
- Do not open a public issue, PR, or discussion about the finding until the
  maintainer says so.

## Scope

- **In scope:** this repo's own content and workflows (leaked secrets in
  `findings-log/`, overly specific error output in drift issues, overly
  broad probes committed to `regression/hurl/`).
- **Out of scope:** Medtronic's production systems beyond read-only
  unauthenticated observation. No POST beyond the two pinned and documented
  in `04-deep-surface.hurl`, no authentication, no token exchange, no
  internal hosts — `AGENTS.md` §§8, 11.

## Client vulnerabilities do not belong here

A vulnerability in a CareLink **client** is not a finding about Medtronic's API.
The public client is
[NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge); report
code vulnerabilities there through its
[private advisory channel](https://github.com/NovaLux12/carelink-bridge/security/advisories/new),
not here. Login, upload, or crash failures with an unchanged vendor surface are a
plain bug — its [bug form](https://github.com/NovaLux12/carelink-bridge/issues/new?template=bug.yml).

What *is* in scope here is anything above: a credential, an internal hostname, or an
exposure in a vendor artefact, reported redacted.
