# The `registration_endpoint` advertisement has been withdrawn from the Auth0 discovery documents (2026-11-12)

**Evidence class: OBSERVED.** Three unauthenticated `GET`s, one per reachable
tenant, plus a re-count of the union field set.

**Requests issued by this pass: 3 of a 60 cap** — the regression suite's standing
per-release probe budget is ~60 requests across nine hosts, and this pass issued
3, all `GET` to `/.well-known/openid-configuration` on three distinct hosts.
**Delay:** ≥2 s between requests, per the sweep's own pacing rule. **Method:**
`GET` only; no `OPTIONS` and no `POST` was sent.

---

## 1. The finding

`regression/hurl/02-sso-oidc.hurl:82` asserts:

```
jsonpath "$.registration_endpoint" == "https://carelink-login-trials.minimed.com/oidc/register"
```

That assertion **failed** when the suite was run on 2026-11-12. The cause is not
a fixture error — the field is gone from the document:

| tenant | `registration_endpoint` | document size |
|---|---|---|
| `carelink-login.minimed.eu` | **ABSENT** | 29 keys |
| `carelink-login.minimed.com` | **ABSENT** | 29 keys |
| `carelink-login-trials.minimed.com` | **ABSENT** | 29 keys |

**The union field count is now 29, not 30.** The missing field is exactly
`registration_endpoint`. Every other field the area-H/area-I work enumerated is
still present.

## 2. What this supersedes

`docs/02-auth-tenants-and-flows.md:98` states:

> **OBSERVED:** `registration_endpoint` is advertised by **all five** tenants and
> **returns 404 to `GET` on all five**

That was true on 2026-10-12. It is **no longer true**: the field is advertised by
none of the three tenants this pass could reach. The five-tenant inventory was
`carelink-login{,-trials,-us,-ap}.minimed.{com,eu}`-shaped; the two regional
hosts (`-us`, `-ap`) were unreachable from here (`UNREACHABLE`, not `ABSENT` — a
DNS/connect failure is a failure, not an absence, so the count is stated as
**three of three reachable**, not "all five").

`docs/02` also carries a correction at :66–69 about `registration_endpoint`
differing only by hostname. That correction is still historically accurate for
the period it describes; what has changed is that the field no longer exists to
differ by hostname.

## 3. Why it does not block the bridge release

`carelink-bridge` **does not reference `registration_endpoint` anywhere** —
verified by grep over `src/` and `test/`. The bridge's login path reads
`authorization_endpoint`, `token_endpoint` and `jwks_uri`, all still present and
unchanged.

So this is vendor drift that affects the **research repo's pinned assertion**,
not the consumer's behaviour. That distinction is the reason the bridge can
still be released while this is recorded rather than fixed first.

## 4. What was changed

- `regression/hurl/02-sso-oidc.hurl:82` — the assertion is replaced with one
  that pins the **absence**, which is the current observable truth and will fail
  loudly if Medtronic re-advertises the endpoint:

  ```
  # 2026-11-12: Medtronic withdrew this advertisement. It was present on all five
  # tenants on 2026-10-12 (docs/02 §3) and absent on all three reachable tenants
  # by 2026-11-12. Pinning the ABSENCE so a re-advertisement also goes red.
  jsonpath "$.registration_endpoint" not exists
  ```

- `docs/02-auth-tenants-and-flows.md` — a dated Correction is added beside the
  original claim rather than replacing it, per this repo's append-only rule for
  claims that were true when made.

## 5. Not claimed

- That the endpoint was *removed* deliberately, or on any particular date. Only
  that it was present 2026-10-12 and absent 2026-11-12.
- That `/oidc/register` itself stopped resolving. Only the **advertisement** was
  checked. `/oidc/register` returned 404 on `GET` when it was advertised, so an
  unadvertised 404 is not a new behaviour and was not re-probed.
- Anything about the two unreachable regional tenants.

## 6. The general lesson

A pinned assertion that pins a **vendor advertisement** inherits the vendor's
right to withdraw it. The suite's own header already says a JWKS key rotation is
"expected drift, not a defect"; endpoint advertisements belong in the same
category and the assertion should have been written to tolerate withdrawal from
the start — or, as here, to pin the current state and go red on change in either
direction.

The catch worth recording: the failure surfaced as `error: Assert failure` with
the actual value `none`, which reads like a parse problem. The suite's summary
line counted the file as failed but printed **"85 passed, 0 failed"** for the
per-assertion tally, so the headline numbers contradicted each other. Trust the
suite-level line, not the assertion tally, when they disagree.
