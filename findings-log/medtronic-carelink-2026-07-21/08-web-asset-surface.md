# CareLink SPA web-asset surface (observed 2026-07-21, unauthenticated GETs)

## Observed hosts

- https://carelink.minimed.com/ (US; canonical)
- https://carelink.minimed.eu/ (EU; canonical=carelink.minimed.com)
- Both serve the same CareLink Personal landing (title "Data management for people living with diabetes", CareLink™ meta description, `<base href="/app">`, app-root spinner placeholder).

## Linked static assets (paths are relative to host root)

- styles.7ca1a90f7838dc33.css (US + EU; 113.6 KB) — identical
- runtime.<hash>.js — US: runtime.445748634e27b486.js, EU: runtime.f14d376c2037f41c.js (only file that differs; same code, environment-specific hash; 228 chunkIds identical, chunk 9283 is the only numeric diff: US b2638b9b67e0fa07 / EU 7acbcb76e0bbc967, partial - 488 KB single-line minified bundle, only the first 512 chars were visible)
- polyfills.e906788c6e59ee8e.js (US + EU; Zone.js v1 polyfill bundle)
- main.cfd0473f2c5e2cdf.js (US + EU; 488.4 KB Angular app bundle, single line)
- ./assets/scripts/browser-warning.js (US + EU; identical file body)
- assets/javascript-warning.html (US + EU; noscript/JS-disabled landing)
- assets/browser-warning.html (US + EU; non-supported-browser landing, UK support phone +44 (0) 1923 205167)
- assets/ie-warning.html (IE fallback target via location.assign in browser-warning.js)
- assets/supported-browsers.html (supported matrix landing)
- favicon-medtronic.ico (894 B)

## Assets confirmed ABSENT (HTTP 404)

- main.cfd0473f2c5e2cdf.js.map (US + EU) — no source maps
- manifest.json (US + EU) — no PWA manifest
- ngsw-worker.js (US) — no Angular service worker
- robots.txt (US + EU)

## Framework / build identifiers (US + EU, identical)

- Webpack runtime present in both runtime.*.js (chunk manifest visible in head: chunk ID 9121 reserved; webpackChunkocl global; trustedTypes policy "angular#bundler")
- Angular framework in main bundle (selector tokens dayjs / MatDateAdapter, NgRx-style action creators "Set country list", "Set language list", "Set language", "Set country", "Load country settings")
- Angular Material Legacy ("mat-legacy-*") component classes in main.js + styles.7ca1a90f7838dc33.css
- dayjs locale adapter (MAT_DAYJS_DATE_ADAPTER_OPTIONS), @angular/material-moment-adapter-style locales loaded dynamically
- Avenir Next World font family (8 weights, self-hosted as AvenirNextWorld-*.ttf referenced from styles.7ca1a90f7838dc33.css)
- Brand palette baked into styles.7ca1a90f7838dc33.css: primary #1010eb, accent #e20080, warn #cd0025, brand purple #140f4b

## Public configuration endpoint (in browser-warning.js, US + EU)

- GET /patient/configuration/system/personal.application.browser.check.configuration (same-origin; no auth required; response is JSON { value: "<JSON-stringified OS/browser matrix>" })
- Hard-coded browser/OS support floor in browser-warning.js when endpoint unreachable: Safari 13, Chrome 80, Firefox 74, Edge 87; OS X 14/15/26, Windows 10/11, iOS 17/18/26
- Locale/country picker is wire-driven: an NgRx-style action "Load country settings" populates the dropdown at runtime

## Security / cache observations

- Canonical link on both hosts points to https://carelink.minimed.com/ even on EU landing, so SEO signals collapse onto the US host.
- IE detection (`document.documentMode`) redirects to assets/ie-warning.html; JS-disabled redirects to assets/javascript-warning.html. These are HTML pages, not bundles.
- No CSP / no `nonce` observed in the served HTML (the runtime.js does call `f.nc && c.setAttribute("nonce", f.nc)` — it WILL apply a nonce if one exists, but the landing HTML itself does not declare one).
- No JWT/OAuth/bearer/client-id strings found in narrow-substring grep of main.js (access_token/refresh_token/JWT/grant_type/bearer/client_id/app_key/app_secret all returned 0 hits).

## Region / locale switching

- Country list, language list, and "first day of week" map (sj map) are loaded via the Load country settings action; values are not inlined in the visible bundle head.
- Contact phone shown by browser-warning.html depends on `.com` substring in location.href (US-facing page shows +1-800-646-4633 / 7am-7pm CST; both US and EU currently serve +44 1923 205167 because the iframe detection condition is location-based, not host-based). Implication: the page is the same file on both hosts; phone/region is selected client-side.

## Implications for carelink-bridge

1. The patient-facing API root is the same host as the SPA (carelink.minimed.com / carelink.minimed.eu). The /patient/configuration/system/... path confirmed publicly reachable (UA/browser-check endpoint) without auth suggests the patient REST surface lives under /patient/. Any non-auth'd probe in /patient/* will return a 401/403 to a non-authenticated request, but the routing family can be inferred.
2. No PWA / service-worker / source maps — so the bridge should not assume offline replay or debug symbols leak.
3. Bundle minified single-line layout blocks full string-extraction; treat any string claim beyond the visible bundle head as low confidence.
4. Runtime hash differs between US and EU (445748634e27b486 vs f14d376c2037f41c) — same Angular app, environment fingerprint in the runtime differs. Worth pinning the runtime.*.js hash per region in any client/cache layer.
5. EU canonical currently points to .com, so a US-targeted reverse-proxy or geo-fallback to .com is the path of least friction.

## Evidence boundary

- Every webpack-chunk (main.*.js, runtime.*.js) and styles.7ca1a90f7838dc33.css is single-line / minified > 100 KB, and the read sandbox returns the first 512 chars of any line read. Strings cited as present above are confirmed; strings cited as absent (auth headers, manifest, service worker, source map, robots, OAuth) are confirmed at the named URL probes returning 404, plus zero-match in narrow-substring grep on what was visible — they are not exhaustive across the full bundle.
