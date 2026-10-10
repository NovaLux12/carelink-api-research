# Subdomain recon — new-hostname hunt (2026-10-09)

**Method:** passive-only enumeration (`subfinder`, crt.sh CT logs), DNS resolution,
then a *single* unauthenticated HTTP GET and one TLS cert peek on a small,
hand-picked subset. Read-only. No credentials. No writes. No auth attempts.
No port scanning. No dev/stage host was probed beyond one GET.

**Not done (deliberately):** no bruteforce DNS, no vhost fuzzing, no path
enumeration, no token acquisition. Where a surface needed auth it was recorded
and skipped.

---

## 0. Read this first — three corrections to the task brief

### 0.1 The "345 already-known names" figure is stale. The real baseline is 678.

`PROBE-FINDINGS.md` §1 says "345 unique names" from CT logs. That was true on
2026-10-08 morning. **The same day's second round (§7) then ran `subfinder`
and recorded 599 names**, and the raw artifacts are still on disk
(`deep/subfinder-all.txt`, `security/names-medtronic.eu.txt`, `crtsh-*.json`,
etc.). Diffing against 345 would have produced ~254 "new" names that were
already recorded a day earlier.

I rebuilt the baseline from **every** pre-existing artifact in the folder —
txt lists, raw crt.sh JSON, jsonl probe rows, and prose in all `.md`/`.java`/
`.py`/`.sh`/`.ts` files — normalised (lowercase, wildcards stripped):

```
KNOWN (in-scope, normalised): 678
    599  deep/subfinder-all.txt          252  crtsh-com.json
    599  deep/sf.txt                    246  names-com.txt
    385  deep/subfinder-com.txt         240  deep/resolved.txt
    345  names-all.txt                  214  deep/subfinder-eu.txt
                                         113  prod-names.txt
                                         105  crtsh-eu.json
                                          99  names-eu.txt
                                          68  security/crtsh-medtronic.eu.json
                                          62  security/names-medtronic.eu.txt
                                          24  scope-prod.txt
                                          21  PROBE-FINDINGS.md
                                          20  tlsx-prod.jsonl
                                          19  hosts.txt
                                          15  SECURITY-FINDINGS.md
                                           9  AUTH-TENANT-FINDINGS.md
```

`recon/known-names.json` records, per name, which file(s) proved it known.

### 0.2 Two of the seven seeds are not Medtronic properties. `carelink.eu` and
### `clcloud.eu` are parked domains and 100% of their output is false-positive.

This is the single most useful result of the pass. See **§3**.

### 0.3 `*.minimed.*` and `*.medtronic.eu` are exhausted. **Zero new names.**

```
  minimed.eu  : 213 collected ->   0 new
  minimed.com : 385 collected ->   0 new
  medtronic.eu: 129 collected ->   0 new
```

The subfinder sources the earlier pass used are exhausted for these three.
Nothing new to find there with this technique; further names would need
crt.sh date-slicing or a fresh CT window.

---

## 1. Exact commands run

All in `research/probe-2026-10-08/recon/`.

```bash
# --- 1. passive enumeration (7 seeds) ---
for d in minimed.eu minimed.com medtronic.eu medtronic.com \
         carelink.eu carelink.com clcloud.eu; do
  subfinder -d "$d" -all -silent -o "sf-$d.txt"
done

# --- 2. build the KNOWN baseline from every pre-existing artifact ---
python3 build-known.py          # -> known-names.txt (678), known-names.json

# --- 3. diff ---
python3 diff.py                 # -> collected-names.txt, new-names.txt

# --- 4. extra passive source for carelink.eu (crt.sh) ---
curl -s 'https://crt.sh/?q=carelink.eu&output=json' -o c3.json
jq -r '.[].name_value' c3.json | sed 's/^\*\.//' | tr 'A-Z' 'a-z' \
  | grep -E '\.carelink\.eu$' | sort -u > crtsh-carelink-eu-names.txt

# --- 5. DNS (A/AAAA/CNAME, 0.5s between queries, sequential) ---
python3 resolve.py new-names-focus.txt resolve.jsonl

# --- 6. wildcard-DNS control test on carelink.eu ---
dig +short zq7x-nonexistent-test-9137.carelink.eu A
dig +short qqqqq.carelink.eu A
dig +short carelink.eu NS          # ns1/ns2.abovedomains.com
dig +short clcloud.eu NS           # ns1/ns2.dns-parking.com

# --- 7. single unauthenticated GET per host of interest (2s apart) ---
curl -s -o body.tmp -w '%{http_code} %{content_type} %{size_download}' \
     --max-time 12 -A 'Mozilla/5.0 recon-research/1.0' https://<host>/

# --- 8. cert peek (no recursion gained -- single-SAN certs) ---
echo | openssl s_client -servername <host> -connect <host>:443 -showcerts \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

Request budget for this pass: **~1 200 DNS queries**, **21 HTTP GETs**,
**3 TLS handshakes**, 2 crt.sh queries. All unauthenticated. All sequential,
≥1.5 s apart per host.

Artifacts: `sf-<domain>.txt` (raw), `known-names.{txt,json}`,
`collected-names.txt`, `new-names.txt`, `new-names-diabetes.txt`,
`new-names-diabetes-com.txt`, `new-names-focus.txt`, `resolve.jsonl`,
`c3.json` + `crtsh-carelink-eu-names.txt`, `oidc-carelink-login.medtronic.com.json`,
`jwks-carelink-login.medtronic.com.json`, `cl-mdt-com.html`.

---

## 2. Headline numbers

| | count |
|---|---|
| subfinder raw, 7 seeds | **4 028** (all already in scope) |
| known baseline | **678** |
| **new (not in the 678)** | **3 358** |
| — `medtronic.eu` / `minimed.*` | **0** |
| — `carelink.eu` / `carelink.com` / `clcloud.eu` | 49 (**all false positives**, §3) |
| — `medtronic.com`, diabetes-keyword subset | 246 (127 resolve, 119 cert-only) |
| — `medtronic.com`, general corporate estate | 2 995 (not diabetes-related, §7) |
| CT-only extra not in subfinder | **1** (`superset.staging.carelink.eu`) |
| DNS resolved (focus set, 260 names) | 131 |
| HTTP GETs issued | 21 (14 new hosts + 7 confirm/control) |
| **Genuinely new, genuinely interesting** | **see §4** |

---

## 3. `carelink.eu` and `clcloud.eu` are parked domains — **entire pass output is noise**

The brief listed `carelink.eu`, `carelink.com`, `clcloud.eu` as seeds. Two of
them are not Medtronic. Evidence:

### 3.1 `carelink.eu` — wildcard DNS onto a domain-monetisation parking IP

```
$ dig +short carelink.eu NS
ns1.abovedomains.com.
ns2.abovedomains.com.

$ dig +short zq7x-nonexistent-test-9137.carelink.eu A
103.224.182.253          <- a random, never-registered name resolves
$ dig +short qqqqq.carelink.eu A
103.224.182.253          <- ditto
```

**Every name under `carelink.eu` resolves.** So `admin.carelink.eu`,
`superset.carelink.eu`, `staging.carelink.eu`, `mail.carelink.eu` etc. are
**not Medtronic hosts** — they are the wildcard answering. Single GET each:

```
superset.carelink.eu    302 -> https://ww38.carelink.eu/
admin.carelink.eu       302 -> https://ww38.carelink.eu/
www.carelink.eu         302 -> https://ww38.carelink.eu/
```

That is a domain-park / Sedo-style redirect. The names exist **only in CT logs**,
because of this cert:

```
common_name: carelink.eu
SANs: *.carelink.eu, *.admin.carelink.eu, *.cmedtronic.carelink.eu,
      *.medtrinic.carelink.eu, *.medtronic.carelink.eu, *.minimed.carelink.eu
issuer: Let's Encrypt R3 / R10 / R11 / R13
not_before: 2023-02-17, 2023-05-18, 2023-08-17, 2023-11-15, 2024-02-13,
            2024-05-13, 2024-08-11, 2024-11-10, 2025-02-08, 2025-05-09,
            2025-08-07, 2025-11-05      <- ~quarterly, machine cadence
```

Six hand-picked wildcards reissued on a fixed ~90-day schedule is not a human
process; it is an **automated parking service mass-issuing wildcards** — which is
also what injects `medtronice`, `medtrinic`, `medtornic`, `cmedtronica`,
`cmedtronic`, `metronic`, `otzctwww.medtrinic`, `ww25`, `ww38`, `www.www`
into every CT-log scraper that queries `carelink.eu`.

> **Actionable for this project:** `*.carelink.eu` is a **poisoned CT namespace**.
> Exclude it from host enumeration and from any future "internal name
> disclosure" finding. The real EU hosts are `carelink.minimed.eu` /
> `clcloud.minimed.eu`. Reporting `superset.carelink.eu` as a Medtronic
> dashboard, or `admin.carelink.eu` as an admin panel, would be a **false
> positive in a disclosure email.**

### 3.2 `clcloud.eu` — an unrelated Dutch company

```
$ dig +short clcloud.eu NS
ns1.dns-parking.com.
ns2.dns-parking.com.
```

subfinder returned 10 names: `lamafurnish`, `lamafurnish9`, `abv`, `abvinvoices`,
`nextcloud`, `odoo`, `www.clcloud.eu`. Resolving A records are `46.17.175.243`,
`185.77.97.172`, `195.200.9.186`, `194.59.166.143` — not Medtronic ranges, and
consistent with parked/redirector space.

Medtronic's cumulus host is **`clcloud.minimed.{eu,com}`**, not `clcloud.eu`.
The seed in the brief is a name collision. `carelink.com` returned exactly one
name, `www.carelink.com`, which is a NXDOMAIN-ish placeholder — also nothing.

---

## 4. Notable findings — the `.medtronic.com` shadow deployment

Everything below was **new to the 678-name baseline** and none of it appears in
`PROBE-FINDINGS.md`, `SECURITY-FINDINGS.md` or `AUTH-TENANT-FINDINGS.md`.
The prior pass found the `.medtronic.eu` shadow; it did **not** enumerate
`*.medtronic.com` (evidence: `security/crtsh-medtronic.com.json` is a 150-byte
error page and `security/names-medtronic.com.txt` is empty). So this is the
missing half of a pattern already half-discovered.

### 4.1 ⭐ `carelink-login.medtronic.com` — a **fourth Auth0 tenant**

Unauthenticated public OIDC doc, 2 765 B:

```
issuer                   https://carelink-login.medtronic.com/
authorization_endpoint   https://carelink-login.medtronic.com/authorize
token_endpoint           https://carelink-login.medtronic.com/oauth/token
jwks_uri                 https://carelink-login.medtronic.com/.well-known/jwks.json
registration_endpoint    https://carelink-login.medtronic.com/oidc/register
```

OAuth policy is **identical** to the three known tenants (field-by-field
`same` on grants, scopes, response types, PKCE methods, id_token algs) — the
same "shadow tenants are full clones" conclusion as `AUTH-TENANT-FINDINGS.md` §1,
now confirmed for a fourth issuer.

It is **not** a clone of the same keys. JWKS kids:

| tenant | kids |
|---|---|
| `carelink-login.minimed.eu` | `8RqxnMm8vg2Go_y1LAVh9`, `vnTNpK5RvkqVEfQgHRsqv` |
| `carelink-login.medtronic.eu` | `jd0EOLxJ8XduYx4lLy3ig`, `gZMBCJcl_t25Es4U_g_ow` |
| **`carelink-login.medtronic.com`** | **`cEgK74cyc5LzAVI9VxEz9`, `80YhF8vW25gJ1_rR_lOOJ`** |

Four independent issuers, four independent signing-key pairs.

**Why it matters for the bridge:** `SECURITY-FINDINGS.md` closes with the open
question "would `clcloud.minimed.eu` accept a token minted by the shadow tenant?"
This adds a second shadow tenant nobody had on the list. If any of the four
issuers is accepted by a CareLink API gateway, cross-tenant token acceptance is
the bug class worth testing in November — and it now has 4 candidate issuers,
not 2. Still **untestable without a token**; not attempted here.

Cert: DigiCert Global G2, `O=Medtronic, Inc.` (note: **no trailing period**,
unlike the `.medtronic.eu` shadow's `Medtronic, Inc.`), single SAN,
`notBefore 2026-10-01`, `notAfter 2027-04-17`.

### 4.2 ⭐ `carelink.medtronic.com` — the health-portal SPA, carrying the S3 finding

```
GET https://carelink.medtronic.com/   -> 200 text/html, 5518 B
sha256 0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d
```

**Byte-identical** to the stored `carelinkhp.minimed.eu` index
(`security/hp-index.html`, same sha256), same `<title>Dashboard</title>`, same
asset fingerprints (`main.fb5f8cb7eb60c4d5.js`, `styles.2de3fe143e8f9892.css`).

Consequence: the bundle previously analysed in **SECURITY-FINDINGS.md S3** —
the one containing the hardcoded `x-api-key` and the `host: https://dev.
commoncore.medtronic.eu/reports-broker/v1/ocl` build-config bug — is **also
served from `carelink.medtronic.com`**, which was never in scope. Two hosts, one
bundle. (The key itself is deliberately not reproduced here; see S3 for the value
and the note that it is verified not live against production.)

Also: `GET /patient/users/me` on this host returns **200 HTML**, not 401. It is
an SPA catch-all, not an API. Do not read that 200 as an auth bypass —
`carelinkhp.minimed.eu` behaves identically and S1 already documents it.
`carelink-support.medtronic.com` returns the same 5 518-byte document.
`carelink-site.medtronic.com` → 301.

### 4.3 `clcloud.medtronic.com` is **gateway-gated**, unlike `clcloud.minimed.*`

```
GET /connect/carepartner/v13/discover/android/3.6
  clcloud.medtronic.com      -> 403 {"message":"Missing Authentication Token"}
  clcloud.minimed.eu         -> 200, 20 256 B discovery document   (recorded)
  clcloud.minimed.com        -> 200, same document                 (recorded)
```

So the `.medtronic.com` deployment does **not** expose the discovery document.
Same 403 body shape as the `v14+` cells in `PROBE-FINDINGS.md` §3. The
`.medtronic.eu` shadow behaves like `minimed` (open discovery); the `.medtronic.com`
one does not. Unexplained — recorded, not diagnosed.

### 4.4 New family: **Minimed Outcomes** — resolves, but on Medtronic-internal IPs

Never mentioned in any prior file.

| name | A record |
|---|---|
| `usminimedoutcomes.medtronic.com` | 144.15.206.78 |
| `minimedoutcomes-usapi.medtronic.com` | 144.15.206.210 |
| `ousminimedoutcomes.medtronic.com` | 144.15.107.26 |
| `usminimedoutcomesstage.medtronic.com` | 144.15.170.40 |
| `ousminimedoutcomesstage.medtronic.com` | 144.15.109.26 |

`144.15.x.x` is the range `PROBE-FINDINGS.md` §7 already identified as
"Medtronic-internal IPs, TLS handshake hangs". Confirmed here: all five give
`http=000` (connection refused / TLS hang) in under 8 s from a public network.
Recorded for the internal-IP list; **not probed further**.

Related and public: `mypump.medtronic.com` → **404 text/html** (2.8 s, real
host, wrong path), `medtronicdiabetes.medtronic.com` (147.154.54.172),
`diabetesqualys.medtronic.com` (scanner host, no DNS answer),
`virtualassistant-diabetes-prod.medtronic.com` (144.15.195.130, internal),
`diabetesresoursesportal.medtronic.com` (185.10.198.46).

### 4.5 Internal-looking names — recorded, status only, **not** probed aggressively

`kubernetes.carelink.medtronic.com`, `vpn.carelink.medtronic.com`,
`internal.carelink.medtronic.com`, `analytics.carelink.medtronic.com`,
`carelink-clp01-ext.corp.medtronic.com`, `apiapp-alb-dr.carelink2.medtronic.com`,
`apiapp-alb.sit7.carelink9.medtronic.com`, `md.sit8.carelink9.medtronic.com`,
`oneapp.sit8.carelink9.medtronic.com`. None of these resolve to anything outside
144.15.x.x except the two `carelink2`/`carelink9` names (144.15.0.11,
144.15.20.105) and `carelink-clp01-ext.corp` (144.15.170.55) — all internal.
Zero of the 260 focus names resolved to an RFC1918 / CGNAT address.

### 4.6 Cert SAN recursion: **nothing gained**

`openssl s_client -showcerts` on `carelink.medtronic.com`,
`carelink-login.medtronic.com`, `clcloud.medtronic.com` — all three are
**single-SAN** certs (`DNS:<the host itself>`). No recursion possible, nothing
new. Recorded as a negative.

---

## 5. Full table — `carelink.eu` / `carelink.com` / `clcloud.eu` (49 new, all noise)

All resolve to the wildcard `103.224.182.253` (except `ww38` at `185.53.179.200`);
all 302 to `https://ww38.carelink.eu/`. Content-type `text/html`. **Classification:
`parked-domain — FALSE POSITIVE` for every row.** Status sampled on 3.

| name | resolves? | status | content-type | classification | new/known |
|---|---|---|---|---|---|
| `admin.carelink.eu` | yes (wildcard) | 302 | text/html | parked domain — FP | NEW |
| `www.admin.carelink.eu` | yes (wildcard) | — | — | parked domain — FP | NEW |
| `mail.carelink.eu` / `www.mail.carelink.eu` | yes (wildcard) | — | — | parked domain — FP | NEW |
| `m.carelink.eu` / `www.m.carelink.eu` | yes (wildcard) | — | — | parked domain — FP | NEW |
| `staging.carelink.eu` / `www.staging.carelink.eu` | yes (wildcard) | — | — | parked domain — FP | NEW |
| `superset.carelink.eu` | yes (wildcard) | 302 | text/html | parked domain — FP | NEW |
| `supersets.carelink.eu` / `www.supersets.carelink.eu` | yes (wildcard) | — | — | parked domain — FP | NEW |
| `superset-staging.carelink.eu` | yes (wildcard) | — | — | parked domain — FP | NEW |
| `superset.staging.carelink.eu` | yes (wildcard) | — | — | parked domain — FP | **NEW, CT-only** |
| `sitemap.carelink.eu`, `sitemaps.carelink.eu` (+`www.`) | yes (wildcard) | — | — | parked domain — FP | NEW |
| `www.carelink.eu`, `www.www.carelink.eu` | yes (wildcard) | 302 | text/html | parked domain — FP | NEW |
| `medtronic.carelink.eu`, `minimed.carelink.eu` (+`www.` ×2 each) | yes (wildcard) | — | — | parked domain — FP | NEW |
| typos: `medtronice`, `medtrinic`, `medtornic`, `cmedtronica`, `cmedtronic`, `metronic`, `otzctwww.medtrinic` (+`www.` variants, 13) | yes (wildcard) | — | — | parked domain — FP | NEW |
| `ww25.carelink.eu`, `ww38.carelink.eu` | yes | — | — | parking redirect **target** | NEW |
| `www.carelink.com` | NXDOMAIN (no A) | — | — | not Medtronic / placeholder | NEW |
| `abv.clcloud.eu`, `abvinvoices.clcloud.eu` (+`www.`), `nextcloud.clcloud.eu`, `odoo.clcloud.eu`, `lamafurnish*.clcloud.eu`, `www.clcloud.eu` | yes | — | — | **unrelated 3rd party**, parked | NEW |

`superset.staging.carelink.eu` is the only name in the whole pass that came from
crt.sh and **not** from subfinder.

---

## 6. Full table — new `medtronic.eu` names (68)

**0 of 68 are interesting.** 63 are NXDOMAIN cert-only leftovers
(`carelink-login-test1k`, `carelink-stage2w`, `carelink-support-stage2a`,
`wwwy.carelink-stage1`, `www-test`, `educationa`, `impactm`, …). 5 resolve, all
public marketing:

| name | resolves? | status | content-type | classification | new/known |
|---|---|---|---|---|---|
| `carelink-support-stage2.medtronic.eu` | yes | not probed | — | dev/stage name, prod IP | NEW |
| `education.medtronic.eu` | yes | not probed | — | marketing | NEW |
| `impact.medtronic.eu` | yes | not probed | — | marketing | NEW |
| `professional.medtronic.eu` | yes | not probed | — | marketing | NEW |
| `www-test.medtronic.eu` | yes | not probed | — | marketing | NEW |
| *(63 more, all NXDOMAIN)* | no | — | — | cert-only | NEW |

---

## 7. Full table — new `medtronic.com` diabetes-keyword names (246)

127 resolve, 119 are cert-only (NXDOMAIN). `medtronic.com` also yielded
**2 995 further new names outside this filter** — the general corporate estate
(`ndNNNNNN.global.medtronic.com`, `*.teneo`, `*.wpn`, `*.mcms`, `*.cc-internal`,
`*.corp`, `*.va`, marketing sites). Expected, not padding-worthy, not listed.

### 7.1 Resolving, prod-looking, **probed** (13)

| name | resolves? | status | content-type | classification | new/known |
|---|---|---|---|---|---|
| `carelink.medtronic.com` | yes (CF) | **200** | text/html 5518 B | **health-portal SPA, byte-identical to `carelinkhp.minimed.eu`** | NEW |
| `carelink-login.medtronic.com` | yes (CF) | **200** | application/json | **4th Auth0 tenant** (OIDC doc) | NEW |
| `clcloud.medtronic.com` | yes (CF) | **403** | application/json | cumulus host, **gateway-gated** | NEW |
| `carelink-support.medtronic.com` | yes (CF) | 200 | text/html 5518 B | health-portal SPA (same doc) | NEW |
| `carelink-site.medtronic.com` | yes (CF) | 301 | — | redirect | NEW |
| `carelink.medtronic.com` `/patient/users/me` | — | 200 | text/html | SPA catch-all, **not** an API | NEW |
| `carelink-support.medtronic.com` `/api/carepartner/v2/patient/users/me` | — | 200 | text/html | SPA catch-all, not an API | NEW |
| `mypump.medtronic.com` | yes | 404 | text/html | real host, no root route | NEW |
| `usminimedoutcomes.medtronic.com` | yes (144.15.206.78) | **000** | — | **internal origin — not publicly reachable** | NEW |
| `ousminimedoutcomes.medtronic.com` | yes (144.15.107.26) | **000** | — | internal origin — not reachable | NEW |
| `minimedoutcomes-usapi.medtronic.com` | yes (144.15.206.210) | **000** (8 s timeout) | — | internal origin — not reachable | NEW |
| `carelink-clinical.medtronic.com` | yes (144.15.206.181) | **000** | — | internal origin — not reachable | NEW |
| `carelink-temptrials.medtronic.com` | yes | **000** | — | not reachable | NEW |

### 7.2 Resolving, dev/stage/test/load — **DNS only, not probed** (114)

Per project policy these are enumerated, not touched. All resolve to public
CloudFront edges (`13.33.x`, `18.24x.x`, `52.2xx.x`, `99.86.x`, `216.137.x`,
`3.17x.x`) except the internal 144.15.x ones. Full list in
`resolve.jsonl` / `c-resolving.txt`. Sample:

`carelink-clinical-stage1{,-next}.medtronic.com`,
`carelink-clinical-support-{stage1,stage1-next,stage3,test1}.medtronic.com`,
`carelink-clinical-test1.medtronic.com`, `carelink-dev1.medtronic.com`,
`carelink-load1.medtronic.com`, `carelink-login-{clinical-stage1-next,
clinical-test1,next,stage1,stage1-next,test1}.medtronic.com`,
`carelink-next.medtronic.com`, `carelink-prod.medtronic.com` (144.15.206.173),
`carelink-stage{1,1-next,2-next,3}.medtronic.com`, `carelink-test1.medtronic.com`,
`carelink-temptrials-support.medtronic.com`,
`carelink-support-{dev1,load1,next,stage1,stage1-next,stage2-next,stage3,test1}`,
`carelink-trials{,-next,-support,-support-next,-login}.medtronic.com`,
`clcloud-{clinical-stage2,clinical-stage3,clinicaltest,next,stage,stage2,stage3,
stage-next,trials,trials-next,ustest}.medtronic.com`,
`commoncore-{clinical-stage1,clinical-stage1-next,clinical-test1,next,stage1-next,
stage2-next,stage3,test1,trials,trials-next}.medtronic.com`,
`status.carelink-stage1.medtronic.com`, `diabetes001.teneo-stage.medtronic.com`.

### 7.3 Cert-only, NXDOMAIN (119) — not listed individually

Include `carelink-cms.medtronic.com`, `carelink-support-stage1u.medtronic.com`,
`carelink-login-clinical-stage1.medtronic.com`, `commoncore-stage1.medtronic.com`,
`trials.medtronic.com`, `minimed.medtronic.com`, `secure-messaging.diabetes.
medtronic.com`, `us-health.api.medtronic.com`, `eu-health.api.medtronic.com`,
`medtronicdatacatalog.medtronic.com`, `go.carelink.medtronic.com`,
`support.carelink.medtronic.com`, `video.carelink.medtronic.com`,
`kubernetes.carelink.medtronic.com`, `vpn.carelink.medtronic.com`,
`internal.carelink.medtronic.com`, `analytics.carelink.medtronic.com`,
`api.carelink-content.medtronic.com`, `status.carelink-content.medtronic.com`,
`md.sit8.carelink9.medtronic.com`, `oneapp.sit8.carelink9.medtronic.com`.

CNAME-only (DNS resolves to a CloudFront alias, but `dig A` returns no address
and the origin refuses public TLS): `carelink-trials-support-next.medtronic.com`
→ `dwx4akx3no2at.cloudfront.ner.`. One GET: `http=000`, not publicly reachable.
Full list: `new-names-diabetes-com.txt` filtered against `rnodns.txt`.

---

## 8. "Found nothing new" — where that is the honest answer

- **`*.minimed.eu` / `*.minimed.com` / `*.medtronic.eu`: nothing new. 213 + 385 +
  129 names collected, 0 new.** The space is saturated for this technique.
- **Cert SAN recursion: nothing new.** All three `.medtronic.com` certs are
  single-SAN.
- **`carelink.eu` / `clcloud.eu`: nothing new *of Medtronic's*.** 49 names, all
  provably not Medtronic.
- **No internal/RFC1918 exposure.** 0 of 260 focus names resolved to a private
  address. Every internal-looking name is on 144.15.x.x and refuses public TLS.
- **No unauthenticated data.** Every API-shaped request returned 401/403/SPA
  HTML. Nothing was read that a logged-out browser cannot already get.

## 9. What I did NOT do

- Did not attempt auth, token acquisition, or any write.
- Did not probe dev/stage/test/load hosts (DNS only).
- Did not enumerate paths on any host, did not bruteforce DNS, did not port scan.
- Did not recurse into `www.*` variations beyond what the passive sources gave.
- Did not write the vendor `x-api-key` anywhere. It remains only in
  `research/probe-2026-10-08/SECURITY-FINDINGS.md` (§S3).
- Did not touch git. All outputs are confined to `research/probe-2026-10-08/recon/`.