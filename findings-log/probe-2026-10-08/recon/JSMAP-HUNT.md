# Source-map hunt — CareLink portals (single-hypothesis pass)

**Date:** 2026-10-10 · **Hypothesis:** a deployed `.js.map` (or an orphaned one)
exists on any CareLink surface, which would expose the original TypeScript and
close the "minified-strings" ceiling on every prior JS finding.
**Outcome: the hypothesis is FALSE. Definitively absent on every surface probed.**

| | |
|---|---|
| **Requests issued** | **75** (cap 90 — never hit) |
| **`.map` URLs probed** | **62** |
| **`.map` URLs returning JSON/JS content-type** | **0** |
| **Offline greps (0 requests)** | 225 chunk files + 2 main bundles + 1 patient main bundle |
| **Requests to a single host (max)** | 42 (`carelink.minimed.eu`), ≥2.2 s apart |

> **Read the "Discrimination" section before re-using any number here.** Two of
> the four hosts return **200 + HTML for paths that do not exist**. Status codes
> are meaningless on them; only `Content-Type` is.

---

## 1. Offline first — the decisive result (0 requests)

The cheapest and most complete test: every lazy chunk already downloaded has been
held locally since 2026-10-09, so the reference-based failure mode
("chunk points at a `.map`") is answered for the whole corpus without a single
request.

```bash
cd research/probe-2026-10-08/security/js

# case-insensitive, -a so binary-ish files are still scanned
grep -railc 'sourcemappingurl' chunks/ 2>/dev/null | wc -l     # -> 0
grep -rail  'sourcemappingurl' chunks/                          # -> (no output)
grep -rail  '# sourceUrl'      chunks/ | wc -l                  # -> 0
grep -rail  '\.js\.map'        chunks/ | wc -l                  # -> 0
grep -rail  'data:application/json' chunks/ | wc -l             # -> 0  (inline base64 maps)
```

### Result

**0 of the 224 lazy chunks contain a `sourceMappingURL` directive.**

Corpus: `chunks/` holds 224 `.js` files + 1 derived `field-callsites.json`
(225 entries, matching the 225-entry `chunk-manifest.json`). All 224 are genuine
`application/javascript` — verified by `file` and by re-fetching one live
(§3.1), so none is an HTML-fallback impostor that would have silently failed the
grep. **Zero chunks reference a source map.**

### Three near-misses, all false positives

1. **`hp-main.js`** — `grep -abo sourceMappingURL hp-main.js` → **1 hit at byte
   offset 1791807**. It is **not a directive**. It is the string literal inside
   webpack's bundled **worker-loader** helper, which builds a Blob-based Worker
   from a template and conditionally appends a map URL:

   ```js
   var nn=function rt(p,k){ … var F=function qe(p,k){ …
     F&&De.push("//# sourceMappingURL="+F+"\n"),De}(p,k),
     re=new Blob(F,{type:"application/javascript"}); …
   ```

   The URL comes from the *worker's own* build, not from this bundle's
   deployment. `CHUNK-CORPUS-FINDINGS.md` §"OpenAPI / source maps" states
   "neither `main.js` nor `runtime.js` contains a `sourceMappingURL` comment" —
   that is **imprecise and worth correcting**: the token is present once in
   `main.js`, inside a library. Same construct, same offset region, confirmed
   independently in the patient bundle (§5).

2. **Three chunks match `sourceURL`** — `259.465abef10506aa4a.js`,
   `6371.954d6da831c7a943.js`, `7093.cb31bbc8544a8eb4.js`. All three are the
   camelCase Angular property **`sourceUrl`** (in a
   `bypassSecurityTrustResourceUrl` / PDF-link code path), not `//# sourceUrl=`.
   Only a case-insensitive grep finds them.

3. **No inline maps.** `data:application/json` (base64 `sourcesContent`) appears
   **0** times, so the "map embedded in the bundle" variant is excluded too.

### Archive cross-check (0 requests)

The Common Crawl / Wayback CDX responses already on disk cover both domains:

| Check | Result |
|---|---|
| distinct archived `carelink.minimed.eu/<id>.<hash>.js` chunk URLs | **82** |
| archived `carelinkhp.minimed.eu/*.js` URLs | **168** |
| `\.js\.map` occurrences across **all** `cdx/*.json` | **0** |
| `sourcemap` / `source-map` strings across all `cdx/*.json` | **0** |
| `sourcemap` strings in `recon/cc/*.md` | **0** |

The only `.map` string anywhere in the archive data is
`http://www.minimed.com/cgi/cgi/nav1.map` (timestamp `19971008021253`) — a 1997
server-side image map, predating source maps by a decade.

---

## 2. Discrimination — mandatory reading

Two hosts answer **200 for paths that do not exist**. Filtering on status code
would have reported a clean sweep of "200 = found".

| Host | Non-existent path → | Discriminator |
|---|---|---|
| `carelinkhp.minimed.eu` | **200 `text/html; charset=UTF-8`, 5518 B** (the SPA `index.html`, `etag: W/"158e-…"`) | `Content-Type` must be `application/json`/`application/javascript` |
| `carelink.medtronic.com` | **200 `text/html; charset=UTF-8`, 5518 B** (byte-identical to `hp-index.html`) | idem |
| `carelink.minimed.eu` | **404 `text/html; charset=iso-8859-1`, 196 B** (classic Apache 404 page) | 404 is a *true* negative here |
| `carelink.minimed.com` | 404, 196 B | idem |

A fabricated control was used on each host class to prove the fallback is
uniform and not path-dependent:

- `carelinkhp.minimed.eu/99999999.ffffffffffffffff.js.map` → 200,
  `text/html`, **5518 B, sha256-identical** to every other fallback body.
- `carelink.minimed.eu/zzzzzz.0000000000000000.js.map` → 404, 196 B, identical
  to every other 404 body.

Both controls behave **exactly** like the real probes, so a real map would have
been unmistakable (a `Content-Type` of `application/json`).

**Byte-count trap, corrected.** Bodies arrive brotli- or gzip-compressed
(`content-encoding: br` / `gzip`) and curl reports the *wire* size. The 5518 B
fallback shows as ~2125 B on the wire. All byte counts below are the
**decompressed on-disk** size.

---

## 3. Lazy-chunk `.map` probes

### 3.1 Clinic portal — stratified sample of 15 (of 224)

Selection was offline, by size rank over the 224 held chunks
(min 78 B · p25 1068 B · median 2278 B · p75 11756 B · max 492 635 B).

| Stratum | Chunk | Local bytes | Probed URL → status / content-type / bytes | Verdict |
|---|---|---:|---|---|
| largest | `298.5d9a9220016d5fa4` | 492 635 | 200 `text/html` 5518 | no map |
| largest | `6831.8323d65e48e01a28` | 316 979 | 200 `text/html` 5518 | no map |
| largest | `4283.91f03738096dce37` | 285 467 | 200 `text/html` 5518 | no map |
| largest | `391.6eb37181e753a853` | 218 752 | 200 `text/html` 5518 | no map |
| largest | `5965.e698b886ce3dd9cc` | 200 275 | 200 `text/html` 5518 | no map |
| smallest | `9296.b5d6597b13bb0ea9` | 78 | 200 `text/html` 5518 | no map |
| smallest | `1361.b0d06fffe68de871` | 78 | 200 `text/html` 5518 | no map |
| smallest | `1411.d3d81a775edc1b01` | 423 | 200 `text/html` 5518 | no map |
| smallest | `3586.df9584e71b6adf1f` | 511 | 200 `text/html` 5518 | no map |
| smallest | `6322.e1cab4c458588720` | 810 | 200 `text/html` 5518 | no map |
| mid (rank 104/224) | `7448.4139a5c75e4b96a9` | 2 185 | 200 `text/html` 5518 | no map |
| mid (rank 109/224) | `1994.6dbe6fea2b5fe2f5` | 2 258 | 200 `text/html` 5518 | no map |
| mid (rank 112/224) | `8505.2101abc59c61ad59` | 2 278 | 200 `text/html` 5518 | no map |
| mid (rank 116/224) | `1139.fcea7badebc234fb` | 2 305 | 200 `text/html` 5518 | no map |
| mid (rank 120/224) | `5101.616b6d270c0ad469` | 2 336 | 200 `text/html` 5518 | no map |

**15/15 no map.** Combined with §1 (0/224 reference one), the "orphaned source
map" failure mode is the only remaining possibility for this portal — and it is
not present in a size-stratified sample covering 0.016 %–100 % of the size range.

### 3.2 Patient portal — 20 of 211

The patient portal's runtime was retrieved live (see §5) and its 211-entry chunk
map extracted. 20 chunks were sampled by even spread across the numeric ID range
(`12, 429, 985, 1541, 1947, 2535, 3268, 3819, 4235, 4842, 5656, 6133, 6429,
6792, 7187, 7506, 8424, 9030, 9504, 9864`).

Every probe returned **404 `text/html; charset=iso-8859-1`, 196 B** —
`carelink.minimed.eu`'s clean Apache 404, confirmed as a *true* negative by the
fabricated control in §2.

**Control fetches proving the naming pattern is right** (all
`200 application/javascript`):

| URL | Decompressed bytes |
|---|---:|
| `carelink.minimed.eu/main.6595daf83bd6d4b1.js` | 3 417 255 |
| `carelink.minimed.eu/runtime.79e2f9040b1dad8f.js` | 8 268 |
| `carelink.minimed.eu/12.c22952a522974f5f.js` | 2 224 |
| `carelink.minimed.eu/985.47eb741416e9cd44.js` | 18 851 |
| `carelinkhp.minimed.eu/298.5d9a9220016d5fa4.js` | 492 635 |

So the `<id>.<hash>.js` pattern resolves on both portals, and only the `.map`
suffix is missing. **20/20 no map.**

---

## 4. Other portals and the eager bundles

| # | URL | Status | Content-Type | Bytes | Verdict |
|---:|---|---:|---|---:|---|
| 1 | `carelinkhp.minimed.eu/main.fb5f8cb7eb60c4d5.js.map` | 200 | `text/html; charset=UTF-8` | 5518 | SPA fallback — no map |
| 2 | `carelinkhp.minimed.eu/runtime.a752bb828cca4b2c.js.map` | 200 | `text/html; charset=UTF-8` | 5518 | SPA fallback — no map |
| 3 | `carelinkhp.minimed.eu/polyfills.e98da8d5da636e6e.js.map` | 200 | `text/html; charset=UTF-8` | 5518 | SPA fallback — no map |
| 4 | `carelinkhp.minimed.eu/99999999.ffffffffffffffff.js.map` | 200 | `text/html; charset=UTF-8` | 5518 | **control** — identical |
| 5 | `carelinkhp.minimed.eu/maps/main.fb5f8cb7eb60c4d5.js.map` | 200 | `text/html; charset=UTF-8` | 5518 | no map (alt dir) |
| 6 | `carelink.medtronic.com/main.fb5f8cb7eb60c4d5.js.map` | 200 | `text/html; charset=UTF-8` | 5518 | SPA fallback — no map |
| 7 | `carelink.medtronic.com/runtime.a752bb828cca4b2c.js.map` | 200 | `text/html; charset=UTF-8` | 5518 | SPA fallback — no map |
| 8 | `carelink.medtronic.com/polyfills.e98da8d5da636e6e.js.map` | 200 | `text/html; charset=UTF-8` | 5518 | SPA fallback — no map |
| 9 | `carelink.medtronic.com/298.5d9a9220016d5fa4.js.map` | 200 | `text/html; charset=UTF-8` | 5518 | SPA fallback — no map |
| 10 | `carelink.minimed.eu/` | 200 | `text/html; charset=UTF-8` | 1833 | real index (see §5) |
| 11 | `carelink.minimed.eu/app/main.6595daf83bd6d4b1.js.map` | 200 | `text/html; charset=UTF-8` | 1833 | SPA index — wrong dir |
| 12 | `carelink.minimed.eu/app/runtime.79e2f9040b1dad8f.js.map` | 200 | `text/html; charset=UTF-8` | 1833 | SPA index — wrong dir |
| 13 | `carelink.minimed.eu/app/polyfills.e906788c6e59ee8e.js.map` | 200 | `text/html; charset=UTF-8` | 1833 | SPA index — wrong dir |
| 14 | `carelink.minimed.eu/app/runtime.79e2f9040b1dad8f.js` | 200 | `text/html; charset=UTF-8` | 1833 | control: **not** the asset root |
| 15 | `carelink.minimed.eu/app/main.6595daf83bd6d4b1.js` | 200 | `text/html; charset=UTF-8` | 1833 | control: **not** the asset root |
| 16 | `carelink.minimed.eu/main.6595daf83bd6d4b1.js.map` | **404** | `text/html; charset=iso-8859-1` | 196 | **no map** |
| 17 | `carelink.minimed.eu/runtime.79e2f9040b1dad8f.js.map` | **404** | `text/html; charset=iso-8859-1` | 196 | **no map** |
| 18 | `carelink.minimed.eu/maps/main.6595daf83bd6d4b1.js.map` | **404** | `text/html; charset=iso-8859-1` | 196 | no map (alt dir) |
| 19 | `carelink.minimed.eu/sourcemaps/main.6595daf83bd6d4b1.js.map` | **404** | `text/html; charset=iso-8859-1` | 196 | no map (alt dir) |
| 20 | `carelink.minimed.eu/zzzzzz.0000000000000000.js.map` | **404** | `text/html; charset=iso-8859-1` | 196 | **control** — identical |
| 21 | `carelink.minimed.eu/141.c1509a3d075b2c1e.js` | **404** | `text/html; charset=iso-8859-1` | 196 | archived hash, now gone |
| 22 | `carelink.minimed.eu/141.c1509a3d075b2c1e.js.map` | **404** | `text/html; charset=iso-8859-1` | 196 | no map |
| 23 | `carelink.minimed.com/` | 200 | `text/html; charset=UTF-8` | 1833 | real index |
| 24 | `carelink.minimed.com/app/` | 200 | `text/html; charset=UTF-8` | 1833 | real index |
| 25 | `carelink.minimed.com/app/main.6595daf83bd6d4b1.js.map` | 200 | `text/html; charset=UTF-8` | 1833 | SPA index — wrong dir |
| 26 | `carelink.minimed.com/app/runtime.79e2f9040b1dad8f.js.map` | 404 | `text/html; charset=iso-8859-1` | 196 | no map |
| 27 | `carelink.minimed.com/app/polyfills.e906788c6e59ee8e.js.map` | 200 | `text/html; charset=UTF-8` | 1833 | SPA index — wrong dir |
| 28 | `carelink.minimed.com/main.6595daf83bd6d4b1.js.map` | **404** | `text/html; charset=iso-8859-1` | 196 | **no map** |
| 29 | `carelink.minimed.com/runtime.79e2f9040b1dad8f.js.map` | **404** | `text/html; charset=iso-8859-1` | 196 | **no map** |
| 30 | `carelink.minimed.com/429.a0690bc198e0315a.js.map` | **404** | `text/html; charset=iso-8859-1` | 196 | no map |

† The `/maps/` probe on `carelinkhp` was intentionally sent with a **tampered**
hash (`…c6b5`) to also confirm that the SPA fallback does not depend on the hash
being a real one. It is indistinguishable from the correct-hash probe.

**Header check (0 extra requests).** Response headers on all five real-JS
fetches — including the patient main bundle and the largest clinic chunk — were
inspected for `SourceMap`, `X-SourceMap`, and `Link: <…>; rel=sourcemap`.
**None present on any host.** The server-side-source-map-header failure mode is
excluded as well.

---

## 5. Bonus: the patient-portal bundle is live and retrievable

This was **not** the hypothesis under test, but it fell out of §3.2 and is worth
more than the negative result it was found next to.

**`carelink.minimed.eu` serves the patient portal's main bundle at the domain
root, not under `/app/`.** The index declares `<base href="/app">` and root-relative
`src="main.6595daf83bd6d4b1.js"`, so the naive read is that the assets live at
`/app/*.js`. **They do not** — `/app/main…js` returns the 1833 B SPA index
(`etag: W/"729-…"`, identical sha256 to `/`). The real asset root is `/`.

A pass that trusted the `<base>` tag would have concluded the patient portal was
unreachable and probed nothing. Two files are now saved locally:

- `security/js/patient-main.js` — 3 417 255 B (application/javascript)
- `security/js/patient-runtime.js` — 8 268 B, containing a **211-entry chunk map**
  (`.p=""`, so chunks are root-relative: `<id>.<hash>.js`)

This is the app that talks to the pump API, so it is where the NGP vocabulary
would live. A free offline grep of `patient-main.js`:

| Token | Hits | Note |
|---|---:|---|
| `N24`, `N40`, `N50` | 1 each | **all substring coincidences** inside a bundled Samsung user-agent wordlist (`SPH-N240`, `SM-N900A`, `…N500`) |
| `N35`, `N47`, `N48`, `N55`, `N131` | 0 | |
| `stop_using_pump`, `errorStrings` | 0 | |
| **`deviceFamily`** | **1** | **real** — see below |
| `medicalDeviceFamily` | 0 | |
| `deviceModel` | 1 | `gi.deviceModel` — real field name |
| `sensorModel` | 1 | `y.deviceDetails.sensorModel` — real field name |
| `GUARDIAN`, `SIMPLERA`, `BLE` | 1 each | one shared enum — see below |

**Issue #81 gets a direct vocabulary answer.** Module `45559`, byte offset
**1 723 264**:

```js
const e = {BLE:"BLE", BLE_X:"BLE_X", SIMPLERA:"SIMPLERA",
           SIMPLERA_X:"SIMPLERA_X", GUARDIAN:"GUARDIAN"}
```

and the consumption site, byte ~2 963 961:

```js
this.userService.getDeviceFamily(p?.username)
  … ({deviceFamily: p}) => {
    const F = p?.startsWith(o.G.BLE),
          T = p?.startsWith(o.G.SIMPLERA),
          v = p?.startsWith(o.G.GUARDIAN);
```

So `deviceFamily` on the wire is one of **`BLE` / `BLE_X` / `SIMPLERA` /
`SIMPLERA_X` / `GUARDIAN`** (the `_X` variants appear to be suffixed forms).
That is the vocabulary half of #81, from the patient bundle, corroborating the
field *name* already found in the clinic chunks. **The wire-*shape* question in
#81 is still open** — this is a minified bundle, so there is no schema, no
comments, and no `file:line`.

**Issue #84 stays negative.** The NGP alarm-code vocabulary (`N24`/`N35`/`N40`/
`N47`/`N48`/`N50`/`N55`/`N131`/`stop_using_pump`) is **not** in the patient main
bundle either. The three apparent hits are user-agent strings. Both the clinic
and patient eager bundles are now searched and both are negative, so #84 must be
answered from a lazy chunk or from a live token — not from either main bundle.

---

## 6. Request ledger vs cap

| Host | Requests |
|---|---:|
| `carelink.minimed.eu` | 42 |
| `carelinkhp.minimed.eu` | 21 |
| `carelink.medtronic.com` | 7 |
| `carelink.minimed.com` | 5 |
| **Total** | **75** / 90 |

Pacing: ≥ **2.2 s** sleep between consecutive requests to the same host, enforced
by the probe harness (`sleep 2.2` when the host repeats). Cap enforced in code:
the harness aborts with a message rather than issuing request 91. Method: GET
only, no credentials, no cookies, no auth headers, read-only. Nothing was written
to any credential file; no git repo or worktree was touched.

Breakdown of the 75: **62 `.map` URL probes** (all negative), **5 real-JS
control fetches**, **8 index.html fetches**.

---

## 7. Why this is a definitive negative — and the exact conditions that would reopen it

The reference-based failure mode is **exhaustively** excluded, not sampled:

- 224/224 clinic chunks — offline grep, 0 requests.
- Both clinic eager bundles (`hp-main.js`, `hp-runtime.js`) and the patient
  `patient-main.js` — the only `sourceMappingURL` token in each is the bundled
  worker-loader string (§1.1).
- No inline `data:application/json` maps.
- No `SourceMap` / `X-SourceMap` / `Link: rel=sourcemap` response header on any
  real JS response.

The orphaned-source-map failure mode is excluded by **62 probes across 4 hosts**,
including all three eager bundles on three hosts, a size-stratified 15/224 of the
clinic chunks, an ID-stratified 20/211 of the patient chunks, two alternate
directories (`/maps/`, `/sourcemaps/`), and two fabricated controls proving each
host's not-found response is uniform.

**Reopen only if:**

1. A **new build hash** is deployed (these builds are dated
   `last-modified: Wed, 26 Aug 2026`), and the new chunk names come from a fresh
   runtime fetch — the old hashes 404 immediately, which is how we know the
   corpus is pinned to one build.
2. A **lazy chunk is fetched that was not in the 224** (the manifest is fixed at
   225 and the corpus is closed; a new chunk means a new build → see above).
3. An **authenticated** surface serves source maps (nothing unauthenticated was
   left untested — every `.map` path probed returned a not-found signal).
4. Someone obtains the build output from a **non-HTTP channel** — npm, a CI
   artefact, a Sentry/Bugsnag upload, a bug-report attachment. The bundles
   themselves are not published to npm (`grep` of `package.json` / no
   `minimed` packages in the workspace `node_modules`).

**Do not re-run this pass.** Record the negative here so it is never repeated.

---

## 8. Commands used

```bash
# ---- 0-request, offline ----
cd research/probe-2026-10-08/security/js
grep -railc 'sourcemappingurl' chunks/ | wc -l          # 0
grep -rail '# sourceUrl' chunks/ | wc -l                # 0
grep -rail '\.js\.map' chunks/ | wc -l                  # 0
grep -rail 'data:application/json' chunks/ | wc -l      # 0
grep -abo 'sourceMappingURL' hp-main.js                  # 1 hit, offset 1791807 (library)
grep -abo 'sourceMappingURL' patient-main.js             # 1 hit, offset 2850610 (library)
cd ../recon && grep -ohi '\.js\.map' cdx/*.json | wc -l # 0
python3 -c "import re,sys
s=open('security/js/patient-runtime.js').read()
m=re.search(r'\{(\s*\d+\s*:\s*\"[a-f0-9]{16,20}\"\s*,?)+\}', s)
print(len(json.loads(re.sub(r'([{,]\s*)(\d+)(\s*:)', r'\1\"\2\"\3', m.group(0)))))"  # 211

# ---- live probe harness (75 requests, cap 90) ----
# <scratch-dir>/jsmap-probe/probe.sh  — GET-only, per-host 2.2s pacing,
# Content-Type discrimination, decompressed byte accounting, request cap enforced.
# bodies/  headers/  consolidated.tsv  batch{1,2,3,5..12}.sh
```

Scratch tooling and raw captures: `<scratch-dir>/jsmap-probe/`
(`headers/*.h`, `bodies/*.body`, `consolidated.tsv`). Bundles retrieved during
the pass are in the workspace at `security/js/patient-main.js` and
`security/js/patient-runtime.js`.
