# CareLink Personal — first real authenticated session (2026-11-11)

**Evidence class: OBSERVED** (live authenticated UI session, operator's own account).
**Method:** desktop preview pane, region `carelink.minimed.eu`, on the operator's
own account (name redacted).
**Cap: 0 of a 0 cap — no request was made.** The pages read were served by the
authenticated app to a human-driven session; nothing was probed, and no endpoint
was contacted by this pass. **Delay:** the standing rule is ≥2 s between requests
to the same host; no request was issued, so no spacing applies and none is claimed.

This is the first time this project has had an authenticated CareLink session, so
what follows is a record of **what the account state is**, not a reverse-engineering
result. It is written down because it changes what several docs assume.

---

## 1. The account has no data on it

Two independent pages agree:

**Dashboard** (`/app/dashboard`):

> The dashboard cannot be displayed at this time. Visit Reports for information

**Reports** (`/app/reports`):

> Please upload data to generate reports.

and the reports page renders **"No data available"** with a calendar showing
`Oct 19 · Oct 26 · Nov 2 · Nov 9` — four empty weeks, no shaded days.

**Every report control is `disabled`.** From the accessibility inventory of
`/app/reports`:

| control | state |
|---|---|
| `Data Export (CSV)` | disabled |
| `Generate Reports` | disabled |
| `7 days` / `14 days` / `30 days` (reporting period) | **all disabled** |
| date-range selector | disabled (`No data available`) |
| calendar prev / next | disabled |
| `Insulin Delivery` / `Standalone CGM` / `Meter` (data source toggles) | **all disabled** |
| `Select my favorites`, `Clear all` | disabled |

The **report type list itself is rendered and enabled** — `Assessment & Progress`,
`Meal Summary`, `Insulin Assessment`, `Weekly Review`, `Daily Report`,
`Device Settings`, `Adherence`, `Logbook`, `Therapy Dashboard`,
`Episode Summary`, `Sensor & Meter Overview` — eleven types, matching the
`supportedReports` count the research corpus records for GB.

So the app is fully functional and the **account is empty**. That is the expected
state for an account before a first upload, and it is not a fault.

## 2. What this settles, and what it does not

**Settled (OBSERVED):**

- The account authenticates against `carelink-login.minimed.eu` (Auth0 Universal
  Login), and the authenticated app is served from `carelink.minimed.eu`.
- The **report type vocabulary is exactly 11 types** for a GB account, and the
  names render as above. The corpus recorded 11 `supportedReports` from the
  unauthenticated country-settings document; this is the first confirmation that
  the *rendered* list matches, on a real account.
- **The login gate includes a reCAPTCHA v2 checkbox** on the password form
  (`www.recaptcha.net/recaptcha/api2/anchor`), which the corpus has never
  recorded. Any automated login — including the bridge's `npm run login`
  strategy 1 — will hit this. **That is a finding about the auth flow, not about
  the account**, and it directly affects the bridge's automated login path.

**Not settled — and must not be inferred from this pass:**

- **Nothing about pump data.** No `connect/data`, `monitor/data` or
  `display/message` response exists to read, because the account has never
  uploaded. The payload census (`src/payload-census.ts`) will say nothing useful
  until a pump or the uploader has pushed at least one day.
- **Nothing about device identity.** There is no device on the account, so there
  is no `deviceFamily`, `deviceModel` or `sensorModel` to observe.
- **Nothing about which data endpoint answers.** All three remain unobserved with
  a token, exactly as `docs/10` records.

## 3. The one code-relevant finding: the captcha

The bridge's automated login (strategy 1, a scripted POST) cannot pass a
reCAPTCHA v2 checkbox. The validation-day procedure already says to *expect*
strategy 1 to fail and strategy 2 (Puppeteer) to be the one that works — this is
the first evidence for **why**, and it is stronger than "Medtronic is rolling out
MFA".

Puppeteer does not solve captchas either. So the honest reading is:

> **Strategy 1 and strategy 2 are both blocked by a bot check on a cold session.**
> Strategy 3 (terminal paste of a token obtained from a real browser) is the only
> one that reliably works, and a token obtained that way is what the bridge should
> expect to hold.

That reorders the login strategies' practical reliability and should be reflected
in `docs/validation-day-instinct.md` and the bridge's login documentation.

## 4. What would move this forward

In order, cheapest first:

1. **One real upload** — run the CareLink uploader (or pair the pump) and let a
   single day land. Everything in §2 becomes observable at that point, and the
   payload census captures it automatically.
2. **`npm run login` against this account** — now that a session exists, this
   tests whether a token obtained interactively can be reused headlessly, which
   is the actual question behind the bridge's login strategies.
3. Only then the data-endpoint questions, which need a token *and* data.

## 5. Provenance and limits of this record

- Read from a human-driven authenticated session in the desktop pane. The
  operator signed in; **no credential was handled by this pass** and none appears
  here.
- **No request was issued by this record.** The numbers and strings above are the
  rendered page, not API responses.
- The automated browser session used earlier in the same session was **not**
  authenticated — its cookie jar is separate — so nothing here derives from it.

---

## 6. The Uploader DMG carries no Java payload (OBSERVED)

Added after inspecting both architecture payloads of
`CareLinkUploader-ACC-7350-3.15.0-osx-installer.dmg`.

| file | bytes | sha256 (first 16) | zlib streams >100 B | ZIP magic | `.class` |
|---|---|---|---|---|---|
| `osx-arm64.dat` | 3,077,355 | `8063fb396ac3be2a` | 480 (9,727,750 B decompressed) | **0** | 0 |
| `osx-x86_64.dat` | 3,169,667 | `8bede07e220f1f87` | 470 | **0** | 0 |

The x86_64 payload had not previously been examined; it is the same shape as
arm64 and likewise contains no Java content.

**One near-miss worth recording so it is not mistaken for a finding later:**
exactly one decompressed stream (offset **5,231**, 1,267,355 B) contains the byte
sequence `.class`, but the surrounding symbol table reads
`_WmWinStyle.classMap` — a **Tk widget-style lookup table**, not a Java class.
It is a false positive and must not be cited as evidence of Java content.

**Conclusion:** the DMG is an InstallBuilder shell only. `uploader.jar` and
`skb.jar` are absent from both architectures. The application JAR is therefore
either fetched at install time or shipped in a payload this artefact does not
contain. **This does not contradict the earlier finding; it confirms it on the
second architecture.**

## 7. The uploader has never been run on the operator's Mac (OBSERVED)

`ssh mac` → no CareLink or Medtronic application in `/Applications`, and no
`~/Library/Application Support` directory for either name. The only JARs on the
host belong to unrelated applications.

This is consistent with §1: an account with no data is what an account looks like
before a first successful upload, and no uploader is installed to produce one.

**Consequence for the download-URL question:** the URL cannot be read from a
local install, because there is no local install. It is delivered to the page by
the authenticated `appConfig` under `application.uploader.url.mac` /
`.win` / `uploader.client.current.version` (§7.10 of
`JS-API-SURFACE.md` records the keys; the values remain unrecorded). Reading
those values requires either an authenticated page context or a
clinician-gated `POST hcp/configuration/application`.
