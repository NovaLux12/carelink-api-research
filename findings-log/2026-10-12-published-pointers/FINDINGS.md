# Area T — does any published document point a client at `csr/v2`, or is it a namespace no config can address?

**Claimed in #10. Run 2026-10-12. Area closed.**

- **Method:** GET only. No POST, no token exchange, no authentication, no `Cookie`/`Authorization`/`x-api-key`,
  no port scanning, no DNS brute force, no wordlist, no new host, no dev/stage host.
- **Total 10 of a 12 cap.** Ten document reads; the two spares were unused. No response
  failed to parse, so nothing was re-requested.
- **≥2.5 s `sleep` between requests to the same host** in the harness (Area C's spacing).
  **Measured floor across the pass: 2.0 s**, not 2.5 s — 8 of 30 inter-request gaps are
  2 s, because requests land on two different CloudFront PoPs (the `via:` header differs
  between `com-05` and `com-06`) whose clocks are not synchronised, so `Date`-header
  arithmetic across a host change is not a valid spacing measurement. `docs/09` §1 records
  the in-harness floor as **≥2 s** and quotes 2.5 s only for the gateway sweep; both are
  satisfied, and the honest floor for this pass is **≥2 s observed**.
- **Harness:** `probe.sh`. Machine log `run.log`, one line per request with status,
  bytes, content-type and a JSON-parse verdict in `requests.tsv`.
- Every candidate is a document already named in `docs/` on disk. Nothing was invented.

## ⚠ Raw captures are deliberately NOT committed

**Read this before re-running anything.** The 69-key public config is
unauthenticated and carries credential-shaped values: a reCAPTCHA site key, and an
`x-api-key` under each of the two `nutrino.cc.*` service keys. Committing `docs/*.json`
would put credentials in the diff. The pass dir therefore ships a `.gitignore` covering
`docs/` and the unscrubbed enumeration, and what is committed instead is:

| artefact | what it is |
|---|---|
| `probe.sh` | what was requested, one line per request, no bodies |
| `requests.tsv` | method / host / path / status / bytes / content-type / parse verdict |
| `enumerate.py` | the enumeration — re-runnable, so the searched key list is auditable without the raw bytes |
| `enumeration-scrubbed.txt` | the full enumeration with sensitive values replaced by typed placeholders, self-checked against `scripts/scrub-patterns.txt` |
| `credential-shapes.py` / `.txt` | key paths, lengths and character-class shapes only |
| `scrub.py` | the redactor; reads its patterns from `scripts/scrub-patterns.txt` |

`scrub.py` **reads** the credential patterns from `scripts/scrub-patterns.txt` rather
than embedding them, because a second copy of a credential pattern is not an exception
to the scrub rule — it is a leak. It also has no code path that can compare two redacted
values, because answering that question *is* the held-back disclosure (§5).

---

## 1. The answer: YES, twice, on all three deployments

**OBSERVED** — 2026-10-12, unauthenticated, `GET /patient/v2/configuration/public`.

Area T was opened to test the assumption that "`csr/v2` is an internal or deprecated
route rather than a client-addressable one — inferred from the *absence* of a recorded
base URL". **The assumption is wrong.** The public config names `csr/v2` in **two
independent keys**, on **all three deployments**:

| key | value (EU host) |
|---|---|
| `system.gc.gz.transition.flags.displayMessage.csrDisplayMessageUrl` | `https://clcloud.minimed.eu/connect/csr/v2/display/message` |
| `csr.cumulus.periodic.data.endpoints.display_message` | `https://clcloud.minimed.eu/connect/csr/v2/display/message` |

Both resolve to the **same URL**, and the host is always the deployment's own sibling
`clcloud` host — EU → `clcloud.minimed.eu`, US → `clcloud.minimed.com`,
trials → `clcloud-trials.minimed.com`. So `csr/v2` is **not** an unreachable namespace.
It is a **published, config-addressable** route, and it is the very route Areas C and N
proved live and POST-only three days ago.

`baseUrlCsr` does **not** exist — zero hits across all ten documents (§4) — but the
route is reachable without it, through the public config instead of the discovery
document. **"No key of that name" was never the question; "can a config-driven client
address it" was, and the answer is yes.**

### The premise was already refuted on disk, before this pass sent a request

**This is the part worth reading twice.** The area's premise — that no
`/connect/csr/v2` string is recorded anywhere in the repo — was **false before the first
request went out**:

> `csr.cumulus.periodic.data.endpoints.display_message` → `https://clcloud.minimed.eu/connect/csr/v2/display/message`
> — **NEW Cumulus namespace: `csr/v2`**
> [source: `findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md` §1, line 99]

The 2026-10-08 archive pass recorded the key **and its value** from a 2026-02-04
capture, flagged it as new, and it never reached `docs/`. `docs/04` lists the key under
"disclosed service hosts" **with no value**; `docs/11` area T then asserted a negative
that its own repository contradicted.

That is [`AGENTS.md`](../../AGENTS.md) §6 item 5 — derived prose contradicting its
source table — except the derived prose is the *priority page*, and the source table is
a findings log nobody re-read before writing a successor area. Grepping the repo's own
logs before probing is what caught it here, and it cost nothing.

## 2. Every published pointer into the cumulus plane, enumerated

**OBSERVED** unless marked. Four distinct discovery documents (all four were read; two
are byte-identical) and the 69-key config on three deployments.

### 2a. `baseUrl*` keys — every one, every region, every document

| document | bytes | sha256 (12) | regions | `baseUrlPde` |
|---|---|---|---|---|
| `clcloud.minimed.eu` `v13/discover/android/3.6` | 20256 | `f84886265667` | US, EU, CLINICAL | `…/connect/pde/v3` ×3 |
| `clcloud.minimed.com` `v13/discover/android/3.6` | 20256 | `f84886265667` | US, EU, CLINICAL | `…/connect/pde/v3` ×3 |
| `clcloud.minimed.com` `v11/discover/android/3.6` (legacy) | 18105 | `2103b7e850c4` | US, EU | `…/connect/pde/v1` ×2 |
| `clcloud-trials.minimed.com` `v6/discover/android/3.6` (legacy) | 10053 | `1aab9bb1e721` | US, EU | `…/connect/pde/v1` ×2 |

All documents are `200 application/json`, `content-encoding: br`, unauthenticated.
**Confirmations of existing claims:** the two `v13` documents are byte-identical, and
their sha256/md5 match [`docs/03`](../../docs/03-discovery-and-versions.md) §1 exactly
(`f8488626…`, md5 `403220ced1a7837372b777fa97ecbb2b`) — re-derived, not re-read.

Per document, the `baseUrl*` key set is `baseUrlAem`, `baseUrlCareLink`,
`baseUrlCumulus`, `baseUrlCms`, `baseUrlPde` — but **not uniformly present**:
`baseUrlCms` is absent from both legacy documents, and `baseUrlAem` is absent from the
trials `v6` document as well, so that document carries **three**, not five. The
distinct `baseUrlCareLink` values are `/api/carepartner/v2` (v13) and `/api/carepartner/v1`
(legacy); `baseUrlCumulus` is `/connect/carepartner/v13` (v13) and `/connect/carepartner/v2`
(legacy). Full per-region listing in `enumeration-scrubbed.txt` §PART 1.

### 2b. The reachability table — the actual finding

Combining §2a with the route verdicts already on disk:

| published pointer | resolves to | verdict | evidence |
|---|---|---|---|
| `baseUrlCumulus` | `/connect/carepartner/v13` | **reachable** | live, GET 401 + `x-ca-err: 990` |
| `csrDisplayMessageUrl` / `csr.cumulus…display_message` | `/connect/csr/v2/display/message` | **reachable** | live, POST-only, 3 hosts (Area C/N) |
| `blePereodicDataEndpoint` | `/connect/carepartner/v6/display/message` | **reachable** | live, POST-only, 3 hosts ([docs/03](../../docs/03-discovery-and-versions.md) §8) |
| `retina.endpoints.config.*.target_url` + `base_uri` | `/connect/retina/v1/personalWebView` | reachable (host family recorded) | [docs/01](../../docs/01-hosts-and-estate.md) |
| **`baseUrlPde`** | **`/connect/pde/v3`** | **UNREACHABLE** | no GET or OPTIONS route for either recorded path under it, 3 hosts (Area C + this session's Area U). The bare prefix was not itself requested |

**Of the five `baseUrl*` keys, the two that point into `/connect/` are `baseUrlCumulus`
(reachable) and `baseUrlPde` (unroutable) — so exactly one of that set is unroutable,
and it is the PDE one.** The route nobody had recorded until 2026-10-11 is published
and reachable; the route the vendor has published in every discovery document since at
least the archive window is dead on every host it is published on.

**Scope, stated because the corpus is bigger than the probe.** The other endpoint-shaped
values in the config were **enumerated, not probed** — `baseUrlAem`, `baseUrlCms`,
`mmm.data.api.url`, `personal.patient.timeline.config.host`,
`nutrino.cc.{broker,metadata}.service.config.host`, `praas.uri.path.reports.ping`,
`retina.*.target_url`, `csr.crm.settings.base.uri` and more (all in
`enumeration-scrubbed.txt` §PART 2). Their reachability is therefore **unassessed**, not
"reachable"; only `baseUrlCumulus`, `baseUrlPde` and the three display-message pointers
have a verdict. "The only unroutable published base URL" is a statement about the
probed subset, and would need those ten probed before it could be a statement about the
whole corpus.

**INFERRED** (stated as such, it is the one claim here resting on reasoning): that this
is a **vendor defect** rather than a client that is expected to ignore `baseUrlPde`.
The reasoning and its assumption: a discovery document that publishes a base URL is
meant to be used — the same document's `baseUrlCumulus` is load-bearing for the
consumer of this repo — so a consistently dead `baseUrlPde` is more consistent with a
retired service left in the document than with a deliberate "ignore this key" contract.
**Nothing observed here settles it.** A `baseUrlPde` call cannot even be attempted,
because the namespace 403s before any application code runs, so no client-side evidence
about intent exists to be gathered. Both readings are given rather than one picked.

### 2c. `system.gc.gz.transition.flags` — a feature-flag subtree in no prior note

**OBSERVED.** A six-key subtree that **no file in this repository recorded before this
pass**, identical on all three deployments:

| key | value (3 of 3) |
|---|---|
| `displayMessage.useCumulusUrls` | **`true`** |
| `displayMessage.personalDisplayMessageUrl` | `…/patient/connect/data` |
| `displayMessage.csrDisplayMessageUrl` | **`…/connect/csr/v2/display/message`** |
| `displayMessage.carepartnerDisplayMessageUrl` | `…/patient/m2m/connect/data/gc/patients/{patientUsername}` |
| `pullGMInfoFromCumulus` | `true` |
| `pullSMSHistoryFromCumulus` | `true` |
| `sendDiagnosticLogsToCumulus` | `true` |
| `sendPeriodicToCumulus` | `true` |
| `sendSMSFromCumulus` | `true` |

This is the most consequential thing the pass found, and it is the mechanism behind §1:
`csrDisplayMessageUrl` is not a stray key. It is one arm of a **three-way dispatch
table** — `personal` / `csr` / `carepartner` — the client selects from, and
`useCumulusUrls` is the master switch that is already **`true`** everywhere. So the
vendor's own client is *instructed by public config* to address `csr/v2`, on every
deployment, today.

The five sibling booleans mean the vendor has already moved **five capabilities** onto
the Cumulus plane — GM info, SMS history, diagnostic logs, **periodic data**, and SMS
sending. `sendPeriodicToCumulus` is what makes `csr.cumulus.periodic.data.endpoints`
necessary in the first place; the two facts corroborate each other.

**INFERRED:** that `gc` → `gz` in the key name is a service migration and that these
booleans are its completion switches. The key name and the boolean names support it;
no document on any surface states it. The *values* are OBSERVED; the reading is not.

### 2d. A second route path in the `csr/v2` namespace, on an internal host

**OBSERVED** in the config: `csr.cumulus.periodic.data.endpoints.periodic_packet`
resolves to an **AWS VPC-endpoint service name** carrying
`/dev/connect/csr/v2/periodic/packet`. Two things follow:

1. **A path in the `csr/v2` namespace that is not `display/message`** — the namespace
   has at least two members, so "the `csr/v2` route" is already an undercount. The
   archive pass recorded this same key on 2026-10-08; what is new here is that it is
   **live in today's document on all three deployments**, and that the `/dev/` stage
   prefix is published.
2. It is an **internal** service name (VPC endpoint, not a public hostname). Recorded,
   **not probed** — consistent with
   [`docs/04`](../../docs/04-configuration.md), which already treats this endpoint as
   internal and unreachable. A VPC endpoint identifier is infrastructure, not a URL, and
   the 2026-10-08 archive pass flagged it as "an infrastructure-identifier disclosure" and
   redacted it by hand as `vpce-<eu-id>`.

> **⚠ This sentence was false in the first draft of this file, and is corrected here
> rather than quietly fixed.** It originally read "the endpoint ID is redacted here and in
> the repo" — while three live identifiers sat in this pass's own committed
> `enumeration-scrubbed.txt`, because the redactor's VPC pattern assumed a 16-hex /
> 9-alphanumeric shape where the real identifiers are **17 / 8**. It matched nothing, and
> the self-check missed that because it only covered the patterns read from
> `scripts/scrub-patterns.txt`, never the local extras. Fixed by promoting the pattern
> into `scripts/scrub-patterns.txt` (where the gate and the drift sweep also see it),
> deleting the local extras, and adding an output-side residue tripwire — proven by
> removing the pattern and confirming the scrubber refuses to report success. A redaction
> layer that reports success while doing nothing is the failure this repo exists to catch,
> and this pass wrote one.

### 2e. `retina.endpoints.config` — the csr plane carries an endpoint the personal plane does not

**OBSERVED**, 3 of 3 deployments. `retina.endpoints.config` is a two-plane object:

| plane | subkeys |
|---|---|
| `personal` | `target_url`, `dashboard.base_uri` = `/connect/retina/v1/personalWebView` |
| `csr` | `target_url`, `dashboard.base_uri` = `/connect/retina/v1/personalWebView`, **plus `transfer_settings.base_uri` = `/connect/retina/v1/settings/audit`** |

`/connect/retina/v1/settings/audit` is a **path in no prior note**.
[`docs/01`](../../docs/01-hosts-and-estate.md) records `/connect/retina/v1/*` as a family
only. **Recorded here, unprobed** — `retina` is a runtime-composed service (its host is
assembled from three config fields; the static host is in no artefact), so a probe would
mean composing a URL the vendor never publishes whole.

## 3. Corrections to `docs/04-configuration.md`

Two corrections, both from direct observation of today's document. **The original
statements are kept visible above each correction** — never deleted.

### 3a. `personal.data.csv.export.enable` is an object, not a boolean

**Corrected 2026-10-12.** `docs/04`'s regional table records this key as a scalar per
deployment (`true` / `true` / `false`). **It is an object keyed by plane**, and the
scalar reading silently hides half the value:

| deployment | `personal` | `csr` |
|---|---|---|
| EU | `{aggregatedData: true, rawData: false}` | `{aggregatedData: true, rawData: false}` |
| US | `{aggregatedData: true, rawData: false}` | `{aggregatedData: true, rawData: false}` |
| trials | `{aggregatedData: false, rawData: false}` | `{aggregatedData: true, **rawData: true**}` |

Two consequences. First, a scalar reader misses `rawData` and the entire `csr` plane —
and **trials `csr.rawData` is `true` where every `personal` value is `false`**, so the
CSV-export capability differs by plane in a way the scalar reading cannot express.
Second, this is the *same* silent-failure class `docs/04` already documents for the
per-key projection's string booleans ("a `resp.value === false` check silently never
fires") — but in the **bulk** document this time, where a `=== true` check against an
object never fires either.

The old scalars happen to agree with `personal.aggregatedData` on all three deployments,
which is why the error survived: the note was right about the numbers and wrong about
the type.

### 3b. The document is 68 flat dotted keys and exactly one nested object

**New, and a parsing trap.** `docs/04` describes the document as "69 **top-level**
keys". True — but a consumer cannot assume a uniform shape:

- **68 of 69** are *literal top-level key names that contain dots*, e.g.
  `personal.device.family.to.model.mapping`,
  `system.gc.gz.transition.flags`, `outages.nextupdateat`.
- **Exactly 1** — `captcha` — has **no dot in its key**. That is the whole of its
  distinction: it is the only key whose *name* is a bare segment. Its shape is
  `{enabled, key, testKey, type}`.

> **⚠ Correction, 2026-10-12 review round.** A first draft of this section said
> `captcha` was "the only genuinely nested object". **That was false, and it was
> contradicted by this pass's own data 60 lines above** — `system.gc.gz.transition.flags`,
> `retina.endpoints.config`, `csr.cumulus.periodic.data.endpoints` and
> `personal.data.csv.export.enable` are all object-valued, and this file calls each of
> them a subtree. **28 of the 69 keys hold objects on EU and US, 30 on trials**
> (the remainder are scalars and arrays). The dotless *name* is the real and only
> distinction; "nested" is about a value's type and applies to 28–30 keys, not one.
> This is `AGENTS.md` §6 item 5 — derived prose contradicting its own source table —
> committed by the same pass that congratulated itself for catching one in `docs/11`.

So `docs/04`'s flat key names `captcha.key` and `captcha.testKey` are **not** top-level
keys; they are subkeys of `captcha`. A walker that splits every key on `.` and does a
dotted lookup (which is precisely the bug in
[`docs/09`](../../docs/09-methodology-and-oracles.md) §5 item 3) will miss `captcha`
entirely, and will find `outages.nextupdateat` as a literal while trying the same trick
on `captcha`. Both shapes are in one document.

Also corrected in passing, by observation rather than by note: `outages.nextupdateat`
**is** populated on trials only (`null` on EU and US) — `docs/04` states this correctly,
and a first reading of this pass appeared to contradict it. It does not. Recorded here
because the near-miss is the kind of correction that otherwise gets written up as a
correction of a correct claim.

## 4. The negative, recorded so it is auditable

The searched set, so the negative can be re-derived rather than believed:

- **10 documents**: 4 discovery (2 distinct byte-strings) + 3 public configs + 3 country
  documents.
- **Every `baseUrl*` key** in all four discovery documents: **44** host×region×key
  combinations — `baseUrlPde` in 10 of them, `baseUrlCareLink` 10, `baseUrlCumulus` 10,
  `baseUrlAem` 8, `baseUrlCms` 6 — enumerated in `enumeration-scrubbed.txt` §PART 1.
  **⚠ Corrected 2026-10-12 review round:** the first draft said 22, which is the
  no-route body count of the *sibling* pass and not this quantity. The counting rule
  is: one combination per (document, CP region, `baseUrl*` key) triple that exists.
- **Every leaf** of all three 69-key configs whose value matches `^https?://` or contains
  `/connect/` — enumerated in §PART 2.
- **Every `csr*`-prefixed top-level key** on all three deployments: 4 each
  (`csr.application.browser.check.configuration`, `csr.control.codes.settings`,
  `csr.crm.settings`, `csr.cumulus.periodic.data.endpoints`) — the second is already
  pinned by the regression suite, and the fourth is §1.
- **Every leaf** of all three country documents.

| needle | hits |
|---|---|
| `baseUrlCsr` | **0** in all 10 documents |
| `/connect/v2` (bare pre-carepartner) | **0** in all 10 documents |
| `csr/v2` | 3 each in the three configs, **0** in any discovery document |

So: **no published document names the bare `/connect/v2`** — the other POST-only route
Area N confirmed. Unlike `csr/v2`, the bare route remains genuinely unaddressable by
config. That asymmetry is the one durable negative here.

## 5. Credential-shaped values — structure only, comparison held

**The public config publishes credential-shaped values.** Recorded structurally, with
**no value printed, hashed, or compared**, per the hold-back in
[`docs/04`](../../docs/04-configuration.md) (`nutrino.cc.*`):

| key | EU | US | trials |
|---|---|---|---|
| `nutrino.cc.broker.service.config.security_headers.x-api-key` | 17 chars, non-alphanumeric (`%#…`) | **40 chars, alphanumeric** | **40 chars, alphanumeric** |
| `nutrino.cc.metadata.service.config.security_headers.x-api-key` | 17 chars, non-alphanumeric | **40 chars, alphanumeric** | **40 chars, alphanumeric** |
| `captcha.key` (reCAPTCHA **site** key) | 40 chars | 40 chars | 40 chars |
| `captcha.testKey` | **`""` — empty string** | **`""`** | **`""`** |
| `personal.mixpanel.analytics.settings.token` | 44 chars | 44 chars | **`""` — empty** |

`docs/04` already publishes the EU placeholder ("17 characters, not a credential") and
already flags the site key as public by design. **What is new and structural:** the two
`nutrino.cc.*` keys carry a **40-character alphanumeric** value on the other two
deployments, matching the credential class this repo's own gate scrubs by prefix — so
the EU placeholder is not merely *different*, it is the **only** deployment where the
value is not credential-shaped.

**The cross-deployment comparison stays held.** Whether those two 40-character values are
equal to each other is not tested, not hashed and not inferred here:
`credential-shapes.py` compares **lengths only**. It does match each value against the
repo's known *credential classes* to label which class a value belongs to — a
classification, not a comparison between deployments. This is the hold-back
`docs/04` asks for, kept intact by a pass that saw the values and chose not to publish
them.

New and minor: **`captcha.testKey` is an empty string on all three** — a published key
that exists and carries nothing. Worth recording because a client that switches on
"testKey is present" rather than "testKey is non-empty" would enable test mode.

## 6. Two smaller structural observations

- **`personal.third.party.apps` is an array with 4 entries on EU, 1 on US, and `null` on
  trials.** `docs/04` records the value as a single string per deployment
  (`DS_EMEA_1_GLOOKOXT` / `DS_AMERICANS`); the live shape is an array of objects. Same
  class of correction as §3a — a scalar reading of an array. **The two planes' entries
  are not even the same shape**: EU entries carry 7 subkeys (`appName`, `audience`,
  `auth0ClientId`, `consentType`, `customFormFields`, `key`, `mediaKey`) while the single
  US entry carries those **plus `consentDate` and `expiresInDays`** — 9. A client reading
  this key positionally, or requiring `consentDate`, sees it on one deployment only. The archive pass already recorded four
  integrations and three new Auth0 clients on 2026-10-08
  ([`ARCHIVE-URLS.md`](../probe-2026-10-08/recon/ARCHIVE-URLS.md) §1); what is new is that
  **US has one and trials has none**.
- **`personal.application.browser.check.configuration` and
  `csr.application.browser.check.configuration` are near-twins that are not identical** —
  same `resolution` block (`800x600`), different elsewhere, on all three deployments.
  This is the same `personal.*` / `csr.*` plane split as §2e and `csr.control.codes` /
  `cua.control.codes`, and it means the two browser-support matrices can drift
  independently. Recorded as an observation; the divergence point is not identified here.

## 7. What this pass does not settle

- **Whether the vendor's clients actually call `csr/v2`.** §2c shows they are
  *instructed* to; that a shipped client follows the instruction is not observable from
  outside without the app artefact (area P). Recorded as the successor, not claimed here.
- **Whether `baseUrlPde` being dead is a vendor defect or an intentional ignore.** Given
  as two readings in §2b.
- **`/connect/retina/v1/settings/audit`** and the VPC-endpoint periodic packet route are
  **recorded, not probed** — internal or runtime-composed hosts.
- **Whether any of this returns data.** Token-gated; stays in
  [`docs/10-open-questions.md`](../../docs/10-open-questions.md) §1.
- The legacy discovery documents' `baseUrlPde = …/pde/v1` rows rest on the *route* being
  dead everywhere (§2 of the sibling pass) plus the *document* being read here. The join
  is stated, not re-probed: `pde/v1/display/message` is dead on all three hosts, and the
  documents publishing that base URL are these four.