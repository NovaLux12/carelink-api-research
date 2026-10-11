# Suggested research areas

> **Navigation** — the map: [`00-summary-the-map.md`](00-summary-the-map.md) · related: [`10-open-questions.md`](10-open-questions.md)

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

### D. The 18-country sweep, completed

`/patient/countries/settings` has 35 keys. 18 countries are swept. **109 recorded**
countries exist in the config's own lists. The interesting ones are the ones where
two keys disagree — we already found `bgUnits` vs `glucoseUnitsDefault`
contradicting each other in BE and CH.

**Attack that specifically:** sweep for *internal contradictions* in a single
country response, not for differences between countries. Unit fields
(`bgUnits`, `glucoseUnitsDefault`, `carbohydrateUnitsDefault`), date fields
(`shortDateFormat`, `reportDateFormat`), and the `mfa.status` / report-availability
flags are where an inconsistency would actually mislead a client.

**Closes when:** the sweep is either complete or the contradictions are enumerated.

### N. Do the two new POST-only routes exist on the other two cumulus hosts?

`connect/csr/v2/display/message` and `connect/v2/display/message` are the only
routes found live-and-POST-only in the CSR and bare-cumulus namespaces, each
confirmed three times on `clcloud.minimed.eu` (OBSERVED,
[findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md]). That pass was single-host
by design, so both routes are currently **one host's** finding.

**Blocker:** four OPTIONS requests, never sent — the 30-request cap was
exhausted (OBSERVED, [findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md] §Limits).

**Closes when:** the same two paths are OPTIONS-probed on
`clcloud.minimed.com` and `clcloud-trials.minimed.com`; either both return the
same CORS signature, or a region split is documented. A negative — 403 +
MissingAuthenticationTokenException on either host — closes it just as firmly.

**Assumptions (INFERRED):** that the carepartner region-identity result transfers
to the `csr`/bare-`v2` legs. It is an inference from a different leg of the same
API, not an observation of these paths.

### O. Is `/patient/reports/*` on `carelink.*` the reports surface for every region?

The 2026-10-10 sweep found `/patient/reports/*` live on `carelink.minimed.eu`,
gated 401/405, while `commoncore`'s broker paths 502 at the origin — so the
reports namespace is not where this repo had recorded it (OBSERVED,
[findings-log/probe-2026-10-08/recon/DRIFT-AND-NEW-2026-10-10.md] §2–3). That
observation is **one host**, and the sibling `.com` and `-trials` deployments
have never been checked for it.

**Blocker:** no token needed to establish existence — but the candidate list must
come from the *recorded* paths on the EU host, not from guessing (the `401`/`405`
split is the discriminator: 405 means POST-only and live, 401 means live and
token-gated).

**Closes when:** the same recorded report paths are probed on `carelink.minimed.com`
and `carelink-trials.minimed.com` with the 200/401/405 discriminator, and the
result either matches the EU host or documents the split. A negative — 404 on both
siblings — closes it and narrows #76's host list.

**Assumptions (INFERRED):** that the three patient deployments expose the same
namespace; the sweep observed only `.eu`, so this is an assumption until probed.

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

### P. Recover the request schema from the vendor's own app, statically

Half of `docs/10`'s open questions — the `markers[]` per-entry field names, the
`deviceFamily` casing, the NGP alarm vocabulary — are blocked on *one
authenticated response each*. The request side of those shapes is compiled into
the CareLink app itself, and no pass has ever decompiled it: the mobile-artifact
note is store metadata only, and the 2026-10-08 app-emulation pass worked from
the public JS bundle and third-party clients
([findings-log/medtronic-carelink-2026-07-21/09-mobile-artifacts.md];
[findings-log/probe-2026-10-08/APP-EMULATION-RESEARCH.md]).

**Blocker:** the artefact is not in the repo and no static-analysis tooling has
been run against it. Provenance of a store download is a decision to record, not
an assumption to make (the APKPure mirror is already recorded as
medium-confidence), and `docs/09`'s no-source-maps finding means the JS path
yields little.

**Closes when:** the logbook/marker entry payload and the family-matching
predicate are recovered verbatim from the app artefact with a named static
tool, written to a dated findings-log with the tool, version and evidence class
recorded — enough to answer the *shape* half of at least one token-blocked row in
`docs/10`, even though the response half stays token-gated. A negative — the
shape is not recoverable from the artefact — is equally a result.

**Assumptions (INFERRED):** that a static pass recovers schema the live surface
gates; the bridge's own notes show the app's family-matcher is five tokens wide
while the vendor ships a device it cannot match, which is the shape of a schema
that static analysis *would* settle — but no one has tried, so the recovery rate
is unknown.

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
5. **Your PR must leave this page fuller than it found it.** Close the area into
   the Closed table with its evidence, and add at least one successor area with a
   blocker and a definition of done — see
   [`CONTRIBUTING-research.md`](../CONTRIBUTING-research.md) step 7 for the
   template and the quality bar. A weekly job files an issue if this page drops
   below three open areas.

## Closed areas

Dated, with the verdict and the evidence. An area leaves this table only by
being superseded — never silently. Letters are not reused.

| Area | Closed | Verdict | Evidence | Closed by |
|---|---|---|---|---|
| C — extend the oracle set to `pde/v3` and `csr` | 2026-10-11 | **Negative on 10 cells, positive on 2.** PDE `v1/v2/v3` `display/message` and `pde/v3/discover/android/3.6` dead on GET **and** OPTIONS (no route on any tested method); `csr/v1`/`v3` and the bare `connect/carepartner/` prefixes dead on both; `connect/csr/v2/display/message` and `connect/v2/display/message` **live, POST-only** — in no prior note. 30 of a 30 request cap, GET+OPTIONS only | [findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md] | #2 |
