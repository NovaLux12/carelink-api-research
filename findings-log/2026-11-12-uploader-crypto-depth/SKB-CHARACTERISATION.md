# libSecureKeyBoxJava.dylib — characterisation, and what SKB actually protects

Scope: `<workdir>/nativelibs/libSecureKeyBoxJava.dylib`
(6,502,032 bytes) + the Java side in `uploader.jar` (9,653 entries, build `b052a3cd…`, spec 3.15.0,
built 2026-05-26) and `skb.jar` (149 entries / 134 classes).

Evidence labels: **OBSERVED** (command run this session, offset/class quoted) / **PUBLISHED** / **INFERRED**.

---

## 1. The binary

**OBSERVED** `file` → Mach-O universal, 2 architectures. Fat header parsed by hand:

| slice | cputype | offset | size |
|---|---|---|---|
| x86_64 | 0x01000007 / sub 3 | 0x4000 | 3,288,176 |
| arm64  | 0x0100000C / sub 0 | 0x328000 | 3,192,464 |

**OBSERVED** x86_64 `__TEXT` sections (file offset = vmaddr in this slice):

| section | size | note |
|---|---|---|
| `__text` | 801,616 | 26.4 % of slice |
| `__const` | **2,218,608** | **73.1 % of slice** |
| `__cstring` | 4,223 | JNI method/class-name table |
| `__gcc_except_tab` | 2,852 | C++ EH |

`__DATA` is 8 KB of file (got/la_symbol_ptr/const) + 2.5 MB `__bss` + 720 KB `__common`.
arm64 mirror: `__text` 670,060, `__const` 2,234,297. Neither slice's `__const` is byte-identical to the other.

**Linked libraries** — only system libs: `/usr/lib/libc++.1.dylib`, `/usr/lib/libSystem.B.dylib`,
`/usr/lib/libobjc.A.dylib`. No dependency on `libuploader.dylib`, no `libcrypto`. Self-contained.

**Imports (49 undefined symbols)** — entirely libc/libc++/ObjC: `_memcpy`, `_memcmp`, `_memset_pattern16`,
`_qsort`, `_fopen/_fread/_fwrite/_fseek`, `_pthread_mutex_*`, `_snprintf`, `_strcpy`, `_objc_msgSend`,
`_objc_alloc`, `___stack_chk_guard`. **No `libcrypto`, no JNI-injection, nothing crypto-looking imported.**
⇒ all cryptography is implemented in the 801 KB of `__text`. **OBSERVED.**

**Exports (75)** — `_JNI_OnLoad`, `_JNI_OnUnload`, and a set of mangled C++ symbols whose class/type
names have been replaced by content-hash identifiers, e.g.
`__ZL12SKB_WrapDataP49l3175f1d6…PvS0_P7JNIEnv_`, `__Z25SKB_ThrowExceptionOnErroriP7JNIEnv_`,
`__Z36JNI_SkbException_getErrorCodeEnumIdxP7JNIEnv_P8_jobjecti`, plus `__ZL5g_jvm`, `__ZL8g_engine`,
`__ZZ19JNI_RegisterNativesvE18obf_engine_methods` and siblings `obf_cipher_methods`,
`obf_transform_methods`, `obf_ka_methods`, `obf_sd_methods`.

Those `obf_*_methods` statics are the `JNINativeMethod[]` tables each obfuscated Java class is
registered with. `JNI_OnLoad` at `0x8880`; `JNI_RegisterNatives` string at `0xca928`.

**OBSERVED** `jni_class_list` (vmaddr `0x2e51b0`, 6 entries × 32 bytes) resolves to:

```
l4887ea602e75f2d9b6cb57badd19854b789481dc87c92693/l9d23c862c8e49ddcac7ee4108e839c0316d0168fdce3ccca
l4887ea602e75f2d9b6cb57badd19854b789481dc87c92693/lc0b2a6f208dda3513dd2fb5fc566735082ac6c0c795b66e5   (SecureData)
l4887ea602e75f2d9b6cb57badd19854b789481dc87c92693/l0f835ec20c37f48ce0cff4e8f16a959830950a0e2b79ad18   (KeyAgreement)
l4887ea602e75f2d9b6cb57badd19854b789481dc87c92693/l85529621beb5ca0dfa4a80c7a0a90355cc2eeb3fa837e49b   (Transform)
l4887ea602e75f2d9b6cb57badd19854b789481dc87c92693/l9fcf14d158c91ef552c8e147bb04e3b16a17fabbf0e0e7bc   (Cipher's native_part)
l4887ea602e75f2d9b6cb57badd19854b789481dc87c92693/la3771657e97e8fdefa8e8182dbcb13417ed89d71714bbb08   (Engine)
```

`l9fcf14d…` is exactly the field type of `com.whitecryption.skb.Cipher.native_part` (**OBSERVED** in the
CFR output for `Cipher.java:11`). So the JNI surface is the SKB object model and nothing else.

**Anti-analysis hooks — OBSERVED as strings only:** `_SKB_Callback_AntiDebug`, `_SKB_Callback_Jailbreak`,
`_SKB_Callback_Root`. I did not trace whether they are wired to the callbacks at runtime; treat as
present-but-unexercised.

---

## 2. White-box technique — present, but *lightweight*, not Chow-scale

### 2.1 Plaintext AES tables are present
**OBSERVED** the canonical AES S-box appears **once** in the x86_64 slice's `__const` at file offset
`0x2c5f70` (verified byte-identical to the standard 256-byte table), and once in the arm64 slice.
It is preceded by `1f 00 00 00` ×4 and followed by the sequence `00,01,02,03,04,05,…,ffffffff` —
i.e. an ordinary T-table/round-constant cluster, not an encoded one. The same plaintext S-box exists in
`libuploader.dylib` at `0xa3cbb0`.

⇒ A standard (non-white-boxed) AES implementation is compiled in. The white-box path is a *separate*
implementation.

### 2.2 Genuine encoded T-boxes exist
**OBSERVED.** Scanning `__const` for 1024-byte blocks whose four interleaved byte-lanes are each a
permutation of 0..255, then filtering by differential uniformity:

- **73 tables** (74,752 bytes) have all four lanes as permutations **and** AES-grade DDT
  (`max_a max_v DDT = 4`, same as the real AES S-box).
- They cluster:
  - `0xcc650`–`0xd0650` — 16 tables (16,384 B)
  - `0xd8380`–`0xdc380` — 16 tables
  - `0x134c90`–`0x138c90` — 16 tables
  - `0x144970`–`0x148970` — 16 tables
  - `0x1af740`, `0x1b1740`, `0x1b2740` — 3 tables each with **lane1 == lane2** (the classic Te-table redundancy signature)
- These are **not** classic AES Te0..Te3: no block matches the plaintext Te-table bytes (**OBSERVED**, 0 hits). Their lanes are affine-masked and then diffused — i.e. *encoded* T-boxes, which is what a white-box AES round looks like.

### 2.3 But the scale is small
**OBSERVED**:

- Encoded T-boxes: **~75 KB** out of 2,218,608 bytes of `__const` (3.4 %).
- 264 other 256-byte permutation tables in `__const` are **pure GF(2)-affine** maps — these are
  *mixing bijections* (white-box encodings), not S-boxes.
- 121 further 256-byte permutations are nonlinear with non-AES DDT (values 64/96/128/160) — consistent
  with S-boxes for the non-AES primitives in the enum (see §3.4), not AES rounds.
- 63 % of `__const` sits in ≥7.5-bit/byte entropy 4 KB blocks, but that mass does **not** have
  permutation-lane structure. It is high-entropy data that is not AES T-boxes.

**Interpretation (INFERRED):** a published Chow-style white-box AES-128 is 1–4 MB of encoded tables
(≈10–40 KB per round × rounds × variants). 75 KB of encoded T-boxes plus 264 mixing bijections across
4+16-table clusters is 1–2 orders of magnitude smaller — a *table-encoded implementation with internal
encodings*, i.e. white-box-class obfuscation, not a heavyweight published-scheme instance.

**Explicitly not claimed:** I have not shown these tables are invertible-into-plain-AES, I have not
shown the encodings are strong, and I have **not** attempted a BGE/DFA-style attack. "Weak white-box"
would be an over-claim; "present and encoded" is what the bytes support.

### 2.4 SKB ships a persistent key cache
**OBSERVED** strings in both `libSecureKeyBoxJava.dylib` (`0xca9xx`) and `libuploader.dylib` (`0xa80exx`):

```
key_cache   persistent   memory   key_cache_max_items
diversification_guid   export_guid   export_key_version
request_count   reference_count   implementation
medtronic.carelink.uploader   /medtronic/carelink/uploader/
skb_cache_   %s%08llx%08llx%s   .kc   %s%s%s%s%s   /dev/urandom   /dev/random
sha1   aes   123456789   %02X
```

and in libuploader only: `skb_key_flow_` + `.json` (`skb_key_flow_<…>.json` — a key-flow audit log).

`%s%08llx%08llx%s` with `%08llx%08llx` is a GUID-format pair, and `SecurityUtils.retrieveSystemId()`
returns a `UUID` whose `getLeastSignificantBits()/getMostSignificantBits()` are consumed elsewhere
(**OBSERVED** in `com/medtronic/i/i/l/iIIiIiiiiIiII`). Consistent with a per-device key cache file
`…/medtronic/carelink/uploader/skb_cache_<guid><guid>.kc` (**INFERRED** from the templates).

⇒ the white-box keys are **device-diversified** and cached to disk, i.e. keys can be extracted from
*this* installation but are not one global constant. `123456789` looks like a default diversification
GUID — a real hardening smell, stated as an observation only.

---

## 3. What the uploader actually uses SKB for

### 3.1 The Java protection layer, quantified
**OBSERVED** across `uploader.jar`: 8,972 `.class` files, 10,010 methods, **385 native methods (3.8 %)**
in **8 classes**. Separately, only **9 classes** carry the `$uploader$COI` native initialiser and **14**
reference `uploader/Loader`.

`uploader/Loader.class` is 120 bytes — a single `static native void l(int)`. `uploader/NativeLoader`
extracts `libuploader.dylib` to a temp file and `System.load`s it.

So the Java-collateral-damage layer is narrow: `com.medtronic.diabetes.utils.SecurityUtils` (all 9 crypto
methods `native`), `EncryptedString`, and the logger/communicator. Everything else is ordinary Java.

**Correction to a natural assumption:** `libuploader.dylib` does **not** implement `SecurityUtils`.
**OBSERVED** its 378 `Java_*` exports are `com_medtronic_minimed_bril_BRILJNI_*` (287),
`gatts_GattStreamJNI_*` (56), `sake_SakeJNI_*` (34), `uploader_Loader_l`, and **zero**
`SecurityUtils`/`HttpClientCommunicator` natives. The string `diabetes/utils/SecurityUtils` does not
occur in either dylib. ⇒ a third native binary is missing from this extraction (**INFERRED**; the
installer manifest at `mac-copy/CareLinkUploader-install.txt:347` shows a third `-cp` entry and line 241
ships `libEncryption.dylib` under `Drivers/usb/VerioVue`, but nothing named for `SecurityUtils`).
**Practical consequence:** every SKB call in this workspace's Java cannot be executed here anyway — the
`native` bodies for `SecurityUtils.encrypt/decrypt` aren't in the two dylibs I have.

### 3.2 Every SKB call site — complete list
**OBSERVED** by scanning every `.class` constant pool in `uploader.jar` for `com/whitecryption/skb`:

| class | SKB API used |
|---|---|
| `com/medtronic/diabetes/solar/logger/MedicalLoggerFactory` | `Engine.createDataFromWrapped`, `Engine.createCipher`, `SkbProvider.<init>`, `SkbException.getMessage` |
| `com/medtronic/diabetes/solar/utils/EncryptedInputStream` | `Cipher.processBuffer`, `SkbException.getMessage` |
| `com/medtronic/diabetes/solar/utils/EncryptedOutputStream` | (`Cipher` only as a parameter type) |
| `com/medtronic/diabetes/solar/utils/proxy/EncryptedString` | (`Cipher` as field/param type) |
| `com/medtronic/diabetes/utils/SecurityUtils` | (`Cipher` as param type) |
| `com/medtronic/diabetes/solar/dataupload/api/impl/rest/HttpClientCommunicator` | (`Cipher`/`SecureData` types only) |
| `com/medtronic/diabetes/solar/Solar` | (`SecureData` field only) |

**Only two classes call SKB at all.** That is the whole footprint. All the actual `encrypt`/`decrypt`
work is delegated through `SecurityUtils`'s native methods.

### 3.3 Use #1 — the CareLink **password**, in memory
`com/medtronic/diabetes/solar/utils/proxy/EncryptedString` (**OBSERVED**, full CFR output):

```java
private static Cipher iIIIiiiiiiiiIi;                 // SKB cipher, static
public  native <T> T access(Accessor<T> var1);        // yields char[] transiently
public  native byte[] getEncryptedValue();
private native void iIIiiiiiiIIiii(Cipher var1, byte[] var2);
// ctor: this.iiIIIiiiiiIiiI = SecurityUtils.getCipherIv(SecurityUtils.retrieveSystemId());
```

`AbstractAuthenticator.getPasswordAuthentication()` (**OBSERVED**) does
`entry.getValue().access(cArray -> new PasswordAuthentication(user, cArray))` — the password is handed to
`PasswordAuthentication` through the SKB accessor and never materialises as a long-lived `String`.
`ConsoleAuthenticator`, `UnattendedAuthenticator`, `JavaFXAuthenticator` all build
`new EncryptedString(char[], 0, n)` from a `char[256]` read straight off the input stream /
`PasswordField`, then persist it via `iIIiIiiiiiIIiI.iIIiiiiiiIIiii(host, port, EncryptedString)`
into `Preferences.userRoot()` (**OBSERVED**).

⇒ **SKB protects the CareLink account password**: at rest in the Java `Preferences` store as
`getEncryptedValue()` (SKB-wrapped, IV derived from the machine UUID), and in memory as SKB `SecureData`
with short-lived plaintext only inside an `access()` callback. This is the strongest and clearest use.

`AbstractAuthenticator`'s constructor additionally does a code-signing check — it Base64s the first
certificate's public key from its own `ProtectionDomain` and compares against a hardcoded constant,
throwing otherwise (**OBSERVED**). That is authenticode pinning of the jar, separate from SKB.

### 3.4 Use #2 — the **diagnostic log** at rest, and it uses ordinary AES
`MedicalLoggerFactory.iIIIIiiiiIiIIi()` (**OBSERVED**):

```java
byte[] iv = SecurityUtils.getRandomIv();
this.IIIiIiiiiIiiii();                                  // new SkbProvider()
this.iIiiiiiiiIiIII = this.iIIiiiiiiIIiii();             // Engine.createDataFromWrapped(...)
Cipher cipher = Engine.createCipher(SKB_CIPHER_ALGORITHM_AES_128_CBC,
                                    SKB_CIPHER_DIRECTION_ENCRYPT, 1, null, this.iIiiiiiiiIiIII);
this.iIIiiiiiiIIiii.write(iv);
this.IIIiiiiiiIIIIi = new EncryptedOutputStream(out, cipher, iv, true);
this.iIiIiiiiiiIiii = new GZIPOutputStream(this.IIIiiiiiiIIIIi, true);
```

and the key material comes from the server, not the binary (**OBSERVED**):

```java
private SecureData iIIiiiiiiIIiii() {
    String s = new String(new char[16]).replace(/*'"'*/, /*'0'*/);   // 16 chars
    byte[] b = (this.iIIiIiiiiIiIIi + s).getBytes(UTF_8);           // key string + zeros
    byte[] k = new byte[16]; System.arraycopy(b, 0, k, 0, 16);
    return Engine.createDataFromWrapped(k, SKB_DATA_TYPE_BYTES, SKB_DATA_FORMAT_RAW,
                                        SKB_CIPHER_ALGORITHM_NULL, null, null);
}
public void setEncryptionKey(String s) { ... }
```

`setEncryptionKey` is driven by `ControlCodes.getLogCipher()` — i.e. `@JsonProperty("encryptionKey")`
from the server's patient-info response (`MedicalLoggerSynchronizer.configureLogging`,
**OBSERVED**). Files are `uploader.log`, gzipped then AES-128-CBC'd, IV prepended.

⇒ **SKB protects the diagnostic log file at rest**, with a *server-supplied* key. The log contains trace
records (`ActionTraceLogger`, `DeviceInfoLogUtils`, snapshot metric fields). `ControlCodes` full form:
logLevel, encryptionKey, traceHistoryUpload, saveSnapshotLocally, virtualException.

Note the algorithm is `AES_128_CBC` — **not** a white-box-only cipher, and the plaintext AES tables at
`0x2c5f70` are consistent with that path being a normal AES. So for the log the white-box protects *the
key*, not the algorithm. `SKB_CIPHER_ALGORITHM_NULL` wrapping is used to hold the raw key bytes.

### 3.5 Use #3 — the **auth token**, and it is conditional
`HttpClientCommunicator` (**OBSERVED**) has three `SecureData` fields, `native String getToken()`,
`native String encrypt(String) throws SkbException`, `native String decrypt(String) throws SkbException`,
`native boolean isEncryptedToken()`, and two private statics taking `(String, SecureData, byte[])`.
`Solar` holds one `SecureData`.

`LocalCommunicator.isEncryptedToken()` returns **`false`** (**OBSERVED**). The REST implementation's is
`native`. ⇒ token encryption is a deployment/server-configuration switch; when off, the token is plain.

### 3.6 What SKB does **not** touch
- **The medical snapshot upload.** `DataUploadCommunicator.sendSnapshot(byte[], String×6, byte[], …)`
  takes a **raw `byte[]`** (**OBSERVED**, interface signature). `UploadDeviceAction` — the only caller
  that ships pump data — references exactly one `SecurityUtils` method in its constant pool:
  `getSecureRandom()` (**OBSERVED**, full constant-pool scan). No SKB, no `encrypt`.
  The bytes come from `IDeviceSnapshot.getRawData()` and go straight into the HTTP body.
  ⇒ medical data in transit is protected by **TLS + bearer token**, not by SKB. (**OBSERVED** signatures, **INFERRED** that no intermediate wrapping occurs — the `sendSnapshot` decompilation is one of the CFR failures.)
- **SAKE link keys.** `packLinkKey`/`unpackLinkKey`/`putLinkKey`/`getLinkKey` are `native` on
  `HttpClientCommunicator` and land in `SakeJNI` (34 natives) inside `libuploader.dylib`. The SKB dylib
  contains no SAKE symbol. **OBSERVED**: zero overlap.
- **Anything in `libuploader.dylib`.** That library has **no** `JNI_OnLoad`, **no** `RegisterNatives`,
  no `_SKB_*` symbols — it exports plain `Java_…` names only. It contains the SKB *engine internals* as
  strings (`skb_cache_`, `key_cache`, `diversification_guid`, `.kc`, …) and 72 encoded AES-grade T-boxes
  of its own (5 clusters, 73,728 bytes) plus its own plaintext AES S-box. But it does not link
  `libSecureKeyBoxJava.dylib`. **INFERRED**: `libuploader` statically links a *second copy* of the SKB
  engine core (WhiteCryption's product is normally statically linked), while `libSecureKeyBoxJava.dylib`
  is a separate dynamic build used only by `skb.jar`'s `Cipher`/`Engine` object model via `JNI_OnLoad`.
  The two share no tables (**OBSERVED**: 0 shared 1024-byte tables, different `__const` hashes).

### 3.7 Answer to the central question
SKB in this uploader protects, in order of evidence strength:

1. **(a) the CareLink credentials** — password wrapped into SKB `SecureData`, persisted as
   `getEncryptedValue()` in `Preferences`, plaintext only inside `access()` callbacks. *Observed in full.*
2. **(e/other) the diagnostic log at rest** — gzip + AES-128-CBC via `Engine.createCipher`, with a
   server-supplied key held as `SecureData`. *Observed in full.*
3. **(c-adjacent) the REST auth token** — optionally, gated by `isEncryptedToken()`; **off** in the
   local communicator. *Observed as API; the native body is not in these dylibs.*
4. **Not (b)**: the uploaded medical payload. Raw `byte[]` → HTTPS.
5. **Not (c)**: SAKE link keys. Those are `SakeJNI` in `libuploader.dylib`, un-white-boxed.

---

## 4. Does SKB gate access to pump data?

**No — not by itself.** Reasoning, all from observations above:

- The pump-data path (`UploadDeviceAction` → `sendSnapshot(byte[])`) never calls SKB. Removing SKB from
  the picture does not obstruct reading or sending a snapshot; it obstructs **logging in**.
- SKB's real gate is on the **credential**, which gates the **server**, not the **pump**. To get pump
  data you need BLE access (SAKE, already reversed and public, and shipped *un-obfuscated* in
  `libuploader.dylib` — 287 plain `BRILJNI` natives, plaintext AES S-box, standard `AES-128-CTR` /
  `AES-128-ECB` strings).
- SKB therefore sits at a **different layer** from the barrier that has already fallen. It protects
  *credential storage* and *log confidentiality*, not the device link and not the upload body.

**Where it is still a real barrier (published/observed):** anyone who wants a **CareLink account
password** off a machine — the `Preferences` blob is SKB-wrapped with an IV derived from the machine UUID,
and in-process the plaintext only exists inside a native `access()` callback. That is genuinely harder
than reading a file. It is a *credential-at-rest* control.

**Honest framing:** SKB is not broken here and not shown weak. It is also not the thing standing between
an attacker and pump data — SAKE plus the plaintext AES tables in `libuploader.dylib` already are, and
that is separately true. The accurate sentence is: **SKB protects the CareLink password and the
diagnostic log; pump data is obtainable through the BLE/SAKE path regardless of SKB.**

---

## 5. Secondary observations worth carrying forward

- **`uploader.jks` ships with the app** (`mac-copy/uploader.jks`, Java KeyStore `feedfeed`, alias
  `medtronic`, cert `X.509`). Its role is TLS trust (the REST client uses `SSLContextBuilder`); not
  cracked here. Whether its private key has a weak/blank password is **not** established.
- **`uploader.cfg`** points at `http://blest.inrange.me:7095/api/dataupload/v1` (plain HTTP, lab host) in
  this copy — a development configuration, not the production `carelink.medtronic.com` in the installer
  manifest.
- **`localweb/data_tokens.json` + `metadata_token.json`** contain base64 `secureToken` blobs for
  `USER_SETTINGS`/`PUMP_HISTORY`/`PUMP_SENSOR_HISTORY`/`REPO_LIST`. These are *server-issued*
  `BLENGP_SECURE_SNAPSHOT_CONTROL_RESPONSE` tokens, not locally generated — do not confuse them with SKB
  output.
- **Version pin:** `skb.jar` built by Ant 1.10.5 on Ubuntu, JDK 11.0.28; `uploader.jar` by Maven 3.9.9 on
  JDK 1.8.0_462. Consistent with a vendor-supplied SKB drop-in plus a Medtronic app build.

---

## 6. Commands run (all read-only)

```
file nativelibs/libSecureKeyBoxJava.dylib
python3  # fat-header / mach_header_64 / load-command / section walker (both slices)
python3  # LC_SYMTAB reader: undefined + exported symbols, both dylibs
strings -a -n 4..10 libSecureKeyBoxJava.dylib | grep ...
python3  # __cstring dump (JNI class/method table)
python3  # jni_class_list + JNI_METHODS pointer resolution
python3  # __const entropy scan (4K/64K blocks), AES S-box search
python3  # Te0/Te1/Te2/Te3 exact-byte match (0 hits)
python3  # 1024-byte 4-lane permutation scan + DDT max + GF(2)-affine test
python3  # 256-byte permutation table census (385 tables: 264 affine, 121 nonlinear)
python3  # cross-check: 0 shared tables between the two dylibs
nm / objdump       # -> "file format not recognized" (no Mach-O binutils here); used hand parser instead
java -jar cfr.jar <skb.jar> --outputdir skbwork/java         # 86 .java
java -jar cfr.jar <single .class>                            # SecurityUtils, MLF, Encrypted*, Authenticators…
python3  # constant-pool walker over uploader.jar: native-method census, SKB call-site graph
python3  # zipfile manifest / signature inspection of uploader.jar and skb.jar
```

**Not done / limits:** no disassembly of `__text` (no Mach-O-capable objdump/radare2 on this host, and I
did not install one); no dynamic run (the binary is macOS, and `SecurityUtils`' native bodies are in a
third library not present); no white-box attack attempt. Anything about *cryptographic strength* of the
SKB encodings is therefore unanswered rather than answered negatively.
