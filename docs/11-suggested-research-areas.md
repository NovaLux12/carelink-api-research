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


> **Area V is CLOSED** (2026-10-13, claim #42) — see the Closed table at the foot of
> this page and
[findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md]. **Recorded negative, with a
> sharper reason than the area expected:** no vendor web bundle contains `baseUrlPde` —
> and no `baseUrl*` key, `discover/android`, `clcloud` or `api/carepartner` is present
> either, because **no web bundle in the corpus reads the discovery document at all**.
> ⚠ **corrected 2026-10-13**: this row first published `discover` as 0 in all five
> bodies. It is **12 in each portal build**, every one a zxcvbn password-dictionary
> word — the conclusion is unchanged and the negative is stronger (17 dictionary hits
> per portal build: 12 `discover` + 5 `pde`), but the number was wrong. See
> [findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md §Correction (2026-10-13) §A]. The document's consumer is
> the mobile client its own path names (`discover/android/3.6`), so "does a client follow
> it" remains **unobserved in both directions** and `docs/03` §9a's INFERRED reading
> stands unchanged. The same corpus produced a **positive on the sibling pointer**: the
> patient bundle follows `csr.cumulus.periodic.data.endpoints` and POSTs its
> `display_message`, while naming `system.gc.gz.transition.flags` and never reading it.
> Its reasoning is preserved below rather than deleted, and its follow-ups were filed as
> **dated addenda to areas F and K**, not as new letters — see
> [Why there is no area AA](#why-there-is-no-area-aa).

> **Area Z is CLOSED** — see the Closed table at the foot of this page and
[findings-log/2026-10-12-area-z-origin-reflection/FINDINGS.md]. `ACAO` is a constant `*`, not an
echo: **45 of 45** cells, 3 hosts × 5 route families × 3 `Origin` conditions. It is left here
rather than deleted so the reasoning survives; a closed area never leaves the page silently
([How to claim one](#how-to-claim-one), rule 5).

> **Area E is CLOSED** — see the Closed table at the foot of this page and
> [findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md]. Its framing
> addendum from area W is **reproduced verbatim below**, not deleted, so the
> reasoning that produced the area survives; a closed area never leaves the page
> silently ([How to claim one](#how-to-claim-one), rule 5). Its successor is the
> dated addendum under **F** below.

#### Addendum (2026-10-13, from area W) — preserved: one deployment swept, two remained

> **Restored 2026-10-13 by area E.** Area E's first version of this page deleted
> this addendum along with the `### E.` heading while the pointer above promised
> the addendum would survive — a pointer promising non-erasure while erasing, which
> is `AGENTS.md` §6 item 5 in miniature. The wording below is area W's, unchanged.
> **Its close condition was met on 2026-10-13 by area E** (negative — all three
> deployments carry the same 69-name key set), so it is history rather than an open
> task. Its `Assumptions (INFERRED)` line is now **tested, not assumed**: the
> per-key grammar *is* keyed off the same flat-name form on all three deployments.

Area W swept all 69 keys plus `captcha`'s four subkeys on **EU only**
([findings-log/2026-10-13-area-w-per-key/FINDINGS.md]): 61 VALUED-match, 5
NULL-404, `captcha`/`default.country` on dedicated routes, zero names outside
the bulk document — and the complete 69-name list is now committed at
[findings-log/2026-10-13-area-w-per-key/keys.txt](../../findings-log/2026-10-13-area-w-per-key/keys.txt),
so the candidate list for the remaining two deployments is closed and needs no
re-derivation. One caveat travels with it: `personal.common.core.reporting.enabled.countries`
does **not** round-trip on EU — its per-key value carries a stray trailing `]`
(reproduced byte-identical), so a cross-deployment value comparison must parse
defensively, not string-compare. **Closes when:** the per-key form has a verdict
for all 69 keys on `.com` and `-trials`, with absent-vs-null resolved per
deployment. A negative (all three identical) counts. **Assumptions (INFERRED):**
that the per-key grammar is keyed off the same flat-name form on all three
deployments — only one has ever been swept.

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

#### Addendum (2026-10-13, from area E): the two config-escape routes have only ever been read on one deployment

**Derived from area E's negative, which is what makes this askable.** E swept
all 69 names per-key on `.com` and `-trials` and found the projection is
byte-for-byte identical to each host's own bulk document, **0 mismatches in 123
valued cells** ([findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md]
§2). That means a third-party client reading config unauthenticated has exactly
**three** read paths, not 69: the bulk document, plus the two keys whose per-key
form is a 404 because they live at **dedicated routes** —
`/patient/configuration/defaultCountry` and `/patient/configuration/recaptcha/key`
— plus `/patient/configuration/messages/{lang}` beside them.

**All three were recorded on `.eu` only**, by the 2026-10-08 namespace pass
([findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md]). No pass has
requested either dedicated route on `.com` or `-trials`, and area E's own log says
so rather than implying it ([source:
findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md §7]). A client that
falls back to `defaultCountry` when the per-key form 404s has **never been
observed to succeed anywhere but the EU host** — and that fallback is exactly what
the `default.country` / `captcha` verdict is for.

**What is missing:** whether the two dedicated routes are live, and return the
same envelope, on the other two deployments; and whether `messages/{lang}` is
still `{"messages":[]}` or has gained content. A **third** question fell out of
E and is the cheaper one: the trials host returned **one real-key 404 carrying
`content-type: application/vnd.nervana`** — a value in **no prior reading anywhere
in this namespace** — so the 404 content-type set is **deployment-dependent and
three-valued**, not the two-valued shape area W recorded on EU.

**Blocker:** a bounded candidate list that already exists on disk and needs no
invention — the three routes above, plus `/patient/configuration/version` and the
`/patient/configuration/` root (both already tried and 404'd on EU, so they are
**controls**, not candidates). That is 5 paths × 2 hosts + 2 controls per host =
**14 requests**, GET only, controls first per host.

**Closes when:** all three routes have a recorded verdict on `.com` and `-trials`,
and the per-deployment 404 content-type set is tabulated. **A negative counts**
and is the likely answer — that the two dedicated routes are EU-only, or that the
whole sibling namespace is identical everywhere, would both close this. The one
outcome that does *not* close it is a new key appearing under
`/patient/configuration/` on a non-EU host, which would reopen the projection
question E just retired.

**Assumptions (INFERRED):** that the `/patient/configuration/` sibling namespace
behaves the same on all three deployments — E established this for the
`/system/` subtree only, on the strength of an identical 69-name key set and
identical per-key verdicts, which is evidence about `/system/` and not about the
siblings. `application/vnd.nervana` is recorded once, on one cell, on one
deployment: that it is a deployment-level constant rather than a per-key or
per-route value is **not** established, and one observation cannot separate those
three readings.

#### Addendum (2026-10-13, verifier round 2 of area E): commit the per-cell digests, or the "0 mismatches" claim is unverifiable forever

**Derived from a failure, not from a topic.** Area E's central claim — **0 value
mismatches across 123 valued cells** — is the one number in its log that **no
reviewer can re-derive.** It passed two verifier rounds as sound and
*unverifiable*, which are not the same property: the claim needs, per cell, both
sides of the equality (the response body to unwrap the envelope, and the host's
resolved bulk subtree), the response bodies were transient by design
(`AGENTS.md` §7, no raw captures), and `verdicts.py` cannot be re-run without
them. The verdict was recorded as **inherent, not a defect** — areas W, G and H
share the same property. **But area E also published a row claiming a second code
path had confirmed it, and no such path existed** ([findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md]
§Correction (2026-10-13), F1). **That is the honest reason it was a fabrication
rather than an overstatement: there was nothing to confirm it with.**

**What would have made it checkable, forever, at zero extra requests.** One line
in `verdicts.py`, emitting a committed `cell-digests.tsv`:

```
host  key  seq  norm  sha256(canonical(parsed value))  sha256(canonical(resolved bulk subtree))
```

Digests, **never values** — so it satisfies `AGENTS.md` §7 exactly as this repo's
bulk-document digests already do, and a verifier can re-hash both sides from the
committed file and confirm the equality without ever holding a body. **This is
one line of code and zero requests; it is not hard, which is exactly why its
absence is a finding rather than an excuse.**

**Foreclosed for area E, and the reason matters.** It cannot be added now: the
bodies are gone, so the digests cannot be computed retrospectively and inventing
them would be worse than not having them. **Foreclosed by the transient bodies,
not by the request budget** — area E used 152 of a 170 cap, so 18 requests were
unspent. The next pass over this namespace must emit it.

**Blocker:** none, zero requests, for the digest artefact alone — it is written
during a sweep, not after one. It becomes possible only while a body is in hand,
which is why it is a property of *running* a sweep rather than of a follow-up.

**Closes when:** any sweep over `/patient/configuration/` commits a per-cell
digest artefact whose two columns a stranger can re-hash, **or** the area that
produced it records in prose that its "0 mismatches" claim is **log-level and
non-re-derivable**, so no later reader mistakes it for a pinned assertion.
**A negative counts:** if the two digest columns ever disagree on a cell, that is
a positive finding about the vendor, not a harness artefact.

**Assumptions (INFERRED):** that a value digest is a sufficient equality witness
here — it is, because every compared cell's bulk side is derivable from the same
host's bulk document, which **is** re-fetchable unauthenticated in 1 request per
host, whereas the response side is not. The one case a digest cannot settle is a
hash collision, which this repo already treats as an acceptable residual for the
same reason (`docs/09` §5 item 3).

#### Addendum (2026-10-13, from the #61 CORS-method pass): the family claim rests on two hosts, and no `commoncore*` cell has ever varied `Origin`

**Derived from a cell nobody had run.** Before 2026-10-13 no **OPTIONS** request had ever
been sent to any `commoncore*` host, so two things were unaskable. Both are now askable, and
one of them has an answer. **OBSERVED, 8 of 8 cells**, 2 hosts × {recorded path,
certainly-absent path} × {`GET`, empty-body `OPTIONS`}: `403`
`MissingAuthenticationTokenException`, `ACAO`/`ACAM`/`ACAH` all `*`, no `ACAC`, no `Allow`,
no `Vary`, all 8 byte-identical once the per-request headers are stripped
([findings-log/2026-10-13-cors-method/FINDINGS.md §3]). So on this origin stack the CORS set
is **neither method-conditional nor path-conditional**, **"emitted only on `OPTIONS`" is
excluded for this family**, and the corollary is the useful half: an `OPTIONS` response
carrying `ACAO: *` **here is not proof that a resource exists**, so `docs/09` §2's
`GET 403 + OPTIONS 200` rule needs the status beside the header, not the header alone
(**no `clcloud.*` host was probed, so nothing here transfers to that family** — the row's own
premise, that these gateways are not browser-callable, is untouched).

**What is missing, in two halves.** (a) **Breadth:** `commoncore-trials.minimed.com` carries
1 of the six counter-examples and was **not** probed — three cells per host is 9 requests
against a cap of 8, so the budget went to two hosts at a full matrix rather than three hosts
at a matched pair, because the controls are mandatory and a pair without a positive control is
not a defended comparison. (b) **A dimension no pass has varied:** `Origin`. Area Z excluded
"ACAO appears only when an `Origin` header is sent" on `clcloud.*` route cells; on
`commoncore*` **no pass has ever sent one**, and this pass sent none deliberately, to match the
captures it follows. `Vary` is absent on all 8 cells — that is a caching directive and **no
emission mechanism is inferred from it**.

**Blocker:** not an idea and not a token — **8 requests**. Four for (a): the same 2 × 2 on the
third host, `GET` and empty-body `OPTIONS`, controls first, positive control
`/reports-broker/v1/ocl` and absence control `/reports-broker/v1/ocl-probe-absent`. Four for
(b): the recorded path and the absent path on one host, each bare and each with
`Origin: https://example.invalid` — a reserved name, so the value can only be echoed or
dropped, never dialled. `Origin` is a request header, so it adds no traffic to a third party.

**Closes when:** the third host has a verdict on the 2 × 2 **and** one host has a verdict on
the `Origin` axis — and a verdict is the header set plus the status, not the header alone, so
that a partial answer cannot read as a settled one. **A negative counts** on both halves and
is the likely answer for (b), given the literal `*` in every cell recorded so far.

**Assumptions (INFERRED):** that these two hosts are representative of the
`commoncore-trials.medtronic.com` / `commoncore.medtronic.com` family — **which is exactly
what half (a) tests, and is not assumed by this addendum's own claim**, since the claim is
stated per host. That the `*` is stage-level gateway configuration rather than a per-route
setting: it appears on a `MissingAuthenticationTokenException`, which is evidence about the
*stage*, but the mechanism remains unestablished, as `docs/09` §2 says. That an `Origin` on a
no-route error would be handled by the same code path as an `Origin` on a routed one —
**untested**, and the two are not interchangeable.

#### Addendum (2026-10-13, from area V): the shipped patient bundle names a timeline host that is not published

**Derived:** none of this was knowable before 2026-10-13 — area V re-fetched the patient
bundle and grepped it, and these four facts came out of that corpus rather than out of
the network [findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md].

**OBSERVED**, patient bundle `main.6595daf83bd6d4b1.js` (3,417,255 B, sha256
`0fb4fbd4…`, captured 2026-10-13, byte-identical on `carelink.minimed.eu` and
`carelink.minimed.com`):

- **`dialog-lite` is 0 hits in all five captured bodies.** The premise that the portal
  calls it is **not supported by the corpus** — a negative, not a refutation of the
  route.
- **`patient-timeline` is 5 hits and every one is an Angular component selector, not a
  URL** — `["app-patient-timeline"]` (byte 1718181),
  `"app-patient-timeline-filter-toolbar"` (1719243), two template calls (1963408,
  1963661) and one `selectors:` array (3340159). A grep on the bare name reports an
  integration that is not there: the `docs/09` §5 false-hit class, on the one token
  this area is specifically hunting.
- The bundle **does** carry `personal.patient.timeline.config` as a quoted literal and
  reads it (selector `Nt`, exported as `bQ`, 3 property reads), and a template reads
  **`.featureEnabled`** off it to choose between rendering the Patient-Timeline tab and
  not (byte 1966110). The timeline is therefore **config-gated in shipped code**, which
  is one step closer to a caller than "it must not be the browser".
- ⚠ The bundle **also names `personal.patient.timeline.host`** — 1 occurrence, and its
  constant `personalPatientTimelineHostURL` occurs **once**, so nothing reads it. The
  **published** key is `personal.patient.timeline.config.host` (`docs/04`, an AWS API
  Gateway answering 403). `personal.patient.timeline.host` is **not** in the 69-name
  list area W committed, i.e. **the bundle names a config key the public document does
  not publish.** Which of the two is real is **not** settled here.

**Blocker:** the shape of `personal.patient.timeline.config` has never been read. This
area asks "who calls `patient-timeline`", and the caller turns out to be gated on that
object's `featureEnabled` — while the object itself is nowhere in this repo's recorded
values and only its `.host` member is named. **It costs zero requests**: the whole
public config document is already downloaded by `regression/hurl/05-public-config.check.sh`,
so one `jq` on that body enumerates the object's full key set.

**Closes when:** `personal.patient.timeline.config` has its **full key set** recorded
from the live public config on all three deployments, and the bundle's two timeline-host
keys are reconciled against it — either the bundle's key is a stale name nothing reads
(half-evidenced now: its constant has zero readers in the eager bundle) or the vendor
publishes a second, unrecorded key. **A negative counts**: "the bundle names a key the
document does not publish, and nothing reads it" is a complete answer.

**Assumptions (INFERRED):** that the patient bundle fetched from `carelink.minimed.eu`
is what the shipped patient web app loads — its asset name is taken from that host's own
entry document in the same run, but no authenticated session confirms a logged-in user
receives it. And that a lazy chunk cannot read the timeline config: **only the eager main
bundle was swept**, the 211 lazy chunks were not (see the addendum to area K).

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

> **Area Q is CLOSED — see the Closed table at the foot of this page and
> [`docs/03`](03-discovery-and-versions.md) §3a.** Closed 2026-10-13 on the area's
> **second** close condition — *recorded as community-reported-and-unverifiable, with
> the reason* — because the boundary is a **request-body** field and `AGENTS.md` §11
> permits no vendor POST beyond the two already-pinned public-`client_id` requests.
> The **mechanism** resolved in code; the **boundary values** did not and cannot be
> resolved from outside the project. **The pass spent 21 requests against a cap of
> 20** — a one-request overrun, disclosed in the log and not smoothed away. **The cap
> was restated to 21 by owner authorisation on 2026-10-13, after the pass
> completed**, so the log's accounting line now reads `21 of a 21 cap`; the declared
> 20 is kept readable beside it, in the log's `## Correction (2026-10-13)`. The
> restatement equals the spend exactly and grants no slack.
>
> **The area as written, kept verbatim so the correction stays readable.** One of the
> two claims it rests on no longer holds. **⚠ Withdrawn:** *"corroborated by a xDrip
> maintainer on PR #4711"*. Read at the artefact, PR #4711's three comments are the
> boundary table (**by the same author as the README that repeats it**), a question,
> and an approval that does not restate or retest the boundary values — so the table
> is **one source stated twice**. **Still stands:** the table is SOURCE-PUBLISHED and
> author-reported, and the *mechanism* — that `appVersion` is a **body** field — is
> SOURCE-OBSERVED at `CarlosJPV src/carelink/cumulus.ts:146` @ `0180b89`, which this
> pass read and which is byte-identical at branch head. **Not re-verified here:** the
> xDrip half, `CareLinkClient.java:664`. Original text:
>
> > **Added 2026-10-11.** `docs/00` and `docs/03` describe the **discovery-path**
> > version axis (`android/3.6`–`3.8` → Auth0 + cumulus v13). Third-party source
> > review found a **second, independent axis on the request body** that our docs do
> > not cover: `POST {baseUrlCumulus}/display/message` rejects `appVersion ≤ 3.6.9`
> > with **HTTP 206 `{"message":"Upgrade application"}`** and accepts `≥ 3.7`.
> > (SOURCE-PUBLISHED — author-reported table, corroborated by a xDrip maintainer on
> > PR #4711. The *mechanism*, that it is a **body** field, is SOURCE-OBSERVED at
> > xDrip `CareLinkClient.java:664` and `CarlosJPV src/carelink/cumulus.ts:146`.)
> >
> > The two axes are constrained in **opposite** directions: the discovery URL must
> > stay **≤ 3.8** (3.9+ falls back to a legacy no-Auth0 config), while the body
> > `appVersion` has **no upper bound**. A client can be correct on one axis and
> > broken on the other.
> >
> > **Why it's ours:** nobody publishes a two-axis compatibility matrix. Every client
> > re-derives it independently — `CarlosJPV`, xDrip and this ecosystem's own
> > `discovery.ts` each found one half.
> >
> > **Closes when:** the two axes are documented together in `docs/03` — **or**
> > recorded as community-reported-and-unverifiable, which is a legitimate close.
> >
> > **Assumptions (INFERRED):** that the body gate and the discovery axis could move
> > independently. No client dates either change, so no drift timeline is asserted.
>
> **What the pass added that the area did not ask for:** the two constraints
> **intersect in exactly `{3.7, 3.8}`** *for the `X.Y` forms the discovery axis has
> been probed at* — `3.7.0`/`3.8.0` clear the body gate but are unobserved on the
> discovery path, since no `X.Y.Z` cell was ever probed — and the one client whose
> source is readable feeds **a single constant** into both axes, correct only because
> `3.8` is in that window, so raising it to `3.9` breaks the discovery axis
> *silently*, on a path this repo already pins. That is a bridge-facing coupling and
> it is now a `docs/10` §1 row.

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

#### Addendum (2026-10-13, from area G): the offline half is ready — per-build model lists as casing candidates

Area G extracted the device table from **each** portal build separately and found
them identical as data (78 table codes + 9 `SKU-*`, 76 quoted name-pairs + 2
unquoted `MMT5100`/`MMT5101` aliases + 9 `SKU-*` pairs, 80-code whole-file
census — same sets in both builds), with `MMT-8600`/`8601` in module `90991`
in both (OBSERVED,
[source: findings-log/2026-10-13-area-g-device-tables/FINDINGS.md]).

**What this gives R:** the exact candidate strings whose casing a wire
`deviceFamily` value must be compared against. The portal builds carry display
names ("Guardian™ 4 system", "Simplera™ system", "MiniMed™ 780G", …) alongside
every code, so a future authenticated response can be matched three ways:
against the model code, against the display name, and against the patient map's
16 family tokens — and whichever matches names the casing convention.

**Blocker (unchanged, restated with the offline half discharged):** one
authenticated `monitor/data` response (token-gated half stays); the offline
half — G's per-build model lists — is done and needs no re-fetch unless the
builds move (re-anchor by the asset sha256 pair `2a7fa8e7…` /
`a054555a…` first).

**Closes when:** one authenticated response records the `deviceFamily` value
verbatim and it is matched against G's table entries, or `docs/05` records the
casing as unobserved with the reason. A negative (casing unobservable without a
token) counts.

**Assumptions (INFERRED):** that the routing field and reported-family field
stay distinct; that table strings are the wire vocabulary.

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

#### Addendum (2026-10-13, from area Q): a second pass, and the label was not the failure — the *count of sources* was

Attached to area S rather than opened as a new letter (every A–Z is in use).

**What was added.** Area Q is the **second** pass in this repo to need these two
classes, and it produced the same awkwardness the 2026-10-11 pass did. It also
surfaced something S's framing does not cover, which is the reason this addendum
exists: **the problem was not the missing label, it was a strength word.**

Area Q's own area text claimed the `appVersion` boundary table was *"corroborated by a
xDrip maintainer on PR #4711"*. Reading the artefact, PR #4711 has **three** comments:
the table (by `CarlosJPV` — also the author of the README repeating it), a question,
and an approval that never restates or retests the boundary values. **The table is
one source stated twice.** The claim would have been equally wrong had
SOURCE-OBSERVED/SOURCE-PUBLISHED been classes all along — a label describes the
*kind* of evidence and says nothing about how many independent sources produced it
(SOURCE-OBSERVED §4, §7,
[findings-log/2026-10-13-area-q-appversion-axis/FINDINGS.md]).

**What is missing:** a rule that distinguishes **one source, restated** from **two
independent sources** — and a rule about strength words (*independently*,
*corroborated*, *confirms*) that says what each requires. Nothing in `AGENTS.md` §2
or §3 requires checking that.

**Blocker:** it is part of the same **maintainer decision** as area S proper, and it
cannot be settled by a research pass — the question is what the repo's *rules* should
say. The audit that would motivate it is not blocked and can be run first (§
`docs/10` §1, the *corroborated independently* row, which carries the full framing).

**Closes when:** either (a) `AGENTS.md` §2 gains SOURCE-OBSERVED/SOURCE-PUBLISHED
**and** a statement of what "independently corroborated" requires — different
authors, different artefacts, neither quoting the other; **or** (b) the decision is to
keep the existing labels, in which case the rule about independence must still be
written, because the failure does not depend on the labels. Either closes it; a
labels-only decision does **not**, which is the point of this addendum.

**Assumptions (INFERRED):** that independence is judged at the level of the
**person or organisation that ran the measurement**, not the artefact — two files in
one repository, or one file and a PR comment on it, are one source. This is the
assumption area Q applied; a maintainer could reasonably define it more strictly, and
the one confirmed instance (`CarlosJPV`'s table in his README and in his own PR
comment) would fail under any definition strict enough to matter.

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

#### Addendum (2026-10-13, from area V): the *patient* chunk corpus is a different, unswept set of 211

**Derived and non-duplicate.** Area K's corpus is the **224** chunks of the **clinic
portal** — `CHUNK-CORPUS-FINDINGS.md` names `hp-main.js` as its measure source. The
**patient** app is a separate webpack build with its own runtime chunk map, and that map
has **211 entries**
([findings-log/2026-10-13-area-v-pde-clients/chunks.txt](../../findings-log/2026-10-13-area-v-pde-clients/chunks.txt)).
Three were sampled once in 2026-10-08 (`JSMAP-HUNT §3.3`); **none of the 211 was ever
fetched as a corpus.** So the gap is not "chunks are unmined" — it is **the patient
corpus specifically**, which K's 224 does not cover.

**The candidate list is closed, committed, and current.** `chunks.txt` was written from
the runtime bundle's own map on 2026-10-13 and **reproduces** the 2026-10-08 record: the
map still has 211 entries and the sampled hashes (`12.c22952a522974f5f`,
`985.47eb741416e9cd44`) are unchanged. URL form is `<id>.<hash>.js` at the **asset
root** (`carelink.minimed.eu`, not `/app/`) because the runtime sets `.p=""`;
`JSMAP-HUNT §5` already recorded that the `<base href="/app">` reading is wrong.

**Why it matters now.** Every bundle claim area V made — "no web bundle reads the
discovery document", "the client follows `csr.cumulus.periodic.data.endpoints` but not
`system.gc.gz.transition.flags`" — is a statement about the **eager main bundle only**,
and that limit is stated at every use. A lazy chunk is exactly where a feature-gated
call site would live, so those negatives are provisional until this set is swept.

**Blocker:** 211 GETs of the committed list from one host — a real request budget
(≈9 minutes at a 2.5 s spacing), not a token. Everything else is already done: the
list, the host, the URL form, and the token set (`baseUrl*` / `discover` / `clcloud` /
`pde` / the nine `transition.flags` leaves).

**Closes when:** all 211 carry a verdict for that token set, each hit read to
literal-vs-directive with a case-sensitivity control exactly as area V read its 13
bodies — **and a negative counts**, since "no lazy chunk carries a discovery key" is
the expected outcome and would convert area V's scoped negative into an unqualified one.

**Assumptions (INFERRED):** that the chunk ids and hashes in the runtime map still
resolve — verified today for the two sampled ids only, not for all 211; and that the
patient `main`+`runtime` pair is the entry point for those chunks, which the runtime's
own `f.u` construction implies but this pass did not trace to a loader.

### L. Recovery of the retired `ipro/hcp` JSF surface

The archives hold a clinician portal from 2013–2022 (`/ipro/hcp/*.jsf`) that predates
everything in `docs/02`. It is the ancestor of the current admin surface. Mapping what
changed gives a migration history, and retired endpoints sometimes reveal legacy
routes still live.

#### Addendum (2026-10-13, from area M): the family is anchored on `carelink.minimed.eu`, and Common Crawl holds it

Area M found this while re-deriving a different claim, and it could not have been
written before that pass ran.

`ARCHIVE-URLS §3` dates `/ipro/hcp/*.jsf` to **2013-05-17 → 2022-05-13** and notes
the `jsessionid` in the URL, but **names no host**. A second, independent corpus
now does: **Common Crawl `CC-MAIN-2020-50` (2020-11-23 → 2020-12-06) holds three
captures of the family on `carelink.minimed.eu` itself**, all at **2020-12-02** —
`/ipro/hcp/` **302**, `/ipro/hcp/login.jsf` **200**, `/ipro/hcp/main/home.jsf`
**302** (OBSERVED, [source: findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md
§3a]). Two query shapes agree on the record set: `matchType=domain` and
`matchType=host`.

So the retired clinician surface ran **on the patient API host**, not on a
separate Medtronic domain — which is the migration fact this area exists to
recover, arriving from a corpus nobody had asked.

**Blocker:** none, and no token. The capture bodies are in Common Crawl and the
metadata is already in this pass's ledger; the work is reading them, which is
**zero requests**. The blocker is budget-shaped, not access-shaped — area M spent
its last request on the host-level confirmation and could not also spend one per
`/ipro/hcp/*.jsf` path, because this API **fails 28% of its queries**
([`docs/09`](09-methodology-and-oracles.md) §4) and a sweep of N paths costs
roughly 1.3 N.

**Closes when** the `/ipro/hcp/*` family is enumerated with a host and a date per
member, and the `carelink.minimed.eu` anchor is either confirmed across the 2013
and 2022 ends or explicitly shown to be a single-period deployment.
**A negative counts** — if the family turns out to be one three-capture entry
with no siblings, that is the answer and it closes the area.

**Assumptions (INFERRED):** that the 2020-12-02 captures belong to the same
deployment as `ARCHIVE-URLS`'s 2013–2022 family rather than to a second portal
sharing the prefix. The assumption is that `/ipro/hcp/*.jsf` names one surface
over time; it rests on the path shape and the JSF convention, and nothing
observed here demonstrates it. **`ARCHIVE-URLS` was not modified by area M** — a
host attribution added to a findings log another pass owns is a correction that
pass's owner should make, so it is recorded here instead.

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


**Every letter A–Z is now in use** — 6 open plus 20 closed — and the priorities page's own gate
`.github/ISSUE_TEMPLATE/config.yml`. A two-letter heading therefore fails that count in two ways
at once: it is invisible to the pattern, and the page's stated count would then disagree with its
own contents. This was already recorded for the sub-declared-gap question in
[`docs/09`](09-methodology-and-oracles.md) §4; area Z hit the same wall.

> ⚠ **Corrected 2026-10-13 by area M.** This read *"9 open plus 17 closed"*. **The
> words are not mine — `git diff origin/main...HEAD -- docs/ | grep -c 'Every letter A'`
> is 0 — but the values are mine to maintain, because closing area M is what broke
> them.** Measured across the three revisions:
>
> | revision | sentence read | actual | `config.yml` |
> |---|---|---|---|
> | `3166c3a` (this branch's base) | 10 open plus 16 closed | **10 / 16** ✓ | 10 |
> | `cd626d6` (area E merged) | 9 open plus 17 closed | **9 / 17** ✓ | 9 |
> | HEAD (area M closed) | 9 open plus 17 closed | **8 / 18** ✗ | 8 |
>
> So this was **not** a stale sentence I inherited — area E had it right, and my
> own closure took closed 17→18 and open 9→8 while `config.yml` moved 9→8. **8 + 18
> = 26 = A–Z**, both figures re-derived from this page, and `config.yml` agrees.
>
> **This is the third time this exact sentence has been wrong.** Area Z fixed it at
> `fbe5d9b` (from "20 open plus 6 closed" to 19 and 7) and recorded why a green gate
> missed it: `research-checks.py` compares `config.yml` against the **heading** count
> (`^### [A-Z]. `), and **nothing anywhere compares this prose against either number**.
> That blind spot is unchanged, so this will drift again on the next closure unless a
> check is added. **Not added here**: extending the gate's own patterns in the same PR
> the gate passed is a maintainer decision, for the reason `docs/09` §4 already records
> about its count-pattern defect. Recorded as the successor instead.

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
| O — is `/patient/reports/*` on `carelink.*` the reports surface for every region? | 2026-10-12 | **Positive, and the area's split does not exist.** All seven recorded paths answer on **all three** patient deployments — `carelink.minimed.eu`, `carelink.minimed.com`, `carelink-trials.minimed.com` — and the responses are **byte-identical across hosts** (one body digest per path, three hosts). 21 of 21 cells reproduce their recorded code: `supported` / `snapshotTimelinesRange` **401**, `generateReport` / `favoriteReports` / `snapshotTimelinesForCalendar` **405**, `reportStatus` **400**, `report` **404**. **24 of a 30 cap**, GET only, controls first on every host, **all 6 passed** — the certainly-absent path `404`s on each host, so the status oracle is sound here (unlike the `clcloud.*` family, where it is uniform and useless) and the `404` is a true absence. **The negative the area anticipated did not occur.** **Two INFERRED premises are now confirmed rather than carried:** the three deployments share the namespace, and the status code is a usable discriminator. **A provenance correction:** the "live, gated 401/405" this area inherited cited a 2026-10-10 sweep whose committed artefact **disclaims itself** — *"a reconstruction from the agent's report"*, evidence *"not reproduced"*, *"re-verify before treating any row as OBSERVED"* ([`DRIFT-AND-NEW-2026-10-10.md:9`](https://github.com/NovaLux12/carelink-api-research/blob/main/findings-log/probe-2026-10-08/recon/DRIFT-AND-NEW-2026-10-10.md)); the bundle inventory it produced names **none** of the camelCase paths; the only committed file naming `snapshotTimelinesRange` is the **archive** table, whose header says the codes are "as archived, **not** as measured live today" (2020-09-29→2021-03-31). So there was no live probe behind "live" — this pass is the first, and it reproduced the archived codes exactly. **Side-findings:** **`Allow: POST, OPTIONS` on all nine `405`s and on nothing else** — 9 of 24 responses, correlating exactly with the POST-only routes. This is a **scoping clarification** of `docs/09` §4's "no `clcloud.*` response carried `Allow`", not a correction of it: that row was already scoped to `clcloud.*` and to "this host family", so a `carelink.*` response carrying the header does not falsify it — it confirms the observation is **family-specific**, and a reader must not generalise it. (`docs/06:27,28,32` already records `Allow` — and its absence — on other patient routes.) Also a **host-aware CSP** that names **`commoncore-trials.medtronic.com`, a host in no prior note**. **⚠ The pass BREACHED the `>=2 s` delay floor** — 21 of 21 same-host gaps fell below it because a declared `DELAY=2.5` was never actually called; not re-run, because a clean re-run would exceed the 30 cap. Its first report of **min −0.538 s** was measured from `run.log` and **understated the breach**: the body-file mtimes give the true **min +0.092 s / max +0.387 s**, and show **no overlap**. It also added **two** backwards-clock-step occurrences (seq 9→10, seq 20→21), not one. Disclosed in full in the log §1a | [findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md] | #24 |
| D — the 18-country sweep, completed | 2026-10-12 | **Both close conditions met: the sweep is complete AND the contradictions are enumerated.** **118** country codes requested — the offline-derived union of the codes the vendor's own three published config documents enumerate — **117** country documents served, every key given an ABSENT / NULL / VALUED verdict, **33/34/35 keys** by country, **no key outside the 35-key vocabulary**, no report-vocabulary delta. **51 internal contradictions across 10 classes**, the headline being that the recorded two-country `bgUnits` vs `glucoseUnitsDefault` anomaly is **30 of 117** documents (BE reproduces; **CH no longer contradicts**; **IT and ES have drifted into it** since 2026-10-08), so `docs/04` is corrected in place with the original claim left readable. Also: three keys recorded as `null` are **absent** (41 of 117 for `cpMobileAppAvailable`, 115 for `stateCodes`) — `docs/04:377` had been contradicting the repo's own pinned assertion; **`ID` is enumerated by all three configs and refused by the endpoint**; KZ and PR publish a postal regex that rejects the document's own example. **119 of a 130 cap**, GET only, controls first. **Spacing floor 2.575 s with 0 of 118 gaps under the declared 2.5 s and 0 under the `>=2 s` floor** — measured from body-file mtimes, which the kernel sets at write time and which are therefore independent of the harness's own clock (**counting rule: consecutive pairs in `run.log` request order, 119 bodies, 118 gaps**; mtime span 304.9 s equals the harness span, confirming the series is the run's own). The harness `date` series disagrees with it (**1.642 s, 14 gaps under 2.5 s, 8 under 2 s**) because that pass recorded **11 negative request durations**, which is impossible, so those timestamps cannot all be faithful; **no cause asserted**. **Caveat on reuse: git does not preserve mtimes, so this oracle is valid only on the machine that ran the probe** — see [`docs/09`](09-methodology-and-oracles.md) §4. Three defects found in the reader itself are recorded, two of which would have manufactured findings | [findings-log/2026-10-12-area-d-country-sweep/FINDINGS.md] | #22 |
| A — is `carelinkhp` really the clinician portal for every region? | 2026-10-12 | **Negative on the area's premise, and it corrected two published claims.** There is **no `.com` `carelinkhp` variant**: all five `carelinkhp*.minimed.{eu,com}` names outside the baseline are **NXDOMAIN**, including `carelinkhp-prod.minimed.eu` — the only one the corpus had named and never probed. The portal is on **five hosts, two TLDs, two builds**, and the split is **product role** (clinic `pow` vs support `cua`), **not region**: every `.eu`/`.com` pair serves the same build. **Two refutations:** `carelink.medtronic.eu` **is** a portal deployment serving the byte-identical clinic bundle (3,397,615 B, sha256 `2a7fa8e7af519c2b`) — `docs/01:69` and `docs/10` §2 called it a false positive, which was caused by a document-path probe on a host family where **the catch-all *is* the entry document**; and `carelink-support.medtronic.com` serves the **support** build, not "the same document" as `docs/07:24`, `docs/01:68` and SECURITY-FINDINGS §S3 had it. A third correction: `docs/08`'s `sha256 f637c8d0…` is the **entry document**, not `main.759cddab23085086.js` (which is `a054555a0f22176e…`). **20 of a 20 cap**, GET only, controls first per host, 8 DNS lookups recorded outside the cap, measured minimum consecutive same-host gap **2 s over 15 gaps**: all 15 ≥ the repo's 2 s floor, **0 below it**, 11 of 15 ≥ the declared 2.5 s, 4 below it. `run.log` cannot distinguish truncation from a clock step from a post-hoc edit, so **no cause is asserted** for those 4 (`docs/09` §4). Cross-checked with area O's body-mtime oracle, offline and zero-request, over the **10 of 15** gaps whose bodies are committed: **0 corrupt-`t0` signatures, minimum 2.637 s, and all 4 short readings measure ≥ 2.5 s at sub-second resolution** — so no gap in this pass was actually short. That is OBSERVED for this pass only, it is **not re-derivable from a clean clone** (git does not preserve mtimes), and it does **not** answer the open question, which concerns areas B, X and Z. This pass contributes **1 pass / 4 occurrences** to that row's `n`, reconciled by the merge queue, not here | [findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md] | #21 |
| I — Auth0 tenant behavioural differences | 2026-10-12 | **Negative on the difference the area hunted; positive on one it did not name; and it corrected two `kid` strings already published.** The estate is **five** tenants, not four — reconciling "three" (`AUTH-TENANT` §1, a policy axis) against "four" (`docs/11`/`docs/10`, a key-material axis) was part of the pass, and **neither number was an error**: they counted two different sets over the same five hosts, and the union revealed that **`carelink-login.minimed.com` was in nobody's policy comparison** and **`-trials` was in nobody's key set**. **The negative, in its strongest form:** substituting each tenant's own hostname out of its discovery document leaves **one digest across all five** (`sha256:0c0db635f5e9b08b…`, 2640 B) — the same *bytes*, not merely the same fields; **30 field names, 0 absent from any document**, and exactly **12 of 30** differing raw, every one a URL containing that tenant's hostname. That **corrects** `AUTH-TENANT` §1: `registration_endpoint` is **not** a separate difference, it differs only by hostname like the other eleven. **The positive:** `x-ratelimit-limit` is **500 on both `.eu` tenants and 100 on the other three** — 10 observations, 2 per tenant, constant within a tenant, and invisible in byte-identical documents (INFERRED as tenant configuration, on the stated assumption Auth0 treats it as static). **Also:** `registration_endpoint` is advertised by all five and **404 to GET on all five** (`/oidc/register` → 404 `application/json`, 60 B, one digest `f006bbd60894…` across five hosts) — ⚠ **this pass's `registration_endpoint` headline was REFUTED and is RETRACTED**: a verifier showed the endpoint is **live and POST-only**, which a GET-only sweep cannot see, and the pass's own supplementary OPTIONS run then confirmed it on **3 of 5** tenants (`204` + `allow-methods: POST` against a per-tenant `404` + `x-auth0-not-found: 1` control); the trials tenant's key set is fetched for the first time (2 further disjoint kids → **10 keys, 0 shared**, discharging `docs/02` §9's "Unknown"); and **two corpus transcription defects settled against the corpus** — `AUTH-TENANT` §8's `medtronic.com` kid (`…_lLOJ`) is wrong in favour of `RECON-SUBDOMAINS`' (`…_lOOJ`), which **resolves `docs/02` §8's unresolved disagreement against the very spelling it recommended**, and `minimed.com`'s second kid is the live string **minus one `Q`** (a *deletion*, so no second reading existed to compare — invisible to §8's method by construction). **19 of a 20 cap** (17 curl + 2 hurl), **GET only**, plus an owner-authorised **supplementary budget of 14 of which 13 were used** (10 OPTIONS probes + 3 diagnostics) — **32 requests total, no POST anywhere**; controls first per host, **both certainly-absent controls returned 404** (`x-auth0-not-found: 1`, one digest across two hosts) so the oracle held and **no stop condition fired**; measured spacing floor **2.000 s**, which this ledger's **1-second timestamps cannot resolve** against the declared 2.5 s — a lower bound, not a measurement, recorded rather than smoothed over (4th pass in a row). New pins on the trials tenant validated live. Successor: the three remaining advertised endpoints, added under area J **and rewritten on 2026-10-12 to use empty-body OPTIONS rather than GET**, since all three are POST-only by specification and a GET-only successor would have repeated this pass's error three more times | [findings-log/2026-10-12-area-i-auth0-tenant-behaviour/FINDINGS.md] | #23 |
| G — cross-check the three model tables against each other | 2026-10-13 | **Negative: both builds' device tables are identical as data.** The clinic `pow` asset (`main.fb5f8cb7eb60c4d5.js`, 3,397,615 B, sha256 `2a7fa8e7af519c2b`) and the support `cua` asset (`main.759cddab23085086.js`, 3,410,666 B, sha256 `a054555a0f22176e`) were fetched separately and extracted separately, offline: identical code sets (78 table codes + 9 `SKU-*`), identical display-name pairs (76 quoted + 2 unquoted `MMT5100`/`MMT5101` + 9 `SKU-*`), identical whole-file census (80 `MMT-*`, same set), identical module-`90991` `["MMT-8600","MMT-8601"]` array, identical answers on 23 patient-map spot checks — so G's premise is unchanged and the reconciliation stays three-way. **Side-finding:** `MMT-8200`/`8201` ("Guardian™ 4 system") and `MMT-8400`/`8401` ("Simplera™ system") are present in **both** builds' tables, so the patient map is the only compared source lacking them. **6 of a 12 cap**, GET only, controls first per host (fabricated asset → per-build 5518 B fallback; root anchors build digests, both reproducing area A), spacing floor **2.595 s**, 4/4 gaps ≥ 2.5 s | [findings-log/2026-10-13-area-g-device-tables/FINDINGS.md] | #32 |
| J — `login-errors.ts` against the live error surface (addendum: the three advertised Auth0 endpoints) | 2026-10-13 | **One routed, two dangling — uniform across all five tenants, no shadow split.** `/mfa/challenge` answers the preflight `204` + `ACAO: *` + exact `allow-methods: GET, PUT, POST, DELETE, PATCH, OPTIONS` on all five (the path with no probe result in any source was live); `/bc-authorize` and `/oauth/global-token-revocation/connection/Auth0` are unrouted on all five — preflight byte-identical to per-host one-character-different controls (one 10 B digest `0802559db137…` across 15 bodies). POST-only-ness of `/mfa/challenge` is INFERRED from specification, not established — no POST sent, and the six-method list is a second live instance of `docs/09` §4's allow-methods trap. Revocation verdict scoped to the `Auth0` connection name. ⚠ **Correction history preserved:** this addendum was written 2026-10-12 as a GET sweep on area I's then-claim that `registration_endpoint` was absent everywhere; a verifier refuted the premise (the endpoint is live and POST-only) and the addendum was rewritten to empty-body OPTIONS before probing — the original wording is retained in the area-I log, not here. **23 of a 26 cap** (20 curl + 3 live hurl pin-validations), GET + empty-body OPTIONS only, controls first per host, all 5 passed, measured `t_sent` floor **2.395 s** (all gaps ≥ 2 s floor; 2 under the declared 2.5 s and 4 negative durations recorded with no cause asserted). EU cells pinned (exact allow-methods, not contains); counts re-measured 193→199 static, 401→413 execute. Successor: the parent half (bridge `login-errors.ts` taxonomy vs provoked errors) as a new `docs/10` §1 row | [findings-log/2026-10-13-area-j-advertised-endpoints/FINDINGS.md] | #34 |
| H — the `reportFileNamingSupportedPumpModels` list, entry by entry | 2026-10-13 | **Positive with residue: 214 entries classified, 86 rows matched, 128 not.** The list lives in the **patient** public config (`personal.common.core.report.generation.reportFileNamingSupportedPumpModels`, 69-key document, re-derived live) — not HCP-only as the area premise had it. In code: wire code 129 · display name 71 · bare number 10 · placeholder 4; 82 wire codes matched by family, 47 unmatched by prefix group; placeholders 4/4 matched (all INSTINCT values); bare numbers and display names 0 matched; normalization changes nothing. Anomalies: `MMT-9015` ×2, `Precision Xtra® / Xceed™` ×2, one trailing-space entry matching the map's own padding exactly, ten `MMT-`+bare pairs. Correction attached in `docs/05`: `MMT-8200/8201/8400/8401` are in **both** report lists and **neither** family table. **5 of a 6 cap**, GET only; 3 hp-namespace requests voided by a harness header defect and disclosed as wasted — the close rests on the patient document alone | [findings-log/2026-10-13-area-h-report-naming/FINDINGS.md] | #33 |
| V — given that `baseUrlPde` names a dead namespace, does any vendor client follow it? | 2026-10-13 | **Negative, and the reason is sharper than the area expected.** No vendor **web** bundle contains `baseUrlPde` or `/connect/pde` — and no `baseUrl*` key, `discover/android`, `clcloud` or `api/carepartner` is present either, because **no web bundle in the corpus reads the discovery document at all**. ⚠ **corrected 2026-10-13**: the bare `discover` token **is** present — **12 in each portal build**, every one a zxcvbn password-dictionary word at identical bytes, so the portal builds carry **17 dictionary hits each** (12 `discover` + 5 `pde`) and none is a pointer; this row first published `discover` as 0 [findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md §Correction (2026-10-13) §A]; the two `baseUrl` hits in the patient bundle are `this.baseUrl = getBaseCmsUrl()`, a CMS media base. Every `pde` hit is accounted for: **5 per portal build, all zxcvbn password-dictionary substrings** (`dropdead`, `helpdesk`, `herpderp`, `topdevice`, `hampden`); **0 case-sensitive in the patient bundle**, whose 25 insensitive hits are 7 unrelated identifiers. **INFERRED, and stated as the limit not the finding:** the consumer is the *mobile* client the document's own path names (`discover/android/3.6`), so “does a client follow it” stays **unobserved in both directions** and `docs/03` §9a's reading is unchanged. **Positive on the sibling pointer:** the patient bundle **follows** `csr.cumulus.periodic.data.endpoints` — 1 genuine read, `display_message` destructured and **POSTed** with `{patientId, role, username}` — while naming `system.gc.gz.transition.flags`, exporting its selector as `z2` and reading `.z2` **0 times in the file**; all nine of its leaves are 0 hits everywhere. Also: **56 of 69** published config keys appear as quoted literals in the patient bundle (raw-substring counting would have said `captcha` 152 times, not 5); patient `.eu`/`.com` are byte-identical; both portal digests reproduce areas A and G; the patient build and its **211-chunk map reproduce the 2026-10-08 record**, so it has not bumped. **13 of a 24 cap**, GET only, 8 controls first per host, measured `t_sent` floor **2.566 s** (9 gaps, 0 under 2.5 s) cross-checked by kernel body-mtimes at **2.599 s** — ⚠ **the mtime figure is not re-derivable from the committed ledger**, because `results.jsonl`'s `body_mtime_epoch` came from `stat -c%Y` (whole seconds) and git does not preserve mtimes; the `2.599 s` is re-stat'ed from bodies still on disk by `spacing.sh`, so the load-bearing floor is the millisecond `t_sent` series, which reproduces from `results.jsonl` alone. Spans agree to 15 ms and no negative durations were recorded. Successors: dated addenda to **area F** (timeline-host key named by the bundle but not published) and **area K** (the 211 patient chunks are not K's 224 portal chunks) | [findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md] | #42 |
| W — is the per-key projection a complete enumeration path for the 69-key document? | 2026-10-13 | **Negative, and it closes the area: the key sets are identical on EU.** All 69 bulk names probed per-key plus `captcha`'s four flat-name subkeys — **61 VALUED-match**, 5 NULL-404 (every null-valued key), `captcha`/`default.country` 404 via their dedicated routes, **zero names outside the bulk document**. The per-key form is a projection, not an enumeration path — the `docs/04` framing is retired, not extended. **77 of an 84 cap**, GET only, controls first, measured spacing floor **2.574 s** by kernel body-mtimes (0 of 76 gaps under 2.5 s); the harness `date` series shows 3 sub-floor gaps with 3 negative durations, the known corrupt-`t0` class (`docs/09` §4), no cause asserted. **Side-findings:** `personal.common.core.reporting.enabled.countries` does **not** round-trip — its value carries a stray trailing `]` (reproduced byte-identical on re-issue); real-key 404s carry **no `content-type`** while the certainly-absent control carries `text/vnd.a`; the 35 country keys and 69 bulk keys are **disjoint vocabularies**; and the complete 69-name list is committed (`keys.txt`) for the first time. Successor: dated addendum to area E (remaining two deployments) | [findings-log/2026-10-13-area-w-per-key/FINDINGS.md] | #31 |
| M — is Common Crawl's zero on the API surface real, or was it the method? | 2026-10-13 | **Partially refuted, and the correction is to the METHOD.** Re-derived through the **CDX index API** instead of computed byte offsets, across **six named crawls with dates**, **all four controls first**, both absence oracles established behind their own positive controls. **Refuted:** CC holds **24 records for `minimed.eu` across 5 of the 6 crawls** (8 / 6 / 5 / 2 / 3 in 2018-39 / 2020-50 / 2022-40 / 2025-30 / 2026-39, incl. `/ipro/hcp/login.jsf` **200** on `carelink.minimed.eu` @2020-12-02), and **`medtronic.eu` is non-empty in all 6** — against `COMMONCRAWL §1`'s own table recording `eu,medtronic)` = 0 blocks in the two crawls it used. **Confirmed, for a different reason:** **no captured path in any of the six begins `/patient/` or `/connect/`**, and `clcloud.minimed.eu` / `carelinkhp.minimed.eu` hold **zero**, established by *enumerating* the successful domain responses rather than by their own failed host queries. **So "essentially zero coverage of the API surface" stands; "not one record for any `carelink*` host" does not**, and "in either of two crawls" was a budget artefact — `CC-MAIN-2024-42` really is zero (404 `No Captures found`) and the other five are not. **Offset method, corrected at the mechanism:** of the three byte ranges `COMMONCRAWL §1` records, **one reproduces exactly at both ends, one starts exactly on its bound but overshoots its recorded end into `com,medtryck)`**, and one could not be fetched at all (`503 SlowDown` ×2) — the *opposite* defect from the recorded "alphabetical neighbours" one — and **the first pass's ranges are not re-derivable, because the record names no offsets**. **Side-findings:** the API **failed 17 of 61 (28%)** — 502 / 504 / 400 / 503 — so **one query never settles a zero**. ⚠ **CORRECTED 2026-10-13 (verifier round 1): this row originally read "with **0** failures against known-covered hosts". That was false — `seq 50`/`53` asked for a host `seq 42` had proven covered 32.6 s earlier and both failed.** Under the counting rule in `failclass.py` (only a **record-form** query names a host, so classify by what the ledger knew *before* the row was sent) the 17 split **2 covered / 0 absent / 13 indeterminate / 2 n/a**: **a gateway error on a host whose coverage was never established carries no information in either direction and must be re-issued, and coverage is not a shield either.** `index.commoncrawl.org` answered **200** here on 2026-10-13 (128 crawls published), recorded as an observation about *this host at this time* and **not generalised**. **61 of a 64 cap** (60 under the claim, **1** under owner authorisation for the overshoot re-read; **3 recorded as unspent**), GET only, **zero requests to any Medtronic host**, measured same-host floor **2.873 s** by kernel body-mtimes, cross-checked at **2.736 s** from `t_sent` (0 gaps under 2.5 s on either oracle). **No `regression/hurl/` pin** — those suites are vendor surfaces and `AGENTS.md` §11 bars one research pass from widening the gate's budget; the rot-prone half is pinned as `docs/09` §4 traps instead. Successor: dated addendum to area L | [findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md] | #44 |
| E — is the per-key projection identical on `.com` and `-trials`? | 2026-10-13 | **Negative on the key set, and that is the answer: the 69-name vocabulary is deployment-portable.** All 69 names plus `captcha`'s four flat-name subkeys swept on both remaining patient hosts — **69 top-level keys on each, 0 outside the committed EU list, 0 of the EU list missing**, and **0 value mismatches across 123 valued cells** (62 `.com` + 61 trials VALUED-match), so the per-key form is a projection on all three deployments and the `docs/04` framing is retired rather than extended. **What is *not* identical is which keys 404** — and it is downstream of the bulk null set, not the grammar: EU and `.com` share the same five null-valued keys name for name, trials has six, adding `mmm.data.api.url`, `personal.linking.request.interval` (in no `docs/` page) and `personal.third.party.apps`. **Two positive findings area W could not have had.** (1) **The stray-`]` quirk does not reproduce** — `personal.common.core.reporting.enabled.countries` parses cleanly on `.com` (2 countries) and trials (13), matching their bulk subtrees exactly; the defect is EU-only as measured, and *EU-specific* and *length-dependent* are both left standing because nothing observed separates them. (2) **⚠ Area W's 404 content-type split does not hold on trials** — one real-key 404 there carries `application/vnd.nervana`, a value in no prior reading, so the header is three-valued and deployment-dependent and "the control carries `text/vnd.a` and real keys do not" is false on one deployment of three; `docs/04`'s standing "do not discriminate on it" is confirmed and strengthened. **152 of a 170 cap**, GET only, **all 4 controls first per host** reproducing W's shapes exactly (404 `text/vnd.a`; 200 `application/json` 281 B), measured spacing floor **2.020 s** by kernel body-mtimes (0 of 150 gaps under the ≥2 s floor); the harness `date` series shows 4 sub-floor gaps and **13 negative durations**, the known corrupt-`t0` class, no cause asserted. Successor: dated addendum to area F — the two dedicated-route escapes were read on `.eu` only | [findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md] | #41 |
| Q — the `appVersion` body gate — a second version axis our docs do not describe | 2026-10-13 | **Closed on the area's second close condition: recorded as community-reported-and-unverifiable, with the reason.** The two axes are now documented together in `docs/03` §3a. **Mechanism confirmed in code**: `appVersion` is a **body** field, at `CarlosJPV/carelink-cumulus-bridge src/carelink/cumulus.ts:146` @ `0180b89` (SOURCE-OBSERVED). **Boundary values not confirmed and not confirmable here** — a body field needs a POST, `AGENTS.md` §11 permits no vendor POST beyond the two already-pinned public-`client_id` requests, and the author's probe *outputs* are gitignored (`.gitignore:12` resolves exactly), so **no pin is possible either** — the claim is unpinned by necessity, loudly. **The finding the area did not ask for:** for the `X.Y` forms the discovery axis has been probed at, the two constraints **intersect in exactly `{3.7, 3.8}`** (`3.7.0`/`3.8.0` clear the body gate but are **unobserved** on the discovery path — no `X.Y.Z` cell was ever probed), and the readable client feeds **one constant** (`'3.8'`, `cumulus.ts:31`) into **both** axes — correct only because `3.8` is in that window, so raising it to `3.9` satisfies the body gate forever and breaks the discovery axis silently. **Zero drift**: all four subject files byte-identical between pinned commit and branch head (blob SHAs), so every `file:line` resolves identically in either revision. **⚠ Correction:** the area's *"corroborated by a xDrip maintainer on PR #4711"* is **withdrawn** — that PR's three comments are the table (**by the same author as the README that repeats it**), a question, and an approval that does not retest it, so it is **one source stated twice**. **21 requests against a cap of 20** — the overrun is **one** request, because `probe-followup.sh` sets `SEQ=18` rather than reading the ledger and was run twice, re-issuing request 19; **no ledger row was deleted to hide it**. **The cap was restated to 21 by owner authorisation on 2026-10-13, after the pass**, so the log's accounting line reads `21 of a 21 cap` with the declared 20 kept readable in its `## Correction (2026-10-13)`. 0 requests to any Medtronic host, by design. Spacing floor **2.765 s** (kernel body-mtime oracle, 18 measurable gaps, 0 under 2.5 s; harness series disagrees at 2.014 s with 3 impossible negative durations — no cause asserted). **Not verified:** the xDrip `CareLinkClient.java:664` half — the file is not at the package root, and that is **this pass's path-reconstruction error**, not a broken citation. Successor: dated addendum to area S (what *independently corroborated* requires) | [findings-log/2026-10-13-area-q-appversion-axis/FINDINGS.md] | #43 |
---

> **Consumer note.** Findings here are consumed by
> [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge), which
> feeds this repo's regression suite, which the bridge runs before a release.
> If something here moves a value the bridge pins, it reaches their release
> checklist — file it here with the `downstream-bridge` label and name
> the constant. Bridge bugs (login, upload, crash) belong in
> [their bug tracker](https://github.com/NovaLux12/carelink-bridge/issues/new?template=bug.yml).
