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

### T. Does any published document point a client at `csr/v2`, or is it a namespace no config can address?

`connect/csr/v2/display/message` is live and POST-only on **all three** cumulus
hosts (OBSERVED, [findings-log/2026-10-12-csr-cross-host/FINDINGS.md]). It sits one
namespace above the `carepartner` legs, and **no recorded document names it** —
the discovery documents declare `baseUrlPde` and the carepartner base URLs, and the
69-key public config declares `csr.control.codes.settings` and
`csr.cumulus.periodic.data.endpoints`, but no `baseUrlCsr` and no
`/connect/csr/v2` string is recorded anywhere.

That matters more than it looks: a route that exists but that **no config-driven
client is pointed at** is unreachable by the entire class of clients that read
their endpoints from the vendor's own documents — a different fact from "live",
and the difference decides whether anyone can use it.

**Blocker:** none for the offline half. Enumerating the discovery documents and
the public config for `csr`-shaped keys is a grep over documents already on disk,
zero requests. The live half is one unauthenticated config read per host.

**Closes when:** every recorded discovery document and the 69-key public config are
enumerated for `csr`-shaped base-URL keys, and either a base URL is named with its
source, or the negative "csr/v2 exists but no published document points at it" is
recorded **with the key list that was searched** so the negative is auditable
rather than merely asserted. A negative counts and closes it.

**Assumptions (INFERRED):** that `csr/v2` is an internal or deprecated route
rather than a client-addressable one — inferred from the *absence* of a recorded
base URL, which is not the same as having searched every document for one. If the
grep finds nothing, the inference has become an observation and this area's real
output is the key list.

### U. Are the `csr/v1`, `csr/v3` and PDE cells dead on `.com` and `-trials` too, or only on `.eu`?

Area N confirmed the **positive** cells are global and said nothing about the
negative ones. `docs/10-open-questions.md` §2 records "no route on any tested
method" for `csr/v1`, `csr/v3` and the PDE set — but that verdict rests on
`clcloud.minimed.eu` alone (OBSERVED,
[findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md]). A dead namespace on one
region is not evidence of a dead namespace on another, and this repo has already
been bitten once by a single-host row propagating into a three-host claim
(`AGENTS.md` §6 item 1).

**Blocker:** none. Six recorded paths × two hosts × GET + OPTIONS = 24 requests,
plus the four control cells per host. Every candidate is a path already recorded
in the Area C harness — no wordlist, no version neighbours added beyond the set.

**Closes when:** each of the six paths has a GET + OPTIONS verdict on
`clcloud.minimed.com` and `clcloud-trials.minimed.com` with controls first on each
host, and `docs/10` §2's row is either confirmed everywhere or restated with its
actual host coverage. **A negative counts in both directions:** finding one of them
live on another host is as valuable as confirming all dead.

**Assumptions (INFERRED):** that route registration is uniform across the three
cumulus stages. Area N's three positive cells all agreed, which is suggestive and
not conclusive — three agreeing samples do not establish uniformity, and the
negative cells are a different namespace.

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

### Q. The `appVersion` body gate — a second version axis our docs do not describe

**Added 2026-10-11.** `docs/00` and `docs/03` describe the **discovery-path** version
axis (`android/3.6`–`3.8` → Auth0 + cumulus v13). Third-party source review found a
**second, independent axis on the request body** that our docs do not cover:
`POST {baseUrlCumulus}/display/message` rejects `appVersion ≤ 3.6.9` with
**HTTP 206 `{"message":"Upgrade application"}`** and accepts `≥ 3.7`.
(SOURCE-PUBLISHED — author-reported table, corroborated by a xDrip maintainer on PR
#4711. The *mechanism*, that it is a **body** field, is SOURCE-OBSERVED at xDrip
`CareLinkClient.java:664` and `CarlosJPV src/carelink/cumulus.ts:146`.)

The two axes are constrained in **opposite** directions: the discovery URL must stay
**≤ 3.8** (3.9+ falls back to a legacy no-Auth0 config), while the body `appVersion`
has **no upper bound**. A client can be correct on one axis and broken on the other.

**Why it's ours:** nobody publishes a two-axis compatibility matrix. Every client
re-derives it independently — `CarlosJPV`, xDrip and this ecosystem's own
`discovery.ts` each found one half.

**Closes when:** the two axes are documented together in `docs/03` — **or** recorded as
community-reported-and-unverifiable, which is a legitimate close.

**Assumptions (INFERRED):** that the body gate and the discovery axis could move
independently. No client dates either change, so no drift timeline is asserted.

### R. Reconcile the `deviceFamily` correction against the client consensus

**Added 2026-10-11.** `docs/05` is corrected — `deviceFamily` **is** an API field on
`/patient/monitor/data`, agreed by three independent clients at named commits. What
is still missing is the **casing of a `deviceFamily` value**, which no client reports.

**Why the correction does not close it:** a destructuring default makes an absent field
indistinguishable from a present one, so a client that *reads* `deviceFamily` proves the
author believed it existed — not that it does.

**Closes when:** one authenticated `monitor/data` response records the key-name and its
value's casing verbatim, **or** a note in `docs/05` records that the value casing stays
unobserved and why. A negative retires the question honestly instead of leaving it
apparently answered.

**Assumptions (INFERRED):** that the routing field and the reported-family field stay
distinct. If a future payload collapses them into one, the correction's shape changes.

### S. Two more evidence classes for third-party source material

**Added 2026-10-11.** `AGENTS.md` §2 defines three (OBSERVED / PUBLISHED / INFERRED). A
pass that reads client source needs a **fourth** kind — someone else's code, written
against a live API — and the 2026-10-11 pass used two more: **SOURCE-OBSERVED**
(file:line at a named commit) and **SOURCE-PUBLISHED** (that repo's README/PR/commit
history). Both are corroboration, never proof of vendor behaviour.

**Why it matters:** evidence with no honest label gets quietly promoted to OBSERVED,
which is the one failure this repo exists to prevent (§1, §6 item 1). The 2026-10-11
pass hit this concretely.

**Blocker:** this changes the repo's stated rules, so it is a **maintainer decision**,
not a research task. It was deliberately **not** actioned by the pass that found it.

**Closes when:** `AGENTS.md` §2 gains the classes with the "never promote to OBSERVED"
rule attached, **or** a note records that third-party source stays under existing labels
and must always be flagged as corroboration. Either closes it; silence does not.

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

1. Open an issue using the **Claim a research area** form (labels
   `research-area,claimed`). State the area letter and title from this page —
   if it is not on this page, it is not claimable here.
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
| N — do the two new POST-only routes exist on the other two cumulus hosts | 2026-10-12 | **Positive, and no region split.** Both `connect/csr/v2/display/message` and bare `connect/v2/display/message` are live and POST-only on `clcloud.minimed.com` and `clcloud-trials.minimed.com` as well as `.eu` — every cell byte-identical including CORS header ordering, controls first on each host. 16 of a 16 cap, GET+OPTIONS only. The pass also produced a **methodology correction**: `access-control-allow-methods` is not a register of a route's methods (`v13/display/message` advertises `OPTIONS` and is GET-capable on all three hosts) | [findings-log/2026-10-12-csr-cross-host/FINDINGS.md] | #8 |

---

> **Consumer note.** Findings here are consumed by
> [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge), which
> feeds this repo's regression suite, which the bridge runs before a release.
> If something here moves a value the bridge pins, it reaches their release
> checklist — file it here with the `downstream-bridge` label and name
> the constant. Bridge bugs (login, upload, crash) belong in
> [their bug tracker](https://github.com/NovaLux12/carelink-bridge/issues/new?template=bug.yml).
