## What this PR does

**Research area I — Auth0 tenant behavioural differences.** Negative on the difference the area hunted (five tenants, byte-identical discovery documents), positive on one it did not name (`x-ratelimit-limit` splits `.eu` from the rest), and two corrections to `kid` strings already published. Closes #23.

The area asked for **behaviour**, not just the policy surface. Re-derived the tenant set from the corpus first: the estate is **five** `carelink-login.*` tenants, and "three" (`AUTH-TENANT` §1, a policy axis) against "four" (`docs/11`/`docs/10`, a key-material axis) were two different sets over those same five hosts. Neither number was an error. Their union exposed the real gap — **`carelink-login.minimed.com` was in nobody's policy comparison, and `-trials` was in nobody's key set.**

## Evidence

| Claim | Class | Source |
|---|---|---|
| The five discovery documents are **byte-identical** once the tenant hostname is substituted out — one digest `sha256:0c0db635f5e9b08b…`, 2640 B, 5 of 5 | OBSERVED | `findings-log/2026-10-12-area-i-auth0-tenant-behaviour/FINDINGS.md` §2; ledger seq 2, 5, 8, 11, 15; `verdict.txt` §B0 |
| 30 field names, **0 absent from any document**; exactly 12 of 30 differ raw and all 12 are URLs containing that tenant's hostname | OBSERVED | same file §2; `verdict.txt` §B, §C |
| **`registration_endpoint` is not a separate difference** — it differs only by hostname, like the other 11. Corrects `AUTH-TENANT` §1 / `docs/02` §1 | OBSERVED | same file §2 |
| `x-ratelimit-limit` is **500 on both `.eu` tenants, 100 on the other three** — 10 observations, 2 per tenant, constant within a tenant, invisible in byte-identical documents | OBSERVED | same file §3; ledger seq 2/3/5/6/8/9/11/12/15/16 |
| That 500/100 is *tenant configuration* rather than a negotiated tier | **INFERRED** | same file §3 — labelled, with the assumption stated; nothing a client does depends on it |
| `registration_endpoint` is advertised by all five tenants and **absent on all five** — `/oidc/register` → 404 `application/json`, 60 B, one digest `f006bbd60894…` across five hosts | OBSERVED | same file §3; `verdict.txt` §D |
| Trials tenant publishes 2 RSA/RS256 keys; **10 keys across 5 tenants, 0 shared** — discharges `docs/02` §9's "Unknown" | OBSERVED | same file §5; `jwks-keys.json` |
| `AUTH-TENANT` §8's `medtronic.com` kid (`…_lLOJ`) is **wrong**; live is `…_lOOJ`, matching `RECON-SUBDOMAINS` §4.1. **Resolves `docs/02` §8's unresolved disagreement against the spelling `docs/02` recommended** | OBSERVED | same file §6 |
| `minimed.com`'s second kid is the live string **minus one `Q`** — a *deletion*, so no second reading existed to compare and `docs/02` §8's method could not have found it | OBSERVED | same file §6; `corpus-audit.txt` §E |
| On `carelink-login.*` a `404` is **two different things**: `x-auth0-not-found: 1` + `text/plain` 10 B (path unknown) vs `application/json` 60 B (routed, nothing to return) | OBSERVED | same file §4; `docs/09` §Oracle C |
| That those two signatures mean different *routing states* | **INFERRED** | same file §4; `docs/09` §Oracle C — the separation is observed, the meaning is not |
| All 10 observed `kid`s are 21 chars | OBSERVED | `verdict.txt` §A — corroborating for the two transcription defects, **not** the proof; the live fetch is |
| A POST to `/oauth/token` to test the `device_code` grant on the trials client | **NOT ATTEMPTED** — area J's subject; out of scope by the claim issue's hard limit | same file §9 |

### Controls, and what each proved

| # | seq | Request | Result | Proved |
|---|---|---|---|---|
| C1 | 1 | `…trials…/.well-known/openid-configurationx` | `404 text/plain` 10 B, `x-auth0-not-found: 1` | A missing well-known doc on this family is a **404**, not a 200 fallback page. **The oracle held** — without it, "field absent" and "fallback document" are indistinguishable. Sent first, before any candidate on the host. |
| C2 | 2 | `…trials…/.well-known/openid-configuration` | `200 application/json` 2825 B | The live counterpart on the same host: C1's 404 is a property of the *path*, not the host. |
| C3 | 14 | `…medtronic.com/.well-known/openid-configurationx` | `404 text/plain` 10 B, **same digest as C1** | The absent-signature is not host-specific — and one host's 404 says nothing about the next host's front door, which is why it cost a second request. |

**No stop condition fired.** Both absent-path controls returned 404.

## Requests used

- [x] **GET only** — no POST, no `-X` override, no `-d`, no token exchange, no authentication, no port scan, no DNS brute force
- [x] Slept ≥2s between requests to the same host — declared **2.5 s**, `sleep` inside the per-host `flock`. **Measured floor 2.000 s, and this ledger's timestamps are 1-second resolution so it cannot resolve the declared 2.5 s** — a lower bound, not a measurement, recorded rather than rounded away (`docs/09` §4 gains a trap row for this; 4th pass in a row)
- [x] Stated cap respected: **19 of a 20 cap** (17 `curl` + 2 `hurl` pin-validation, both exit 0)

**Not run, deliberately:** the full `02-sso-oidc.hurl` suite. I validated the **two new pin cells** live through a different client (`hurl`); re-running the file's ~10 pre-existing cells would have breached the committed cap. Those cells are unchanged and are covered by the weekly drift sweep.

## The rules

- [x] No credential, session value, or patient identifier anywhere in the diff. The surface carries client IDs and JWKS material: `kid`s are published by the vendor at an unauthenticated URI and are recorded; the RSA moduli and `x5c` chains are **not committed** (`bodies/` is gitignored, `jwks-keys.json` carries `kid`/`kty`/`alg`/`use` only, with the reason in the file). One Auth0 custom-domain hostname appears in those chains and stays out of this repo's history.
- [x] Any internal hostname redacted to `<service>.<internal>`
- [x] Corrections and retractions preserved, not smoothed over — `docs/02` §8 keeps its original recommendation with the correction attached, and `docs/00`'s dated 2026-10-11 record was **left saying "four tenants"** with an addendum rather than rewritten to "five"
- [x] Claims the regression suite pins updated in this PR; `./scripts/research-gate.sh` exits 0

**Assertion counts**, re-measured with the one counting rule (`scripts/measure_assertions.py`): **167 → 184 static, 359 → 380 execute per run**. All four static sites and both runtime sites updated, then **re-grepped by hand** — including `README.md:386`, the site the gate's regex cannot see because it is wrapped across a line break inside a bold span (`docs/09` §4).

**Open areas** 18 → 17: `docs/11` updated and `.github/ISSUE_TEMPLATE/config.yml` agrees (the gate checks both).

## Gate

```bash
./scripts/research-gate.sh        # must exit 0 — CI runs the same script
```

```
research-gate.sh exit: 0
```

Run under the pool gate lock (`flock -w 1800 .loop/gate.lock`), write phase only.

## If this changes what a newcomer needs to know first

- [x] `README.md` updated — "Four auth tenants, four completely disjoint signing keys" → five tenants / ten keys, with the byte-identical-document fact
- [x] `docs/00-summary-the-map.md` updated — tenant count, plus the dated-record addendum

## Downstream consumer impact

- [ ] No pinned consumer value affected
- [x] A pinned value moved — **the trials tenant is new to the regression suite** and two `kid` strings in `docs/02` were wrong. The bridge's `drift:check` now runs two additional pin cells against `carelink-login-trials.minimed.com`; a **key rotation there will turn the suite red, and that is expected drift to re-record, not a bridge outage**. `docs/02` §1's table (which the bridge reads for issuer/client configuration) changed on three rows. This is additive and affects no client constant — `login.ts` behaviour is unchanged, because §1's "no separate clinical auth handling" conclusion **survives** and is now confirmed at five tenants. Filing as `downstream-bridge` for visibility rather than because a release is blocked.

## Priorities

**Successor added as a dated addendum to open area J** (`docs/11`), with a mirrored row in `docs/10` §1 — not a new letter, since every A–Z is in use and a two-letter heading is invisible to the gate's area checks.

**J addendum — sweep the three remaining advertised-but-absent Auth0 endpoints across all five tenants** (`/bc-authorize`, `/mfa/challenge`, `/oauth/global-token-revocation/connection/*`). *Blocker:* none — GET only, bounded list (3 paths × 5 tenants, every one named inside a discovery document this project already holds). *Closes when:* each has a verdict on all five tenants, controls first per host; **a negative closes it**. *Why it's derived from what this pass saw:* `registration_endpoint` was advertised by all five and absent on all five, its siblings were recorded on the EU tenant only, `/mfa/challenge` has no probe result in any source, and §4 established the oracle (`Content-Type` + `x-auth0-not-found`) that makes the sweep unambiguous and cheap. A client coding against an advertised endpoint that 404s produces a failure mode area J's `login-errors.ts` classification does not enumerate.

The claim issue had proposed the issuer-count leg of `docs/10` §1 instead. That leg is **now discharged inside this PR** rather than left as a successor: the inventory it needed is complete for probeable hosts at five, and all seven archive-only hosts are dev/stage/test by name, which policy enumerates and never probes. `docs/10` still records `COMMONCRAWL` §4e's self-disagreement (prose says 12, its own list says 7) because **that arithmetic is not mine to resolve** — both readings remain given.

---

<details>
<summary>Diagrams checklist</summary>

- [x] Mermaid only (GitHub renders it natively)
- [x] Every branch is labelled — an unlabelled branch is an INFERRED claim in disguise. `docs/02` §1's diagram now has a single labelled sink instead of the old unlabelled dashed "never fetched" edge that the trials tenant used to dead-end into
- [x] One diagram answers one question

</details>