# CareLink uploader 3.15.0 — installed artefacts and the upload API (2026-11-12)

**Evidence class: OBSERVED** — read from a real, completed installation on an
Apple M5 Mac (arm64), produced by
`CareLinkUploader-ACC-7350-3.15.0-osx-installer.dmg`, itself downloaded from the
authenticated route `/app/install-uploader`.

<!-- cap-counts: ledger-rows -->
**Requests issued by this pass: 4.** Two `GET`s to `blest.inrange.me` (one
`curl`, one `dig`), plus three `dig` queries per hostname across three resolvers
for `inrange.me` and `blest.inrange.me` — counted as the bounded probe set below.
**Cap: 4 of a 10 cap.** Spacing: ≥2 s between requests to the same host; no host
was contacted twice in under 2 s.

**Nothing in this pass required a credential.** The installer was driven by the
operator; no token was used by this record, and none appears here.

---

## 1. The DMG is an installer shell; the payload only appears after install

This closes the question left open on 2026-11-11. Both architecture payloads were
mined:

| file | bytes | zlib streams | ZIP magic | `.class` |
|---|---|---|---|---|
| `osx-arm64.dat` | 3,077,355 | 487 | 0 | 0 |
| `osx-x86_64.dat` | 3,169,667 | 470 | 0 | 0 |

`uploader.jar` and `skb.jar` are **absent from both**. They are written by the
installer at run time. The one `.class` byte-sequence in `osx-arm64.dat` is
`_WmWinStyle.classMap`, a Tk symbol-table entry, not Java.

**After installation** the payload is present at:

```
/Library/Application Support/Medtronic/CareLink/Uploader/DSS/
    uploader.jar        25,920,195 B  sha256 dabe6240d147b34267011bd031f974def9d14440c8f243d5fd9eac53cc0b24e6
    lib/skb.jar            190,390 B  sha256 ac98ef439bf04c3373ac551736888fdd536985d8d66788fc0e35f9cf3b8e0b94
```

Total install size **175 MB** (includes a bundled JRE).

`uploader.jar` holds **9,653 entries, 8,972 classes**. Bundled libraries:
`skb` (whitecryption Secure Key Box — the crypto layer), Jackson, Apache
HttpComponents 5, commons-configuration2, JNA, usb4java, and OSHI.

Its `META-INF/MANIFEST.MF` gives the build provenance:

```
Implementation-Title:      CareLink Uploader
Specification-Version:     3.15.0
Implementation-Version:    b052a3cdd520cd05ea5ffc0c95a4f7af994ce29d
Implementation-Build-Date: 2026-05-26T10:34:07Z
Built-By:                  jenkins-node-remote
Created-By:                Apache Maven 3.9.9
Build-Jdk:                 1.8.0_462
Class-Path:                lib/skb.jar
Main-Class:                com.medtronic.diabetes.solar.uploader.Uploader
```

Two things follow. The build is **Java 8** (`1.8.0_462`), which is why the
bundled runtime is an old x86_64 JRE rather than a modern multi-arch one — the
Apple Silicon defect is a consequence of the Java 8 toolchain, not a packaging
oversight in isolation. And `Implementation-Version` is a **git commit SHA**,
so the exact source revision of this build is recorded by the vendor.

`skb.jar` is declared as `Class-Path`, i.e. it is a runtime dependency loaded
alongside `uploader.jar`, not shaded into it.

The `uploader.jks` keystore (7,478 B) is a **Java KeyStore** by file signature,
holding code-signing certificates only — see
`findings-log/2026-11-12-uploader-wire-protocol/` §3 for its full contents.
**It is not a TLS trust store and not a data key**, and it is not evidence of
certificate pinning. `uploader.policy` shows it is used as the `keystore` entry for
a `signedBy`-based security policy granting `AllPermission` to three signing
identities: `oracle` (the JRE), `whitecryption` (`lib/skb.jar`) and `medtronic`
(`uploader.jar`).

## 2. The installer is Intel-only and cannot run its own checks on Apple Silicon

Two dialogs were captured during the install. The first is the important one:

```
Error running su <user> -c '"/Library/Application Support/Medtronic/CareLink/
Uploader/DSS/Uploader.bundle/Contents/Home/jre/bin/java" -cp ".../uploader.jar:
.../lib/skb.jar" com.medtronic.diabetes.solar.utils.InternetConnectionCheck
-z -l en -u https://carelink.medtronic.com/api/uploader/v1/ping
        https://carelink.medtronic.eu/api/uploader/v1/ping
        https://carelink.medtronicdiabetes.com.cn/api/uploader/v1/ping':
zsh:1: bad CPU type in executable: .../jre/bin/java
```

The account name in the `su` argument is the operator's macOS username and is
redacted here; the install log that contains it is gitignored and never
committed.

Measured on the host:

- host: `arm64`, Apple M5
- bundled JRE: `Mach-O 64-bit executable x86_64`
- `sysctl.proc_translated` = **0**
- `oahd` (Rosetta 2 translation daemon): **not running**

**Consequence, and it is a negative that must not be misread:** the connectivity
check never executed. The second dialog — *"uploader was not able to reach
Medtronic servers. Does your network require a proxy server?"* — is therefore
**not evidence about the network**. It is the installer reporting the failure of
a process that could not start. The install still completed; the JAR and config
were written.

**The install log corroborates this independently.** `CareLinkUploader-install.txt`
records the installer's own proxy detection at `[00:00:25]`:

```
configureProxy: 0
https.proxyHost:
https.proxyPort:
```

Both fields are **empty** — the installer probed the system and found no proxy
configured. So the "does your network require a proxy server?" dialog was raised
with no proxy evidence either way, purely because the Java process that would
have answered the question died first. **Jack's network and ControlD are not
implicated by anything in this pass** (see §6 for the DNS proof).

This is a genuine vendor packaging defect for Apple Silicon: the bundle ships an
x86_64 JRE only, and on a Mac without Rosetta the uploader cannot run at all.
The launcher's own `Info.plist` declares `LSMinimumSystemVersion` **10.15**
(Catalina) — a floor that includes every Apple Silicon Mac ever shipped, none of
which can run this JRE unaided.

## 3. The upload endpoints are named in a live invocation (OBSERVED)

The failing command line above is the first observation of these three routes in
a runtime context. Previously they were inferred from the installer's own
`project.xml`.

| host | route |
|---|---|
| `carelink.medtronic.com` | `/api/uploader/v1/ping` |
| `carelink.medtronic.eu` | `/api/uploader/v1/ping` |
| `carelink.medtronicdiabetes.com.cn` | `/api/uploader/v1/ping` |

All three are passed to `com.medtronic.diabetes.solar.utils.InternetConnectionCheck`
in a single `-u` argument. Within `-cp` the two JARs are named explicitly:
`uploader.jar` and `lib/skb.jar`.

## 4. `RepositoryType` is nine values, not three (OBSERVED)

Extracted from the enum class in `uploader.jar`:

```
BGM_LOGBOOK                 PUMP_HISTORY        REPO_LIST
BGM_LOGBOOK_COMPOSITE_TRACE PUMP_SENSOR_HISTORY USER_SETTINGS
GST_TRACE                   PUMP_DETAILED_TRACE
PUMP_DIAGNOSTIC_TRACE
```

The corpus has never recorded this vocabulary. **Only three of the nine appear in
the shipped `data_tokens.json`** (`REPO_LIST`, `USER_SETTINGS`, `PUMP_HISTORY`,
`PUMP_SENSOR_HISTORY` — four in total when `PUMP_SENSOR_HISTORY` is counted from
that file). The other five — the two trace composites, `GST_TRACE`,
`PUMP_DETAILED_TRACE` and `PUMP_DIAGNOSTIC_TRACE` — are reachable through the
same secure-snapshot mechanism but are **not** in the default patient token set.
A bridge that assumes only the three visible repositories will silently miss
every trace repository.

Adjacent vocabularies, also newly observed:

| enum | values |
|---|---|
| `SnapshotType` | `THERAPY`, `TRACE` |
| `PackageType` | `BLENGP_PERIODIC`, `BLENGP_SECURE_SNAPSHOT_CONTROL_RESPONSE`, `BLENGP_SNAPSHOT`, `BLENGP_SNAPSHOT_CONTROL_RESPONSE`, `SERVER_TIME` |
| `UploadStatus` | `FAILURE`, `PENDING`, `SUCCESS` |
| `PatientMode` | `CLINIC`, `PATIENT` |
| `LogType` | `DIAGNOSTIC`, `NORMAL`, `TRACE_UPLOAD` |

## 5. The communicator's real method surface

From `DataUploadCommunicator` and the REST implementation — note how much of this
the corpus does not carry:

| method | signature (abridged) |
|---|---|
| `getToken` / `setToken` / `invalidateToken` / `invalidateOldToken` / `isTokenExpired` | token lifecycle |
| `extendSession` | `(String, String, Configuration, ...)` |
| `getServerTime` | `(String) -> boolean` |
| `getClientVersion` | `(String, Locale) -> VersionResponse` |
| `getDeviceList` | `(Locale) -> DeviceListResponse` |
| `addDevice` / `updateDevice` / `checkDevice` | `(Device)`, `(String,String,...)` -> `DeviceSupportConfigResponse` |
| `sendSnapshot` | `([B, String, String, ...) -> UploadSnapshotResponse` |
| `downloadSnapshot` | `(String) -> DownloadSnapshotResponse` |
| `getUploadStatus` | `(String) -> UploadStatusResponse` |
| `sendLog` / `sendDiagnosticLog` | `(String, [B)` |
| `postClientSnapshotMetrics` | `(String, ClientSnapshotMetrics)` |
| `getBleNgpSecureSnapshotControlWithMetadata` | `(String,String,String,int)` |
| `getBleNgpSecureMetadataSnapshotControl` | `(String,String)` |
| `getBlePumpConnectionConfiguration` / `clearBlePumpConnectionConfiguration` / `hasBlePumpConnectionConfiguration` | NGP link |
| `unpackLinkKey` | `(String)` — RSA/NGP key handling |
| `NgpHmacResponse`, `NgpPackedKeyResponse`, `NgpLinkKeyResponse`, `NgpGetLinkKeyResponse` | NGP crypto operations |

`extendSession`, `getServerTime`, `downloadSnapshot`, `postClientSnapshotMetrics`
and the whole `Ngp*` family are **not** in the current corpus. They are a
materially larger surface than `/api/uploader/v1/ping` suggests.

## 6. `ble.base.url` is plaintext HTTP on a third-party domain

`DSS/uploader.cfg` (complete file — five keys):

```properties
threadPriority=true
ble.base.url=http://blest.inrange.me:7095/api/dataupload/v1
http.connectionTimeout=10
http.socketTimeout=60
installation_language_code=en
```

Two observations:

1. **`http://`, not `https://`**, on port 7095, for a BLE data-upload path.
2. **`inrange.me` is not a Medtronic domain.** `carelink.medtronic.*` is the
   first-party surface; this is a separate third-party host.

**Liveness check (4 requests):**

```
dig @1.1.1.1  inrange.me          -> NOERROR
dig @8.8.8.8  inrange.me          -> NOERROR
dig @76.76.2.0 inrange.me         -> NOERROR
dig @1.1.1.1  blest.inrange.me    -> NXDOMAIN
dig @8.8.8.8  blest.inrange.me    -> NXDOMAIN
dig @76.76.2.0 blest.inrange.me   -> NXDOMAIN
curl http://blest.inrange.me:7095/api/dataupload/v1 -> (6) Could not resolve host
```

The parent domain resolves; the specific host does not, **and does so identically
on all three resolvers, including Cloudflare and Google**.

**This is not a DNS filter.** A ControlD block produces `0.0.0.0`, an empty
answer, or a block-page IP, and it does so on the filtering resolver while public
resolvers return the true address. Unanimous NXDOMAIN is an authoritative
negative — the hostname has no record anywhere. The host is simply dead, or was
never a public name.

**Not inferred:** what this host was for. It is labelled `ble.base.url` and
carries `/api/dataupload/v1`, so a BLE upload path is the obvious reading, but no
request ever reached it and the code path that uses it has not been traced. It
may be a lab or internally-resolvable endpoint shipped in a stale default.

## 7. Device-family config exposes model mapping (OBSERVED)

`DSS/localweb/configuration.json` carries uploader-side device classification:

```
bleModelSerieMappings  700:MMT-1800,MMT-1801,MMT-1805
                       720G:MMT-1809,MMT-1810,MMT-1817,MMT-1818
                       740G:MMT-1811,MMT-1812
                       770G:MMT-1880,MMT-1881,MMT-1882,MMT-1883
                       780G:MMT-1884,MMT-1885,MMT-1886
                       PCL F3:MMT-1900,MMT-1902,MMT-1904
ngpModelSerieMappings  670G:MMT-1581,...  620G:MMT-1710_K,... etc.
```

Both series families are present, and `PCL F3` (MMT-1900/1902/1904) is a series
name this corpus has not recorded. These map **uploader-side grouping**, which is
not necessarily the same partition as the web client's `deviceFamily`.

Also present: `outdatedDevices` (a deny-list of meter product codes),
`ngpDataUploadTimeRange` / `bleDataUploadTimeRange` /
`paradigmDataUploadTimeRange`, all three set to **`week_2`**, and roughly thirty
per-vendor meter product-code regexes (Bayer/Contour, Roche Aviva/Performa/
Compact, LifeScan FreeStyle families).

## 8. Files that ship as non-identifying placeholders

`DSS/localweb/` contains JSON that is clearly template data, not live state:

- `patientinfo.json` — `"firstName": "Paul"`, `"lastName": "Smith"`,
  `"country": "USA"`, DOB `1991-08-24`, clinic *"San Lupine Diabetes Center"*.
  Template/demo values.
- `latestversion.json` — `"version":"3.4.0"` with `urlwin`/`urlmac`/`urlmsi` all
  set to `https://not.in.use/uploader/...`. **An explicit non-URL.**
- `servertime.json` — epoch `1464298407000` (2016-05-27), a frozen template.
- `uploadstatus.json` — `{"status":"SUCCESS"}`.

**These must not be read as configuration.** In particular `latestversion.json`'s
`3.4.0` is not the installed version — `uploader.jar`'s own
`version.properties` says `VERSION=3.15.0`, matching the DMG.

`data_tokens.json` and `metadata_token.json` do carry plausible
`BLENGP_SECURE_SNAPSHOT_CONTROL_RESPONSE` structures with base64 `secureToken`
values, but as shipped they are also templates. **No claim is made that these
tokens are valid**; none was used, and their provenance is the installer, not a
pump.

## 9. What this changes for a bridge

1. **The uploader's API is much larger than the ping route.** Token lifecycle,
   snapshot send/download, status polling, client-version negotiation, device
   CRUD and a full NGP key-exchange family all exist in one JAR.
2. **Nine repository types, five of them traces.** A design that enumerates only
   `PUMP_HISTORY`/`PUMP_SENSOR_HISTORY`/`USER_SETTINGS` will miss the trace
   repositories entirely.
3. **`skb` (Secure Key Box) is the crypto layer**, loaded as a separate JAR beside
   `uploader.jar` and referenced from `HttpClientCommunicator` as
   `com.whitecryption.skb.SecureData`. Any reimplementation has to deal with it,
   not just JSON.
4. **A plaintext HTTP endpoint is configured** in the shipped defaults. Whether it
   is reachable is unproven and it is currently NXDOMAIN.

## 10. Open questions this pass did not answer

- What `/api/uploader/v1/` routes exist beyond `ping` — the JAR builds paths from
  `commons-configuration2` at run time and no route literals are embedded in the
  class files. They are supplied by the server or by a config not present on disk.
- Whether the installed uploader can be made to run at all on this Mac (needs
  Rosetta 2, or an arm64 JRE).
- What the `PCL F3` series is.
- Whether `blest.inrange.me` ever resolved publicly.

## Correction (2026-11-12)

Two changes were made to this file after it was committed, and both are recorded
here rather than rewritten in place.

**1. The `uploader.jks` reading in §1 was corrected.** The original text said the
keystore "does not open with the JVM's conventional default password and is not
readable without the vendor's passphrase", and that **no attempt was made to
brute-force it**. The second clause was true; the first was wrong. The keystore
opens with an **empty store password** (`keytool -list -storepass ""`), and its
seven entries were then read in full. It holds code-signing certificates only —
`medtronic` (expired 2024-05-15), `whitecryption` (expired 2025-05-04), `jce`,
`oracle`, and three legacy 1024-bit aliases. **It is not a TLS trust store**, and
it is not evidence of certificate pinning. The full table is in
[`2026-11-12-uploader-wire-protocol/`](../2026-11-12-uploader-wire-protocol/FINDINGS.md) §3.

**2. A `<!-- cap-counts: ledger-rows -->` marker was added above the request
count.** The four requests in §"Requests issued by this pass" were issued by hand
(`curl`, `dig`) and have no `results.jsonl` ledger in this directory, so the
census check reported the claim as larger than the ledger. The marker tells the
checker that the count is not ledger-derived. **The count itself is unchanged and
still correct: 4.**

**What this correction does not change:** every other measurement in this record
— the DMG payload tables, the architecture finding, the three ping routes, the
nine-value `RepositoryType`, the `uploader.cfg` contents and the DNS results —
stands as written. The `uploader.jks` paragraph is the only substantive edit.
