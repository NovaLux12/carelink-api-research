# CareLink Personal public surface (observed 2026-07-21, unauthenticated GETs)

## Regions and surface

- Two patient-facing web-app domains: carelink.minimed.com (US, login at /app/login) and carelink.minimed.eu (EMEA). The EU page declares `canonical=carelink.minimed.com`, so they are the same product surface.
- A separate clinician product, CareLink System / CareLink Pro, exists for healthcare professionals; the older CareLink Pro is Windows desktop, Medtronic documents a migration path to the web CareLink System.
- CareLink Network for implanted cardiac devices is a different product family and is out of scope.
- Privacy/ToS documents vary by region: EU/EMEA GDPR-aligned Privacy Statement effective 2025-09-01; Terms of Use last updated 2024-04-24; US site privacy with CCPA addendum last revised 2019-12-16; Singapore variant dated 2022-10-19; LATAM/CA/GB/EU PDFs all on carelink.minimed.eu/media/...

## Apps (Google Play / App Store metadata)

- MiniMed Mobile US: com.medtronic.diabetes.minimedmobile.us, updated 2026-05-12
- MiniMed Mobile EU: com.medtronic.diabetes.minimedmobile.eu, updated 2026-05-04
- CareLink Connect US: com.medtronic.diabetes.carepartner.us, updated 2026-06-22
- iOS CareLink Connect US id 1535972481 (1.5/5, 119 MB, EN+28)
- Play privacy declarations on Mobile and Connect are identical: "No data shared with third parties"; collects "Personal info, Health and fitness and 3 others"; "Data is encrypted in transit"; "You can request that data be deleted"
- CareLink Express Mobile EU on iOS is for cardiac devices, not diabetes

## Product behaviour

- CareLink Personal is a free, web-based therapy-management tool. It ingests data from insulin pump, CGM, blood glucose meter, and smart insulin pen. It generates PDF reports (Assessment & Progress, Weekly Review, Sensor & Meter Overview). Reports can be batched, viewed online, saved, printed, emailed.
- Patients can share data with an HCP either by handing over username+password in-clinic or by giving the username only and receiving a remote linking request. Up to five care partners can be linked via the CareLink Connect app.

## Supported devices (from the FAQ)

- Pumps: MiniMed 780G, 770G, 740G, 720G, 700, 670G, 640G, 630G, 620G, 530G, and Paradigm families (515/715, 522/722, 522K/722K, 523/723, 523K/723K, Veo 554/754 — Veo "Versions outside of the US")
- CGM: Guardian Connect (standalone) and Guardian 4
- Meters: Ascensia CONTOUR family (incl. NEXT LINK 2.4, NEXT LINK, PLUS LINK 2.4, NEXT ONE, NEXT USB, USB, XT, BREEZE, LINK), Abbott FreeStyle / Lite / Freedom Lite, LifeScan OneTouch family, Roche Accu-Chek (Aviva, Nano, Active, Compact, Compact Plus)

## Upload paths

- MiniMed 700-series → MiniMed Mobile auto-sync to CareLink, OR a "Blue Adapter" USB
- MiniMed 600-series → black CareLink USB or CONTOUR NEXT LINK 2.4 / PLUS LINK 2.4 meter
- Paradigm → white CareLink USB (Windows only; Mac must use CONTOUR NEXT LINK meter)
- Meters via manufacturer cables
- All USB uploads require a desktop/laptop CareLink Uploader application; uploads are not possible on phones/tablets. The CareLink Uploader is now Java-free.

## Auth

- Username + password. Two-step email verification at signup; the US product page hedges with "depending on your country of residence's security requirements" you may be re-prompted, and the EU FAQ states 2FA is "available in certain geographies."
- No SMS, no TOTP, no OAuth documented anywhere in the patient product.
- EMEA Privacy Statement: after 24 months of inactivity the CareLink Personal account is de-activated.

## System requirements

- Computer OS: Windows 10, 11; macOS Catalina 10.15, Big Sur 11, Monterey 12, Ventura 13
- Browsers: Google Chrome, Apple Safari
- Mobile: iOS 13.x-16.x is listed for CareLink Connect; full CareLink Personal is not available on mobile

## Reports / export

- Patient-facing export surface observed = PDF (view online, save, print, email)
- CSV export is documented in the CareLink System User Guide PDF for the clinician-side CareLink System / CareLink Pro path; it is not explicitly surfaced as a patient feature in the CareLink Personal FAQ

## Terms of Use (PDF, 2024-04-24)

- Personal, non-commercial use only
- "Under no circumstances may you frame this web site or any of its content or copy portions of this web site to a server."
- Medtronic reserves the right to terminate access on breach and to cooperate with authorities
- Liability cap EUR 100
- Site intended for persons 18+
- No explicit "no scraping" clause in the retrieved PDF, but the framing/server/abusive-use restrictions plus the cooperation-with-authorities clause together constrain automated bulk extraction

## Privacy posture

- EMEA Privacy Statement (2025-09-01): servers in the EEA; lawful bases are explicit consent (health data), legitimate interest, contract, legal obligation. Named processors include Nutrino Ltd (Israel; hosting / R&D / tech support for CareLink Personal), Medtronic Bakken Research Centre BV (Netherlands; statistics), Medtronic BV (Netherlands; EU Authorised Rep / vigilance). The explicit hook for any local bridge: "With your consent, we will share your personal data with any other parties you choose such as third-party providers of mobile applications you have subscribed to."
- US privacy (2019-12-16, CCPA): "We do not sell personal information of California consumers"; explicitly does NOT cover HIPAA PHI (a separate Notice of Privacy Practices applies).
- Singapore privacy (2022-10-19) is structurally similar to EMEA.

## Operational

- The "connectivity" support page references a "recent CareLink software and network outage" and instructs users to re-enter credentials in MiniMed Mobile and CareLink Connect apps — i.e. global session invalidation is a real, recurring risk.

## Developer / API surface

- No public, Medtronic-hosted developer documentation for CareLink Personal was found on medtronic.com, minimed.com, medtronicdiabetes.com, medtronic-diabetes.com, or carelink.minimed.{com,eu}.
- The only plausible Medtronic developer URL surfaced by search was https://developer.medtronic.com/welcome; direct fetch failed at the transport layer, so its content (and any auth-provider details) is UNVERIFIED and should not be cited.
- The "CareLink Open API Reference" at mymobilepracticemanager.com is a third-party clinic-engagement platform, not a Medtronic domain; the v1.6 PDF returned HTTP 403 on direct fetch.
- The only practical API surface for a local bridge is the unofficial community reverse-engineered ecosystem (carelink-python-client, CareLinkJavaClient, AdhocAdam/CareLink, mddub/minimed-connect-to-nightscout, yo-han/Home-Assistant-Carelink) — none endorsed by Medtronic.

## Implications for a local carelink-to-nightscout bridge

1. Auth is username+password with email 2FA; the bridge must support interactive 2FA at first sign-in and tolerate forced re-auth after backend session invalidations.
2. No official API exists — use a community-maintained client (carelink-python-client or similar) as the de-facto protocol reference, pin to specific commits, and add parsing regression tests since Medtronic has historically broken consumers without notice.
3. Document clearly: the bridge uses the user's own credentials on the user's own machine against a destination the user chose; do not aggregate across users.
4. Rate-limit politely and back off on errors to avoid being treated as "abusive, illegal, disruptive" use under the ToS.
5. Avoid framing, copying to a server, or republishing Medtronic content/branding.
6. Data is health-related data under GDPR; minimise identifying metadata in any external transmission.
7. Reports can be exported as PDF per patient; CSV is documented only for the clinician-side CareLink System.
8. MiniMed Mobile is the modern sync vector for 700-series pumps; the bridge does not need to talk Bluetooth to the pump directly.

## Open questions

- Exact endpoint shape and authentication flow for the patient-facing CareLink Personal API used by MiniMed Mobile / CareLink Connect (not publicly documented).
- Whether developer.medtronic.com publishes anything relevant to diabetes (fetch failed; content unverified).
- Whether a CSV export exists on the patient-side CareLink Personal at all (not observed in patient-facing docs).
- Whether email 2FA is required every login in a given geography, or only at signup.
- Whether the cardiac CareLink Network and diabetes CareLink Personal share any backend identity / API / developer programme.
- Exact list of countries offered in the EU CareLink signup dropdown (the EMEA Privacy Annex 1 lists ~40 EMEA countries).
