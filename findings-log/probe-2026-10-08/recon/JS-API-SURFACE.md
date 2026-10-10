# JS API surface — `carelinkhp` (CareLink Clinic / HCP portal) bundle

**Date:** 2026-10-09 · **Mode:** purely offline static analysis · **Network calls made:** 0

**Asset:** `security/js/hp-main.js` — 3,397,615 B, 102 lines, minified Angular 17
webpack build, `webpackChunkpow` namespace. Downloaded 2026-10-08 23:15.
Companion: `security/js/hp-runtime.js` (8,597 B).

**Scope note up front:** the previous JS mining is in `APP-EMULATION-RESEARCH.md`
§8–§10 (device table, report catalogue, `hcp/*` map). This pass does **not** redo
that; it recovers it exactly, then goes after the families that doc did not reach.
The "NEW" section below is the delta.

> ⚠️ **Credential handling.** The bundle contains one hardcoded `x-api-key` literal
> for the `reports-broker`/`reports-metadata` service. Its value is **not
> reproduced here**. It is the same value already recorded in
> `APP-EMULATION-RESEARCH.md` §10. All artefacts written to `recon/js/` have it
> replaced with `<REDACTED-see-APP-EMULATION-RESEARCH-s10>`. Treat it as a public
> client-side key, not a secret — it ships to every visitor of the portal.

---

## 0. Commands used

```bash
cd research/probe-2026-10-08/security/js

# size / shape
wc -c hp-main.js; file hp-main.js; wc -l hp-main.js

# 1. hosts
rg -o 'https?://[a-zA-Z0-9._~:/?#@!$&()*+,;=%-]+' hp-main.js | sort | uniq -c | sort -rn
rg -o '[a-zA-Z0-9][a-zA-Z0-9._-]{2,60}\.(?:medtronic|minimed|amazonaws|cloudfront|intercom|pusher)\.[a-z]{2,6}' hp-main.js | sort | uniq -c | sort -rn
rg -o '\b[a-zA-Z0-9][a-zA-Z0-9-]{1,40}\.(?:com|eu|net|org|io|co\.uk|dev|appspot|cloudfront\.net|amazonaws\.com)\b' hp-main.js | sort -u

# 2. paths
rg -o --byte-offset '" ?/?hcp/[a-zA-Z0-9._()/-]*"' hp-main.js
rg -o '"[A-Za-z0-9_./()\[\]{}+$@:~!?&=%-]*/[A-Za-z0-9_./()\[\]{}+$@:~!?&=%-]{1,70}"' hp-main.js | sort -u

# 3. templates
rg -o '`[^`]{0,60}/[a-zA-Z0-9._/-]{2,40}[^`]{0,40}`' hp-main.js | sort -u
rg -o '\(\([a-zA-Z0-9_.]+\)\)' hp-main.js | sort | uniq -c | sort -rn

# 4. device vocabulary
rg -o 'MMT-?[0-9]{2,5}[A-Za-z]*' hp-main.js | sort | uniq -c | sort -k2
rg -o 'SKU-[0-9A-Za-z-]+' hp-main.js | sort | uniq -c | sort -k2
rg -o 'deviceType:"[^"]*"' hp-main.js | sort | uniq -c

# 5. enums / tables
rg -o '\.[A-Za-z_$][A-Za-z0-9_$]{1,30}="[A-Z][A-Z0-9_]{1,30}"' hp-main.js | sort -u

# 6. realtime
rg -oF -e WebSocket -e EventSource -e sendBeacon hp-main.js | wc -l

# context windows (the workhorse)
rg -o --byte-offset '.{250}PATTERN.{350}' hp-main.js
```

Byte offsets are into `hp-main.js` and are stable as long as the file is.
Extracted artefacts: `recon/js/*.txt`, `recon/js/alias-endpoint.tsv`,
`recon/js/hcp-literals.tsv`.

---

## 1. Host / hostname literals

### 1.1 Absolute URLs, Medtronic-owned

| Host | Count | Byte offset | Note |
|---|---:|---:|---|
| `https://dev.commoncore.medtronic.eu/reports-metadata/v1/ocl` | 1 | 3323496 | hardcoded default for the reports **metadata** service |
| `https://dev.commoncore.medtronic.eu/reports-broker/v1/ocl` | 1 | 3323793 | hardcoded default for the reports **broker** service |

Verbatim (`recon/js/commoncore-service-configs.txt`):

```js
const $={security_headers:{"x-api-key":"<REDACTED>"},
  host:"https://dev.commoncore.medtronic.eu/reports-metadata/v1/ocl",
  report_data_time_lines_range:"/reports/ReportDataTimelinesRange/patients",
  report_data_time_lines_for_calendar:"/reports/ReportDataTimelinesForCalendar"},
q={security_headers:{"x-api-key":"<REDACTED>"},
  host:"https://dev.commoncore.medtronic.eu/reports-broker/v1/ocl",
  generate_report:"/reports/generateReport",report_status:"/reports/reportStatus",
  report_csv:"/reports/reportCsv",report_pdf:"/reports/reportPdf"},
```

**This is the entire Medtronic host surface of the bundle.** Two occurrences of
one `dev.` host. Nothing else. See §7 for why.

### 1.2 Absolute URLs, third-party / library (not API surface)

| Host | Count | What |
|---|---:|---|
| `https://api-js.mixpanel.com` | 1 | Mixpanel collector (`api_host` default) |
| `https://mixpanel.com` | 1 | Mixpanel `app_host` |
| `https://cdn.mxpnl.com` | 1 | Mixpanel CDN |
| `https://cdn.mxpnl.com/libs/mixpanel-recorder.min.js` | 1 | session-replay recorder |
| `https://mixpanel.com/projects/replay-redirect?` | 1 | replay redirect |
| `https://js.pusher.com` | 2 | Pusher CDN (`m_cdn_http`/`m_cdn_https`) |
| `http://js.pusher.com` | 1 | Pusher CDN (non-TLS default) |
| `https://sockjs.pusher.com` | 1 | SockJS websocket host |
| `https://stats.pusher.com` | 1 | Pusher telemetry host |
| `https://pusher.com` | 1 | link in Pusher docs URL |
| `https://cdnjs.cloudflare.com/ajax/libs/pdfobject/2.1.1/pdfobject.min.js` | 1 | PDF viewer |
| `https://webpjs.appspot.com` | 1 | WebP support detection |
| `http://www.w3.org/2000/svg` | 192 | SVG namespace (noise) |
| `http://www.w3.org/1999/xlink` | 25 | XLink namespace (noise) |
| `http://www.w3.org/…/1999/xhtml`, `/XML/1998/namespace`, `/2000/xmlns/`, `/1999/02/22-rdf-syntax-ns#`, `/1998/Math/MathML` | 1 ea | XML namespaces (noise) |
| `http://opensource.org/licenses/mit-license` | 11 | license banner (noise) |
| `https://material.angular.io/guide/theming` | 1 | doc link |
| `https://angular.dev/best-practices/security#…` | 1 | doc link |
| `https://ngrx.io/guide/store/configuration/runtime-checks` | 1 | doc link |
| `https://github.com/pusher/pusher-js/tree/cc4910…#encrypted-channel-support` | 1 | comment link |
| `https://github.com/stevermeister/ngx-cookie-service/issues/86#…` | 1 | comment link |
| `https://jspdf.default.namespaceuri/` | 1 | jsPDF namespace |
| `examples/PDF.js/web/viewer.html` | 1 | pdf.js viewer path |

**Distinct third-party hosts: 12.** **Distinct Medtronic hosts: 1.**

### 1.3 Hostnames that are NOT in the bundle (decisive negatives)

`rg -oiF` counts vs case-sensitive counts:

| Token | `-i` hits | case-sensitive hits | Verdict |
|---|---:|---:|---|
| `minimed` | 5 | 5 | only `asset_logo_minimed.svg`, `minimedgo.inpen.name.US` ×2, `V.minimedGo`, `V.minimedGoOLID` |
| `carelink` | 0 | 0 | **absent** |
| `patient/` | 0 | 0 | **absent** |
| `monitor/` | 0 | 0 | **absent** |
| `pde/` | 0 | 0 | **absent** |
| `carepartner` | 3 | 3 | all three are analytics event *names* (`click_carepartner_existing_reset_search` etc.), not paths |
| `/oauth` | 0 | 0 | **absent** — the 2 case-insensitive hits are the zxcvbn wordlist (`coauthored`, `coauthor`) |
| `/api/` | 0 | 0 | the 2 hits are Pusher doc links `/docs/channels/server_api/…` |

> **The clinic-portal bundle contains zero patient-CareLink endpoints.** It is a
> different application from the mobile app. It reaches the patient portal only
> via the "invite to personal" family (§2.3). Anyone looking for
> `/patient/connect/data` or `/connect/carepartner/v13/display/message` in this
> file will not find them and should not keep looking.

---

## 2. API path literals

### 2.1 `hcp/*` — 183 distinct literals, 188 const bindings

All live on the **portal origin** (relative paths, no host). Byte-offset of the
constants table: **2761700–2768900**, module `66703`, re-exported by module
`42205`. Full alias→path map in `recon/js/alias-endpoint.tsv`
(188 export aliases resolved, of which 8 map to the `/hcp/…` leading-slash
duplicates below).

Counting, precisely: **189 raw quoted hits → 183 distinct paths**; **175** begin
`hcp/` and **8** begin `/hcp/` (a second binding of the same path, so those 8 are
not additional endpoints). One further literal has a leading space.

Grouped by family, with in-bundle reference counts (`0` = the constant is
declared and re-exported but **no call site exists in this bundle** — its
consumer is in a lazy chunk):

| Family | Distinct | Notes |
|---|---:|---|
| `hcp/users…` → `hcp/user/*` | 29 | full clinic-user admin API |
| `hcp/clinics/*` | 40 | incl. 12 `toggle/*` and 5 MFA endpoints |
| `hcp/patients/*` | 47 | incl. 18 `((patientId))/*` |
| `hcp/configuration/*` | 21 | app/product/config bootstrap (6 direct + 15 `public/*`) |
| `hcp/reports/*` | 10 | 4 of them audit-log reports |
| `hcp/dataUpload/*` | 6 | |
| `hcp/insights/v1/*` | 8 | |
| `hcp/anonymization/*` | 4 | |
| `hcp/access-data/*` | 4 | + `hcp/v2/clinics/access-data` |
| `hcp/follow-up/*` | 4 | |
| `hcp/user…` remote/`fastLinking`/`linkedPatient` | 7 | |
| `hcp/sso/*` | 3 | login/logout/reauth |
| `hcp/registrationCheck/*`, `hcp/ping/ping`, `hcp/locale/*`, `hcp/countries/*`, `hcp/remoteLinking/*`, `hcp/settings-calculator/*` | 14 | 4 of these have **0** call sites |

**Complete list, verbatim** (from `recon/js/hcp-literals.tsv`, 189 hits /
183 distinct):

<details><summary>expand</summary>

```
hcp/access-data                                        hcp/configuration/public/cms-config.json
hcp/access-data/activate                               hcp/configuration/public/cua.control.codes.settings
hcp/access-data/revoke                                 hcp/configuration/public/cua.crm.settings
hcp/access-data/suspend                                hcp/configuration/public/hcp.banner.notifications
hcp/anonymization/createUserName                       hcp/configuration/public/logbook.supported.entry.types
hcp/anonymization/getCountryAnonymizationSetting      hcp/configuration/public/personal/media/config
hcp/anonymization/getNewSystemId                       hcp/configuration/public/pow.common.core.report.generation
hcp/anonymization/updateClinicAnonymization            hcp/configuration/public/pow.country.media.groups
hcp/clinics/access-data/disable                        hcp/configuration/public/pow.crm.settings
hcp/clinics/care-teams                                 hcp/configuration/public/pow.follow.up.settings
hcp/clinics/clinic-outcomes/reference                  hcp/configuration/public/pow.invite.to.personal.uri
hcp/clinics/createClinic                               hcp/configuration/public/pow.nutrino.cc.broker.service.config
hcp/clinics/disableDataSharing                         hcp/configuration/public/pow.nutrino.cc.metadata.service.config
hcp/clinics/disableMultiFactorAuth                     hcp/configuration/public/system.logbook.entry.validation.config
hcp/clinics/enableMultiFactorAuth                      hcp/configuration/user
hcp/clinics/getClinic                                  hcp/configuration/whitelisted
hcp/clinics/getClinicMultiFactorAuthParams             hcp/countries/getCountryStates
hcp/clinics/getClinicPreferences                       hcp/countries/getPostalCodePattern
hcp/clinics/getClinicUserSecurityProfile               hcp/dataUpload/generateUrl
hcp/clinics/getClinics                                 hcp/dataUpload/getRecentUploadInfo
hcp/clinics/getCountryLocaleSettings                   hcp/dataUpload/getSnapshot
hcp/clinics/getDefaultMfaSettings                      hcp/dataUpload/getTokenStatus
hcp/clinics/getPasswordRules                           hcp/dataUpload/getTrace
hcp/clinics/notifications/contact-info                 hcp/dataUpload/getUploaderLogs
hcp/clinics/registerKey                                hcp/fastLinking/fastLinking…
hcp/clinics/remote-monitoring/settings                 hcp/fastLinking/isFastLinkingAllowed
hcp/clinics/reports/supported                          hcp/follow-up/domains
hcp/clinics/resetToDefaultSecuritySettings             hcp/follow-up/domains/((domainId))
hcp/clinics/toggle/blinded-cgm                         hcp/follow-up/templates
hcp/clinics/toggle/clinic-outcomes                     hcp/follow-up/templates/((templateId))
hcp/clinics/toggle/clinic-user-settings                hcp/insights/v1/acceptTerms
hcp/clinics/toggle/csv                                 hcp/insights/v1/generateOneTimeCode
hcp/clinics/toggle/patient-dashboard                   hcp/insights/v1/generateReport
hcp/clinics/toggle/remote-monitoring                   hcp/insights/v1/generateReportWithCode
hcp/clinics/toggle/status                              hcp/insights/v1/getReportPdf
hcp/clinics/toggle/therapy-data                        hcp/insights/v1/getReportStatus
hcp/clinics/toggle/titr-settings                       hcp/insights/v1/userStatus
hcp/clinics/updateClinic                               hcp/insights/v1/validateOneTimeCode
hcp/clinics/updateClinicPreferences                    hcp/locale/translation
hcp/clinics/updateClinicUserSecurityProfile            hcp/linkedPatient
hcp/configuration/access/config                        hcp/linkedPatient/password/compliance
hcp/configuration/appContext                           hcp/linkedPatient/password/rules
hcp/configuration/application                          hcp/linkedPatient/username/check
hcp/configuration/productContext                       hcp/patients/((patientId))/care-partner
hcp/configuration/productContext                       hcp/patients/((patientId))/care-partner/link
hcp/patients/((patientId))/care-partner/unlink
hcp/patients/((patientId))/control-codes               hcp/patients/getInviteToPersonalSubjectPlaceholder
hcp/patients/((patientId))/insights/disable            hcp/patients/getInviteToPersonalTemplate
hcp/patients/((patientId))/logbook/entries             hcp/patients/getPatient
hcp/patients/((patientId))/logbook/entries/filled      hcp/patients/getPatientsMealProfilesAndDailyHabits
hcp/patients/((patientId))/logbook/entries/last        hcp/patients/linkPatient
hcp/patients/((patientId))/long-acting/settings        hcp/patients/otc-linking/allowed
hcp/patients/((patientId))/otc-linking/code            hcp/patients/otc-linking/code/email/send
hcp/patients/((patientId))/otc-linking/email/template  hcp/patients/otc-linking/code/sms/send
hcp/patients/((patientId))/otc-linking/sms/template    hcp/patients/sendInviteToPersonal
hcp/patients/((patientId))/preferences                 hcp/patients/unFlagPatient
hcp/patients/((patientId))/remote-monitoring/settings  hcp/patients/unarchivePatient
hcp/patients/((patientId))/reports/supported           hcp/patients/unlinkPatient
hcp/patients/((patientId))/send/follow-up              hcp/patients/updatePatient
hcp/patients/((patientId))/toggle/blinded-cgm          hcp/patients/updatePatientsMealProfilesAndDailyHabits
hcp/patients/addPatient                                hcp/ping/ping
hcp/patients/archivePatient                            hcp/registrationCheck/checkClinicRegistrationKey
hcp/patients/care-partner/search                       hcp/registrationCheck/checkUsername
hcp/patients/clearPatientsFlags                        hcp/remoteLinking/isRemoteLinkingAllowed
hcp/patients/flagPatient                               hcp/remoteLinking/remoteLinkPatient
hcp/patients/getAllClinicArchivedPatients              hcp/reports/generateAuditLogs
hcp/patients/getAllClinicUnarchivedPatients            hcp/reports/generateReport
hcp/patients/reports/supported                         hcp/reports/getAuditLogCsv
hcp/reports/getAuditLogStatus
hcp/reports/getAuditLogsTimelinesForCalendar           hcp/reports/getReportCsv
hcp/reports/getReportPdf                               hcp/reports/getReportStatus
hcp/reports/getSnapshotTimelinesForCalendar            hcp/reports/getSnapshotTimelinesRange
hcp/settings-calculator/acceptDisclaimer                hcp/settings-calculator/generateReportPdf
hcp/settings-calculator/recalculate                     hcp/settings-calculator/recommendedValues
hcp/sso/login  hcp/sso/logout  hcp/sso/reauth          hcp/user/acceptTermsOfUse
hcp/user/activateUser  hcp/user/changeEmail  hcp/user/changePassword
hcp/user/changeUsersEmail  hcp/user/checkPassword  hcp/user/checkUserIdentifier
hcp/user/createUser  hcp/user/cua/admin/info  hcp/user/deactivateUser
hcp/user/deleteUserReportPreferences  hcp/user/demote  hcp/user/forgotPassword
hcp/user/forgottenPasswordChange  hcp/user/getAllUsers  hcp/user/getCountryLanguages
hcp/user/getCountryTitles  hcp/user/getCurrentUser  hcp/user/getMfaUserStatus
hcp/user/getUserLanguages  hcp/user/getUserPreferences  hcp/user/getUsers
hcp/user/loginUser  hcp/user/password  hcp/user/promote  hcp/user/resetUsersPassword
hcp/user/sendMfaCode  hcp/user/sendMfaCodeAfterReCaptcha  hcp/user/unlockAccount
hcp/user/updateUser  hcp/user/updateUserConfigs  hcp/user/updateUserPreferences
hcp/user/validateEmail  hcp/user/verifyMfaCode  hcp/v2/clinics/access-data
```

</details>

**Quirk worth recording:** the literal is `" /hcp/linkedPatient"` — **with a
leading space**. Byte offset 2762570 region. Harmless (browser collapses it in
the request line) but it means a naive string match on `/hcp/linkedPatient`
against this file's raw bytes will need to account for it.

### 2.2 Non-`hcp` path families

| Path | Count | Byte offset | What |
|---|---:|---:|---|
| `connect/retina` | 1 | 2860907 | Retina service path prefix — see §6 |
| `/crm` | 2 | 2401851, 2404579 | non-production CRM base URI fallback |
| `/pusher` | 3 | 2420727 area | Pusher library default HTTP path |
| `/pusher/auth` | 2 | 2420727 area | Pusher channel-authorisation endpoint |
| `/pusher/user-auth` | 1 | 2420862 | Pusher user-authentication endpoint |
| `/app/<key>?protocol=7&client=js&version=…` | template | 2430974 | Pusher handshake |
| `/timeline/v2/` | 1 | 2475869 | Pusher telemetry path (`statsHost`) |
| `/reports/generateReport` `reportStatus` `reportCsv` `reportPdf` | 1 ea | 3323793 | commoncore **broker** |
| `/reports/ReportDataTimelinesRange/patients` `ReportDataTimelinesForCalendar` | 1 ea | 3323496 | commoncore **metadata** |
| `/docs/channels/server_api/authenticating_users` `authorizing-users/` `/docs/javascript_quick_start` | 1 ea | 2422166 | Pusher docs links |
| `/settings/uploader` | 1 | 2942467 | **SPA route**, not an API path |
| `/tech-error/:status` | template | — | SPA route |

**Distinct non-`hcp` path families: 8** (retina, crm, pusher×4, timeline, reports×2, docs).

### 2.3 Families already known vs. not

Against `PROBE-FINDINGS.md` + `APP-EMULATION-RESEARCH.md` §10, the following
`hcp/*` families are **entirely absent from prior notes**:

- `hcp/sso/{login,logout,reauth}` and `hcp/ping/ping` — the portal's own session API
- `hcp/user/*` — 29 endpoints, the whole clinic-user admin surface
- `hcp/clinics/*` — 40 endpoints incl. MFA, security profile, and 12 `toggle/*`
- `hcp/patients/((patientId))/logbook/{entries,entries/filled,entries/last}`
- `hcp/patients/*otc-linking*` — 6 endpoints
- `hcp/patients/otc-linking/allowed`
- `hcp/patients/{getPatient,updatePatient,linkPatient,unlinkPatient,sendInviteToPersonal,getInviteToPersonalTemplate,getInviteToPersonalSubjectPlaceholder}`
- `hcp/patients/getPatientsMealProfilesAndDailyHabits` + `updatePatients…`
- `hcp/patients/((patientId))/long-acting/settings`
- `hcp/patients/((patientId))/preferences`
- `hcp/patients/((patientId))/toggle/blinded-cgm`
- `hcp/countries/{getCountryStates,getPostalCodePattern}`
- `hcp/registrationCheck/{checkUsername,checkClinicRegistrationKey}`, `hcp/clinics/registerKey`
- `hcp/configuration/{productContext,appContext,application,user,access/config,whitelisted}`
- `hcp/configuration/public/{pow.crm.settings,cua.crm.settings,personal/media/config,cms-config.json,pow.follow.up.settings,pow.country.media.groups,hcp.banner.notifications,pow.common.core.report.generation,pow.invite.to.personal.uri}`
- `hcp/v2/clinics/access-data`
- `hcp/dataUpload/generateUrl`, `getTokenStatus`

---

## 3. Runtime URL templates

### 3.1 `((placeholder))` — Angular `HttpClient` param interpolation

Only four placeholders exist in the whole bundle:

| Placeholder | Count | Used in |
|---|---:|---|
| `((patientId))` | 33 | 18 `hcp/patients/((patientId))/*` paths |
| `((templateId))` | 2 | `hcp/follow-up/templates/((templateId))` |
| `((countryCode))` | 2 | `hcp/configuration/public/user-identifier-settings?countryCode=((countryCode))` |
| `((domainId))` | 1 | `hcp/follow-up/domains/((domainId))` |

The interpolator is Angular's standard `HttpUrlEncodingCodec`:

```js
class Js{handle(A){return A.interpolateParams&&A.interpolateParams.default||A.key}}
```

So the runtime routes are, e.g.:

```
hcp/patients/((patientId))/{preferences,remote-monitoring/settings,long-acting/settings,
 control-codes,care-partner,care-partner/link,care-partner/unlink,send/follow-up,
 insights/disable,logbook/entries,logbook/entries/filled,logbook/entries/last,
 otc-linking/code,otc-linking/email/template,otc-linking/sms/template,
 reports/supported,toggle/blinded-cgm}
```

Manual `.replace()` is used in exactly one place (offset 2404600 area):

```js
this.http.get(e.zpq.replace("((countryCode))", R))
```

### 3.2 Server-driven base-URL composition — the important ones

These are the templates where **the host is not in the bundle**.

**(a) Retina remote-monitoring settings** — module `69143`, offset **3009313**.
Verbatim (`recon/js/retina-remote-monitoring-url.txt`):

```js
getRetinaRemoteMonitoringSettings(P,b){
  return this.store.select(m.$tM).pipe(switchMap(B=>{
    if(B){
      const V = B?.target_url + B?.clinic?.base_uri + B.clinic.endpoints.default_settings_uri;
      return this.http.get(P ? V+`?clinicId=${b}` : V);
    }
    return this.store.select(m.$tM).pipe(switchMap(H=>{
      const $ = H.target_url + H.clinic.base_uri + H?.clinic?.endpoints.default_settings_uri;
      return this.http.get(P ? $+`?clinicId=${b}` : $);
    }));
  }),catchError(()=>of(null)));
}
```

Three-part server-supplied host composition: `target_url` + `clinic.base_uri` +
`clinic.endpoints.default_settings_uri`, optionally `?clinicId=<id>`. Fed by the
`retinaEndpointsConfig` app-config slot.

**(b) CRM service URLs** — offset 3294261:

```js
lr = (crmConfig) => `${crmConfig.baseUri}/${crmConfig.product}/${crmConfig.version}`
Ai = (crmConfig) => `${crmConfig.baseUri}/${crmConfig.product}`
```

where `baseUri` comes from `productContext.crmSettings["base.uri"]` in production,
or the literal `"/crm"` otherwise (offset 2401851):

```js
const R = n.c.production ? U?.crmSettings["base.uri"] : "/crm";
```

**(c) CMS + media config** — module `87880`, offset **3186300**:

```js
loadMediaConfigs(we,Ce)      → `${Ce}/media/configurations/${we}.json`
loadPersonalMediaConfigs(we) → `${YPf}/${we}`     // YPf = hcp/configuration/public/personal/media/config
loadCmsConfigs(we)           → forkJoin([
                                 `${we}/cms-config.json`,
                                 `${we}/${document.domain}/cms-config.json`,
                                 LVD ])            // LVD = hcp/configuration/public/cms-config.json
getHttCall(we)               → http.get(we) … 404 → of({})
```

Two things here. `document.domain` in a URL template means the config is
**host-scoped** — the same bundle on a different hostname fetches a different
config. And `getHttCall` **silently swallows 404** and returns `{}`, so a missing
CMS config is indistinguishable from an empty one.

**(d) Reports broker/metadata** — offset 3326827:

```js
let pe = he.host;
switch(Ae){
  case R.TIMELINE_RANGE:      pe += he.report_data_time_lines_range;      break;
  case R.DATA_FOR_CALENDAR:   pe += he.report_data_time_lines_for_calendar; break;
}
return { headers: Ce, url: pe };
```

**(e) Portal login redirect** — offset 1702838:

```js
const B = new URL(e.YBY, window.location.origin);   // YBY = "hcp/sso/login"
B.searchParams.set("country", S); B.searchParams.set("lang", v);
E && B.searchParams.set("type", E);                   // HSP | POW | STUDY
C && B.searchParams.set("state", C);
P && (B.searchParams.set("ext-otc","true"), B.searchParams.set("username", w.username));
window.location.assign(B.toString());
```

**(f) Product context is origin-driven** — offset 2401851:

```js
loadProductContext(){ let U = {currentDomainUrl: window.location.origin}; … 
  return this.http.post(e.MN6 /* hcp/configuration/productContext */, U) … }
```

The client **tells the backend which host it is on**, and the backend answers with
a different CRM host, product type, and locale set. Same bundle, different
hostname ⇒ different backend surface.

---

## 4. Device / pump vocabulary

### 4.1 Model codes — verbatim, with counts

All from the device table at module `68462`, byte range **2999400–3007200**
(dumped to `recon/js/device-table-raw.txt`). **80 distinct `MMT-*`, 9 distinct
`SKU-*` = 89.** Every one appears exactly once **except `MMT-8062`** (×3 — twice
in the PUMP table, once in the commoncore mock payload).

<details><summary>verbatim device table</summary>

```js
const e = {
PUMP: {
  DEFAULT:{name:"",shortName:"",minValue:40,maxValue:400,webDashboardEnabled:!1},
  "MMT-1510":{name:"MiniMed™ 620G",shortName:"620G",webDashboardEnabled:!1},
  "MMT-1710":{name:"MiniMed™ 620G",shortName:"620G",webDashboardEnabled:!1},
  "MMT-1714":{name:"MiniMed™ 630G",…}, "MMT-1715":{name:"MiniMed™ 630G",…},
  "MMT-1511"/"MMT-1711"/"MMT-1512"/"MMT-1712": "MiniMed™ 640G",
  "MMT-1883"/"MMT-1740"/"MMT-1741"/"MMT-1742"/"MMT-1780"/"MMT-1781"/"MMT-1782": "MiniMed™ 670G",
  "MMT-1800"/"MMT-1801"/"MMT-1805": "MiniMed™ 700",
  "MMT-1809"/"MMT-1810"/"MMT-1817"/"MMT-1818": "MiniMed™ 720G",
  "MMT-1811"/"MMT-1812": "MiniMed™ 740G",
  "MMT-1880"/"MMT-1881"/"MMT-1882": "MiniMed™ 770G",
  "MMT-1884"/"MMT-1884XCU"/"MMT-1885"/"MMT-1885XCE"/"MMT-1886"/"MMT-1886XCE"/"MMT-1886XCF": "MiniMed™ 780G",
  "MMT-1900"/"MMT-1902"/"MMT-1904": "PCL F3",
  "MMT-515":{name:"MiniMed™ Paradigm 515",shortName:"Paradigm 515",webDashboardEnabled:!1},
  "MMT-715":{name:"MiniMed™ Paradigm 715",shortName:"Paradigm 715",webDashboardEnabled:!0},
  "MMT-551":{name:"MiniMed™ 530G - 551",…}, "MMT-751":{name:"MiniMed™ 530G - 751",…},
  "MMT-522":{name:"MiniMed™ Paradigm 522",…}, "MMT-722":{name:"MiniMed™ Paradigm 722",…},
  "MMT-523":{name:"MiniMed™ Revel - 523",…}, "MMT-723":{name:"MiniMed™ Revel - 723",…},
  "MMT-554":{name:"Paradigm Veo - 554",…},    "MMT-754":{name:"Paradigm Veo - 754",…},
  "MMT-1906"/"MMT-1907"/"MMT-1908": "MiniMed™ NMX7",
  "MMT-8162"/"MMT-8163": "MiniMed™ NMX8"  (minValue:50),
  "MMT-8062"/"MMT-8063"/"MMT-8082"/"MMT-8083"/"MMT-8084"/"MMT-8085": "Minimed Flex" (minValue:50)
},
SENSOR: {
  DEFAULT:{name:"",shortName:"",minValue:40,maxValue:400,webDashboardEnabled:!1},
  "MMT-7763"/"MMT-7731": "Enlite Sensor",
  "MMT-7811"/"MMT-7821"/"MMT-7910"/"MMT-7911": "Guardian™ Sensor 3",
  "MMT-7841": "Guardian™ 4 Sensor",
  "MMT-5120": "Simplera Sync™",
  MMT5100:"Synergy Sensor", "MMT-5100":"Synergy Sensor",
  MMT5101:"Synergy Sensor", "MMT-5101":"Synergy Sensor",
  "MMT-5420":"Instinct™ Sensor",
  "SKU-78893-01"/"SKU-78959-01"/"SKU-78960-01"/"SKU-78953-01"/"SKU-78955-01"/"SKU-78957-01":
      "Instinct™ Sensor",
  "SKU-78954-01"/"SKU-78956-01"/"SKU-78958-01": "Instinct™ Go"
},
StandaloneCGM: {
  DEFAULT:{name:"",shortName:"",minValue:40,maxValue:400,webDashboardEnabled:!1},
  "CSS-7200"/"CSS-7201"/CSS7200/CSS7201/gm3_snapshot: "Guardian Connect",
  "MMT-8200"/"MMT-8201"/gm4_snapshot: "Guardian™ 4 system",
  "MMT-6500"/"MMT-6501"/"MMT-8400"/"MMT-8401": "Simplera™ system"
},
InsulinDelivery: {
  DEFAULT:{name:"InPen",shortName:"InPen",minValue:40,maxValue:400,webDashboardEnabled:!1},
  "MMT-105NNBLNA":{name:"InPen",shortName:"InPen",webDashboardEnabled:!1,features:{
      patientListNonPremium:"InPen",
      clinicOutcomes:"minimedgo.inpen.name.US",
      dataCalendar:"MiniMed Go",
      patientDashboard:"minimedgo.inpen.name.US",
      patientListPremium:"InPen"}}
}};
var a = function(n){ return n.SIMPLERA_SYSTEM = "Simplera™ system", n }(a||{});
```

</details>

**Model codes present in the bundle but NOT in `APP-EMULATION-RESEARCH.md` §8:**

| Code(s) | Where |
|---|---|
| **`MMT-8600`, `MMT-8601`** | `const S=["MMT-8600","MMT-8601"]`, module `90991`, offset **3229672** — **not in the device table at all** |
| `MMT-515`, `MMT-715`, `MMT-551`, `MMT-751`, `MMT-522`, `MMT-722`, `MMT-523`, `MMT-723`, `MMT-554`, `MMT-754` | in the PUMP table, Paradigm/Revel/Veo era |
| `MMT5100`, `MMT5101` (unhyphenated) | SENSOR table, aliases of `MMT-5100`/`MMT-5101` |
| `CSS7200`, `CSS7201` (unhyphenated) | StandaloneCGM table, aliases of `CSS-7200`/`CSS-7201` |
| `MMT-1884XCU`, `MMT-1885XCE`, `MMT-1886XCE`, `MMT-1886XCF` | present, but the doc's 780G row renders them as `MMT-1884XCU` / `MMT-1885XCE` / `MMT-1886XCE` / `MMT-1886XCF` — consistent |

### 4.2 `MMT-8600` / `MMT-8601` — why it matters

Module `90991`, verbatim:

```js
const S = ["MMT-8600","MMT-8601"];
…
if (Ce.dM.includes(o.x2)) {                       // o.x2 === "InPen"
  const pe = Object.values(Ue.InsulinDelivery)[0];
  Ae.device = pe ? ie(pe, Q) : o.x2;
} else {
  Ae.device = ie( se[ S.includes(Ce.dM) ? Ce.sM : Ce.dM ], Q );
}
```

Read: for these two model codes the patient-list selector **ignores
`deviceModel` and displays `sensorModel` instead** (field `dM` = device model,
`sM` = sensor model — both minified). `Se` is the merged device table, and
neither `MMT-8600` nor `MMT-8601` is a key in it, so for these devices the
lookup can only succeed via the sensor-model branch.

**Interpretation (flagged, not asserted):** the portal ships device codes it
cannot name, and for those codes it deliberately prefers the *sensor* identity
for display. That is the signature of a pump whose own model code carries no
clinician-facing meaning — i.e. hardware that pairs with a separately-branded
sensor. Whether that is a Simplera-generation pump, an Instinct, or something
else **cannot be determined from this bundle** and should not be guessed at in
the repo.

### 4.3 Device *type* vocabulary — the wire tokens

Module `71825`, offset **3045682**, verbatim:

```js
const e = function(a){ return a.CC="CC", a.COSMOS="COSMOS",
  a.COSMOS_WHITELISTED="COSMOS_WHITELISTED", a.DEVICE="DEVICE", }(e||{});
```

And the pairing map, offset **3324368** (`recon/js/device-type-map.txt`):

```js
const Se = new Map([
  ["COSMOS_CC",         {single:[{deviceType:"CC"}],                        dual:[{deviceType:"CC"}]}],
  ["DEVICE_CC",         {single:[{deviceType:"CC"}],                        dual:[{deviceType:"Cosmos"},{deviceType:"CC"}]}],
  ["CC_COSMOS",         {single:[{deviceType:"Cosmos"}],                    dual:[{deviceType:"Cosmos"}]}],
  ["CC_DEVICE",         {single:[{deviceType:"Cosmos"}],                    dual:[{deviceType:"Cosmos"},{deviceType:"CC"}]}],
  ["COSMOS_CC_COSMOS",  {single:[{deviceType:"Cosmos"}],                    dual:[{deviceType:"Cosmos"}]}],
  ["DEVICE_CC_DEVICE",  {single:[{deviceType:"Cosmos",lastPeriod:!0}],      dual:[{deviceType:"Cosmos"},{deviceType:"CC"}]}],
  ["CC_COSMOS_CC",      {single:[{deviceType:"CC",lastPeriod:!0}],          dual:[{deviceType:"CC"}]}],
  ["CC_DEVICE_CC",      {single:[{deviceType:"CC",lastPeriod:!0}],          dual:[{deviceType:"Cosmos"},{deviceType:"CC"}]}],
  ["COSMOS_DEVICE_CC",  {single:[{deviceType:"CC"}],                        dual:[{deviceType:"Cosmos",lastPeriod:!0},{deviceType:"CC"}]}]
]);
```

Literal counts: `deviceType:"CC"` ×13, `deviceType:"Cosmos"` ×12. Note the
casing split — the **enum** is `"COSMOS"` but the **`deviceType` value** is
`"Cosmos"` (mixed case), which is the same class of trap as the
`"Simplera™ system"` / `SIMPLERA` case-sensitivity issue already flagged in
`APP-EMULATION-RESEARCH.md` §8.

The map encodes nine **dual-system pairings** — pump-side and sensor-side device
types for the same period, with `lastPeriod:!0` marking which one was active at
the end. `COSMOS_CC` / `CC_COSMOS` / `CC_DEVICE` / `DEVICE_CC` are all distinct
rows, so the pairing is ordered, not commutative.

### 4.4 Decisive negatives for issue #81

| Token | Case-sensitive hits | Verdict |
|---|---:|---|
| `deviceFamily` | 2 | only a localStorage patient-filter object `{deviceFamily: Ut.Ey.all, ageGroups:[…]}`. **Not an API field.** |
| `medicalDeviceFamily` | **0** | absent |
| `NGP` | **0** | all 51 case-insensitive hits are `loadingPromise`, `NavigateByUrl`, `kingpin`, `pingpong` in the zxcvbn wordlist |
| `BLE_MINIMED` | **0** | absent |
| `BLE` | **0** (as a token) | 2,735 case-insensitive hits are `TABLE`, `ENABLED`, `TABLE`… |
| `GUARDIAN` | **0** (as a token) | 29 hits are 3 in the zxcvbn wordlist (`guardian`, `guardians`, `guardianship`) and the rest are the **display names** in the device table (`Guardian™ Sensor 3`, `Guardian™ 4 Sensor`, `Guardian Connect`, `Guardian™ 4 system`) |
| `SIMPLERA` | 2 | only the TS enum key `SIMPLERA_SYSTEM` (value `"Simplera™ system"`) |
| `Ut.Ey.all` | 1 | deviceFamily-filter enum, server-populated |

**Conclusion for #81:** this bundle cannot answer the `deviceFamily` question.
The clinic portal's device vocabulary is **model codes** (`MMT-*`, `SKU-*`) and
**deviceType** (`CC`, `Cosmos`, `DEVICE`) — not the mobile payload's
`deviceFamily`/`medicalDeviceFamily` (`GUARDIAN`/`NGP`/`CGM`/`CC` per
`APP-EMULATION-RESEARCH.md` Round 3). The only overlap is the token **`CC`**,
which this bundle confirms as a first-class device *type*. Both the mapping keys
`deviceFamilyMapping` / `deviceToFamilyMapping` / `deviceModelMapping` are read
from `appConfig` and are **null in the shipped bundle**, so the live mapping is
entirely server-side. Recorded as an open question, not a resolution.

---

## 5. Alarm / status / code tables

### 5.1 What is here

| Enum | Verbatim values | Module/offset |
|---|---|---|
| Report job status | `NOT_READY="NOT_READY"`, `READY="READY"`, `ERROR="ERROR"`, `UNKNOWN="UNKNOWN"` | `15113`, 1011209 |
| Report job ops (broker) | `REPORT_STATUS=0`, `REPORT_CSV=2`, `REPORT_PDF=3` | 3323405 |
| Metadata request kind | `TIMELINE_RANGE=0`, `DATA_FOR_CALENDAR=1` | 3324368 |
| Report id → translation | 14 rows, ids 1–14 (verbatim below) | 1011543 |
| Product type | `HSP="HSP"`, `POW="POW"`, `STUDY="STUDY"` | `15113`, 1010460 |
| Report format | `PDF="pdf"`, `HTML="html"` | `15113` |
| Data source | `Meter="METER"`, `Sensor="SENSOR"`, `Pump="PUMP"` | `15113` |
| Password/OTP policy outcome | `OK`, `RENEW`, `REQUIRE`, `SUGGEST`, `NEED_CAPTCHA`, `EXPIRED_CODE` | 3355567 |
| Patient-clinic link | `ACCEPTED="ACCEPTED"`, `MANAGE="MANAGE"`, `POSTPONED="POSTPONED"` | 68746 |
| User status | `NEW="NEW"`, `SUSPENDED="SUSPENDED"`, `ACTIVE="ACTIVE"` | `54891`, 2502542 |
| MFA policy | `MANDATORY`, `OPTIONAL`, `NOT_AVAILABLE` | `54891` |
| Access-data filter | `ALL_PATIENTS`, `PATIENTS_WITH_ID_MRN` | `54891` |
| Access-data status | `AGGREGATED_AUTO_INSULIN`, `ALL_INSULIN` | `54891` |
| User groups | `user.clinic.user`, `user.clinic.admin`, `user.clinic.registrar`, `user.clinic.developer` | `54891` |
| Device type | `CC`, `COSMOS`, `COSMOS_WHITELISTED`, `DEVICE` | `71825`, 3045682 |
| Password rules | `requireLowerCase`, `requireUpperCase`, `requireSpecialCharacter`, `minLength`, `requireNumericCharacter`, `charactersAllowed`, `charactersNotAllowed`, `passwordStrength`, `containsUserData`, `previouslyUsedPassword` | `42301` |
| HTTP status (app-local) | `UnknownError=0`, `NotModified=204`, `BadRequest=400`, `Unauthorized=401`, `Forbidden=403`, `NotFound=404`, `InternalServerError=500`, `ServiceUnavailable=503`, `GatewayTimeout=504` | ~1526143 |
| Constants | `sessionTimeout`, `session_valid_to`, `v=5`, `E=10` (logout retry count) | ~1957784 |
| Date/format | `"YYYY-MM-DD"`, `"MM-DD-YYYY"`, `"1875-01-01"`, `new Date(1900,0,1)`, `60`, `{Sunday:0,…}` | `38175` |

Report id → translation map, verbatim:

```js
[[PatientDashboard,      {translation:"reports.patient.dashboard.title",           id:1}],
 [AssessmentAndProgress, {translation:"reports.assessment.and.progress.title",      id:2}],
 [BolusWizardFoodBolus,  {translation:"reports.food.bolus.wizard.report.title",     id:3}],
 [InsulinAssessment,     {translation:"reports.insulin.assessment.title",          id:4}],
 [WeeklyReview,          {translation:"reports.weekly.review.title",               id:5}],
 [DailyDetails,          {translation:"reports.daily.report.title",                id:6}],
 [DeviceSettings,        {translation:"reports.device.settings.report.title",      id:7}],
 [Adherence,             {translation:"reports.adherence.report.title",             id:8}],
 [Logbook,               {translation:"reports.logbook.report.title",              id:9}],
 [Dashboard,             {translation:"reports.dashboard.report.title",            id:10}],
 [EpisodeSummary,        {translation:"reports.episode.summary.report.title",      id:11}],
 [SensorAndMeterOverview,{translation:"reports.sensor.and.meter.overview.report.title", id:12}],
 [DataTable,             {translation:"reports.data.table.report.title",           id:13}],
 [SettingsHistory,       {translation:"reports.settings.history.report.title",      id:14}]]
```

### 5.2 Patient / user field vocabulary (module `54891`, offset 2501700)

Anonymisation column names — the `X-System-ID` surface:

```
PATIENT_FIRST_NAME  PATIENT_LAST_NAME  DATE_OF_BIRTH  SYSTEM_ID  DIABETES_TYPES
PATIENT_EMAIL  MRN  GENDER  MOBILE_PHONE  CARE_TEAM  NOTES  BLINDED_STATUS
```

Patient-list CSV columns (offset 3017382, **24** of them, verbatim array):

```
FLAGGED_PATIENT_INDICATOR LAST_NAME FIRST_NAME SYSTEM_ID DATE_OF_BIRTH PATIENT_ID
EMAIL PERSONAL_LINKED_STATUS DEVICE UPLOADED_DATE TRIAGE_STATUS LAST_FOLLOW_UP
THERAPY_DATA GLUCOSE_INDICATOR TIME_IN_AUTO_MODE TRIAL_ARM_ID BLINDED_CGM
ACTIONS_ICON TIME_BELOW_LOWEST_RANGE TIME_BELOW_RANGE TIME_ABOVE_RANGE
TIME_ABOVE_HIGHEST_RANGE COEFFICIENT_OF_VARIATION SENSOR_WEAR
```

Wire patient fields: `firstName lastName dob group systemId diabetesType email mrn
gender phone careTeam notes age linkedWithPersonal trialArmId phoneDetails
personalUsername blindedStatus tags`.

### 5.3 What is NOT here

- **No NGP alarm codes.** No `"N24"`, no `errorStrings`, no alarm-code table.
  `rg -o '\bN[0-9]{1,3}\b'` produces only date fragments and version numbers.
  Issue #84's vocabulary is **not** in this bundle.
- **No pump-status enums.** No `BLUETOOTH_OFF`, `PUMP_PAIRING_LOST`,
  `LOST_PUMP_SIGNAL`, `UPDATING`, `SUSPENDED` (as a pump status), or
  `lastSGTrend` values.
- **No treatment/marker types.** `MEAL` and `INSULIN` appear exactly once each
  in the whole file and not as quoted string literals — they are substrings.
  No `BOLUS_WIZARD_FOOD_BOLUS`-as-marker, no `bolusType`, no `Marker` schema.
- **No control-code vocabulary.** `cua.control.codes.settings` is fetched by
  alias only; the schema lives in a lazy chunk.
- **No logbook entry-type vocabulary**, same reason.

**Why:** the clinic portal reads *reports and summaries*, not raw pump payloads.
The raw-data vocabulary the bridge needs lives in the mobile app, not here.

---

## 6. Realtime / push channel

### 6.1 The channel: Pusher Channels over SockJS, branded "Retina"

Module `28291`, offset **1630561**, verbatim (`recon/js/retina-pusher-service.txt`):

```js
const C = function(I){ return I.SETTINGS_CHANGED = "Clinic_Settings_Update", I }(C||{}),
      P = function(I){ return I.PATIENT="P", I.CLINIC="C", I }(P||{}),
      b = function(I){ return I.IN_PROGRESS="InProgress", I.COMPLETED="Completed",
                               I.FAILED="Failed", I }(b||{});
class H {
  clinicRecalculationsCompleted(){ … }
  constructor($,q,j){ …; this.timeOutPeriod = 18e5; … }

  initPusherConnection($){
    if(this.currentClinicUserId !== $){
      this.unsubscribeRetinaPusher();
      this.currentClinicUserId = $;
      try{
        this.store.select(w.AU).pipe(takeUntilDestroyed(this.destroyRef)).subscribe(q=>{
          this.subscribeOnRetinaPusher(q.appKey, q.cluster, this.transformedChannelId($));
        });
      }catch(q){ console.log(q) }
    }
  }

  subscribeOnRetinaPusher($, q, j){
    const U = new Pusher($, { cluster: q });
    this.pusherSubscription = U.subscribe(j);
    this.pusherSubscription.bind(C.SETTINGS_CHANGED, ({ map: R }) => {
      if (R.type === P.CLINIC && R.status === b.COMPLETED &&
         (window.location.pathname.endsWith(ROUTE.patients) &&
          this.store.dispatch(loadPatientTheraphyData({})), this.unsubscribeRetinaPusher()),
       R.type === P.PATIENT && R.status === b.COMPLETED){
        const z = +R.identifier;
        z === this.currentPatientId && window.location.pathname.endsWith(ROUTE.dashboard)
          && this.store.dispatch(getPatientDashboard({ patientId: z, clinicId: +this.currentClinicUserId }));
        this.unsubscribeRetinaPusher();
      }
    });
    this.unsubscribeRetinaPusherByTimeout();
  }

  unsubscribeRetinaPusher(){ … unbind(); unsubscribe(); disconnect(); }

  unsubscribeRetinaPusherByTimeout(){
    const $ = setTimeout(() => this.unsubscribeRetinaPusher(), this.timeOutPeriod);
    clearTimeout($);
  }

  transformedChannelId($){ const q = +$; return (q*q + q).toString(16); }
}
```

**Facts:**

1. **Event name:** `Clinic_Settings_Update`.
2. **Payload shape:** `{ map: { type: "C" | "P", status: "InProgress" | "Completed" | "Failed", identifier: <patientId> } }`.
3. **Channel name derivation — deterministic, no secret:**
   `channelId = (clinicUserId² + clinicUserId).toString(16)`. Anyone holding a
   clinic user ID can compute any user's channel name. Channel-name opacity
   provides no authorisation here; the only real gate is the Pusher `appKey`,
   which arrives in `appConfig.pusherSettings` to every authenticated clinic user.
   The bundled pusher-js comment even cites
   `…pusher-js#encrypted-channel-support`, i.e. the developers considered it.
4. **The 30-minute timeout is dead code.** `unsubscribeRetinaPusherByTimeout()`
   calls `setTimeout(...)` and then `clearTimeout(...)` on the returned handle in
   the same synchronous block. The timer never fires; `timeOutPeriod = 18e5`
   (1 800 000 ms = 30 min) is inert. The subscription is torn down only by the
   event handler or explicit `initPusherConnection` churn.
5. **Feature flag is off in this build.** Module `17762`:
   `const e = { production: !0, retinaEnabled: !1, cuaEnabled: !1, currentDomainUrl: null }`
   (`recon/js/env-flags.txt`). `retinaEnabled` is referenced 3×, `cuaEnabled`
   22×; the only write found is `.cuaEnabled = Oe.c.cuaEnabled`. So the Pusher
   code is present but the feature ships disabled in this bundle.

### 6.2 Pusher library configuration (verbatim, offset 2420727)

```
_PROTOCOL=7, m_wsPort=80, m_wssPort=443, m_wsPath="",
m_httpHost="sockjs.pusher.com", m_httpPort=80, m_httpsPort=443,
m_httpPath="/pusher", m_stats_host="stats.pusher.com",
m_authEndpoint="/pusher/auth", m_authTransport="ajax",
m_activityTimeout=12e4, m_pongTimeout=3e4, m_unavailableTimeout=1e4,
m_userAuthentication={endpoint:"/pusher/user-auth", transport:"ajax"},
m_channelAuthorization={endpoint:"/pusher/auth", transport:"ajax"},
m_cdn_http="http://js.pusher.com", m_cdn_https="https://js.pusher.com"
```

Both auth endpoints are pusher-js **defaults**, on the pusher-js host, not on a
Medtronic host. There is no evidence in this bundle of a Medtronic-hosted Pusher
auth proxy.

### 6.3 No SSE, no other websocket

| Transport | Count | Verdict |
|---|---:|---|
| `EventSource` | 0 | no SSE |
| `WebSocket` | 10 | all inside pusher-js (transport selection) |
| `sendBeacon` | 3 | Angular/Mixpanel telemetry, not an API push |
| `SharedWorker` / `BroadcastChannel` | 0 | — |
| `navigator.onLine` | 6 | connectivity check only |

### 6.4 Polling that *does* exist

| Poll | Interval | Endpoint |
|---|---|---|
| Session keep-alive | on demand (`continueSession()`) | `GET hcp/ping/ping` (`responseType:"text"`) |
| Session-timeout dialog countdown | **1 000 ms** (`setInterval(…,1e3)`), logs off at `cookie("session_valid_to") + 60 000` ≤ now | none (local) |
| Report generation status | **2 000 ms** (`repeat({delay:2e3})`) until status ≠ `NOT_READY` | `hcp/reports/getReportStatus` and the commoncore broker `report_status` |
| Access-token refresh | one-shot `setTimeout(expiry − now)`, reschedules on completion | `POST hcp/sso/reauth` |
| Logout | **10** retries at **1 000 ms** (`retry({delay:1e3})`, counter `E=10`) | `GET hcp/sso/logout` |

Session API, verbatim (offset ~1535000):

```js
logIn(Ft)         { return this.http.post(w.k68, Ft) }                     // hcp/user/loginUser
logOut()          { return this.http.get(w.FA1, {observe:"response", responseType:"text"}) }  // hcp/sso/logout
continueSession() { return this.http.get(w.JgQ, {responseType:"text"}) }  // hcp/ping/ping
refresh()         { return this.http.post(w.a44, null) }                  // hcp/sso/reauth
```

---

## 7. NEW — not in PROBE-FINDINGS.md / APP-EMULATION-RESEARCH.md

Ordered by value to this project. Each item states why I believe it is new.

### 7.1 `MMT-8600` / `MMT-8601` — model codes with no name in the same bundle

> `const S=["MMT-8600","MMT-8601"]`, module `90991`, offset **3229672**. Used as
> `S.includes(Ce.dM) ? Ce.sM : Ce.dM` — i.e. for these two codes the portal
> displays the **sensor** model, not the device model.

**Why new:** `rg -o 'MMT-?[0-9]{2,5}'` finds each exactly once, and that one
occurrence is *outside* the device table (2999400–3007200). The device table
that ships in the same file has no entry for either code. No prior note mentions
8600/8601. This is the strongest device-vocabulary lead the bundle contains, and
it is orthogonal to issue #81's `deviceFamily` question (see §4.4 — that question
is *not* answerable here).

### 7.2 `connect/retina` — a service namespace with a header exemption

> ```js
> intercept(N, ue){
>   return N.url.includes("connect/retina") ||
>     (N = N.clone({ setHeaders: { "X-System-ID": "ProWeb" } })),
>     ue.handle(N);
> }
> ```
> offset **2860907**.

**Why new:** no prior note records the `X-System-ID: ProWeb` header at all, and
none records that a path-matching exemption exists for it. Two facts fall out:
(a) every portal request carries `X-System-ID: ProWeb`; (b) **the retina service
is the one path that must not carry it** — which is a strong hint that the retina
service authenticates differently (different host, different principal). Also
confirms the namespace name for a service whose host is server-configured.

### 7.3 The Retina base URL is a 3-part server-composed URL

> `target_url` + `clinic.base_uri` + `clinic.endpoints.default_settings_uri`
> `[+ "?clinicId=<id>"]`, module `69143`, offset **3009313**.

**Why new:** this is the clinic-portal analogue of `baseUrlCumulus` /
`baseUrlPde` from the mobile discovery doc, which *is* documented — but this
instance is not. It means there is at least one more Medtronic service host
reachable only through an authenticated config fetch. It also means the
retina service is **per-clinic** (`?clinicId=`), which is a different tenancy
model from anything in the notes.

### 7.4 Pusher channel name = `(n²+n).toString(16)` — deterministic, unkeyed

> `transformedChannelId($){ const q = +$; return (q*q + q).toString(16); }`
> offset **~1632000**.

**Why new:** no prior note mentions any realtime channel, let alone its name
derivation. Two consequences worth carrying forward: (a) the transform is
reversible/arithmetic — channel names are guessable from any clinic user ID, so
the channel offers no secrecy; (b) `appKey` comes from `appConfig.pusherSettings`
to every logged-in clinic user, so the channel offers little isolation either.
The 30-minute self-unsubscribe is dead code (`setTimeout` immediately followed by
`clearTimeout` in the same block).

### 7.5 `hcp/sso/{login,logout,reauth}` + `hcp/ping/ping` — the portal's own session API

> `logIn → POST hcp/user/loginUser`, `logOut → GET hcp/sso/logout`,
> `continueSession → GET hcp/ping/ping`, `refresh → POST hcp/sso/reauth`.
> Plus `window.location.assign(new URL("hcp/sso/login", origin) + ?country&lang&type&state[&ext-otc&username])`.

**Why new:** `AUTH-TENANT-FINDINGS.md` records the **mobile** Auth0 flow and
notes `/connect/session/status` is dead. This is a *second, independent* session
mechanism — a server-side cookie/OIDC bounce on the portal's own origin, keyed on
`session_valid_to`, unrelated to the `/oauth/*` surface. The 401 handler also keys
on the exact CareLink error shape already documented (`error.type === "InvalidToken"`)
and exempts precisely two endpoints from session-expiry redirect: `hcp/user/loginUser`
and `hcp/user/forgotPassword`.

### 7.6 `hcp/user/*` — 29 clinic-user-admin endpoints, previously absent

> `loginUser getCurrentUser createUser activateUser deactivateUser promote demote
> getUsers getAllUsers changeEmail changePassword changeUsersEmail
> resetUsersPassword unlockAccount forgotPassword forgottenPasswordChange
> validateEmail checkPassword checkUserIdentifier getMfaUserStatus verifyMfaCode
> sendMfaCode sendMfaCodeAfterReCaptcha acceptTermsOfUse updateUser
> updateUserConfigs updateUserPreferences deleteUserReportPreferences
> getUserPreferences getUserLanguages getCountryLanguages getCountryTitles
> password cua/admin/info`

**Why new:** `APP-EMULATION-RESEARCH.md` §10 lists `hcp/user/checkUserIdentifier`
as the *only* `hcp/user` endpoint. The other 28 were not extracted. Notable:
`getMfaUserStatus` / `verifyMfaCode` / `sendMfaCodeAfterReCaptcha` establish that
**the portal enforces MFA**, and the reCAPTCHA site key is delivered by
`POST hcp/configuration/user` (`pow.captcha.enable`,
`pow.client.user.google.recaptcha.key`) — i.e. an authenticated endpoint, so the
site key cannot be harvested unauthenticated.

### 7.7 `hcp/clinics/*` — 40 endpoints incl. MFA policy and 12 `toggle/*`

> `getClinics getClinic createClinic updateClinic getClinicPreferences
> updateClinicPreferences getCountryLocaleSettings getPasswordRules registerKey
> care-teams notifications/contact-info remote-monitoring/settings reports/supported
> clinic-outcomes/reference access-data/disable
> getClinicUserSecurityProfile updateClinicUserSecurityProfile
> resetToDefaultSecuritySettings getClinicMultiFactorAuthParams
> getDefaultMfaSettings enableMultiFactorAuth disableMultiFactorAuth disableDataSharing
> toggle/{csv,patient-dashboard,blinded-cgm,therapy-data,remote-monitoring,
> clinic-outcomes,clinic-user-settings,titr-settings,status}`

**Why new:** §10 recorded only `clinic-outcomes/reference` and
`access-data/disable`. The MFA quartet, the security-profile trio and the nine
remaining toggles were not extracted. The toggles are a **clinic-wide feature
kill-switch list** — a per-clinic inventory of what data the clinic's users can
see at all.

### 7.8 `hcp/patients/((patientId))/logbook/{entries,entries/filled,entries/last}`

> Three endpoints, verbatim from the constants table at 2765473–2765623.

**Why new:** not in §10 at all, and directly relevant — the ROADMAP's deferred
`markers[]` item is exactly "logbook entries". These are the *read* side of the
treatments schema whose *validation* schema (`system.logbook.entry.validation.config`)
and *type* schema (`logbook.supported.entry.types`) §10 did find. Three endpoints
that belong together were previously documented as one.

### 7.9 `hcp/patients/*otc-linking*` — 6 endpoints, no prior mention

> `hcp/patients/otc-linking/allowed`
> `hcp/patients/otc-linking/code/email/send`
> `hcp/patients/otc-linking/code/sms/send`
> `hcp/patients/((patientId))/otc-linking/code`
> `hcp/patients/((patientId))/otc-linking/email/template`
> `hcp/patients/((patientId))/otc-linking/sms/template`
> Plus `ext-otc=true&username=` on the `hcp/sso/login` redirect, and translation
> keys `otc_login_app`, `click_get_otc_code`, `success_get_otc_code`,
> `error_otc_login_general`, `error_otc_login_code_exists`, `EXPIRED_CODE`.

**Why new:** zero prior mention of `otc` in any note. It is a one-time-code
linking flow: eligibility check, email/SMS code dispatch, code verification, and
email/SMS template management. **I am not asserting what "OTC" stands for** — the
bundle does not say, and guessing (retail/over-the-counter device? out-of-town
clinic?) would be worse than recording the shape.

### 7.10 `appConfig` keys that are base URLs / external hosts

> From `POST hcp/configuration/application`, offsets 2402700–2404200:
> `split.service.uri`, `personalUriBase`, `application.uploader.url.mac`,
> `application.uploader.url.win`, `uploader.client.current.version`
> (`{urlmac,urlwin,urlmsi}`), `pow.mmo.config`
> (`{mmoenabled,mmoappurl,mmoapiurl,returnurl,isClinicEnabled}`),
> `pow.mixpanel.analytics.settings` (`{enabled,token,host}`),
> `pow.deployment.region`, `pow.countries.regions`, `pow.udi.number` /
> `hsp.udi.number` (EU MDR Unique Device Identifier),
> `pow.report.generation.settings` (`{maxLimit:5}`),
> `pow.csv.grouping.time`, `pow.insights.call.configuration`,
> `pow.migration.linking.countries.not.allowed`,
> `pow.personal.link.gdpr.warning`, `pow.countries.certificatio…`,
> `pow.data.sharing.configurable.countries`, `clinical.feature.enabled`.

**Why new:** §8 mentions `appConfig` only as "the live mapping is server-driven"
and names five selectors. The **host-bearing** keys were not extracted — and
they are the reason the bundle contains only one Medtronic hostname.
`personalUriBase` is the base URI for inviting a patient onto the *personal*
CareLink portal; `pow.mmo.config.mmoapiurl` is a second API host the portal hands
off to (offset 2939585, writing `appSelected=MMO`, `user` and `mmoConfig`
cookies with `returnurl: window.location.origin` before `window.location.href`).

### 7.11 `productContext` is origin-driven

> `loadProductContext(){ let U = { currentDomainUrl: window.location.origin };
>   return this.http.post("hcp/configuration/productContext", U) … }`
> offset **2401851**.

**Why new:** no note records that the client discloses its own origin to select
the backend. It means the same bundle served from two hostnames resolves to two
different CRM hosts, product types (`HSP`/`POW`/`STUDY`) and locale sets — which
is a plausible mechanism behind the `carelinkhp*.minimed.*` fan-out in
`PROBE-FINDINGS.md` §1. **Open question:** whether the config differs by
`Origin`/`Host` header or by the POSTed `currentDomainUrl` — not determinable
offline.

### 7.12 Analytics: the clinic user ID is sent to Mixpanel

> ```js
> init(re){ this.enabled = re?.enabled && re?.token && n.c.production;
>   if(this.enabled){ const De = { ip:!1, opt_out_tracking_by_default:!0 };
>     if(re.host) De.api_host = re.host;
>     Jr.init(atob(re.token), De);
>     Jr.register({ AppType:"POW" });
>     this.userId && this.userCountry && (Jr.identify(this.userId), Jr.people.set({ $country:this.userCountry }));
>     this.applyConsentState(); } }
> ```
> offset **1902367**. Recorder loaded from `cdn.mxpnl.com/libs/mixpanel-recorder.min.js`
> with mask classes `mp-mask|fs-mask|amp-mask|rr-mask|ph-mask`.

**Why new:** no note records analytics at all. `Jr.identify(clinicUserId)` is a
pseudonymous identifier leaving the machine; `ip:!1` and
`opt_out_tracking_by_default:!0` are the mitigations. The token is
`atob()`-decoded from `appConfig.mixpanelSettings`, so it is server-driven and
was **not** recoverable offline.

### 7.13 Complete route enum — 62 routes = the portal's full feature inventory

> Module `82086`, offset **3114800**, verbatim in `recon/js/route-enum.txt`
> (62 distinct route values; the module also exports a 1-value sibling enum
> `{Secondary:"secondary"}`, excluded):
>
> `dashboard patients clinics login login-otc loading-page forgot-password mfa
> user-consents requirements my-profile clinic-management clinic-profile
> clinic-report-settings feature-settings clinic-anonymization-settings
> clinic-users mmo-home mmo-maintenance security settings reports report-settings
> recent-activity control-codes profile user-profile user-report-settings
> clinic-admin-policy clinic-user-policy authentication audit-log allow-domain
> password-reset email-validation supported-browsers tech-error/:errorCode
> clinic-registration terms-of-use privacy-policy public contact-us help
> settings-calculator uploader-instructions uploader clinic-outcome outcomes
> reference-study clinic logbook cua access-data register active progress
> carelink-config traces followup-history clinic-templates hidden-printing
> patient-details-secondary`

**Why new:** a route list is a feature list, and §10 recorded only the endpoints.
New routes imply unrecorded capabilities: `mmo-home`/`mmo-maintenance`,
`requirements`, `clinic-registration`, `carelink-config`, `control-codes`,
`recent-activity`, `traces`, `audit-log`, `cua` (the CUA product), `outcomes` /
`reference-study`.

### 7.14 `hcp/settings-calculator/*` — declared but unconsumed in this bundle

> `acceptDisclaimer`, `generateReportPdf`, `recommendedValues`, `recalculate`.
> All four have **zero** reference sites outside the constants and re-export
> tables (verified: `rg -o '\.\$F8|\.Kmi|\.M8i|\.eoE'` → 0).

**Why new:** §10 did not list them at all. Their consumers live entirely in
lazy chunks — which is itself the coverage-limit finding (§8).

### 7.15 Nine of fifteen `hcp/configuration/public/*` schemas

> `pow.common.core.report.generation`, `pow.follow.up.settings`,
> `pow.country.media.groups`, `hcp.banner.notifications` — §10 recorded 6 of the
> **15** `hcp/configuration/public/*` keys.

**Why new:** count. §10 lists `pow.nutrino.cc.{metadata,broker}.service.config`,
`cua.control.codes.settings`, `user-identifier-settings`,
`system.logbook.entry.validation.config`, `logbook.supported.entry.types` — 6.
There are **15**. The 9 not previously recorded:

```
hcp/configuration/public/cms-config.json
hcp/configuration/public/cua.crm.settings
hcp/configuration/public/hcp.banner.notifications
hcp/configuration/public/personal/media/config
hcp/configuration/public/pow.common.core.report.generation
hcp/configuration/public/pow.country.media.groups
hcp/configuration/public/pow.crm.settings
hcp/configuration/public/pow.follow.up.settings
hcp/configuration/public/pow.invite.to.personal.uri
```

(`cua.crm.settings` is also read as the CUA variant of `pow.crm.settings` in a
selector: `(0,a.Mz)(patientDashboardEndpointsConfig, Qe => Qe ? e.GfZ : e.RCv)`
— i.e. the portal swaps between the clinic and CUA CRM config objects at
runtime, offset 3294261.)

---

## 8. "Noise I filtered" — do not re-chase these

| Noise | Size | Why it matched |
|---|---|---|
| **zxcvbn password-strength dictionaries** | offsets ~80 000–1 000 000+, several hundred KB | Comma-separated English words. Produces false hits for `amazon.com`, `guardian`, `guardianship`, `coauthored`, `pingpong`, `kingpin`, `espn.com`, `yahoo.com`, `gmail.com`, `rediff.com`, `salon.com`, `rivals.com`, `scout.com`, `about.com`, `web.com`, `duckduckgo.com`, `bing.com`, `1up.com`, `cloudflare.com`, **`ngp`** (`kingpin`/`pingpong`), **`guardian`** |
| **Angular `loadingPromise`** | 10 hits | `loa·ding·P·romise` — contains `ngP` case-insensitively. **This is what makes `NGP` look present when it is not.** |
| **`www.w3.org` XML namespaces** | 225 hits | SVG/XLink/RDF/MathML namespace URIs in `jsPDF` and `pdf.js` |
| **jsPDF operator names** (`/FlateDecode`, `/ASCII85Encode`, `/CIDSystemInfo`, `/Annot`, `/Form`, `/Sig`, `/Outlines`, `/Image`, `/Pattern`, `/Type1`, …) | ~40 distinct | PDF object names inside the bundled jsPDF |
| **Locale chunks** `"./af.js" … "./zh.js"` | ~200 | dayjs lazy locale map; matches every `xx/xx` path regex |
| **pusher-js docs links** | 5 | `/docs/channels/server_api/authorizing-users/`, `/docs/javascript_quick_start`, `github.com/pusher/pusher-js#encrypted-channel-support` |
| **Angular CDK / Material internals** | throughout | `cdkConnectedOverlay*`, `mat-legacy-*`, `ng-animating`, `ng-trigger`, `ng-leave`, `VP8LColorIndexInverseTransformAlpha`, `%COMP%` |
| **pdf.js worker strings** | ~60 KB | `msg:"invalid code lengths set"`, `msg:"invalid literal/length code"` |
| **`Math` / date format strings** | — | `MM/dd/yyyy`, `d0/M0/0000`, `HR_24`, `00.000.000/0000-00` — these are *format masks*, not paths |
| **Analytics event names** | ~200 | `click_carepartner_existing_reset_search` etc. — contain `carepartner` but are not paths |
| **A stray leading space** in `" /hcp/linkedPatient"` | 1 | Makes a literal `/hcp/linkedPatient` grep miss |

**Rule of thumb for the next person:** on this file, a token with a high
case-insensitive count and **zero** case-sensitive hits is noise. Verify with the
case-sensitive query before believing anything.

---

## 9. Coverage limits — stated honestly

1. **Only 3 of ~227 JS chunks are on disk.** `chunks.txt` captured just the three
   eagerly-loaded scripts. `hp-runtime.js` contains a **225-entry lazy-chunk
   manifest** (`f.u = e => (2076===e?"common":e)+"."+{12:"cfb28faf…",40:"9cffbe…",
   …,9864:"4d4bad27…"}[e]+".js"`). `hp-main.js` references **27** distinct chunk
   IDs via `r.e(...)`; the rest are loaded on navigation. **Per the brief I did
   not download any of them.** All of them are served from the same origin and
   are trivially fetchable in a future pass.

2. **The feature modules live in the lazy chunks.** Verified from the route table
   (offset 2857357): `settings → r.e(3348)`, `login → r.e(259)`,
   `forgot-password → r.e(2118)+r.e(9463)`, `mfa → r.e(5312)`,
   `user-consents → r.e(7093)+r.e(9164)`, `clinic → r.e(2873)+r.e(5221)`,
   `cua → r.e(5637)+…`, `uploader-instructions → r.e(2076)+r.e(342)`.
   Every module that actually *calls* the dashboard/report/logbook/control-code
   endpoints is one of these. **This bundle is the shell, not the features.**

3. **Quantified: 4 of 183 `hcp/*` endpoints have zero call sites here** (all
   `hcp/settings-calculator/*`). The other 179 have 1–5 call sites. But a
   "call site" in `hp-main.js` is frequently just the module-42205 re-export
   block, so treat 179 as an upper bound on what is genuinely exercised here,
   not a lower bound.

4. **Hosts are ~1% recoverable from this file.** One Medtronic hostname
   (`dev.commoncore.medtronic.eu`) in 3.4 MB. Every production host is delivered
   at runtime by `POST hcp/configuration/productContext` (which is itself
   origin-driven) and `POST hcp/configuration/application`. **Static analysis of
   this bundle cannot enumerate the Medtronic host estate.** Do not conclude the
   estate is one host.

5. **Alarm / NGP code tables: absent.** Not "not found by my regexes" — the
   portal does not handle pump alarms. §5.3 lists the specific absences. Issue
   #84's vocabulary is **not** here and this file should not be cited for it.

6. **No code was beautified.** All offsets are into the raw minified file. Line
   numbers are meaningless (102 lines, most >64 KB). Cite byte offsets.

7. **No execution, no network, no eval.** Every claim is a string literal or a
   syntactic fact about the minified source.

---

## 10. Open questions for a follow-up pass (offline-blocked)

- **Q1.** What are `MMT-8600` / `MMT-8601`? Unanswerable from this bundle. A
  product page or a `deviceModelMapping` value from an authenticated
  `hcp/configuration/application` response would settle it.
- **Q2.** Does the same bundle served from `carelinkhp-prod.minimed.eu` (or any
  other CT name) return a different `productContext`? Requires network.
- **Q3.** What is `split.service.uri`, and who consumes it? Declared, never used
  in this bundle.
- **Q4.** What are the 225 lazy chunks' endpoint strings? **This is the single
  highest-value remaining action** and needs one `curl` of ~225 files.
- **Q5.** Is the Pusher `appKey` per-clinic or global? Visible only in an
  authenticated `appConfig.pusherSettings`.
- **Q6.** Does `retinaEndpointsConfig.target_url` point at a `*.minimed.*` host
  or a third party? Authenticated-only.
- **Q7.** What does `OTC` stand for in `otc-linking`? Do not guess in the repo.
