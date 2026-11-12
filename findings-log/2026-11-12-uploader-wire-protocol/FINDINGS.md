# CareLink uploader — decompiled wire protocol, crypto and prior art (2026-11-12)

**Evidence class: OBSERVED unless marked.** Companion to
`findings-log/2026-11-12-uploader-installed-payload/`, which records the
artefacts and their provenance. This record covers what the code *inside*
`uploader.jar` actually says, and how it compares to everything already
published.

**Requests issued by this pass: 0.** All work is static analysis of local
artefacts plus reading already-cloned public repositories. No Medtronic host was
contacted, and no credential was used.

**Cap: 0 of a 0 cap — no request was made.** **Delay:** the standing rule is ≥2 s
between requests to the same host; no request was issued, so no spacing applies
and none is claimed. Public repositories were read from local clones; GitHub API
calls made by a helper to enumerate an organisation's repository list are
non-Medtronic and not counted against the vendor cap.

**Tooling:** CFR 0.152 and Procyon 0.6.0, both run under OpenJDK 17. CFR requires
an **absolute** jar path (it throws an NPE on a relative one — recorded because it
cost a cycle). 5,593 `.java` files were produced.

---

## 1. The HTTP layer is native code, and that is the ceiling

`HttpClientCommunicator` decompiles to 464 lines with **67 `native` methods**.
Verified directly:

```
$ java -jar cfr.jar /abs/path/uploader.jar --outputdir /tmp/cfr-chk
$ grep -c native .../HttpClientCommunicator.java
67
```

CFR emitted signature-only stubs, which is **not** a decompiler failure: the
methods have no `Code` attribute at all. Their bodies live in a native library
that is **not in the jar**:

```
$ unzip -l uploader.jar | grep -E '\.(dylib|so|dll)$'
   ... 23 entries, ALL of them com/sun/jna/*/libjnidispatch.so
```

Every native library in the jar belongs to JNA. There is no Medtronic dylib, no
`lib/` tree, and no protector payload. `com.whitecryption.skb.SecureData` and
`SkbException` are named as **unloadable classes** in CFR's own header — they
resolve only at runtime, from `lib/skb.jar` and its native core.

**Consequence:** URL assembly, headers, HTTP verbs, TLS configuration and the SKB
glue are all unreachable statically. Any statement about them is inference.

## 2. What survived: the model API is intact

The obfuscator encrypted *string literals* but left the *model classes* readable —
accessor names and Jackson's default bean naming reconstruct the wire names
exactly.

**The envelope.** Every request extends `BaseMessage`:

```java
public class BaseMessage implements Serializable, Secure {
    private String iIIiIiiiiIiIIi;   // getTarget()
    private String iIIiIiiiiiiiII;   // getToken()
    public String getToken();
    public String getTarget();
}
```

So the wire envelope is **`{token, target}`** on every call. Field order in the
decompiled source is not wire order; the accessors are what matter.

**Serialisation.** One `ObjectMapper` configured with
`JsonInclude.NON_NULL`. Across the whole decompiled tree there is exactly **one**
`@JsonProperty` annotation in Medtronic's own code:

```java
@JsonProperty(value="encryptionKey")   // ControlCodes.java:35
```

Everything else relies on default bean naming, which is why the accessor names are
the wire names.

**Verb.** Only `HttpPost` is imported anywhere under `dataupload`. Every operation
is a POST. (INFERRED from imports and the absence of `HttpGet`; high confidence,
but not proven — the verb could be set inside a native body.)

**56 model classes** were mapped with field names and types. The significant ones:

| class | role |
|---|---|
| `UploadSnapshotResponse` | result of a snapshot push |
| `DownloadSnapshotResponse` | server → client snapshot pull |
| `UploadStatusResponse` | poll of an upload's state |
| `VersionResponse` | client-version negotiation |
| `DeviceListResponse` | devices bound to the account |
| `DeviceSupportConfigResponse` | per-device support policy |
| `UploaderConfigurationResponse` | server-pushed config |
| `AddDeviceRequest`, `BleConnectionRequest` | device registration |
| `BleNgpSecureSnapshotControlResponse` | secure-snapshot control |
| `NgpHmacResponse`, `NgpPackedKeyResponse`, `NgpLinkKeyResponse`, `NgpGetLinkKeyResponse` | NGP key exchange |
| `PatientInfo`, `Device`, `DeviceGroup`, `Time`, `TraceUpload`, `ControlCodes` | supporting |

**A cross-check that matters.** The shipped `localweb/*.json` fixtures match
`VersionResponse`, `BleNgpSecureSnapshotControlResponse` and `UploadStatusResponse`
field-for-field — independent confirmation the model reading is correct. But those
fixtures are **stale**: `latestversion.json` claims `3.4.0` while the jar's
`version.properties` says `3.15.0`. Use them as schema evidence, never as
configuration.

## 3. `uploader.jks` is a code-signing keystore, not a TLS trust store

This corrects a natural but wrong assumption. `uploader.jks` is a Java KeyStore
holding **signer certificates** — Oracle, whiteCryption and Medtronic — referenced
only by `uploader.policy`'s `signedBy` grants:

```
keystore "uploader.jks";
grant signedBy "whitecryption", codeBase "file:${user.dir}/lib/skb.jar" { AllPermission };
grant signedBy "medtronic"     { AllPermission };
```

**It is not certificate pinning and not a data key.**

The keystore opens with an **empty store password** (`keytool -list -storepass ""`).
It holds seven entries, and the expiry dates are worth recording because two of the
three signing identities have lapsed:

| alias | owner | valid to | key |
|---|---|---|---|
| `jce` | JCE Code Signing CA, Oracle | **2030-12-31** | 2048-bit RSA, SHA256withRSA |
| `oracle` | Oracle Corporation | **2030-12-29** | 2048-bit RSA, SHA256withRSA |
| `whitecryption` | whiteCryption Corporation | **2025-05-04 — EXPIRED** | 2048-bit RSA, SHA256withRSA |
| `medtronic` | Medtronic, Inc | **2024-05-15 — EXPIRED** | 3072-bit RSA, SHA256withRSA |
| `old_jce` | JCE CA, Sun Microsystems | 2020-04-25 | 1024-bit DSA (**weak**) |
| `old_oracle` | Oracle / Sun | 2016-04-14 | 1024-bit (**weak**) |
| `old_whitecryption` | whiteCryption / Sun | 2020-04-25 | 1024-bit DSA (**weak**) |

**The Medtronic code-signing certificate expired on 2024-05-15, and the
whiteCryption one on 2025-05-04** — yet this build is dated 2026-05-26. The
keystore was shipped carrying an already-expired signer. Because `uploader.policy`
grants by `signedBy` against *this* keystore, the expiry does not break the local
policy check (a keystore entry is trusted regardless of its validity window), but
it does mean the shipped trust set is stale by two years. Three legacy aliases also
retain 1024-bit DSA keys.

TLS pinning is nonetheless *likely* — `X509Certificate[] → KeyStore` and
`SSLContextBuilder` methods exist, all native, with no certificate resources in the
jar. **Unproven**, and this keystore is not evidence of it.

## 4. SAKE is solved; SKB is the wall, and it is avoidable

Two corrections to the starting assumptions, both verified.

**The `sake_whitepaper.pdf` in `OpenGuardian4` is not Medtronic's SAKE.** It is
*"SAKE*: A Symmetric AKE Protocol with PFS for IIoT"* (Fan et al., IEEE TII 2022),
a three-party academic protocol that shares only the acronym. The real
documentation is `OpenMinimed/Documentation/sake.md` and `key_databases.md`.

**SAKE itself is not white-boxed and is already reversed.** `libandroid-sake-lib_v210.so`
(54,908 B, stripped ELF ARM) contains the **standard Rijndael S-box verbatim at
offset 0xa568**, with intact JNI symbols naming struct fields
(`SAKE_CLIENT_S_keyDatabase_get`). The scheme is AES-128-CTR plus a truncated
CMAC-AES, a 6×20-byte handshake, and static per-device-type key databases — two of
which are published in the clear. A Python reimplementation already exists.

**SKB is the white-box layer, and it is not in these artefacts.** `skb.jar` is 149
entries / 134 classes with **zero native libraries**; the white-box core is
`libSecureKeyBoxJava.dylib`, which is absent from both the jar and the installed
`lib/` directory. SKB is therefore described here by interface, not by tables.

Its NIST position: **CMVP #2284, FIPS 140-2 Level 1, status Historical (2014)**,
one ARMv7 configuration, and — importantly — *"Mitigation of Other Attacks: N/A"*.
**NIST never evaluated the white-box property.**

**Verdict: not worth attacking, because it is unnecessary — not because it is
unbreakable.** No published attack on SKB exists; that is *unproven*, not *proven
broken*, and the distinction must be kept. Three cheaper routes avoid it entirely:

1. **`SakeJNI` is 34 of 36 methods native** into `libuploader.dylib` — drive the
   library as a black box rather than reimplementing it.
2. **Hook the `EncryptedString` / `Encrypted*Stream` boundary** — the plaintext
   exists on the Java side of that seam.
3. **`LocalCommunicator` already provides an offline mode** shipped by the vendor.

**Incidental weakness worth recording:** `controlCodes.encryptionKey` ships as the
39-byte ASCII string `thisisasimpleencryptionkeyandisverylong` in cleartext in the
template `patientinfo.json`. It is template data and not a live key, but it is a
poor default.

## 5. Device and transport matrix

**Every device name, BLE UUID and log message is encrypted at the call site.** They
are `StringDecryptor.decryptString(...)` invocations into `libuploader.dylib`, which
is not present. A full constant-pool scan of all 9,653 entries found 27
UUID-shaped strings — **all JNA/oshi third-party GUIDs, zero Medtronic**. No
Medtronic BLE UUID could be decoded, and none is guessed at here.

**Resource bundles are thin.** Seven base bundles carry display names and wizard
text only; the pump bundles hold two keys each (`"MiniMed™ 700 Series"`,
`"600 Series"`). No protocol hints, no error strings.

**`BluetoothNGP` is a misnomer** — it is the BLE *700-series* driver, returned by
`BlePump.makeDevice()`. The 600-series NGP path uses a USB-dongle driver instead.
**There is no NGP-over-native-BLE path.**

| family | transport |
|---|---|
| 700, 720G, 740G, 770G, **780G**, PCL F3 | BLE |
| 620G, 630G, 640G, 670G | USB link device |
| all Paradigm | USB link device |

The "Blue Adapter" is an off-the-shelf **FTDI `0x0403:0x6001`** or
**CP210x `0x10C4:0xEA60`** USB-serial dongle, driven as a virtual COM port — not
host-native BLE.

**The 780G upload is cloud-mediated.** Certificate enrolment, then a SAKE session,
then link-key/HMAC retrieval against `blest.inrange.me:7095` (per `uploader.cfg`
and `DataUploadNGPLinkSupport`). That is a hard dependency for any
reimplementation, and that host is currently NXDOMAIN — see the companion record.

**One config discrepancy:** `MMT-1886XCF` appears in the compiled-in default
mapping and the device catalogue but **not** in the shipped `configuration.json`,
so server-pushed config gates it without a new build.

**`PCL F3`** (MMT-1900/1902/1904) — "PCL" is Medtronic's published *Personalized
Closed Loop* (2019, NCT04203823), BLE, supported. But **no FDA record exists under
those model numbers**, there is no product page, and it is **not** the MiniMed Flex
(MMT-8072 / K253743). The "F3" suffix is unidentified. INFERRED, flagged as such.

## 6. Prior art: nobody uploads, and two repo corrections

Seven projects were cloned and read: `ondrej1024/carelink-python-client`,
`benceszasz/CareLinkJavaClient`, `benceszasz/xDripCareLinkFollower`, upstream
`NightscoutFoundation/xDrip`, `yo-han/Home-Assistant-Carelink`, `palmarci/OpenGuardian`
and all twelve `OpenMinimed/*` repos, plus `AdhocAdam/CareLink`.

**Firm negative: no public project uploads to CareLink.** Every POST across all
eight is authentication, `/display/message`, or Nightscout. `yo-han` is the trap —
its "uploader" writes to Nightscout, not to Medtronic.

Two leads toward an upload plane, **neither of them code**: an OpenMinimed note that
a HAT service is *"likely involved in uploading"* (a hedge), and the unresolved
`hcp/dataUpload/generateUrl` literal. The device-type enum at
`key_databases.md:35` names **type 5 = "CareLink Upload Application"**, which
suggests upload is BLE-ingest-then-push, not a client-facing API.

**Correction 1 — the `carepartner/v2` heading is stale, not the finding.**
`docs/06-patient-api-surface.md:72` is headed
`## /api/carepartner/v2/* — declared, not used`. The body already says both base
paths are live and token-gated, and the repo's own regression suite exercises the
namespace:

```
regression/hurl/03-patient-api.hurl:50  GET .../api/carepartner/v2/users/me
regression/hurl/03-patient-api.hurl:55  GET .../api/carepartner/v2/links/patients
```

Four call sites exist in two independent public projects
(`carelink_client2.py:36,39`; `api.py:218,225`). So the *heading* contradicts the
body and the tests. **The finding stands; the heading is wrong.** This is a
narrower correction than "the doc is false".

**Correction 2 — the repo conflates xDrip's fork with upstream.** The
`benceszasz` fork pins `v6/android/3.1` on `.com`; upstream pins `v13/android/3.8`
on `.eu`. These are different pins in different codebases and must not be quoted
as one.

**Genuinely new, not previously recorded:**

| item | evidence |
|---|---|
| `numUploads=30` query parameter | `carelink_client2.py` |
| `RecentUploads` / `DataUpload` schema (5 fields incl. `mobileUploaded`) | repo had only a bare 405 |
| `POST /patient/sso/reauth` as the refresh verb | 3 independent clients |
| `/patient/sso/login` + consent form-field vocabulary | multiple |
| `mmcl/.../authorize/{login,consent}` as distinct leaves | multiple |
| `application_country` / `application_language` cookies | multiple |
| `Referer` contract on data calls | multiple |
| `recentUploads[].device` as a third routing discriminator | not `deviceFamily` |

**One live discrepancy, recorded and not resolved:** the vendor bundle sends
`role: 'CARE_PARTNER'` while every client sends lowercase; and `recentUploads` is
405-on-POST per this repo but GET per xDrip. Both are consistent with
`docs/09:229`'s warning that `Allow` is not a method register.

## 7. What would close the remaining gaps

The blocker is not the jar. It is two absent artefacts:

1. **`libuploader.dylib`** — 67 native HTTP bodies, `StringDecryptor`, all device
   names and BLE UUIDs, and the `SakeJNI` surface. It is installed at
   `DSS/Uploader.bundle/Contents/Home/...` but was not extracted in the pass that
   produced these records.
2. **A single mitmproxy capture** against the uploader's own traffic. One capture
   would settle URL paths, headers, `Content-Type`, the enum `.name()` strings on
   the wire, and whether TLS pinning is active — everything inference currently
   covers.

Neither requires credentials beyond the operator's own session.

## Correction (2026-11-12)

> ⚠ **The blocker in §7 has been resolved, and the sentence above is now wrong
> in a way that would have cost a second pass.** `libuploader.dylib` was
> recovered the same day and measured. It is **not** the library §7 describes.
>
> **What §7 said**, preserved verbatim so the retraction stays visible: *"**`libuploader.dylib`**
> — 67 native HTTP bodies, `StringDecryptor`, all device names and BLE UUIDs,
> and the `SakeJNI` surface. It is installed at `DSS/Uploader.bundle/Contents/Home/...`
> but was not extracted in the pass that produced these records."*
>
> **Three of those four are false, and one of them was false about the install
> path as well.** Measured against the recovered file (11 681 712 B, sha256
> `8a927fe36646ed5a…`, **x86_64 only**):
>
> | §7 claimed the file holds | measured |
> |---|---|
> | the `SakeJNI` surface | ✅ **34 exports**, set-identical to the JAR's 34 `ACC_NATIVE` methods |
> | 67 native HTTP bodies | ❌ **0** — no `HttpClientCommunicator` symbol of any kind |
> | `StringDecryptor` | ❌ **0** — the string does not occur in the file |
> | all device names and BLE UUIDs | ❌ **0** — no `MMT-` code, no UUID but the SIG base UUID, no pump vocabulary |
>
> The install path in §7 is also wrong: the file is unpacked to
> `DSS/lib/macos/x86_64/libuploader.dylib`, not under
> `Uploader.bundle/Contents/Home/`. It is the **BLE/transport** library —
> `BRILJNI` (287 exports), `GattStreamJNI` (56), `SakeJNI` (34) and
> `uploader.Loader.l` (1) — and nothing else.
>
> **The consequence for §1 and §5 is the part that matters.** The JAR declares
> **1 370 native methods across 38 classes**; this library serves **378** of
> them. The HTTP bodies and the string decryptor live in at least one **further,
> still-unlocated** artefact. So *"the blocker is one absent dylib"* was a wrong
> model of the gap, and §1's ceiling statement stands unchanged: URL assembly,
> headers, TLS configuration and the SKB glue remain unreachable statically.
> **§5's negative survives the recovery in full** — the recovered library
> contains zero Medtronic BLE UUIDs, so *"No Medtronic BLE UUID could be decoded"*
> is still true and is now true of the one artefact §7 named as the place they
> would be found.
>
> **§4's SKB sentence is also superseded.** It read *"the white-box core is
> `libSecureKeyBoxJava.dylib`, which is absent from both the jar and the
> installed `lib/` directory"*. The file is recovered (6 502 032 B, **universal
> x86_64 + arm64**), and it is the SKB engine — `SKB_DrbgSha`, `SKB_GetPublicKey`,
> `SKB_WrapData`, `SKB_CacheEngine`, twelve mangled `SKB_Get…` accessors and the
> `AntiDebug`/`Jailbreak`/`Root` callbacks. **The verdict in §4 is not changed by
> this**: no claim is made that SKB is broken or that its white-box tables are
> recoverable, and *"not worth attacking, because it is unnecessary"* stands.
>
> **One correction to the count circulated with the recovery, recorded here
> because §7's blocker sentence is what sent people looking:** the figure "379
> `BRILJNI` symbols" is a substring miscount (`grep -c 'Java_'` counts 379
> occurrences of a five-character literal, one of which begins no symbol). The
> real export count is **287**.
>
> Full record, including the build-path leak, the BRIL identification and the
> Apple-Silicon architecture finding:
> `findings-log/2026-11-12-uploader-native-libraries/FINDINGS.md`.

## 8. Not claimed

- No HTTP verb, header, URL path or `Content-Type` beyond the `{token, target}`
  envelope and the POST inference.
- No Medtronic BLE UUID.
- No claim that SKB is broken. No claim that it is safe either.
- No claim about what `PCL F3`'s suffix means.
- No claim that any shipped `secureToken` or `sakeKey` value is valid.
