# Suggested research areas

**Pick something up.** Every area below states what is known, what is missing, and
what would close it. Nothing here is a guess dressed up as a task — each one has a
specific blocker.

Priority is roughly: **cheapest-and-highest-value first**. Token-gated items are
grouped at the end because they need something we don't have.

---

## Already blocked on a token — don't start here

These need an authenticated response on a real account. If you have one, tell us;
everything else on this page moves.

| Area | Blocker |
|---|---|
| `deviceFamily` wire shape | one logged `monitor/data` response |
| NGP alarm-code vocabulary | an authenticated `application` config |
| `relativeOffset` clock semantics | any real payload |
| Report bodies from `commoncore` | a clinician-scoped token |

---

## Tier 1 — no token needed, high value

### A. Is `carelinkhp` really the clinician portal for every region?

`carelinkhp.minimed.eu` and `carelink.medtronic.com` serve byte-identical bundles
of the *clinic* portal. `carelink.medtronic.eu` returns the 5518-byte SPA fallback
— a false positive. But the **`.com` clinic variant beyond `carelink.medtronic.com`
has never been found.**

Worth checking: whether any `carelinkhp*.minimed.com` style host serves a
*different* bundle (a US clinic app rather than a mirrored EU one), and whether
that one contains patient-namespace paths the EU one doesn't.

**Closes when:** you can name the clinic-portal hosts and show which bundle each
serves, by sha256.

### B. The `v12/display/message` endpoint

`v12` is live and was in no prior note. `v6` exists but is POST-only; `v11/v12/v13`
answer GET. We don't know what v12 does that v13 doesn't, or whether any client
uses it.

**Closes when:** a documented comparison of v11/v12/v13 response shapes with the
same account. Blocked on a token for the *body*, but the **routing** picture is
already open — check which cells are reachable, whether v12 has an `OPTIONS` route
where v13 doesn't, and whether the `x-ca-err` code differs between them.

### C. Extend the oracle set to the `pde/v3` and `csr` namespaces

Both were probed at root and returned the router's no-route 403. But "403" on
`clcloud` means *no route*, not *no resource* — and **no `OPTIONS` probe was ever
run**. A resource that exists but only defines POST returns exactly this.

The `carepartner` axis gave us a clean discriminator (`MissingAuthenticationToken`
vs `UnauthorizedException` + `x-ca-err: 990`) and an `OPTIONS` CORS probe found a
POST-only route that a GET-only probe called dead.

**Closes when:** `OPTIONS` + the error-type oracle have been run across
`pde/v3/`, `csr/`, and the bare `connect/carepartner/` family. This is ~30 GETs
and some OPTIONs, all unauthenticated, and it either finds routes nobody knew
existed or closes the space properly.

### D. The 18-country sweep, completed

`/patient/countries/settings` has 35 keys. 18 countries are swept. **109 recorded**
countries exist in the config's own lists. The interesting ones are the ones where
two keys disagree — we already found `bgUnits` vs `glucoseUnitsDefault`
contradicting each other in BE/ES/IT.

**Attack that specifically:** sweep for *internal contradictions* in a single
country response, not for differences between countries. Unit fields
(`bgUnits`, `glucoseUnitsDefault`, `carbohydrateUnitsDefault`), date fields
(`shortDateFormat`, `reportDateFormat`), and the `mfa.status` / report-availability
flags are where an inconsistency would actually mislead a client.

**Closes when:** the sweep is either complete or the contradictions are enumerated.

### E. Config-key archaeology on `/patient/configuration/system/*`

The per-key form is confirmed unauthenticated and returns a 21/21 exact match
against the public document — in a `{"value": "<string>"}` envelope where **booleans
arrive as strings**. But only the non-null keys were probed.

Every `null`-valued key currently 404s. The interesting question: **is there a key
that exists on one deployment but not another**, or a key whose per-key form works
where the bulk document returns nothing? Probe the 69 by deployment and record
which are absent rather than null.

**Closes when:** the per-key form is confirmed/refuted for all 69 keys × 3
deployments.

### F. What the timeline and dialog-lite gateways actually are

Both are AWS API Gateway stage-wide `ANY /{proxy+}` catch-alls. `dialog-lite` 500s
on every invocation (the Lambda throws); `patient-timeline` 403s uniformly. Neither
is browser-callable — zero of 90 responses carried `Access-Control-*`.

So: how does the portal call them? **It must not be the browser.** Look for a
server-side proxy in the portal bundle, or a `m2m` / `gc` call pattern from the
patient API. The patient config names them, but a service only reachable from
Medtronic's own backend is a different piece of architecture than one a client can
call.

**Closes when:** you can name the caller and say whether a third-party client can
reach these services at all.

---

## Tier 2 — cheap, moderate value

### G. Cross-check the three model tables against each other

We hold three partial device tables — the patient config's family→model map, the
clinic bundle's device table, and the HCP report config — and they **disagree with
each other**. `MMT-8600`/`8601` are in the patient map but absent from the clinic
bundle. We never did the full three-way reconciliation.

**Closes when:** one table of every model code, with which source(s) list it and
which don't.

### H. The `reportFileNamingSupportedPumpModels` list

The public config has `personal.common.core.report.generation.reportFileNamingSupportedPumpModels`
— a list of pump models with a specific naming behaviour. It was recorded but never
interpreted. It's a small, closed list worth extracting and matching against the
family map.

### I. Auth0 tenant behavioural differences

All four tenants share the same OAuth *policy* but have disjoint keys. Does any
tenant differ in a way that matters — a `code_challenge_methods` difference, a
redirect-registration difference, a scope difference? Only the policy surface was
compared, not the behaviours.

**Closes when:** the four tenants' `/.well-known/openid-configuration` documents are
diffed field by field, behaviour not just policy.

### J. `login-errors.ts` against the live error surface

The bridge classifies Auth0 failure modes into named errors with operator-facing
messages. Those were derived from the vendor surface. Are they *complete*? Probe the
authorize/token error responses you can provoke unauthenticated (`invalid_client`,
`unauthorized_client`, `access_denied`, `invalid_request`) and check the classification
enumerates every one it can receive.

**Closes when:** every reachable Auth0 error is either handled or explicitly listed
as unhandled.

---

## Tier 3 — digging further for its own sake

### K. The chunk corpus, for real this time

224 lazy chunks are mined for endpoints and field names. **They were never mined for
control flow** — no analysis of what the call-sites do with the 89 field names, or
what the conditional logic implies about the request shape.

`system.logbook.entry.validation.config` shows entry shapes are **state-dependent**
(picking one removal reason triggers a free-text field). Tracing how the chunks
build the logbook entry payload would recover the request schema, not just the field
names.

### L. Recovery of the retired `ipro/hcp` JSF surface

The archives hold a clinician portal from 2013–2022 (`/ipro/hcp/*.jsf`) that predates
everything in `docs/02`. It is the ancestor of the current admin surface. Mapping what
changed gives a migration history, and retired endpoints sometimes reveal legacy
routes still live.

### M. Common Crawl, properly

`index.commoncrawl.org` is unreachable from some hosts, and the earlier pass had to
work around it via `cluster.idx`. **The `*.minimed.eu` / `*.minimed.com` API-set was
reported as a zero-return for CC**, which is suspicious — CC frequently covers URLs
Wayback doesn't. Worth a careful pass confirming whether the CC index genuinely has
nothing, or the byte-range offsets were wrong (a prior pass found its own offsets
landing on alphabetical neighbours).

---

## How to claim one

1. Open an issue using the **New research area** form, title `research: <area>`.
2. Say what you will probe, the request cap, and what "closed" means for that area.
3. When you have a result — positive **or negative** — open a PR with the finding
   and, if it pins something that must not rot, a regression entry.
4. **Negative results are first-class.** This repo's #84 was closed by proving
   something doesn't exist across 73 paths, 28 key names, and four corpora. That is
   a good contribution.
