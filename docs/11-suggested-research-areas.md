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
| Does a `200` carry `Access-Control-Allow-Origin`? | one authenticated cross-origin request. Every browser-visible response on `clcloud.*` today is an error (401/403) and **none carry CORS**, so callability from a browser is unproven in both directions (see [`10-open-questions.md`](10-open-questions.md) §1) |

#### Addendum (2026-10-12, from area O): 24 more non-2xx responses, still zero `200`s

Attached to the `Access-Control-Allow-Origin` row above, as area O's claim issue
specified — it is the same question one gate further in, and this pass moved it
without a token.

**What was added.** Area O probed `/patient/reports/*` on all three
`carelink.minimed.*` patient hosts. **All 24 responses carried no
`access-control-allow-origin`** — not the 6 `401`s, not the 3 `400`s, not the
nine `405`s, not the 6 `404`s (OBSERVED,
[findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md] §6d). That is
**corroboration, not continuation**: area X's "0 non-2xx responses carrying CORS
anywhere" was measured on `clcloud.*`, and this is a different host family with
a different origin stack (`Apache/2.4.62` behind CloudFront, not AWS API
Gateway).

**Why it does not discharge the row.** The row asks about a **`200`**, and this
pass produced **no `200` at all** — every cell in the namespace is a 4xx. So the
token-gated half is now *more* precisely bounded than before: for
`/patient/reports/*` on `carelink.*`, the CORS question cannot be answered from
the outside at all, on any host, by any amount of further unauthenticated
probing.

**Blocker (unchanged, restated from what this pass established):** the remaining
unknown is what a successful response carries, which needs an authenticated
cross-origin request against a route that is known to exist. Area O establishes
*which routes exist* — 6 of the 7 on each of 3 hosts — so the token-gated half
of this row now has a precise target list instead of a vague one.

**Closes when:** one authenticated cross-origin request to any of the six live
`/patient/reports/*` paths on any of the three hosts shows a `200`'s CORS
headers, **or** the row is retired as unanswerable and the unauthenticated
negative is promoted to the standing position. **A negative closes it** — and
this pass is evidence that the negative is the likely answer, so this row should
be expected to close by downgrade rather than by discovery.

**Assumptions (INFERRED):** that `connect-src`/`frame-src` in the CSP the same
responses carry implies the browser client *needs* cross-origin access to the
report hosts. The CSP is host-aware and names the vendor's own data-plane hosts
per region (§6c of the pass log), which is suggestive, but no response observed
here demonstrates an actual cross-origin call.

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

### V. Given that `baseUrlPde` names a dead namespace, does any vendor client follow it?

Added 2026-10-12. **Derived from area T + area U** — this could not have been written
before 2026-10-12, because until then the published base URL set had never been
enumerated and nobody knew `baseUrlPde` was the one unroutable pointer in the corpus.

`baseUrlPde` is published on **every region of every discovery document** and resolves
to `/connect/pde/v3`, which has **no GET or OPTIONS route for either recorded path
under it**, on all three cumulus hosts (OBSERVED,
[findings-log/2026-10-12-published-pointers/FINDINGS.md §2b];
[findings-log/2026-10-12-pde-csr-cross-host/FINDINGS.md]). The same day, a different
key — `system.gc.gz.transition.flags.displayMessage.csrDisplayMessageUrl` — turned out to
be live, load-bearing and already switched on.

**What is missing:** whether the vendor's own frontends act on the published flags.
`system.gc.gz.transition.flags` has **five sibling capability booleans, all `true`**
(`pullGMInfoFromCumulus`, `pullSMSHistoryFromCumulus`, `sendDiagnosticLogsToCumulus`,
`sendPeriodicToCumulus`, `sendSMSFromCumulus`), which says five capabilities already
moved to Cumulus — so the flag mechanism is demonstrably in use. Nobody has ever looked
for a `pde`-shaped token in a frontend bundle, because nobody knew the key existed.

**Blocker:** one offline grep pass over the patient and clinician bundle captures for
`pde` / `baseUrlPde` / `transition.flags` tokens — **zero requests** if those captures
are still on disk. If they are not, this becomes a token- and artefact-blocked row and
belongs in the table at the top of this page instead.

**Closes when:** the bundles are searched for `pde`-shaped tokens and the result is
**either** a call site that uses the published `baseUrlPde` value, **or** a recorded
negative that no client in the corpus addresses PDE at all — in which case the vendor
publishes a base URL that nothing follows, which is the finding. **A negative counts**,
and is the likelier of the two outcomes given the namespace 403s before application code.

**Assumptions (INFERRED):** that the bundles on disk are the ones the shipped apps load.
They were captured 2026-10-08 and **never re-fetched**, so a bundle version bump would
invalidate the negative — state the capture date with the result, always.

> **Area Z is CLOSED** — see the Closed table at the foot of this page and
[findings-log/2026-10-12-area-z-origin-reflection/FINDINGS.md]. `ACAO` is a constant `*`, not an
echo: **45 of 45** cells, 3 hosts × 5 route families × 3 `Origin` conditions. It is left here
rather than deleted so the reasoning survives; a closed area never leaves the page silently
([How to claim one](#how-to-claim-one), rule 5).


### W. Is the per-key projection a complete enumeration path for the 69-key document?

Added 2026-10-12. **Derived from area T**, which produced the full 69-key name list for
the first time and showed the document's shape is **not** uniform.

The per-key form at `/patient/configuration/system/<key>` returned **21/21**
byte-identical subtrees for non-null keys, and null-valued keys 404 — so the form cannot
tell "absent" from "null", and `docs/04` rejected it under `/patient/v2/`. But it has
never been run in the **reverse** direction: from a name the bulk document does not
carry to the per-key form. Nobody knows whether that namespace has keys the bulk
document does not.

**What is missing:** whether the two key sets are identical. Area T also found the
document's **68 of 69 key *names* are literal dotted strings and exactly one is a bare
segment** (`captcha`), while 28–30 of the keys hold object *values*. A reverse probe
therefore has to decide what "name" means before it can be bounded: a naive splitter on
`.` misses `captcha`, and a type-blind walker misses every object-valued key.

**Blocker:** none, and the candidate list is finally closed: 69 flat names plus
`captcha`'s four subkeys, all derived from documents on disk. Only the null-valued ones
(5 per patient deployment, 6 on trials) need the 404-means-absent-or-null rule stated.

**Closes when:** every key the bulk document carries has a per-key verdict on one
deployment, **and** any per-key name outside the bulk document is recorded. **A negative
— identical key sets — closes it**, and would retire the "69-request enumeration path"
framing in `docs/04`.

**Assumptions (INFERRED):** that the per-key grammar is keyed off the same flat-name
form on all three deployments. Only one deployment has ever been swept.

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

### Why there is no area AA
#### Addendum (2026-10-12, from area Y): the corpus is two sources, not one

Found while building area Y's index, and **the correction the rest of this page depends on** —
see [Why there is no area AA](#why-there-is-no-area-aa). Zero requests.

**`results.jsonl` is not the whole corpus.** Host evidence also lives in
`findings-log/probe-2026-10-08/recon/ORACLE-PROBE-MATRIX.md`, the repo's own "one-request-per-row
log". Area Y read the machine-readable ledgers first and found
`connect/carepartner/v6/display/message` `GET` on **zero** hosts — which would have marked a
correctly-evidenced three-host claim **false**. The matrix carries all three.

Two more traps in reading it: the `namespace` column **already includes `connect/`** (prefixing it
again yields `connect/connect/…`), and some rows carry the version in the path tail while others
leave it to the `ver` column. And the index's `--coverage` lookup originally returned **before**
the matrix was merged, so it answered from a smaller corpus than the report printed beside it —
**the same "check that cannot fail" shape this page already warns about**.

**Blocker:** none, zero requests. `audit-index.py` (in the area Y log) merges both sources and
emits both readings where a matrix row is ambiguous, so a claim can never be marked unevidenced
because a parser guessed.
**Closes when:** the two sources are documented as the corpus on this page, and any host-coverage
query reads both.
**Assumptions (INFERRED):** that `results.jsonl` + `ORACLE-PROBE-MATRIX` is sufficient. Other
markdown logs (`VERSION-AXIS.md`, `AWS-GATEWAYS.md`) carry host evidence too; no claim was marked
defective on the index alone.


**Every letter A–Z is now in use** — 17 open plus 9 closed — and the priorities page's own gate
counts open areas by matching `^### [A-Z]. ` headings against the number stated in
`.github/ISSUE_TEMPLATE/config.yml`. A two-letter heading therefore fails that count in two ways
at once: it is invisible to the pattern, and the page's stated count would then disagree with its
own contents. This was already recorded for the sub-declared-gap question in
[`docs/09`](09-methodology-and-oracles.md) §4; area Z hit the same wall.

**So a pass that discovers a successor cannot mint a letter.** The options are: attach it to an
existing open area as a dated addendum (what area Z did — see area Y), or record it in
[`docs/10`](10-open-questions.md) §1 as an open question rather than a claimable area. **Neither
is as good as a real area, and the honest reading is that this repository has exhausted its
area namespace.** Extending the gate's area pattern to `AA`-style headings is a maintainer
decision, not a side effect of a research pass — same reasoning as the gate's own pattern in
[`docs/09`](09-methodology-and-oracles.md) §4.

## Closed areas

Dated, with the verdict and the evidence. An area leaves this table only by
being superseded — never silently. Letters are not reused.

| Area | Closed | Verdict | Evidence | Closed by |
|---|---|---|---|---|
| C — extend the oracle set to `pde/v3` and `csr` | 2026-10-11 | **Negative on 10 cells, positive on 2.** PDE `v1/v2/v3` `display/message` and `pde/v3/discover/android/3.6` dead on GET **and** OPTIONS (no route on any tested method); `csr/v1`/`v3` and the bare `connect/carepartner/` prefixes dead on both; `connect/csr/v2/display/message` and `connect/v2/display/message` **live, POST-only** — in no prior note. 30 of a 30 request cap, GET+OPTIONS only | [findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md] | #2 |
| N — do the two new POST-only routes exist on the other two cumulus hosts | 2026-10-12 | **Positive, and no region split.** Both `connect/csr/v2/display/message` and bare `connect/v2/display/message` are live and POST-only on `clcloud.minimed.com` and `clcloud-trials.minimed.com` as well as `.eu` — every cell byte-identical including CORS header ordering, controls first on each host. 16 of a 16 cap, GET+OPTIONS only. The pass also produced a **methodology correction**: `access-control-allow-methods` is not a register of a route's methods (`v13/display/message` advertises `OPTIONS` and is GET-capable on all three hosts) | [findings-log/2026-10-12-csr-cross-host/FINDINGS.md] | #8 |
| U — are the `csr/v1`, `csr/v3` and PDE cells dead on `.com`/`-trials` too, or only on `.eu`? | 2026-10-12 | **Negative, 3 hosts wide.** All six cells dead on **both** methods on both remaining hosts — 24 of 24 cells `403 MissingAuthenticationTokenException`, controls first on each host, 32 of a 32 cap. All 28 no-route bodies byte-identical (42 B, `sha256:f249b63cb2fc`), and that digest matches the `.eu` capture, so the router's no-route response is one artefact shared by three hosts. `docs/00`'s "Not re-probed on `.com`/`-trials`" caveat is **discharged**; nothing flipped to live | [findings-log/2026-10-12-pde-csr-cross-host/FINDINGS.md] | #11 |
| T — does any published document point a client at `csr/v2`? | 2026-10-12 | **Positive, and the premise was wrong.** The public config names `csr/v2` in **two** keys on **all three** deployments (`…csrDisplayMessageUrl` and `csr.cumulus.periodic.data.endpoints.display_message`, same URL), with `useCumulusUrls` already `true`; `baseUrlCsr` does not exist, so the route is addressed from **config, not discovery**. 10 of a 12 cap, GET only. Also found the **`system.gc.gz.transition.flags` switchboard** (absent from every prior key list), the **only** unroutable published base URL (`baseUrlPde`), and two corrections (`personal.data.csv.export.enable` is an object not a boolean; the document is 68 flat dotted keys + 1 nested `captcha`). **The premise had already been refuted on disk** by [findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md](https://github.com/NovaLux12/carelink-api-research/blob/main/findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md) §1 line 99 and never reached `docs/` | [findings-log/2026-10-12-published-pointers/FINDINGS.md] | #10 |
| B — the `v12/display/message` routing picture | 2026-10-12 | **Positive on the audit target, and the premise needed no correction.** `v12/display/message` is `401` + `UnauthorizedException` + `x-ca-err: 990` on **all three** hosts, 3 of 3 — but `docs/03` §6 and `docs/06` had asserted "401 on all three hosts" on **one** raw row (`.eu` only, duplicated across two files), so the claim is now *confirmed and evidenced* rather than restated. All 8 controls passed, controls first per host. **`v12` does not differ from `v13` on preflight**: `OPTIONS v{11,12,13}/display/message` all `200` + CORS, and `x-ca-err: 990` is identical across `v11`/`v12`/`v13`. **The gateway does not add CORS uniformly:** `discover/android/3.6` returns `401` with zero `Access-Control-*` at every version, same host and session — but this is **an observation, not a cause**: across all 101 captured heads every CORS-carrying response is a `200`, so "per-route configuration" is **not established** and became successor X. 17 of a 24 cap, ****23 of 24** including hurl validation of the new pins**, GET+OPTIONS only, measured spacing floor **2.033 s** (13 of 14 same-host gaps ≥2.5 s; the one short gap is **arithmetically impossible if both timestamps are faithful** — which assumes a monotonic clock, and `docs/09` declines to assert that cause — and is recorded as a provenance problem, not smoothed over. The 42 B no-route digest `f249b63cb2fc` independently reproduces the area U artefact. ⚠ **Its CORS corpus premise was superseded by area X the same day** — the 10 CORS-less `200`s are not all on "a different host surface"; four are `clcloud.*` discovery documents. The observation stands; the inference did not ([findings-log/2026-10-12-area-b-v12-routing/FINDINGS.md] §Correction) | [findings-log/2026-10-12-area-b-v12-routing/FINDINGS.md] | #4 |
| X — why the two `clcloud.*` route families differ in their CORS headers | 2026-10-12 | **Negative on the separating cell the area named, and a correction to the confound it rested on.** The area said no separating cell existed; **one was already in the corpus.** Of the 10 captured `200` heads with no `access-control-allow-origin`, **4 are on `clcloud.*`**, not on "a different host surface" — so on `clcloud.*` a `200` carrying no preflight *does* exist, and status was never standing in for CORS presence. Re-derived live on all three hosts: **25 of a 26 cap**, GET + empty-body OPTIONS only, controls first per host, **all 7 controls passed**; **9 further `200`-without-CORS responses, every one a `GET` of a discovery payload**; **0 non-2xx responses carrying CORS anywhere**; and sending `Origin` changed **none** of the **6** paired bare/`Origin` cells (6 route×method pairs, controls excluded), which **excludes** the "ACAO only when an `Origin` is present" mechanism. **It does not exclude area B's reading (b)** — "the route demands a token on `OPTIONS`" — nor reading (a), nor "emitted only on `OPTIONS`": a first draft of this row claimed (b) was refuted, and that was withdrawn, because the reason assumed a configured route would carry `ACAO` on its own `200` `GET`, which is the thing in dispute. **The cause is not established and this row does not establish it** — all three readings fit 25 rows, and separating them needs a CORS-configured `clcloud.*` route that also answers `200` on `GET`, of which **none is recorded on any host**. The four archive heads are **gitignored**, so the 24/14/10 split is not re-derivable from a clean clone. Measured spacing floor **2.291 s** (20 of 21 same-host gaps ≥2.5 s; the one short gap is **arithmetically impossible if both timestamps are faithful** (it assumes a monotonic clock, which `docs/09` declines to assume elsewhere) and is recorded as a provenance problem, **not smoothed over** — the second such gap in two passes). The separating cell is now **pinned** on the public `200` `GET`, at zero extra requests per drift sweep | [findings-log/2026-10-12-area-x-cors-separation/FINDINGS.md] | #15 |
| Z — does any `clcloud.*` route reflect `Origin`, or is `ACAO` a fixed `*`? | 2026-10-12 | **Negative, as predicted: `ACAO` is a CONSTANT `*`, never an echo.** Each preflight route's `OPTIONS` was sent under **three** conditions — bare, `Origin: https://example.invalid`, `Origin: https://probe-two.invalid` — on all three cumulus hosts, because **one `Origin` cannot distinguish an echo from a constant** and that is exactly why the archive (and area X's single-`Origin` pass) could not answer it. **45 of 45 data cells returned `ACAO: *`; 0 echoed; 1 distinct value.** All 6 controls passed **first on every host** (live `401` + `x-ca-err: 990`; dead `403` at the corpus no-route digest `f249b63cb2fc`, byte-identical on all three). `ACAM` is a **per-route constant**, 9 of 9 cells each across 3 hosts × 3 conditions, and **does** differ from the literal `OPTIONS` on two routes — `csr/v2` → `OPTIONS,POST`, bare `v2` → `POST,OPTIONS`, the same method set in a **different declared order**. `ACAC`, `access-control-max-age` and **`vary`** absent on all 51 responses. 60 of a 69 cap (51 harness + 9 hurl pin-validation), GET+OPTIONS only, measured minimum same-host gap **2.042 s** with **5 of 48** gaps under the declared 2.5 s — **none below the `>=2 s` floor**, the third pass in a row to record one (running count in `docs/09` §4). **No cause established.** **Positive side-finding:** `v6/display/message` — the vendor's own published `blePereodicDataEndpoint` — answers `200` + `ACAO: *` on **all three** hosts, closing a gap where it had only a `.eu` yes/no `CORS` flag and **two hosts never `OPTIONS`-probed**. ⚠ **The area's own premise was corrected before probing**: it asserted `ACAO` on all three hosts for `csr/v2`, bare `v2` and `v6`, and that was evidenced for **none** of the three — area Y's defect class. See the "corpus is two sources, not one" note under **Why there is no area AA** | [findings-log/2026-10-12-area-z-origin-reflection/FINDINGS.md] | #17 |
| Y — how many "all three hosts" claims rest on a single row? | 2026-10-12 | **All 29 in-scope claims confirmed by row — the negative result, and it closes the audit.** Every multi-host claim in the area's stated scope (**`docs/03` + `docs/06`**, 29 lines) resolves to a row per host. The `clcloud.*` route claims are three-host evidenced because areas B, X, N, U and Z each swept all three hosts on 2026-10-12. **Four candidate findings — none of them in scope, and two of them withdrawn**, and they are the more useful half of the record: **Y-1 WITHDRAWN** — `docs/03:38`'s "all three hosts return the same document" was alleged to be two-host evidenced on the strength of one pass's ledger, and **area X's tracked ledger refutes that**: all three hosts at 20256 B, one digest. **`docs/03:38`** and `01-discovery-pin.hurl` are unchanged from main — `docs/03` does carry **one** other edit from this pass, the claim-#10 method-axis correction, which is unrelated to Y-1. **Y-2 corrected** — `docs/08:37` claimed five hosts while citing `SECURITY-FINDINGS §S3`, which says **"at least twice"**, and labelled it OBSERVED from a file that forbids that label. **Y-3 WITHDRAWN** — `docs/02` was alleged to over-claim a five-tenant comparison; `AUTH-TENANT-FINDINGS §1`'s three tenants *include* trials, and `docs/02` is unchanged. **Y-4** the 2026-10-12 captures are gitignored, so some pages are not re-derivable from a clean clone — recorded, not fixed. **0 requests, 0 cap.** **The lesson the record carries:** two of the four candidate findings (Y-1 and Y-3) were produced by reading **one file as the corpus** — the exact defect area Z's addendum names, written by the pass immediately before this one. It took **three verification rounds** to repair the arithmetic built on the false premise before anyone checked the premise. `audit-index.py --selftest` now asserts its two views read one corpus | [findings-log/2026-10-12-area-y-three-host-audit/FINDINGS.md] | #19 |
| O — is `/patient/reports/*` on `carelink.*` the reports surface for every region? | 2026-10-12 | **Positive, and the area's split does not exist.** All seven recorded paths answer on **all three** patient deployments — `carelink.minimed.eu`, `carelink.minimed.com`, `carelink-trials.minimed.com` — and the responses are **byte-identical across hosts** (one body digest per path, three hosts). 21 of 21 cells reproduce their recorded code: `supported` / `snapshotTimelinesRange` **401**, `generateReport` / `favoriteReports` / `snapshotTimelinesForCalendar` **405**, `reportStatus` **400**, `report` **404**. **24 of a 30 cap**, GET only, controls first on every host, **all 6 passed** — the certainly-absent path `404`s on each host, so the status oracle is sound here (unlike the `clcloud.*` family, where it is uniform and useless) and the `404` is a true absence. **The negative the area anticipated did not occur.** **Two INFERRED premises are now confirmed rather than carried:** the three deployments share the namespace, and the status code is a usable discriminator. **A provenance correction:** the "live, gated 401/405" this area inherited cited a 2026-10-10 **JS-bundle scan** that names none of the camelCase paths; the only committed file naming `snapshotTimelinesRange` is the **archive** table, whose header says the codes are "as archived, **not** as measured live today" (2020-09-29→2021-03-31). So there was no live probe behind "live" — this pass is the first, and it reproduced the archived codes exactly. **Side-findings:** **`Allow: POST, OPTIONS` on all nine `405`s and on nothing else** — 9 of 24 responses, correlating exactly with the POST-only routes. This is a **scoping clarification** of `docs/09` §4's "no `clcloud.*` response carried `Allow`", not a correction of it: that row was already scoped to `clcloud.*` and to "this host family", so a `carelink.*` response carrying the header does not falsify it — it confirms the observation is **family-specific**, and a reader must not generalise it. (`docs/06:27,28,32` already records `Allow` — and its absence — on other patient routes.) Also a **host-aware CSP** that names **`commoncore-trials.medtronic.com`, a host in no prior note**. **⚠ The pass BREACHED the `>=2 s` delay floor** — 21 of 21 same-host gaps fell below it because a declared `DELAY=2.5` was never actually called; not re-run, because a clean re-run would exceed the 30 cap. Its first report of **min −0.538 s** was measured from `run.log` and **understated the breach**: the body-file mtimes give the true **min +0.092 s / max +0.387 s**, and show **no overlap**. It also added **two** backwards-clock-step occurrences (seq 9→10, seq 20→21), not one. Disclosed in full in the log §1a | [findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md] | #24 |
---

> **Consumer note.** Findings here are consumed by
> [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge), which
> feeds this repo's regression suite, which the bridge runs before a release.
> If something here moves a value the bridge pins, it reaches their release
> checklist — file it here with the `downstream-bridge` label and name
> the constant. Bridge bugs (login, upload, crash) belong in
> [their bug tracker](https://github.com/NovaLux12/carelink-bridge/issues/new?template=bug.yml).
