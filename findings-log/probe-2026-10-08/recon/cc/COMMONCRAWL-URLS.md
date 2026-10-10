# COMMONCRAWL-URLS.md — Common Crawl + `*.medtronic.*` archive record

**Date:** 2026-10-09 · **Subagent pass:** passive archive-only recon
**Closes two gaps** left open by `recon/ARCHIVE-URLS.md`: (a) "no Common Crawl
sweep", (b) "no `*.medtronic.{eu,com}` coverage at all" (its §8.3).

**Requests to Medtronic/MiniMed infrastructure: ZERO.** No DNS, no TLS, no HTTP to
any `*.minimed.*`, `*.medtronic.*`, `*.medtronic-diabetes.*` or `*.carelink*`
host. Every request went to `data.commoncrawl.org` or `web.archive.org`, enforced
mechanically by `q.sh` / `qr.sh` (host allowlist + vendor denylist + counter).

**File ownership:** this pass owns `recon/cc/`. It did not touch `recon/cdx/`,
`recon/*.md`, or any git repo/worktree. No credentials were used, requested or
written.

---

## 0. Request budget

| item | count |
|---|---|
| **Total archive HTTP requests, this directory** | **26** (cap **45**) |
| of which spent by the earlier partial pass in this dir (#1–#16) | 16 |
| of which spent by this pass (#17–#26) | 10 |
| Requests to vendor infrastructure | **0** |
| Credentials used / written | **0** |

Full log with exact URLs and byte ranges: `request-log.tsv` (26 rows).
Counter: `request-count.txt`. Rate spacing ≥2 s enforced in `q.sh` / `qr.sh`.

**One request was wasted and is logged as such (#18).** The `Range:` header was
passed through an unquoted shell variable, so curl saw two URLs, streamed the
whole 842 MB `cdx-00101.gz` into the log file instead of the output file, and the
run was killed. `request-log.tsv` was repaired to its 17 valid rows and an
explicit row 18 was added recording the failure. It cost bandwidth, not budget.

### The Common Crawl index API is unreachable from here

`https://index.commoncrawl.org/collinfo.json` — **request #1 (earlier pass) and
#17 (re-test) both failed with `curl (56) OpenSSL SSL_read: unexpected eof while
reading`**, and the plain-`http` variant (#3) returned `curl (52) Empty reply from
server`. `data.commoncrawl.org` over the identical TLS path works fine (11
successful responses). So this is a **host-level reachability failure on
`index.commoncrawl.org`**, not rate limiting and not a transient error. **No
guesswork has been substituted for it.**

**Consequence:** every Common Crawl result below comes from the
`data.commoncrawl.org` bulk path instead — `cluster.idx` byte-offset lookup
followed by ranged `cdx-NNNNN.gz` fetches. Method and exact byte ranges are in
§1. This is *more* precise than the index API (it gives exact, complete ranges)
but it caps coverage to **two crawls** rather than all ~100.

---

## 1. Method — how the Common Crawl sweep was done without the index API

1. `cluster.idx` for two crawls was already on disk from the earlier partial pass:
   `CC-MAIN-2026-39` (104.7 MB, crawl 2026-09-04 → 2026-09-17) and
   `CC-MAIN-2024-42` (121.4 MB, crawl 2024-10-03 → 2024-10-16).
2. `locate.py` binary-searches `cluster.idx` (TSV: `key␣ts⇥shard⇥offset⇥length⇥lineno`)
   for the byte range covering a SURT prefix. **Costs zero requests** — it is a
   local file. This is the step the earlier pass got wrong.
3. `qr.sh` fetches exactly that byte range from `cdx-NNNNN.gz` (HTTP 206) and
   `gzip -dc` reassembles the concatenated gzip members.

Ranges computed locally (`ranges39.txt`, `ranges42.txt`):

| prefix | crawl | CDX shard | bytes | records recovered |
|---|---|---|---|---|
| `com,medtronic)` … `com,medtronicdiabetes,origin)` | 2026-39 | `cdx-00101.gz` | 45 560 954–47 031 753 | **15 000** |
| `com,minimed)` … `com,minimicroled)` | 2026-39 | `cdx-00102.gz` | 741 698 501–742 330 673 | **6 000** |
| `com,medtronic)` … `com,medtronic,wwwp)` | 2024-42 | `cdx-00097.gz` | 26 751 110–27 650 507 | **9 000** |

**The earlier pass's ranged fetches (#7–#15) all missed.** Their computed offsets
landed on alphabetical *neighbours* — `com,medtravi)`, `eu,medstor)`,
`eu,minifootball)`, `com,minimedesignerstudio)` — i.e. the offsets were wrong, and
because each was truncated at 3 000 lines the target records were never reached.
`raw-*.cdx` / `raw24-*.cdx` on disk are therefore **misleading artefacts and should
not be read as results**. The corrected fetches are `cc39-com-medtronic.cdx`,
`cc39-com-minimed.cdx`, `cc24-com-medtronic.cdx`.

### Coverage established by pure local index inspection (0 requests)

Grepping the two `cluster.idx` files for SURT prefixes is definitive, because
`cluster.idx` contains one line per block and every URL belongs to a block:

| SURT prefix | CC-MAIN-2026-39 | CC-MAIN-2024-42 |
|---|---|---|
| `eu,minimed)` | **0 blocks** | **0 blocks** |
| `com,minimed)` | 1 block (6 000 recs, all `www`/apex marketing) | **0 blocks** |
| `eu,medtronic)` | **0 blocks** | **0 blocks** |
| `com,medtronic)` | 4 blocks (+ `com,medtronicdiabetes,origin`) | 2 blocks (+ 6 `com,medtronic,wwwp`) |

> **Headline negative, and the single most useful thing Common Crawl told us:**
> **Common Crawl has essentially zero coverage of the MiniMed API surface in
> either crawl.** Not one record for `carelink.minimed.{eu,com}`,
> `clcloud.minimed.{eu,com}`, `carelinkhp.minimed.eu`, `carelink-login.*`,
> `status.minimed.com`, or any `*.minimed.eu` name at all. What it *does* have for
> `com,minimed)` is 95 records on the **marketing site** (`minimed.com/<locale>/…`,
> `robots.txt`, `/en-us/virtual-pump`, `/en-us/us-sunshine-act`). And it has
> **zero `*.eu`** for either registrable domain.
>
> So Common Crawl is **not** a substitute for the Wayback pass on the API surface —
> which is the opposite of what the brief expected. Its unique value turned out to
> be elsewhere (§3, the `medtronic-diabetes*` domain family).

---

## 2. Queries issued by this pass (#17–#26)

| # | label | target | result |
|---|---|---|---|
| 17 | `cc-index-api-test` | `index.commoncrawl.org/collinfo.json` | **000 — host unreachable** |
| 19 | `cc39-com-medtronic` | CC 2026-39 CDX, `com,medtronic*` | 206, 1.47 MB, **15 000 rows** |
| 20 | `cc39-com-minimed` | CC 2026-39 CDX, `com,minimed*` | 206, 632 KB, **6 000 rows** |
| 21 | `cc24-com-medtronic` | CC 2024-42 CDX, `com,medtronic*` | 206, 899 KB, **9 000 rows** |
| 22 | `wb-eu-medtronic-filtered` | Wayback `medtronic.eu` domain, diabetes/config filter | 200, **1 630 rows, 25 hosts** |
| 23 | `wb-com-medtronic-nonwww` | Wayback `medtronic.com` domain, **excluding `www`**, API/config filter | 200, **3 000 rows (hit limit), 52 hosts** |
| 24 | `wb-com-auth-mag` | Wayback `medtronic.com`, `commoncore\|carelink-login\|mmcl\|mdtlogin\|carelink-content\|connect.` | 200, **3 000 rows (hit limit)** |
| 25 | `wb-com-patient-v2` | Wayback `medtronic.com` (non-www), `/patient/\|configuration/public\|/configs/\|\.json$` | 200, **2 000 rows (hit limit)** |
| 26 | `wb-eu-patient-v2` | Wayback `medtronic.eu` (non-www), same filter | 200, **27 rows** |

Query #16 (the earlier pass) covered `medtronic.com` *including* `www` and hit
its 3 000-row limit after only `www.medtronic.com` + `carelink.medtronic.com` —
which is why the `.com` non-`www` space had never been reached. Query #23 adds an
explicit `filter=!original:^https?://(www\.)?medtronic\.com` negation to get past
it. That is the fix for ARCHIVE-URLS §8.1.

**Normalised families recovered:** 7 674 total across #22–#26; **4 382**
API/config-shaped; **966** after removing the `…/API/API/API/…` SPA-fallback
recursion artefact that the Wayback crawler produced against `connect.medtronic.com`
(see §7). **117 distinct hosts.**

---

## 3. NEW — the `medtronic-diabetes*` domain family (Common Crawl only)

**Nothing in `PROBE-FINDINGS.md`, `ARCHIVE-URLS.md`, `PUBLIC-CONFIG-FINDINGS.md`
or `recon/known-names.json` mentions any of these.** They are a separate
registrable-domain cluster from both `minimed.*` and `medtronic.com`, and they are
exactly the kind of thing a `*.minimed.*` sweep can never see.

### 3a. New registrable domains (10)

| domain | CC records | span | what it is |
|---|---|---|---|
| **`medtronic-diabetes.com`** | **1 009** | 2026-09-06 → 2026-09-16 | the **EU multilingual diabetes property** — ~90 locale prefixes (`de-CH`, `da-DK`, `ar-MENA`, `en-ZA`, `el-GR`, `is-IS`, …). Codes include **401 and 403** → partly auth/waf-gated |
| **`medtronicdiabetes.com`** | 132 | 2026-09-08 → 2026-09-09 | **every capture is a bare `301`** — a pure redirect domain (US diabetes site → the above) |
| `medtronicdiabeteslatam.com` | 7 | 2026-09-08 → 09-11 | LatAm (`/pump/brasil/`, `/mdi-br/`) |
| `medtronicdiabetesbrasil.com` | 2 | 2026-09-17 | BR |
| `medtronicdiabetesproducttraining.com` | 2 | 2026-09-13 | 404 on `/llms.txt` and `/robots.txt` — **archived-then-probably-dead** |
| `medtronic-diabetes-mena.com` | 6 | 2026-09-13 | all `301` → archived-then-probably-dead |
| `medtronic-diabetes-look.com` | 3 | 2026-09-10 | `/en_gb/check` → **403 `text/plain`** |
| `medtronicminimed.com` | 1 | 2026-09-08 | brand-level domain, `/robots.txt` → `302` |
| `medtronicdbs.com` / `medtroniceureka.com` / `medtronicheart.com` | 3 each | 2026-09 | `301` + **`502`** — almost certainly parked/unrelated, **do not attribute to Medtronic without checking** |

### 3b. New subdomains (9)

`hcp.medtronic-diabetes.com` (HCP material portal, `?product_type_rest=27`,
`?document_type_rest=8`) · `resources.cloud.medtronic-diabetes.com` (46 PDF
documents under `sites/prd/files/documents/<YYYY-MM>/`, incl. `2025-09` and
`2025-10` DPF notices) · `wepartner.medtronic-diabetes.com` (`/s/`,
`/s/pdf-viewer`, `registration-form`; **503** on `/ch-CH/s/?language=de`) ·
`e-learning.medtronic-diabetes.com` · `virtualpump.eu.medtronic-diabetes.com` ·
`origin.medtronicdiabetes.com` · `info.medtronicdiabetes.com` (Eloqua tracking
`elqTrackId`/`elqak` params in the URL) · `*.medtronic.myprofile` ·
`medtronicinteract.secure.app`.

### 3c. The `wecare` family on `medtronic-diabetes.com` — a patient-portal entry point not in any file

```
/<locale>/wecare                              302
/<locale>/wecare/login?destination=/<locale>/wecare/profile      200  (9 locales)
/<locale>/wecare/login?destination=/<locale>/wecare/account/personal  200 (3 locales)
/<locale>/wecare/account/password             200
/<locale>/wecare/profile                      302
/<locale>/wecare-info                         200
```
plus the untranslated aliases `/wecare-fr`, `/<locale>/carelink`,
`/<locale>/guardian-connect` (301 and **403**), `/<locale>/check-compatibility-app[/search]`,
`/<locale>/products/minimed-insulin-pump-accessories`.
**The `destination=` parameter is a post-login deep-link parameter** — the same
shape as the Auth0 `redirect_uri` mechanism the bridge relies on, on a completely
different domain. Worth recording so nobody conflates them.

### 3d. `medtronicdiabetes.com` preserves the pre-`medtronic-diabetes.com` US path vocabulary

Archived only as `301`s, but it is the clearest historical record of the retired US
support taxonomy: `/customer-support/minimed-630g-system-support/pump-alarms-alerts-messages/{low-battery-pump,resume-bolus}`,
`…/setting-a-dual-wave-bolus`, `…/cgm-calibrating`, `…/home-screen-smartguard-auto-mode`,
`…/find-your-model-number`, `/customer-support/product-and-service-updates/notice{17,23}-letter`,
`/download-library/minimed-{508,511}`, `/treatment-and-products/carelink-personal-diabetes-software`,
`/symptoms/dka`, `/cgm-pharmacy-copay`, `/mySentry`, `/get-it-back`,
`/res/img/notice12/NGP-Pump-Retainer-FCA-Letter.pdf`.
Note the **`/mySentry`** path — a discontinued pump feature, still reachable by URL.

---

## 4. NEW — the `*.medtronic.eu` shadow deployment (the gap ARCHIVE-URLS §8.3 called "highest-value follow-up")

Query #22 returned **1 630 rows across 25 hosts**, of which **20 are non-`www`
hosts and none of them is in any existing project file.**

### 4a. New hosts on `medtronic.eu`

| host | archived | status | what it is |
|---|---|---|---|
| **`carelink.medtronic.eu`** | **916 rows**, 2020-01-10 → 2025-08-11, 567 families | **the EU shadow-deployment CareLink (HCP) portal.** Same AngularJS 1.x + Bower + Foundation stack as `carelink.medtronic.com`, but a **separate content-tree namespace** — `crs/pow/*` → `crm/pow/*`, not the patient site's `crs/ocl/*` → `crm/ocl/*` (§5) | |
| **`carelink-test.medtronic.eu`** | 273 rows, 2020-12-18 → 2020-12-29 | build **`?v=3.2.339`** — *the same build number* `ARCHIVE-URLS §2d` records for `carelinkhp-test.minimed.eu` | |
| `clcloud.medtronic.eu` | `/` → **403** @2025-01-21 | **shadow-deployment Cumulus edge.** Same JSON-403 as `clcloud.minimed.eu` root (ARCHIVE-URLS §6) | |
| `clcloud-next` · `clcloud-oustest` · `clcloud-stage-next` `.medtronic.eu` | 403 each, 2025-01-08 → 02-05 | | |
| **`dev.commoncore.medtronic.eu`** | `/reports-broker/v1/ocl` **403** and `/reports-metadata/v1/ocl` **403** @2025-07-27 | **resolves ARCHIVE-URLS §6's "most interesting unknown".** These are the *dev* twins of the two services the 2026-02-04 public config names on prod `commoncore.medtronic.eu` — and they confirm the `reports-broker/v1` + `reports-metadata/v1` path shapes and the **`/ocl` suffix** from a second, independent source | |
| `stage1.commoncore.medtronic.eu` | **502** @2024-09-23 | archived-then-probably-dead | |
| `carelink-login-dev` · `carelink-login-stage1-next` · `carelink-login-test1` `.medtronic.eu` | 302 each, 2025-01-21 → 02-16 | **shadow Auth0 login hosts**, none of which is one of the project's four named tenants | |
| `carelink-next` · `carelink-support-next` `.medtronic.eu` | **502** @2025-01-19 / 01-22 | archived-then-probably-dead | |
| `carelink-stage1` · `carelink-stage1-next` · `carelink-stage3` · `carelink-test1` · `carelink-support-stage1` · `carelink-support-stage1-next` `.medtronic.eu` | 301/revisit, 2022-03 → 2025-02 | | |

### 4b. NEW API namespace: the `/hcp/*` clinician REST surface

**This exists on both `.com` and `.eu` and is recorded nowhere in the project.**
All archived **200, unauthenticated**, on 2020-04-09 / 2020-08-09:

```
/hcp/clinics/getCountryLocaleSettings?countryCode={GB|US}
/hcp/configuration/application
/hcp/configuration/getPersonalDeploymentUrl
/hcp/configuration/product/info
/hcp/configuration/user
/hcp/countries/getAllCountries
/hcp/countries/getPostalCodePattern?countryCode={GB|US}
/hcp/locale/translation?locale={de|en|en_GB|en_US|es_ES}
/hcp/media/getConfig?level=APP[&locale=…]
/hcp/user/getCountryLanguages
/hcp/user/getCountryTitles?countryCode={GB|US}
/hcp/user/getCurrentUser            401 @2025-07-25   <- the only gated one
```
Plus an unauthenticated `/public/*` group on `carelink.medtronic.eu`:
`/public/{clinicRegistration,contactUs,privacyPolicy,supportedBrowsers,termsOfUse,uploaderInstructions}`,
and `/secured/mfa` (2021-11-27), `/login`, `/forgot-password`, `/nojs`.

**Read:** `/hcp/*` is the HCP twin of the patient API the bridge uses — same
`/hcp/<area>/<verb>/<noun>` shape, `getXxx` naming, and a lone 401 on the
identity call. It is a *different* deployment (shadow domain, `pow` content
namespace, its own version ladder) so it is not a drop-in for the bridge, but it
is the best available template for how Medtronic structures the clinician side.

### 4c. NEW: `connect.medtronic.com` — a 2 862-row B2B portal with its own REST + OpenID stack

```
/api/core/wellknown/v1/mdtb2bsite/countries                              200
/api/core/notification/v1/{count,search}                                 401
/api/core/notification/v2/count                                          401
/api/common/users/userinfo                                               401
/api/configuration/appconfig/v1/params                                   401
/api/channelconnect/v1/{inventoryEntries,salesOutEntries}                401
/api/channelconnect/v1/{inventoryEntries,salesOutEntries}/search/findBySubmissionId   401
/api/channelconnect/v1/submissions/reporting/dashboard/grid/download    401
/api/connect-cms/v1/cms/forms/{downloadHide,rdtAlignmentExpiry}/fieldsets?country=DF   200
/api/connect-cms/v1/cms/forms/CheckoutNotes/fieldsets                   400
/api/connect-aardt/v1/data/accountAlignmentEntities                     404
/api/openid/connect/{userinfo,token,revocation,endsession}  401/405/302
/api/openid/.well-known/openid-configuration                            404
```
**`/api/openid/connect/*` is a fifth OIDC surface**, independent of the four Auth0
tenants the project tracks. Note `/api/openid/connect/endsession` is **302** while
`userinfo` is **401** and `token`/`revocation` are **405** — the POST-only pattern
PROBE-FINDINGS §5 already documents on the Auth0 tenants, reproduced here.

Also on this host: `/apps/portal/features.json`, `/apps/portal/locales/__lng__/__ns__.json`,
`/apps/cent/data/mockdata/{carriers,checkoutsample,insights,orderMoreInfo,shipments}.json`
(all **200** @2019-10-18 — six years stale, archived-then-probably-dead fixture data).

### 4d. NEW: `mdt-connect-product-v1` product API

`api-us.medtronic.com/mdt-connect-product-v1/products/<SKU>/details?locale=en-US&country=US`
→ **400** for 9 device SKUs between 2024-12-02 and 2025-07-31
(`Medtronic_LPG1510`, `_ID_1_5`, `_AFR_00002`, `_VAMF4444C100TU`, `_7IC80`,
`_ETUF2514C102E`, `_VAMC3838C150TU`, `_VAMC4242C100TU`).
The sibling matrix exists but is empty: `api-{eu,dev-us,dev-eu,stage-us,pp-us,it-us,it1-eu,…}.medtronic.com`
all return only `/` 301/404 plus `/robots.txt` and `/sitemap.xml` 404 — i.e.
**hosts that exist and route but serve nothing at the root.** Archived-then-probably-dead.

### 4e. NEW: 8 shadow Auth0 login hosts, none of them one of the four named tenants

```
carelink-login-stage1-next.medtronic.com          301 @2025-02-15
carelink-login-test1.medtronic.com                301 @2025-02-07
carelink-login-clinical-stage1-next.medtronic.com 301 @2025-02-10
carelink-login-clinical-test1.medtronic.com       301 @2025-02-07
carelink-login-dev.medtronic.eu                   302 @2025-01-21
carelink-login-stage1-next.medtronic.eu           302 @2025-02-10
carelink-login-test1.medtronic.eu                 302 @2025-02-16
```
PROBE-FINDINGS §8 established **four** candidate issuers (`carelink-login.minimed.{eu,com}` +
`carelink-login.medtronic.{eu,com}`). The archive adds **eight more named hosts**,
all non-prod. None of their `/.well-known/openid-configuration` is archived, so
their JWKS kids remain unknown — the "would a shadow-tenant token be accepted"
question (SECURITY-FINDINGS) now has **12** candidate hostnames rather than 4,
though still only 4 with any known key material.

---

## 5. NEW — the CMS version ladder is **two ladders**, not one

ARCHIVE-URLS §4 documents one ladder for the *patient* site. The shadow HCP
deployment runs a **parallel, independently-numbered** one:

| shadow deployment (`crs`→`crm` + **`pow`**) | first archived | | patient site (`crs`→`crm` + **`ocl`**) | first archived |
|---|---|---|---|---|
| `crs/pow/3.11` | 2024-02-26 | | `crs/ocl/14.01` | 2020-12-29 |
| `crm/pow/3.12` | 2024-07-05 | | `crs/ocl/14.11` | 2024-02-26 |
| `crm/pow/3.13` | 2024-11-27 | | `crm/ocl/14.12` | 2024-09-12 |
| `crm/pow/4.1` | 2025-07-25 | | `crm/ocl/15.5` | 2026-09-26 |

**`ocl` (CareLink product code, patient) vs `pow` (shadow HCP) are different
content namespaces**, and `3.11→4.1` vs `14.01→15.5` are different version axes.
Do not merge them. Corroborating detail: the shadow HCP portal's *build* numbers
(`?v=3.2.339`, `?v=3.3.392`) match `carelinkhp*.minimed.eu`'s build numbers, so the
`pow` tree is the **same codebase as the `ocl` tree**, deployed under a second
hostname — a mirror, not a fork.

---

## 6. Archived config / JSON documents (target #4)

### 6a. Common Crawl contributed **zero** JSON documents

Across all three correctly-fetched CDX shards: **0 captures** of any
`*.json`/`*.xml`/`*.yaml` on any `minimed`/`medtronic` host. The only structured
mimes are `text/plain` robots.txt. **Common Crawl adds nothing to the config
harvest** — a clean negative, and it means the Wayback-only harvest in
ARCHIVE-URLS §2 stands unchallenged.

### 6b. The answer to `/patient/v2/configuration/public`'s sibling question

**There is no `/patient/*` on `medtronic.eu` or `medtronic.com` at all** — query #26
(`/patient/|configuration/public|/configs/|/hcp/|\.json$` over the whole non-`www`
`medtronic.eu` domain) returned 27 rows, **all** of them `/hcp/*`, `/.well-known/*`
or `/crm|crs/pow/*/*.json`. The patient API lives exclusively on `*.minimed.*`.

**But the HCP deployment has the exact analogue**, and it is a **flat-key
namespace with a `pow.` prefix** — the structural twin of the patient's
`/patient/configuration/system/<key>`:

```
/hcp/configuration/public/cms-config.json             412  @2025-07-27
/hcp/configuration/public/pow.browser.check.configuration  412  @2025-07-27
/hcp/configuration/public/pow.invite.to.personal.uri       412  @2025-07-27
/hcp/configuration/public/pow.crm.settings                 200  @2024-07-05  (carelink.medtronic.com)
/hcp/configuration/public/pow.crm.settings                 200  @2024-02-26  (carelink.medtronic.eu)
```

- **`cms-config.json` is the HCP sibling of `/patient/v2/configuration/public`.**
  Confirmed present on **28 distinct `carelink*.medtronic.com` hostnames**.
- All `412 Precondition Failed application/json` — the archive captured the URL and
  content type but **no body** (WAF rejection of the crawler). The *URL existence*
  across 28 hosts is the evidence; the values are not recoverable from the archive.
- **`/hcp/configuration/public/<key>` is confirmed by a `200`** for
  `pow.crm.settings`, so the endpoint shape is real, not just a WAF echo.

### 6c. Full list of archived Medtronic JSON documents recovered, with dates

| archive ts | code | mime | document |
|---|---|---|---|
| 2024-02-26 | **200** | json | `carelink.medtronic.eu/crs/pow/3.11/i18n/ui/sso/{en,es}.json` |
| 2024-02-26 | **200** | — | `carelink.medtronic.eu/hcp/configuration/public/pow.crm.settings` |
| 2024-07-05 | **200** | json | `carelink.medtronic.com/crm/pow/3.12/media/configurations/us.json` |
| 2024-07-05 | **200** | — | `carelink.medtronic.com/hcp/configuration/public/pow.crm.settings` |
| 2024-11-27 | **200** | json | `carelink.medtronic.eu/crm/pow/3.13/i18n/ui/sso/en.json` |
| 2024-11-27 | **200** | json | `carelink.medtronic.eu/crm/pow/3.13/media/configurations/gb.json` |
| 2025-07-25 | **200** | json | `carelink.medtronic.eu/crm/pow/4.1/media/configurations/gb.json` |
| 2025-07-27 | 412 | json | `/hcp/configuration/public/cms-config.json` × 28 hosts |
| 2025-07-27 | 200 | `application/vnd.sire` | `www.medtronic.com/api/assets/medtronic-wide/public/cf/regions/americas/en-us/products/**diabetes**/software-systems-technologies/carelink%E2%84%A2-system-important-safety-information.json` (+ `.model.json`) |
| 2025-08-03 | 200 | `application/vnd.sire` | `…/products/diabetes/software-systems-technologies/carelink-system.json` |
| 2025-08-06 | 200 | `application/vnd.sire` | `…/cardiac-rhythm/software/carelink-express-mobile-app.json` (+ `.isw`, `.isw.model`) |
| 2025-07-28 → 08-09 | 200 | `application/vnd.sire` | 20+ `www.medtronic.com/api/assets/medtronic-wide/public/cf/{regions/*/}*.json` product-content documents |
| 2025-08-08 | **200** | json | `www.medtronic.com/content/dam/medtronic-com/us-en/mobileapps/iOS/demo-mycarelink-heart/files/countries.json` — a **CareLink iOS app bundle asset** in a DAM demo directory |
| 2015-03-02 | 200 | json | `catalyst.medtronic.com:80/pub/scripts/json/{productCategories,products,therapeuticAreas,therapies}.json` — retired product-catalog API |
| 2019-10-18 | 200 | json | `connect.medtronic.com/apps/portal/{features,bu-settings}.json`, `/apps/portal/locales/__lng__/__ns__.json`, `/apps/cent/data/mockdata/*.json` |
| 2025-07-27 | 200 | json | `aibe{,-dev,-qa}.medtronic.com/_nuxt/builds/latest.json`, `chatrouter-dev.medtronic.com/_nuxt/builds/latest.json` |
| 2025-07-28 | **200** | json | `status.carelink-stage1.medtronic.com/api/v2/status.json` **and `/incidents/wk31cp3crv7t.json`** — an archived **statuspage incident record** |
| 2025-07-28 | 200 | json | `gcssp.assets.medtronic.com/_ui/assets/js/gaTracking.json` |

**Dating a schema change from these:** the `pow.crm.settings` key is archived **200**
on **2024-02-26** (`.eu`, `crs`→`crm` boundary era) and again **2024-07-05** (`.com`,
`crm/pow/3.12`). The `crm/pow` tree first appears between **2024-02-26 and
2024-07-05**, and reaches **4.1 by 2025-07-25** — a *different* migration cadence
from the patient tree's `crm/ocl/14.12` (2024-09-12) → `15.5` (2026-09-26).
**No `configs/v1/*.json` and no `/patient/v2/configuration/*` sibling exists on any
`medtronic.*` host** — those remain exclusively `carelink.minimed.*`.

---

## 7. Coverage limits, artefacts and honest negatives

1. **Two Common Crawl crawls only** (2026-39, 2024-42). The index API is
   unreachable, so the other ~100 crawls were not sweepable within budget. Every
   conclusion in §3 is scoped to those two crawls' date windows.
2. **Zero `*.eu` coverage in Common Crawl** for both crawls. The EU story in this
   document comes entirely from Wayback, not Common Crawl.
3. **Queries #23, #24, #25 all hit their 3 000 / 2 000-row limits.** `collapse=urlkey`
   orders by SURT key, so each sweep is **alphabetically truncated**; hosts later in
   the alphabet on `medtronic.com` (`n…z`) were never reached. `connect.medtronic.com`
   alone is 2 862 rows, so it consumed most of #24's budget.
4. **`raw-*.cdx` / `raw24-*.cdx` on disk are wrong and must not be read as results**
   — see §1. They are the earlier pass's mis-offset fetches.
5. **The `…/API/API/API/…` recursion** in `connect.medtronic.com` /
   `americas.connect.medtronic.com` (depth up to 15, all `200`) is the Wayback
   crawler walking an SPA route that returns 200 for every path — an artefact, not
   a URL family. Excluded from the 966-family figure.
6. **`medtronicdbs.com`, `medtroniceureka.com`, `medtronicheart.com`** show
   `301` + `502` and are **not** assumed to be Medtronic-owned. Flagged, not attributed.
7. **`status.carelink-stage1.medtronic.com/incidents/*.json`** — an archived incident
   document. Not fetched; no body retrieved. Listed because an outage record on a
   non-prod CareLink host is exactly the kind of thing the project wants if a future
   pass is allowed to replay it.
8. **Nothing here was verified live.** Every status code is a 2015–2026 archive
   observation. "Dead" below means *archived-then-probably-dead*, not NXDOMAIN.
9. **No dev/stage host was contacted.** All the `carelink-{stage1,stage2-next,test1,dev1,load1,next}`,
   `carelink-clinical-*`, `carelink-trials*`, `clcloud-{next,oustest,stage-next}`,
   `commoncore-{dev,stage1,preprod1,loadlab1,clinical-test1}`, `api-{dev,stage,pp,it,it1,it2,it3}-*`
   and `aible*`/`chatrouter-dev` names were **enumerated from the archive only**,
   consistent with the project's standing rule.
10. **Not attempted for want of budget** (19 requests unused): a
    `medtronic.com` sweep excluding `www` *and* the heavy hosts, to reach the `n…z`
    tail; a dedicated `wwwp.medtronic.com` sweep; a `carelink-clinical-*.medtronic.com`
    deep path sweep (only its `/hcp/configuration/public/*` came back in #25).

---

## 8. Dead / retired host candidates — "archived-then-probably-dead"

Determined purely from archive evidence. **Not resolved, not contacted.**

| host / path | last archived | archived code | assessment |
|---|---|---|---|
| `carelink.medtronic.com/app/modules/**` (AngularJS 1.x) | 2021-10-30 | 200 | superseded by the Angular/webpack generation (`/main.*.js`, `runtime.*.js` from 2022-06 on the same host) |
| `carelink.medtronic.eu/app/modules/**` | 2020-12-30 | 200 | same generation, EU shadow |
| `connect.medtronic.com/apps/cent/data/mockdata/*.json` | 2019-10-18 | 200 | six-year-stale SPA fixtures |
| `catalyst.medtronic.com:80/pub/scripts/json/*` | 2015-03-02 | 200 | ten-year-old product-catalog API |
| `api-{eu,dev-us,dev-eu,stage-us,stage-eu,pp-us,pp-eu,it-us,it-eu,it1-eu,it1-us,it2-*,it3-*}.medtronic.com` | 2025-07-27 | 301/404 on `/`, `/robots.txt`, `/sitemap.xml` | hosts that route but serve nothing at root |
| `medtronicdiabetesproducttraining.com` | 2026-09-13 | **404** `/robots.txt` + `/llms.txt` | archived-then-probably-dead |
| `medtronic-diabetes-mena.com` | 2026-09-13 | **301** × 4 | pure redirect, probably retired |
| `medtronicdiabetes.com` (the US diabetes site) | 2026-09-09 | **301** × 120 | retired in favour of `medtronic-diabetes.com` |
| `carelink-next.medtronic.eu` · `carelink-support-next.medtronic.eu` | 2025-01-19 / 01-22 | **502** | archived-then-probably-dead |
| `stage1.commoncore.medtronic.eu` | 2024-09-23 | **502** | |
| `stage1` · `preprod1` · `loadlab1` · `clinical-test1` `.commoncore.medtronic.com` | 2025-07-27 | **502** × 3 paths | |
| `dev.commoncore.medtronic.{eu,com}` | 2025-07-27 | **403** | dev, not dead — gateway-rejected |
| **`commoncore.medtronic.com` (prod)** | — | **never archived** | still zero captures, exactly as `commoncore.medtronic.eu` was. **The prod reports host remains the project's biggest archive blind spot on `medtronic.*`** — now confirmed on *both* TLDs, not just `.eu` |
| `carelink-login-*.{medtronic.eu,medtronic.com}` (8 hosts) | 2025-02-16 | 301/302 on `/` only | non-prod shadow tenants, never crawled |
| `connect.medtronic.com:80` | 2004-08-10 | 302 | 20-year-old pre-2010 host, clearly retired |
| `wwwp.medtronic.com` `;jsessionid_*=` URLs | 2024-10-16 | 200 | see §9 — legacy JSP app |

---

## 9. ⚠ Session material — which files must not be republished

**This pass's own harvest is clean.** Scanned every file created here for
`sessionData`, `sessionID=`, `id_token_hint`, `access_token=`, `sessionid_`:

| file | markers | verdict |
|---|---|---|
| `w1.json`, `w2-eu.json`, `w3-com.json`, `w4-auth-mag.json`, `w5-patient-v2.json`, `w6-eu-patient.json` | **0** | clean |
| `cc39-com-medtronic.cdx`, `cc39-com-minimed.cdx` | **0** | clean (`cc39-com-minimed.cdx`'s two regex hits are unrelated third-party domains, `minimepastry.com` / `minimermaidtails.com`) |
| **`cc24-com-medtronic.cdx`** | **8 058** | **⚠ CONTAINS SESSION MATERIAL — do not publish** |

**Two contaminated files, both the same host.**

| file | markers | host | origin |
|---|---|---|---|
| **`cc24-com-medtronic.cdx`** | 8 058 | `wwwp.medtronic.com` | this pass (#21) — a **correct** fetch |
| **`raw24-com-medtronic.cdx`** | 16 776 | `wwwp.medtronic.com` | the earlier partial pass (#15) — a **mis-offset** fetch, unusable as results anyway |

All markers on both are on one host, **`wwwp.medtronic.com`**, and are **Java
`jsessionid_*` values embedded in the URL path** (JSP URL-rewriting), in four URL
shapes, all `http(s)://wwwp.medtronic.com/…` between 2024-10-03 and 2024-10-16.
Redacted shape only:

```
http://wwwp.medtronic.com/<path>/;jsessionid_<app>=<VALUE>
http://wwwp.medtronic.com/<path>/<file>.html;jsessionid_<app>=<VALUE>
```

**No value from these has been printed, copied, quoted, decoded or summarised
anywhere in this document** — only the parameter *name* and the redacted shape.
The underlying property is a public-archive fact, not something this pass caused:
an authenticated session identifier sitting in a crawlable URL. Treat both files as
contaminated; if a diff or export is ever produced from `recon/cc/`, exclude them or
scrub the `;jsessionid_*=` segment first. Every other `.cdx` and `.json` in this
directory scans clean (verified: `raw-com-medtronic.cdx`, `raw-eu-medtronic.cdx`,
`raw-com-minimed.cdx`, `raw-eu-minimed.cdx`, `raw24-eu-medtronic.cdx`,
`raw24-com-minimed.cdx`, `w1–w6*.json`, `cc39-*.cdx` — all 0 markers).

The two files flagged in ARCHIVE-URLS §7 (`cdx/r18.json`, `cdx/r32.json`, the
`sessionData` JWS/JWE class on `mdtlogin{,-ocl}.medtronic.com`) were **not touched
or re-read by this pass** and remain quarantined in `recon/cdx/`.

---

## 10. Method notes / reproduction

- `locate.py` — binary search over a `cluster.idx` TSV to find the CDX byte range
  for a SURT prefix. Local, 0 requests. **The earlier pass's equivalent was buggy;
  this is the corrected version.**
- `qr.sh` — ranged `data.commoncrawl.org` fetch with the same allowlist/denylist/
  cap/2 s guards as `q.sh`. Writes the HTTP code via `-w` to stdout and the body
  via `-o`, so the log can never be corrupted by response bytes (the bug in #18).
- `ccparse.py` — SURT→host, path extraction, host/family aggregation.
- `q.sh` — the earlier pass's plain-URL fetcher (kept; still guarded).
- `ranges39.txt`, `ranges42.txt` — computed byte ranges.
- `request-log.tsv`, `request-count.txt` — the audit trail. 26 rows, 26 requests.