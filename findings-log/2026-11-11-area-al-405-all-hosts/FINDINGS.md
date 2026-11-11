# Area AL — is the `/hcp/configuration/` 405 a handler-level constant on every host that mounts it?

**Claim:** NovaLux12/carelink-api-research#194
**Date:** 2026-11-11
**Cap:** **0 of a 0 cap — no request was made**
**Delay:** the standing rule for this repo is ≥ 2 s between requests to the same host; no request was issued, so no spacing applies and none is claimed.
**Result:** **Positive, on all four hosts, at zero requests — the evidence already existed.**

---

## The answer

**The 405 is a handler-level constant on all four clinic hosts, not a per-deployment property.**

| host | `/hcp/configuration/<absent>` | `/hcp/<absent>` | `server` |
|---|---|---|---|
| `carelink.medtronic.com` | **405**, 0 B, `Allow: POST, OPTIONS` | 404, 0 B | `Apache/2.4.62` |
| `carelink.medtronic.eu` | **405**, 0 B, `Allow: POST, OPTIONS` | 404, 0 B | `Apache/2.4.62` |
| `carelink-support.medtronic.com` | **405**, 0 B, `Allow: POST, OPTIONS` | 404, 0 B | `Apache/2.4.62` |
| **`carelinkhp.minimed.eu`** | **405**, 0 B, `Allow: POST, OPTIONS` | 404, 0 B | `Apache/2.4.62` |

**4 of 4.** Identical status, identical byte count, identical `Allow` value, identical `Server` string. Not one deployment deviates.

## Why this cost nothing, and why that is the finding

AL was minted by area AG, which had measured the boundary on **two** hosts and could not afford `carelink-support`'s root and `/hcp/` cells or `carelinkhp` at all. AL's stated blocker was **scope discipline**, not requests: `carelinkhp` is the recorded baseline and `AGENTS.md` §10 is titled "Do not re-run".

**Area AK then measured all four hosts anyway** — for a different question (the 5518 B fallback's extent), and its matrix happened to include the exact cell AL needed: `/hcp/configuration/<absent>` on `carelinkhp.minimed.eu`.

So the answer to AL was already committed before AL was claimed. `findings-log/2026-11-10-area-ak-portal-spa-fallback/results.jsonl` **seq 19**:

```
host          carelinkhp.minimed.eu
path          /hcp/configuration/zz-ak-absent-4713
http_status   405
body_bytes    0
content_type  (none)
allow         POST, OPTIONS
server        Apache/2.4.62 (Red Hat Enterprise Linux) OpenSSL/3.5.5
```

**This is finish-first work done properly**: before spending a request, ask what the committed tree already determines. The alternative — re-probing four hosts to re-derive a committed result — would have cost 8 requests and produced the same table.

## The evidence, restated from AK's ledger

Every cell below is copied from `findings-log/2026-11-10-area-ak-portal-spa-fallback/results.jsonl`, not re-measured:

| host | seq | path | status | bytes | `allow` |
|---|---|---|---|---|---|
| `carelink.medtronic.com` | 3 | `/hcp/zz-ak-absent-4713` | 404 | 0 | — |
| `carelink.medtronic.com` | 4 | `/hcp/configuration/zz-ak-absent-4713` | **405** | 0 | `POST, OPTIONS` |
| `carelink.medtronic.eu` | 8 | `/hcp/zz-ak-absent-4713` | 404 | 0 | — |
| `carelink.medtronic.eu` | 9 | `/hcp/configuration/zz-ak-absent-4713` | **405** | 0 | `POST, OPTIONS` |
| `carelink-support.medtronic.com` | 13 | `/hcp/zz-ak-absent-4713` | 404 | 0 | — |
| `carelink-support.medtronic.com` | 14 | `/hcp/configuration/zz-ak-absent-4713` | **405** | 0 | `POST, OPTIONS` |
| **`carelinkhp.minimed.eu`** | 18 | `/hcp/zz-ak-absent-4713` | 404 | 0 | — |
| **`carelinkhp.minimed.eu`** | 19 | `/hcp/configuration/zz-ak-absent-4713` | **405** | 0 | `POST, OPTIONS` |

The absent name is `zz-ak-absent-4713`, verified at **0 `git grep` hits** across the whole repository at base `e71b1a9` — so it is a name this surface has never seen, and the 405 cannot be a route answering.

## What this settles

Area AG's own INFERRED assumption was that `Allow` comes from a route's registered methods, and AG **refuted** that by finding the absent path answers the same 405 + `Allow` as a real POST-only route. AL's job was to ask whether that refutation is a property of the handler or of two deployments' configuration.

**It is the handler.** A constant that reproduces identically on four deployments, across two different build generations, is not per-deployment configuration. (OBSERVED for the reproduction; **INFERRED** for the handler-vs-configuration reading — the mechanism itself was never observed, only its invariance.)

## The reading it supports, and the one it does not

**Supported:** on this family, `405 + Allow` under `/hcp/configuration/` carries **no information about a route's existence**. It is emitted for a path that cannot exist. Any pass that reads a 405 there as "route present, wrong method" is reading a subtree constant.

**Not supported:** that `Allow: POST, OPTIONS` is wrong about the *real* routes. It happens to agree with `/hcp/configuration/application` — the header is not false, it is just not discriminating. Area AB's six-route verdicts are unaffected.

## What this does not establish

- **Nothing about `hcp/patients/`.** Whether the constant extends beyond `/hcp/configuration/` is area **AQ**'s question, claimed in this run.
- **Nothing about the mechanism.** AL shows the constant is invariant across four hosts; it does not show *why*. Area **AN** is the mechanism question.
- **Not a disclosure.** Every cell is an unauthenticated GET to a path that does not exist, on a public host.

## Successor

**AR** — does the `/hcp/configuration/` 405 constant extend to sibling subtrees under `/hcp/`, and is `Allow`'s *value* also constant across them? AQ tests `hcp/patients/`; AR would test a third subtree and would say whether the constant is a property of `/hcp/` as a whole. Blocked on: needing a third subtree whose route literals are recorded, which AQ may supply.

## Request accounting

**0 of a 0 cap.** No request was issued and none was needed — the answer was in `findings-log/2026-11-10-area-ak-portal-spa-fallback/results.jsonl` at four rows. Zero vendor traffic, zero spacing question, zero failures.

This is the second area in two runs to close at zero requests by reading a committed ledger instead of re-deriving it.
