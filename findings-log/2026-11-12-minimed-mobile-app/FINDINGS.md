# MiniMed Mobile 3.3.0 — the production upload path, obtained and inspected (2026-11-12)

**Evidence class: OBSERVED** unless marked. This record covers the Android
artefact of MiniMed Mobile, which is the upload route for the 780G on a modern
phone. It is a new axis for this project: the CareLink Uploader analysed in
`2026-11-12-uploader-installed-payload/` is a desktop client, and Medtronic's own
documentation names **MiniMed Mobile's "Sync to CareLink"** as the primary upload
path, with CareLink Connect being a care-partner *viewer* that does not upload.

<!-- cap-counts: ledger-rows -->
**Requests issued by this pass: 1** — a single `GET` to `d.apkpure.com` for the
XAPK. **Cap: 1 of a 10 cap.** **Delay:** the standing rule is ≥2 s between
requests to the same host; only one request was made, so no spacing applies and
none is claimed. No Medtronic host was contacted and no credential was used.

**Provenance, and its limits.** The artefact came from the APKPure mirror, not
from Google Play. `findings-log/medtronic-carelink-2026-07-21/09-mobile-artifacts.md`
already records APKPure as a **medium-confidence** source for this project, so
this is established practice rather than a new concession — but it is still a
mirror, and the APK should be treated as *medium-confidence provenance* even
though its internal metadata is self-consistent. It is **not redistributed or
committed**; `.gitignore` excludes it.

---

## 1. Identity

| field | value |
|---|---|
| package | `com.medtronic.diabetes.minimedmobile.eu` |
| name | MiniMed™ Mobile |
| versionName | **3.3.0** |
| versionCode | **1091** |
| minSdk / targetSdk | 33 / 35 |
| container | XAPK, 36,057,231 B |
| base APK | 21,294,359 B |
| DEX | `classes.dex` 9,572,872 B, `classes2.dex` 4,559,600 B |

The prior mobile note covers `com.medtronic.diabetes.carepartner` (CareLink
Connect) only. **This package is not recorded anywhere in the corpus.**

## 2. It requests NFC and BLE — it is not a passive viewer

From `manifest.json`, the permission set includes:

```
com.medtronic.minimed.permission.SECURE_LOCAL_BROADCAST
android.permission.BLUETOOTH_ADVERTISE
android.permission.BLUETOOTH_CONNECT
android.permission.NFC
android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE
android.permission.FOREGROUND_SERVICE_DATA_SYNC
android.permission.RECEIVE_BOOT_COMPLETED
```

`BLUETOOTH_ADVERTISE` is notable: a viewer does not need to advertise. Combined
with `FOREGROUND_SERVICE_CONNECTED_DEVICE`, this is a client that holds a live
connection to the pump.

## 3. The native stack — SAKE confirmed on a production artefact

`config.arm64_v8a.apk` carries five native libraries:

| library | bytes |
|---|---|
| `libsqlcipher.so` | 5,182,792 |
| `libfblyyzyocs.so` | 3,675,584 |
| `libvdlbwnyfem.so` | 1,297,336 |
| `libandroid-sake-lib.so` | **129,184** |
| `libStreamLibrary.so` | 41,848 |

`libandroid-sake-lib.so` is an **ELF 64-bit ARM aarch64, stripped, built by NDK
r28c**, and it contains the standard **Rijndael S-box at file offset `0x5bf8`**:

```
sbox = 63 7c 77 7b f2 6b 6f c5 30 01 67 2b fe d7 ab 76
```

That is the same marker the public OpenMinimed research found in a different SAKE
build, and it confirms **SAKE is not white-boxed in the production app** — it is
plain AES-family primitives with the standard tables intact. It exports **163**
`Java_com_medtronic_minimed_sake_SakeJNI_*` symbols.

**The protocol's struct vocabulary is readable from the symbol table**, which is a
significant recovery — these are the field names of the handshake:

```
SAKE_CHALLENGE_S            SAKE_SERVER_STATE_E
SAKE_SECURE_LINK_S          SAKE_CLIENT_STATE_E
SAKE_TRANSCRIPT_HASH_S      SAKE_DEVICE_TYPE_E
SAKE_INITIALIZATION_VECTOR_S  SAKE_PROTOCOL_VERSION_E
                              SAKE_PERMIT_VERSION_E
handshake status:
  E_SAKE_HANDSHAKE_NO_ERROR / E_SAKE_HANDSHAKE_ERROR_INVALID
```

So the SAKE handshake is: a **challenge**, an **initialisation vector**, a
**transcript hash**, a resulting **secure link**, driven by **client and server
state machines**, parameterised by **device type**, **protocol version** and
**permit version**. That is a structural map of the handshake recovered without
decompiling a single instruction.

## 4. The secure-repository protocol: a WebSocket with Play Integrity attestation

The app has a `com.medtronic.securerepositories` package not present in the
desktop uploader. Its `MessageType` enum is the protocol vocabulary:

```java
public static MessageType ATTESTATION;
public static MessageType DEVICE;
public static MessageType KEY;
public static MessageType NONCE;
```

Its interface:

```java
public interface NetworkSecureRepository {
    void cancel();
    void configure(NetworkSecurityRepositoryConfiguration cfg);
    void requestData(RepositoryListener listener);
}
```

**The transport is a WebSocket, not plain HTTP.** The job classes make this
unambiguous — `NonceJob`, `SJob` and `InitJob` each hold a `WebSocketCommunicator`
and a `WebSocketEventListener`, and `WebSocketCommunicator` wraps an
`OkHttpClient` and `okhttp3.WebSocket`:

```java
public WebSocketCommunicator(OkHttpClient client, String target, Certificate certificate);
```

and its methods are `connect()`, `closeConnection()`, `addListener()`,
`removeListener()`, `sendStringMessage(String)`, `sendByteStringMessage(byte[])`,
plus a nested `EchoWebSocketListener extends WebSocketListener` with
`onOpen`/`onMessage`/`onClosed`/`onFailure`.

**Two security properties follow from that signature, and neither is inferred:**

1. **A `Certificate` is a constructor parameter.** The communicator is built with
   a specific certificate supplied by the caller, and the class holds a
   `PIN_PREFIX` static and a `certificateStatus` boolean. This is **certificate
   pinning by construction** — it is not a network-security-config pin, it is
   handed to the object that opens the socket.
2. **`AJob` carries a `Long cloudProjectNumber`, a `Context`, and an
   `IntegrityManager`, wired to a `com.google.android.gms.tasks.OnSuccessListener`.**
   That is **Google Play Integrity API attestation** — the app asks Google to
   attest that it is genuine and running on an unmodified device, and only then
   proceeds. So the handshake is gated on device attestation, not just a
   credential.

The job sequence under `internal/sequencejobs/network/` is `InitJob`, `NonceJob`,
`AJob`, `SJob`, `DJob`, plus `MessageTransformer`. Read against the message types
and the attestation dependency, the handshake is: **open the socket (`InitJob`) →
obtain a server nonce (`NonceJob`) → attest the device with Play Integrity
(`AJob`) → establish the session (`SJob`) → exchange device data (`DJob`).**
**INFERRED** from class composition and job order; the message bodies are not
recovered.

**A correction to an earlier reading in this record's own draft:** this is *not* a
`POST`-based upload protocol equivalent to the desktop uploader's. It is a
long-lived WebSocket session with a challenge–response handshake in front of it.

## 5. The strings are protected by a native packer

The `MessageType` class is not ordinary Java. It contains:

```java
private static native Object[] $vdlbwnyfem$B4b4275d5(String str, int i6, String str2);
private static native void     $vdlbwnyfem$E4b4275d5(Object obj, Object obj2);
private static native /* synthetic */ void $vdlbwnyfem$COI();
static { System.loadLibrary("vdlbwnyfem"); Loader.l(223409996); }
```

Every enum constant is constructed via a native call. The same pattern drives
`libfblyyzyocs.so`. **Consequence: string constants and control flow for these
classes do not exist in the DEX** — they are materialised at runtime by the
packer. That is why the decompiled Java contains **no CareLink or minimed
hostnames at all**:

```
$ grep -rhoE "https?://[a-zA-Z0-9.-]+" --include=*.java out/ | sort | uniq -c | sort -rn
     29 http://logback.qos.ch
     19 http://schemas.android.com
      8 https://www.slf4j.org
      ...
      1 https://teneo-cloud.medtronic.com
```

**⚠ Corrected 2026-11-12 — the single host is not the chatbot.** This record
originally read *"One Medtronic host in the entire decompiled tree, and it is the
support chatbot."* **That is wrong.** `teneo-cloud.medtronic.com` is a **device
enrolment, certificate and firmware-package API**, with 107 readable `teneo`
classes: `EnrollmentClient` (`createEnrollment`, `completeEnrollment`,
`checkCertificateStatus`), `SecureSessionClient` (`createSession`,
`getDeviceToken`), `PackageUpdateClient` (`checkPackageUpdateEligibility`,
`downloadPackage`), and an `AuthorityType` enum of
**`Registration`, `Certificate`, `Firmware`**. It carries PKCS#7 enrolment bodies
and drives the firmware-over-the-air feature. It does **not** carry pump therapy
data. Full detail:
`2026-11-12-minimed-mobile-app/APP-UPLOAD-SURFACE.md` §5.1.

**The packer covers the DEX, not the whole artefact** — 160 classes are
referenced but not defined, and they are what orchestrates Sync to CareLink. So
the negative above is about the *readable* DEX and is weaker than it looks; see
`APP-UPLOAD-SURFACE.md` §6.

## 6. Other artefacts worth naming

- `assets/msso_config.json` — a CA Mobile SSO (MAS) configuration, **encrypted**
  (not readable as text; it is a binary blob despite the `.json` name).
- `assets/Symantec Class 3 Secure Server CA - G4.der.cer` — **13 bytes**, which
  is not a certificate. The filename is a decoy or a stub; it is not usable as a
  trust anchor. **Not claimed to be anything.**
- `assets/fblyyzyocs/0.odex`, `assets/fblyyzyocs.szip`, `assets/vdlbwnyfem.szip`
  — the packer's payloads, matching the two protector libraries by name.
- `libsqlcipher.so` — SQLCipher, so the local database is encrypted.

## 7. What this means for the upload question

The question this record set out to answer was: *does the mobile app upload
through the same API surface as the desktop uploader?*

**Answer: no — it is a different protocol.** Evidence:

1. The mobile app has a `securerepositories` network layer with `NONCE`/`KEY`/
   `ATTESTATION`/`DEVICE` messages. The desktop uploader has none of this; it uses
   `{token, target}` POSTs to `/api/uploader/v1/*`.
2. `libandroid-sake-lib.so` is present as an **Android aarch64 ELF**. The desktop
   uploader's SAKE lives inside its x86_64 `libuploader.dylib`. Same protocol,
   **different builds** — so the SAKE work done by OpenMinimed transfers, but the
   binary does not.
3. The app's own upload endpoints never appear as strings, because the packer
   materialises them at runtime.

**So the desktop-uploader API findings do NOT transfer to the mobile path.** That
is a firm negative and it matters: it means the `/api/uploader/v1/ping` family is
the *desktop* upload plane, and the modern 780G path is something else that has
not yet been named.

## 8. What is not established

- **Any upload endpoint URL, or the WebSocket target.** The URL is passed into
  `WebSocketCommunicator`'s constructor by a caller, and the packer defeats static
  string recovery for the callers. This needs either a runtime hook (Frida on a
  rooted device) or a mitmproxy capture from a real phone.
- **The wire format** of the four `MessageType` messages.
- **Whether SAKE is used for the server link at all**, or only for the pump BLE
  link. The library is present; which of the two links it secures is unproven.
  The presence of a separate `KEY` message type and a Play Integrity attestation
  suggests the server link has its own key establishment, so SAKE may be
  BLE-only — **INFERRED, not shown**.
- **The `msso_config.json` contents.**
- Anything requiring the app to run.

## 9. The cheapest routes to close the gap

In order of cost:

1. **Frida hook on `$vdlbwnyfem$B4b4275d5`** (or the `Loader.l` call) — the
   packer's decryption function is a single named native entry point. Hooking it
   dumps every decrypted string the app uses, which would produce the endpoint
   list in one run. Requires a rooted device or an emulator.
2. **Static unpacking of `libvdlbwnyfem.so`** — 1.3 MB of aarch64; the decrypt
   routine and its key schedule are in there. This is the tractable static route,
   and it is the same problem as the desktop uploader's `StringDecryptor`.
3. **mitmproxy against the WebSocket** — the hardest of the three, and the one to
   leave until last: the socket is built with a caller-supplied `Certificate` (so
   pinning is by construction) and the handshake requires a **Play Integrity**
   attestation token, which a repackaged or proxied client cannot obtain. A
   proxied phone would need a Frida pinning bypass *and* would still present a
   genuine attestation, so this may work on an unrooted device with a user
   certificate — but the packing and the attestation are two independent obstacles
   and only a real attempt will say which bites first.

**A negative counts, and this record contains a firm one:** the mobile app does
not share the desktop uploader's API surface, and it additionally gates its
handshake on Play Integrity in a way the desktop client does not.

---

## 10 · Corrections, 2026-11-12 (see `APP-UPLOAD-SURFACE.md`)

Two readings in this record are **wrong** and are corrected in the companion
record. Both are measured against the same artefact, no new download.

1. **§5, "`teneo-cloud.medtronic.com` … is the chatbot, not upload".** It is not
   the chatbot. It is a device-enrolment / certificate / **firmware package** API:
   107 plain-Java classes with readable routes
   (`/enrollments`, `/authority-requests`, `/certificates/status`, `/device-tokens`,
   `/secure-sessions`, `/package-statuses`, `/package-versions/available`) and an
   `AuthorityType` enum of `Registration | Certificate | Firmware`. It is the FOTA
   backend. It is still not the pump-therapy upload. See `APP-UPLOAD-SURFACE.md` §5.1.

2. **§4, "the transport is a WebSocket, not plain HTTP".** True of the
   `securerepositories` layer; **unproven for upload**. The only consumer of that
   layer visible in the DEX is the **local database key store** —
   `DatabaseKeyManager` stores `APP_LOGS_DATABASE_KEY` via `StorageSecureRepository`,
   and `createNetworkSecureRepository()` (the half that would carry data) has **no
   caller in the DEX**. See `APP-UPLOAD-SURFACE.md` §5.2.

**The decisive finding, which §7 states correctly but for the weaker reason:**
section 7 says the endpoints "never appear as strings because the packer
materialises them at runtime". The stronger and now-measured version is that
**160 of 860 `com/medtronic` classes are referenced by the DEX but not defined in
it**, and they are exactly the business layer — `minimed/bl/**` **0** defined,
`minimed/data/**` **0**, `minimed/ngpsdk/**` **0** — including
`ui/menu/fb` (`SyncToCareLinkPresenter`), `bl/backend/*`,
`data/repository/dbflow/snapshotqueue/NgpQueuedSnapshotDto`,
`transferblock/TransferBlockDataDto`. The upload code is not encrypted *in place*;
it is **deleted from the DEX and loaded from the payload**. So the negative is
about the shipped plaintext, not about the running program, and **no static
analysis of this APK can name the upload endpoint** — the §9 route 1 (hook
`Loader.l`) is the only tractable one.

Also corrected there: `assets/msso_config.json` is **13 random bytes**, not an
encrypted CA MAS config, and no CA MAS SDK is linked at all (`com/ca/mas`,
`MASFoundation` = 0 occurrences); the Symantec `.cer` is likewise 13 bytes, as
§6 already suspected.

## Correction (2026-11-12)

**`SakeJNI` is packed: the dylib is analysable, its Java contract is not.**

§3 of this record quotes 163 `Java_com_medtronic_minimed_sake_SakeJNI_*` exports
from `libandroid-sake-lib.so` and lists the handshake struct vocabulary they
carry. That measurement is correct and stands. What this record did **not** say,
and should have, is that **the Java class declaring those natives is not in the
DEX.**

Measured across both DEX files:

```
SakeJNI                       0 occurrences
medtronic/minimed/sake        0 occurrences
BRIL                          0 occurrences
```

But `libandroid-sake-lib.so` exports 163 methods bound to exactly
`com.medtronic.minimed.sake.SakeJNI`. **The declaring class is supplied at
runtime by the packer**, which is consistent with the 160 classes §5 records as
referenced but not defined.

**Why this matters:** §3 as originally written implies the SAKE layer is
readable end to end. It is not. The *native* side is fully analysable and its
symbol names are the best static description of the protocol available; the
*Java contract* that calls into it is packed, and no static reading of this
artefact recovers it. A reimplementation must therefore work from the 163 symbol
names and the OpenMinimed reconstruction, not from a decompiled calling
convention.

**Also verified, and it is a positive:** the jadx run reported 7 errors, so the
decompile was checked for completeness before its negatives were relied on.

- **0** `securerepositories` classes missing — all 63 DEX-defined classes have a
  `.java` file.
- **0** files carry a jadx decompile-failure marker.
- The 63-defined vs 33-files difference is **inner classes**, which jadx nests
  inside the parent file.

So the negatives in this record and in `APP-UPLOAD-SURFACE.md` are taken over a
complete decompile, not a partial one.
