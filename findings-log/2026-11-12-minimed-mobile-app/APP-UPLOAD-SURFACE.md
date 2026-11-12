# MiniMed Mobile 3.3.0 — does it upload through the desktop uploader's API surface?

**Evidence class: OBSERVED unless marked.** Companion to `FINDINGS.md` in this
directory, which records the artefact and the BLE/SAKE layer. This record answers
one question only: **is the mobile upload path the same API surface as the
CareLink Uploader's, or a different one?**

**Requests issued by this pass: 0.** All work is static analysis of the extracted
artefact under
a local analysis directory (base APK, two DEX,
five native libs, `assets/`). No Medtronic host was contacted.

**Answer, up front.** **A different surface — and the difference is not a
different set of URLs, it is that the upload code is not in the DEX at all.**
The DEX contains **zero** occurrences of `display/message`, `dataupload`,
`carepartner`, `clcloud`, `cumulus`, `inrange`, or `api/uploader` (checked
against both DEX files, all five `.so` files and every text asset — §6). The
package that orchestrates Sync to CareLink (`ui/menu/fb` = `SyncToCareLinkPresenter`,
and the whole `minimed.bl.*` + `minimed.data.*` layer) is **referenced by the DEX
but not defined in it** — 160 classes are loaded from an encrypted payload at
runtime (§4). Two *other* network planes are fully readable and are neither the
desktop uploader's nor, on the evidence available, the pump-data path (§3, §5).

**Two corrections to this directory's `FINDINGS.md`, both measured:**

1. §5 states the single Medtronic host `teneo-cloud.medtronic.com` "is the
   support chatbot, not upload". **It is not the chatbot.** It is a full
   device-enrolment / certificate / **firmware package** API, with 107 classes of
   plain Java and readable routes (§5). The chatbot reading is unsupported by
   the code.
2. §4's framing that the app "uploads via a WebSocket" is **not established**.
   The WebSocket is the `securerepositories` layer, whose demonstrated consumer in
   the DEX is the **local database key store** (`DatabaseKeyManager` → `StorageSecureRepository`),
   not the pump-data upload. Whether the upload leg uses it is unknown, because the
   upload leg is packed (§4, §7).

---

## 1 · Every host and route string in the artefact

### 1.1 The complete set of HTTP(S) literals

Exhaustive, from both DEX files' string tables:

```
https://teneo-cloud.medtronic.com/diab001/api/v1      <- the ONLY Medtronic URL
https://www.googleapis.com/auth/games[_lite]         <- Play Games, library
https://%s/%s/%s                                     <- Firebase Installations
https://developer.android.com/...                     <- error-message URLs
https://firebase.google.com/support/privacy/...
https://github.com/google/gson, ReactX, slf4j, youtrack
http://logback.qos.ch/codes.html[...]                <- 29 logback diagnostics
http://schemas.android.com/apk/res/{android,auto}
http://xml.org/sax/features/{namespaces,validation}
http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd
```

`https://%s/%s/%s` at `com/google/firebase/installations/remote/c.java:109` is
Firebase's, not Medtronic's.

### 1.2 Negative table — the desktop uploader's surface, absent

| needle | base.apk DEX ×2 | all 5 `.so` | all text assets | verdict |
|---|---|---|---|---|
| `display/message` | 0 | 0 | 0 | **ABSENT** |
| `dataupload` | 0 | 0 | 0 | **ABSENT** |
| `carepartner` | 0 | 0 | 0 | **ABSENT** |
| `clcloud` | 0 | 0 | 0 | **ABSENT** |
| `cumulus` | 0 | 0 | 0 | **ABSENT** |
| `inrange` | 3 hits, all substring | 0 | 0 | ABSENT (`inrange.me` = 0) |
| `api/uploader` | 0 | 0 | 0 | **ABSENT** |
| `7095` | 2 hits, both resources | 0 | 0 | ABSENT (see below) |
| `auth0` | 0 | 0 | 0 | **ABSENT** |
| `code_challenge` | 0 | 0 | 0 | **ABSENT** |

The two `7095` hits are `navigation_bar_item_large_label_view = 2131297095`
(`j2/g.java:247`, `q5/y0.java:844`) — an Android resource id whose decimal
expansion contains the digits. **Not a port.** The three `inrange` hits are
`BC_LABEL_INRANGE70180` (a Time-in-Range display string) and
`TimeInRangeData` — the ordinary English phrase, not the domain.

`blest.inrange.me` and the desktop uploader's `:7095` BLE base URL
(`uploader.cfg`, `2026-11-12-uploader-installed-payload/FINDINGS.md` §6) are
therefore **absent by name**. See §6 for the caveat that makes this weaker than
it looks.

### 1.3 The routes that *are* present — from `RemoteConstants`

`com/medtronic/teneo/requests/RemoteConstants.java:5-13`:

```java
AUTHORITIES_ENDPOINT              = "/authority-requests";
CERTIFICATE_STATUS_CHECK_ENDPOINT = "/certificates/status";
DEVICE_TOKEN_ENDPOINT             = "/device-tokens";
ELIGIBILITY_ENDPOINT              = "/package-versions/available";
ENROLLMENT_REQUEST_ENDPOINT       = "/enrollments";
PACKAGE_STATUS_ENDPOINT           = "/package-statuses";
SECURE_SESSIONS_ENDPOINT          = "/secure-sessions";
CONTENT_TYPE_JSON                 = "application/json";
FORM_URLENCODED                   = "application/x-www-form-urlencoded";
```

Plus one route built by concatenation in
`com/medtronic/teneo/requests/ConnectSessionRequest.java:11`:

```java
super(config, "/secure-sessions/" + str + "/connect", buildJson(config, bArr, map));
```

**None of these is a pump-data route.** They are enrolment, certificate, device
token, session and firmware-package routes (§5).

---

## 2 · The networking layer

Three independent HTTP stacks, no Retrofit and no Volley:

| # | stack | library | who |
|---|---|---|---|
| 1 | **OkHttp 4.12.0** | `okhttp/4.12.0` user-agent string; 130 `okhttp3/*.java` classes decompiled | `securerepositories` (WebSocket) |
| 2 | **`java.net.HttpURLConnection`** | plain JDK, hand-rolled | `com.medtronic.teneo` (80 classes) |
| 3 | OkHttp again, as the transport under 2? | **not shown** — teneo uses `HttpURLConnection` explicitly (`HttpConnectionRequest.execute`, `com/medtronic/teneo/HttpConnectionRequest.java:129`) | — |

`retrofit2` = **0** occurrences; `com.android.volley` = **0**. So there are **no
Retrofit interfaces to enumerate** — the task's usual shortcut does not exist
here. Every route is a string constant or a concatenation (§1.3).

### 2.1 The `securerepositories` layer is native, not Java

`com/medtronic/securerepositories/NetworkSecureRepositoryImpl.java:15` is a class
whose entire behaviour is JNI:

```java
class NetworkSecureRepositoryImpl implements NetworkSecureRepository {
    static { System.loadLibrary("vdlbwnyfem"); Loader.l(-2082279142); $vdlbwnyfem$COI(); }
    public native void cancel();                                             // :71-74
    public native void configure(NetworkSecurityRepositoryConfiguration cfg);
    public native void requestData(RepositoryListener listener);
}
```

The **target URL is a runtime constructor argument**, never a literal:

```java
// NetworkSecurityRepositoryConfiguration.java:8-10
private Certificate certificate;
private Long cloudProjectNumber;
private String url;

// WebSocketCommunicator.java:72
public WebSocketCommunicator(OkHttpClient okHttpClient, String str, Certificate certificate)
```

`NetworkRepositoryFactory` is itself `native`-only and constructs nothing in
Java. **Consequence: the WebSocket host cannot be read from this artefact by
string search, and its absence from §1.2 is not evidence that it is not a
CareLink host.**

### 2.2 Certificate handling — three distinct mechanisms

1. **OkHttp pinning, by construction** — `WebSocketCommunicator` takes a
   `java.security.cert.Certificate` as a constructor parameter and holds
   `private static String PIN_PREFIX` (`:16`) and `private boolean certificateStatus` (`:17`).
   That is caller-supplied pinning, not a `network_security_config` pin.
2. **A custom `X509TrustManager` in the teneo stack** —
   `com/medtronic/teneo/HttpConnectionRequest.java:68-89` delegates to the
   platform trust managers **and then requires the leaf certificate to `.equals()`
   a supplied `X509Certificate`**, else throws
   `"Invalid server certificate provided: " + url + " - Received: " + issuer`
   (`:87`). This is **certificate pinning implemented in Java, in the clear, with
   the failure path readable**. Installed by
   `com/medtronic/teneo/config/Config.java:63-65` (`setServerCertificate` →
   `new HttpConnectionRequest.PinnedFactory(cert)`), using `TLSv1.2` (`:102`).
3. **Play Integrity attestation, separately from TLS** — `AJob`
   (`securerepositories/internal/sequencejobs/network/AJob.java:17-19,30,39`)
   holds `Long cloudProjectNumber`, `Context`, `IntegrityManager` and calls
   `performJwtAttestation` on success/failure of
   `com.google.android.play.core.integrity.IntegrityTokenResponse`.

### 2.3 `network_security_config` and bundled certs — the task's six sub-questions

- **`res/xml/` contains no `network_security_config.xml`.** Only
  `data_extraction_rules.xml`, `nfc_tech_filter.xml`, `splits0.xml`.
- **The manifest declares no `networkSecurityConfig` and no
  `usesCleartextTraffic`** (searched the binary AXML string pool for both:
  `[]`), and `android:debuggable` is absent.
- **`assets/Symantec Class 3 Secure Server CA - G4.der.cer` is 13 bytes** —
  `bc62d36401b95efab22f1677ee`. It is not a DER certificate (no `30 82` SEQUENCE
  header) and not a stub of one. **Confirmed the parent's suspicion: the name is a
  decoy.** Same for every other "JSON" asset:

| asset | bytes | hex |
|---|---|---|
| `assets/msso_config.json` | 13 | `ae734c8901bf9bb5713bc2a7c0` |
| `assets/Symantec … .der.cer` | 13 | `bc62d36401b95efab22f1677ee` |
| `assets/analyticsMappings.json` | 13 | `5af37215018f02166bffdb3a46` |
| `assets/fblyyzyocs/0.odex` | 13 | `4ca1012e0197ba6d88f531329e` |
| `assets/vdlbwnyfem.szip` | **12** | `c01ea7c4d3f5e4da2d3c1c6f` |

Five files of random bytes with descriptive extensions. **The packer has replaced
their contents** — they are name-only placeholders so that any code that asks for
them by name succeeds in opening something.

**Direct answer on `msso_config.json`: it is not "encrypted CA MAS config", it is
13 random bytes, and the name does not appear in the DEX at all** (`msso_config`
= 0 hits). No CA Mobile SSO SDK is linked either: `com/ca/mas`, `MASFoundation`,
`MASApplication` = **0 occurrences**. So the file is an inert placeholder for a
component this build does not link.

---

## 3 · Authentication — no Auth0, no OAuth, no PKCE in this artefact

| needle | count | note |
|---|---|---|
| `auth0` | 0 | — |
| `code_challenge` / `PKCE` | 0 | — |
| `openid` | 1 | a lone string, no OIDC library |
| `grant_type` | 1 | in a **resource name pool**, adjacent to `gps`, `gradient` — an Android resource identifier, not OAuth |
| `client_id` | 2 | `default_web_client_id`, `failed_client_id` — **Firebase** generated resources |
| `Bearer ` | 3 | teneo `PackageStatusRequest.java:34`, `CheckPackageUpdateEligibilityRequest.java:18`, `DownloadPackageRequestObjectRequest.java:19` |
| `X-MDT-API-KEY` | 1 | `com/medtronic/teneo/auth/ApiKeyAuthHandler.java:7` |

So the auth vocabulary in the DEX is:

- **`Authorization: Bearer <deviceToken>`** — `SecureSessionClient.getDeviceToken()`
  → `DeviceTokenRequest` → `POST /device-tokens` returns
  `DeviceToken { long expiresIn; String token; }` (`models/DeviceToken.java:9-10`).
  A **device** token, not a user token.
- **`X-MDT-API-KEY: <key>`** — the default header name in `ApiKeyAuthHandler:7`,
  an alternative `AuthHandler` implementation.
- `AuthHandlerDefault` does nothing (`backend/auth…` is a no-op passthrough), so
  the default `Config` sends **no auth header at all**.

**No Auth0 tenant, no client ID, no audience, no redirect URI appears anywhere in
this artefact.** CareLink Connect's public Auth0 client IDs
(`FINDINGS.md` §"public discovery", `docs/02-auth-tenants-and-flows.md`) —
`0FGoNwY0SP8ZmESYSfEOgMw03c58c1hk` (US), `PeAhkbhQWlQRxJiQxWfcFBiGus1lxfe9` (EU) —
are **not** in MiniMed Mobile's DEX. Likewise `com.medtronic.carepartner:/sso`
is absent.

**What the app does declare** is a deep-link intent filter, parsed from the
binary manifest:

```
scheme="carelink"  host="www.carelink.com"  pathPrefix="/registration"
```

That is the **registration hand-off** the UI text names
(`BC_MESSAGE_CREATE_A_PATIENT_ACCOUNT_ON_CARELINK`), not an OAuth callback.
`www.carelink.com` is recorded elsewhere in this corpus as **NXDOMAIN**
(`findings-log/probe-2026-10-08/recon/RECON-SUBDOMAINS.md:362`), so this
deep link is dead or region-specific.

**Login itself is a WebView.** `ui/startupwizard/SignInActivity.java:5,13`
holds a `WebViewEx webView`; `ui/menu/carelink/CareLinkWebActivity.java:18` holds
another, with `native Intent z0(Context, String)` / `native Intent a(Context, String)`
(`:32`, `:43`) building the intent from a **runtime string**. So the CareLink
SSO page URL is supplied at runtime — **that is the real reason no CareLink
hostname is in the DEX for the sign-in leg**, independent of the packer.

---

## 4 · The upload path specifically — and the finding that decides the question

### 4.1 `SyncToCareLinkActivity` is a view; its presenter is not in the DEX

`com/medtronic/minimed/ui/menu/SyncToCareLinkActivity.java` is 178 lines with
**34 `native` methods and zero Java method bodies** (`grep -c '\) \{'` = 0). It
implements `fb$a`, and **`fb` — the presenter, source-file
`SyncToCareLinkPresenter.java` — is referenced but never defined**:

```
class SyncToCareLinkActivity extends PresentableActivity<fb> implements fb$a   // :13
```

`Lcom/medtronic/minimed/ui/menu/fb;` is present in the DEX **type table** and
absent from the DEX **class-def table**.

### 4.2 This is systematic, not one class — 160 classes are reference-only

Parsed `class_defs` directly out of both DEX headers (12,587 classes defined
total) and compared against every `Lcom/medtronic/*;` descriptor in the string
tables (860 referenced):

```
com/medtronic descriptors : 860
defined in DEX            : 700
REFERENCE-ONLY            : 160
```

And by package, the removals are exactly the business layer:

| package | defined in DEX |
|---|---|
| `com/medtronic/minimed/ui/` | 191 |
| `com/medtronic/minimed/bl/**` | **0** |
| `com/medtronic/minimed/data/**` | **0** |
| `com/medtronic/minimed/ngpsdk/**` | **0** |

Reference-only classes include everything the upload question turns on:

```
com/medtronic/minimed/ui/menu/fb;                                  <- SyncToCareLinkPresenter
com/medtronic/minimed/bl/backend/auth/a;
com/medtronic/minimed/bl/backend/y;                                <- "backend"
com/medtronic/minimed/ui/startupwizard/SignInPresenter;
com/medtronic/minimed/data/carelink/model/CgmInfo;
com/medtronic/minimed/data/repository/dbflow/snapshotqueue/NgpQueuedSnapshotDto_Table;
com/medtronic/minimed/data/repository/dbflow/transferblock/TransferBlockDataDto_Table;
com/medtronic/minimed/data/repository/dbflow/history/HistoryDataDto_Table;
com/medtronic/minimed/data/repository/dbflow/slicerecord/SliceRecordDto_Table;
com/medtronic/minimed/data/repository/dbflow/identity/IdentityRecord_Table;
com/medtronic/minimed/data/repository/dbflow/certificate/TlsCertificateDto_Table;
```

**So: every class that would contain the upload URL, the upload payload and the
auth header for the upload leg has been deleted from the DEX.** The DEX keeps the
UI (191 `ui/` classes), the two helper clouds (§3, §5) and the third-party
libraries. The `.bl` (business logic) layer — which by name must contain the
Sync-to-CareLink orchestration — is gone.

### 4.3 What survives that describes the payload *shape*

The **DBFlow table names** are Kotlin metadata and therefore not removed:

```
NgpQueuedSnapshotDto     "queued snapshot"   <- a queue of snapshots to send
TransferBlockDataDto     "transfer block"
SliceRecordDto / SliceMetricDto
HistoryDataDto
IdentityRecord
TlsCertificateDto
```

That is the strongest available signal about the payload, and it is a
**structural convergence with the desktop uploader**, not an identity:

| concept | desktop uploader (`2026-11-12-uploader-installed-payload` §4) | MiniMed Mobile 3.3.0 |
|---|---|---|
| unit of transfer | `PackageType.BLENGP_PERIODIC`, `BLENGP_SNAPSHOT`, `BLENGP_SECURE_SNAPSHOT_CONTROL_RESPONSE` | `NgpQueuedSnapshot`, "transfer block" |
| repository vocabulary | `PUMP_HISTORY`, `PUMP_SENSOR_HISTORY`, `PUMP_DETAILED_TRACE` | `HistoryData`, `SliceRecord` |
| send call | `sendSnapshot([B, String, String…)` → `UploadSnapshotResponse` | *(packed — not readable)* |

**INFERRED:** both clients queue BLE-level "snapshots"/"transfer blocks" from the
same 780G NGP protocol and push them to a cloud ingest. That they converge at the
*device-protocol* level is expected — it is the same pump. That they converge at
the *HTTP API* level is **not shown**, and §1.2 is consistent with the opposite.

### 4.4 The upload UI strings, for completeness

`resources.arsc` carries the full Sync-to-CareLink surface, which confirms the
feature is in this build and is a **push**, not a pull:

```
BC_TITLE_SYNC_TO_CARELINK              BC_MESSAGE_CARELINK_SERVER_UPLOAD_FAILED
BC_LABEL_CARELINK_UPLOADS              BC_MESSAGE_CARELINK_UPLOAD_FAILED_SERVER_NOT_RESPONDING
"Upload your pump data to CareLink"    "One time upload to CareLink"
"Automatically updates your history to CareLink"
"your diagnostic logs will be automatically and periodically uploaded to CareLink"
```

The last one is a **second, separate upload client** — §5.3.

---

## 5 · Two readable network planes, neither of them the pump-data path

### 5.1 `teneo-cloud.medtronic.com` — device enrolment + firmware, not a chatbot

`com/medtronic/teneo/Smoke.java:23` is the only place the base URL is written:

```java
Config config = new Config("https://teneo-cloud.medtronic.com/diab001/api/v1");
```

**This corrects `FINDINGS.md` §5's "that is the chatbot, not upload".** The 107
`teneo` classes define, in plain readable Java:

| class | purpose (from its own method names) |
|---|---|
| `EnrollmentClient` | `createEnrollment`, `checkEnrollmentStatus`, `completeEnrollment`, `failEnrollment`, `updateAuthorities`, `checkCertificateStatus` |
| `SecureSessionClient` | `createSession`, `connectSession`, `getSession`, `closeSession`, `getDeviceToken` |
| `PackageUpdateClient` | `checkPackageUpdateEligibility`, `checkPackageStatus`, `downloadPackage` |
| `AuthorityType` enum | **`Registration`, `Certificate`, `Firmware`** |
| `Enrollment.Status` enum | `Started`, `Issued`, `Complete`, `Failed` |
| `SecureSession.Status` enum | `Secured`, `Failed`, `InProgress` |

with PKCS#7 enrolment bodies
(`EnrollmentClient.java:95`: `Utils.toPem(..., "-----BEGIN PKCS7-----", "-----END PKCS7-----")`)
and `POST /authority-requests` carrying `signed_certificate`
(`CertificateStatusCheckRequest.java:15`).

That is a **PKI enrolment and firmware-package distribution plane** — the
`com/medtronic/minimed/fota/` (firmware-over-the-air) feature's backend. It
matches `AuthorityType.Firmware` and `POST /package-statuses` +
`/package-versions/available`. **It is not a chatbot and it does not carry pump
therapy data.**

**Caveat, stated because it limits the finding:** the only `new Config(...)` in
the whole tree is inside `Smoke.java`, which is a **`public static void main`
smoke test** (`Smoke.main`, `Smoke.java:20`) carrying a hard-coded
`teneo-stage.medtronic.com` certificate. **No production code path constructs a
`Config` in the DEX** — the real instantiator is in the packed layer. So the
*production* teneo base URL is **not proven** to be `teneo-cloud.medtronic.com`;
that string is proven to exist and to be the production host *in this build's own
resource strings*, but the binding is made elsewhere.

### 5.2 `securerepositories` — a WebSocket with attestation, whose DEX consumer is the *key store*

`MessageType` (`internal/sequencejobs/network/model/MessageType.java:10-13`):

```java
public static MessageType ATTESTATION;
public static MessageType DEVICE;
public static MessageType KEY;
public static MessageType NONCE;
```

`Message` is `{ "type": String, "data": String }` (`Message.java:9-13`) —
a two-field envelope, base64-ish payload inside `data`.

The job chain is `InitJob → NonceJob → AJob → SJob → DJob`
(`internal/sequencejobs/JobExecutor.java:11-18` names all five in one constructor).

**But the one consumer visible in the DEX is not upload.** It is
`com/medtronic/applogs/repository/db/DatabaseKeyManager.java`:

```java
:20  public static final String APP_LOGS_DATABASE_KEY = "APP_LOGS_DATABASE_KEY";
:30  public final String generateDataBaseKey()   -> KeyFactory.generateAesKey()
:36  storageSecureRepository.putData(APP_LOGS_DATABASE_KEY, databaseKey, listener)
```

and `m4/c.java:107` does the same for `APP_ANALYTICS_DATABASE_KEY`. So the
`StorageSecureRepository` half of the protocol is **key escrow for the SQLCipher
databases** — a KEY/NONCE exchange, not a data upload.

**`createNetworkSecureRepository()` — the half that would carry upload — is
called from nowhere in the DEX**
(`SecureRepositoryFactory.java:36` is a `native` declaration; `grep` finds no
caller). Its caller is packed.

**So `FINDINGS.md` §4's "the transport is a WebSocket, not plain HTTP" is true of
this layer and unproven of the upload.** The four message types are consistent
with an upload leg; they are equally consistent with key escrow, which is the one
use the DEX actually demonstrates.

### 5.3 The app-log uploader — a working, readable upload client, but of logs

This is the one place a complete upload path *is* readable, and it is worth
recording as a template:

`com/medtronic/applogs/dispatch/AppLogsDispatchingManager.java:302-307`:

```java
protected final AppLogsData prepareAppLogsData(byte[] appLogsData, String exportStartingTime)
    String publicKey = this.configurator.getPublicKey();
    if (publicKey == null || publicKey.length() == 0)
        throw new IllegalStateException("No Public RSA key for logs encryption.");
```

then compress → encrypt → base64
(`d2` metadata names `compressedData`, `encryptedData`, `encodedData`), with
`ZIP_FILE_LENGTH_LIMIT = 3816816` and 500 records per chunk (`:37-38`), and

```java
// AppLogsUploadingManager.java:31-35
DispatchingClient client = getConfigurator().getUploadingDispatchingClient();
if (client == null) throw new IllegalStateException("Missing an client to send app logs to CareLink.");
client.invoke(prepareAppLogsData(appLogsData, dispatchingStartTime));
```

`DispatchingClient` is a **one-method interface** (`invoke(AppLogsData)`) with
**no implementation in the DEX** — it is injected by the packed layer. Encryption
is `RSA/ECB/OAEPWithSHA-256AndMGF1Padding`
(`com/medtronic/appanalytics/utils/a.java:50-51`) with an AES key — i.e. **RSA-wrapped
AES, envelope encryption**, the same *pattern* the desktop uploader uses with
`skb`/SKB.

**This is a diagnostic-log uploader, not a therapy-data uploader.** But it proves
the app has a *general* "encrypt-then-POST to a service supplied at runtime"
discipline, and that the endpoint for even this leg is injected, not literal.

---

## 6 · Why §1.2's negatives are weaker than they look — the packer

The DEX is **not** the whole program. Three artefacts establish that:

1. **`assets/fblyyzyocs.szip`, 2,356,173 bytes, Shannon entropy exactly 8.00 bits/byte,**
   147,260 distinct 16-byte blocks out of 147,260 — no ECB repetition, no
   recognisable magic (`PK`, `dex`, zstd, lz4, gzip, wasm all absent at offset 0).
   **That is an encrypted payload**, and it is the largest non-DEX object in the
   APK.
2. **`assets/fblyyzyocs/0.odex`** — a 13-byte placeholder by that name (§2.3), i.e.
   the packer's *extracted* form is produced at runtime, not shipped.
3. **`libfblyyzyocs.so` (3,675,584 B) and `libvdlbwnyfem.so` (1,297,336 B) both
   export exactly one JNI symbol** — `Java_<pkg>_Loader_l(int)` — and nothing
   else Medtronic-shaped. `Loader` is:

```java
public final class Loader {
    public AFD afd;  public AIS ais;
    public static native synchronized void l(int i6);   // fblyyzyocs/Loader.java:8
}
```

Their symbol tables name a commercial protector: `__dcp::DCPObfuscatedAsset`,
`DCPDeflatedAsset`, `DCPBlobAsset`, `DCPAndroidAssetImpl<...>`, `DCPException`,
plus `memfd_create`, `mprotect`, `dl_iterate_phdr` in the import list —
**runtime-decrypted, in-memory class/asset loading.** `libfblyyzyocs.so` is 95 %
`.data` (3.49 MB of 3.68 MB at 7.66 bits/byte), which is a second copy of
encrypted payload in the library itself.

**Consequence for the negatives:** `display/message`, `clcloud`, `carepartner`
etc. are absent from the *plaintext* of the artefact. Because ~160 classes are
loaded from that encrypted payload, the absence is **evidence about the shipped
plaintext, not proof of absence from the running program**. What it *does* prove
is that those strings are not available to static search — so **no static
analysis of this APK can name the upload endpoint**, and any claim to the
contrary (including one this record might be read as making) would be wrong.

**A related correction:** the packer is why `FINDINGS.md` §5 says "the
decompiled Java contains no CareLink or minimed hostnames". That is right, but the
cause is **two** things, and only one is the packer — §3 shows the sign-in URL is
a runtime `Intent` argument in `CareLinkWebActivity`, which would be absent from
the DEX even without packing.

---

## 7 · Verdict

**OBSERVED:**

1. **Zero** occurrences of the desktop uploader's surface — `display/message`,
   `dataupload`, `api/uploader`, `clcloud`, `cumulus`, `carepartner`, `inrange`,
   `:7095` — across both DEX files, all five native libraries and every text
   asset (§1.2).
2. **Zero** Auth0 / OAuth / PKCE / `client_id`-for-CareLink material; the only
   carrier auth is `Authorization: Bearer <deviceToken>` and `X-MDT-API-KEY` (§3).
3. Three separate network stacks: OkHttp-4.12 WebSocket (`securerepositories`),
   `HttpURLConnection` (`teneo`), and OkHttp-as-transport elsewhere. **No Retrofit,
   no Volley** (§2).
4. A **second Medtronic cloud plane** at `teneo-cloud.medtronic.com/diab001/api/v1`
   with eight readable routes for enrolment, certificate, device-token and
   **firmware package** operations, plus `AuthorityType{Firmware}` (§5.1). This is
   **not** the chatbot, correcting `FINDINGS.md` §5.
5. A complete, readable **app-log** upload client using RSA-OAEP-wrapped AES with a
   runtime-injected `DispatchingClient` (§5.3).
6. `network_security_config` absent; two *Java-implemented* pinning mechanisms
   (OkHttp `Certificate` constructor argument; a `checkServerTrusted` that
   requires the leaf to equal a supplied cert); plaintext Java pinning at
   `HttpConnectionRequest.java:87` (§2.2).
7. `assets/msso_config.json`, `analyticsMappings.json`, the Symantec `.cer` and
   `fblyyzyocs/0.odex` are **13 random bytes each** — name-only placeholders (§2.3).
8. **160 of 860 `com/medtronic` classes are referenced but not defined**, and they
   are exactly the business layer: `minimed/bl/**` **0** defined,
   `minimed/data/**` **0**, `minimed/ngpsdk/**` **0** (§4.2).

**INFERRED:**

- The mobile app **does not share the desktop uploader's HTTP API surface**, and
  more strongly, that surface **cannot be determined from this artefact at all**,
  because the classes implementing Sync to CareLink are in an encrypted payload
  (§4.2, §6).
- The `NgpQueuedSnapshot` / `TransferBlock` / `HistoryData` table names indicate
  the app queues BLE-level snapshots for delivery, structurally like the
  uploader's `BLENGP_SNAPSHOT` / `sendSnapshot` — **device-protocol convergence,
  not API convergence** (§4.3).
- The WebSocket `securerepositories` layer is a plausible upload transport
  (`NONCE`/`KEY`/`ATTESTATION`/`DEVICE`), but the only consumer proven in the DEX
  is database-key escrow (§5.2).

**NOT ESTABLISHED — state plainly, do not paper over:**

- **Any upload URL, host, method or payload for pump/therapy data.** Not "unknown
  value of a known field" — the code is absent.
- Whether Sync to CareLink uses the WebSocket, the teneo plane, or a third
  surface. Three candidates exist; none is excluded.
- The **production** teneo base URL. Only `Smoke.java`'s test constant and a
  resource string name a host, and `Smoke` is a `main()` smoke test.
- The contents of `assets/fblyyzyocs.szip` and the `libfblyyzyocs` `.data` blob.
  Entropy 8.00 with zero ECB repetition means no ciphertext-only attack; this
  needs a key, a hook, or a runtime dump.
- Whether `appVersion 3.8.0` (the repo's body-gate finding,
  `docs/03-discovery-and-versions.md:244,366-368`) has any bearing here. **The
  app's `versionName` is 3.3.0 and no `appVersion` string exists in the plaintext**
  — so the `android/3.6`-vs-`3.8` discovery/body-gate axis and this app's version
  namespace were never shown to be the same axis, and nothing in this artefact
  connects them.
- Whether the 160 packed classes are *all* of the business layer or a subset
  (a smaller set could be packed and the rest simply absent).

---

## 8 · The cheapest route to close the gap

Ranked by cost, and all of them **runtime**, because static is exhausted:

1. **Hook `Loader.l(int)`** — one symbol, `Java_fblyyzyocs_Loader_l` and
   `Java_vdlbwnyfem_Loader_l`. It is called from 164 classes before any class
   initialises, and it is the packer's single decryption entry point. A Frida
   hook that dumps the returned bytes / the post-decrypt class bytes yields the
   whole business layer, including `SyncToCareLinkPresenter` and `bl/backend`.
2. **Dump the DEX class loader at runtime** — the 160 missing classes must exist
   as `Class` objects. `Java.perform` + enumerate `enumerateLoadedClasses()` and
   call `getDeclaredMethods()` gives method names and signatures even without
   bodies.
3. **mitmproxy** — last, and it will hit two independent obstacles: the OkHttp
   `Certificate` pin passed into `WebSocketCommunicator`, and the Play Integrity
   attestation in `AJob`. Unlike the desktop uploader, **this client cannot be
   proxied without defeating both**, which is a materially higher bar than the
   desktop case (`2026-11-12-uploader-wire-protocol` §7).

**What static analysis bought, and it is not nothing:** the *shape* of the three
planes, the complete route list of the teneo plane, the message vocabulary of the
WebSocket plane, both pinning mechanisms in source form, and a firm, searchable
**negative** for every string the desktop uploader uses.
