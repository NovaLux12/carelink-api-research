# CareLink uploader — the native libraries, recovered (2026-11-12)

**Evidence class: OBSERVED** — byte-level static analysis of four Mach-O dylibs
recovered from the installed 3.15.0 payload, plus the `uploader.jar` they are
loaded beside. Companion to
`findings-log/2026-11-12-uploader-installed-payload/` (the artefacts and their
provenance) and `findings-log/2026-11-12-uploader-wire-protocol/` (what the JAR
says). **This record closes the first of that record's two blockers and
corrects two claims made about what the recovery would buy.**

**Requests issued by this pass: 0.** All work is local: `file`, `strings`,
`nm`-equivalent Mach-O parsing, and the jar's own class files. No Medtronic host
was contacted and no credential was used.

**Cap: 0 of a 0 cap — no request was made.** **Delay:** none applies, because no
request was issued — the standing rule (≥2 s between requests to the same host)
was not engaged, and no spacing is claimed. **Methods:** no `GET`, `OPTIONS` or
`POST` was sent to any host. The two `dig`/`curl` liveness probes belonging to
this investigation are accounted for in the companion record, not here.

**Tooling:** `strings -a`, `file`, CFR 0.152 under OpenJDK 17, and a hand-rolled
Mach-O export-table reader (LIEF 1.0). The `binutils` on this host cannot read
Mach-O (`nm: file format not recognized`), so symbol counts below come from the
export trie and the `LC_SYMTAB` table, not from `nm`.

---

## 1. What was recovered

Four dylibs, all from the installed tree, all `Mach-O 64-bit`:

| file | bytes | sha256 (first 16) | slices |
|---|---:|---|---|
| `libuploader.dylib` | 11 681 712 | `8a927fe36646ed5a` | **x86_64 only** |
| `libSecureKeyBoxJava.dylib` | 6 502 032 | `35268c069c866c38` | **x86_64 + arm64** |
| `libhidapi.dylib` | 80 688 | `07c9e289544973ba` | x86_64 only |
| `libusb4java.dylib` | 203 472 | `f1cec0435353929b` | x86_64 only |

`libuploader.dylib` is installed by the vendor at
`DSS/lib/macos/x86_64/` — the install log records that directory being created
and that one file being unpacked into it, and **records no `macos/arm64`
directory at all** (§3). `libSecureKeyBoxJava.dylib`, by contrast, is unpacked
into `Uploader.bundle/Contents/Home/`, beside the JRE, and is a universal binary.

Both facts are measured (`file`, and the export trie read per slice), not
inferred.

## 2. The count is 287, and the record must not carry 379

Prose circulating before this pass said "379 `_Java_com_medtronic_minimed_bril_BRILJNI_*`
symbols". **That figure is wrong, and the error is a classic substring miscount:**

```
$ strings -a libuploader.dylib | grep -c 'Java_'
379
$ strings -a libuploader.dylib | grep -o '_Java_com_medtronic_minimed_bril_BRILJNI_' | wc -l
287
$ strings -a libuploader.dylib | grep -c '^_Java_'
378
```

379 is the number of *occurrences of the bare substring* `Java_` — one of them is
a stray literal `Java_` that begins no symbol. The true export populations, read
from the Mach-O export trie:

| JNI class | exported methods | natives declared in `uploader.jar` |
|---|---:|---:|
| `com.medtronic.minimed.bril.BRILJNI` | **287** (286 + `swig_1module_1init`) | 287 |
| `com.medtronic.minimed.gatts.GattStreamJNI` | 56 | 56 |
| `com.medtronic.minimed.sake.SakeJNI` | 34 | 34 |
| `uploader.Loader` | 1 (`l`) | 1 |
| **total `Java_` exports** | **378** | — |

Total exports incl. non-JNI: **500**. Total `LC_SYMTAB` entries: **780**.

The two columns agree class-by-class — a 287/56/34/1 match between the JAR's
`native` method tables (read out of the class files' `ACC_NATIVE` flags) and the
dylib's export trie. **That agreement is the real result here**, because it says
this dylib is the exact implementation for these three JNI classes and no other:
there is no fourth Medtronic JNI surface hiding in it.

**Counting rule, stated before the number** (AGENTS.md §6 item 7): one unit is
one *distinct exported symbol* whose name matches `_Java_<class>_<method>`, read
from the export trie; the two `swig_*` and `_init` forms are counted where they
appear; the JAR side is one `ACC_NATIVE` method in the corresponding class file.
The two are compared as sets, not totals.

## 3. BRIL is confirmed as a real BLE stack, and the build path leaks

**BRIL is identified — OBSERVED.** The dylib carries 19 distinct absolute source
paths under `…/scp_extra/bril/`, resolving to **17 distinct `.cpp` files**:

```
driverBle/GAP/ScanUtils.cpp          driverBle/HCI/CmdBuilder.cpp
driverBle/HCI/EventHandling.cpp      driverBle/StateHandling.cpp
driverBle/h_dvcBLE.cpp               driverBle/utils/{OsalAux,TimeoutHandling,TimerFunctions}.cpp
interface/CBFactory.cpp              interface/private/{AddServiceSM,DiscoverCharacteristicsSM}.cpp
interface/private/{DevInfoStorage,iStorageLoader,SafeDelegate}.cpp
interface/private/{iCBCentralManager,iCBPeripheral}.cpp
windows_usart/SerialPortPOSIX.cpp
```

That is a **GAP / HCI / scan state machine over Apple's CoreBluetooth delegate
API**, and the runtime strings confirm it is linked against CoreBluetooth's
Objective-C classes rather than a vendored stack: `CBCentralManager` (42 hits),
`CBPeripheral` (149), `CBPeripheralManager` (60), plus the
`SwigDirector_CBPeripheralDelegate` / `SwigDirector_CBCentralManagerDelegate`
proxies that route CoreBluetooth callbacks back into C++ through SWIG.
Loaded frameworks: `CoreFoundation`, `IOKit`, `Foundation`, `AppKit`, `Security`
and `libobjc` — **`CoreBluetooth.framework` is not in `LC_LOAD_DYLIB`**, so the
CB classes are reached by name at run time, which is why the `strings` hits are
class names and not a link-time dependency.

`SerialPortPOSIX.cpp` under `windows_usart/` is the other half: the USB-serial
path is in this same library, so the transport split recorded in the wire-protocol
record's §5 (BLE for the 700-series and PCL, USB link device for 620G–670G and
Paradigm) is **implemented in one dylib, not two**.

**The build path leak — OBSERVED, and redacted by rule.** The `__FILE__` strings
carry the CI account's absolute home directory, the Jenkins workspace name
`uploader_macos_pipeline`, and the build tree `…/build/dcp/src_{analysis,protected}/`.
25 path strings survive, split **16** under `src_analysis` and **9** under
`src_protected` — i.e. the vendor compiles the same BRIL sources twice, once as
analysis and once as protected, which is a structural hint about their own
obfuscation split. **The verbatim paths are not reproduced in this record**
(AGENTS.md §3, §7: no machine path in a diff); the finding is the *shape*, and
the shape above is what a reader needs.

`src_protected` also carries `3rdParty/boost/boost/asio/**` (6 `.ipp` files), so
the HTTP/async layer is Boost.Asio — which matches the exported
`boost::asio::detail::*` symbols and the `kqueue_reactor` import.

## 4. ⚠ Corrected in-flight: `libuploader.dylib` is **not** the HTTP/StringDecryptor library

The wire-protocol record's §7 said the missing `libuploader.dylib` held *"67
native HTTP bodies, `StringDecryptor`, all device names and BLE UUIDs, and the
`SakeJNI` surface"*. Measured against the recovered file, **one of those four is
right and three are not**:

| claimed to be inside | measured |
|---|---|
| `SakeJNI` surface | ✅ **34 exports**, exactly matching the JAR |
| 67 native HTTP bodies (`HttpClientCommunicator`) | ❌ **0** — no `HttpClientCommunicator` symbol, no JNI export for that class |
| `StringDecryptor` (443 natives) | ❌ **0** — the string `StringDecryptor` does not occur in the file at all |
| all device names and BLE UUIDs | ❌ **0** — see §5 |

`StringDecryptor` declares **443 native methods** in the JAR and **none** of them
is exported here. `Solar` (48 natives) and `Uploader` (56) are likewise absent.
The jar's **1 370 native methods across 38 classes** are served by at least
*three* native modules, and this recovery accounts for **378** of them.

So the earlier framing — "the blocker is one absent dylib" — was wrong in a way
that would have cost a second full pass. The correct statement:

- **`libuploader.dylib` is the BLE/transport library** (`BRILJNI`,
  `GattStreamJNI`, `SakeJNI`, `uploader.Loader`), and it is now recovered.
- **The HTTP bodies and the string decryptor live somewhere else**, and that
  artefact has not been located. Only two `dlsym` imports and no
  `RegisterNatives` import are present, so the binding for those other natives is
  not done from inside this library.
- **INFERRED, flagged:** `uploader.Loader.l(int)` is the one synthetic native in
  a class named `Loader`, referenced by 14 classes including `StringDecryptor`,
  `Solar`, `HttpClientCommunicator` and all five `*Check` utilities. A single
  `native void l(int)` that 14 unrelated classes depend on is the shape of a
  *dispatcher* — most plausibly `RegisterNatives`-by-table, or a decryptor
  unpacked to a temp file and `System.load`ed (the JAR ships 22 `libjnidispatch`
  blobs and **zero** `lib/` entries, and `NativeLoader` in the JAR does write a
  temp file and `System.load` it). **The assumption is that the `0xCAFEBABE`
  absence in this dylib does not rule that out**, since the payload would be
  decrypted at run time. Nothing here proves it, and no attempt was made to
  execute the library.

## 5. It adds **no** device vocabulary — the negative, stated plainly

This is the most useful thing the recovery does *not* buy, so it is recorded as a
negative rather than left as an absence:

```
$ strings -a libuploader.dylib | grep -cE 'MMT-?[0-9]{4}'        -> 0
$ strings -a libuploader.dylib | grep -iE 'insulin|bolus|basal|sensor|pump'  -> 0
$ strings -a libuploader.dylib | grep -oE '<uuid pattern>' | sort -u
00000000-0000-1000-8000-00805F9B34FB        (the Bluetooth SIG base UUID, x1)
$ strings -a libuploader.dylib | grep -ciE 'alarm' -> 1  ("[ALARM]: E_ATTRIBUTES_DISCOVERED ...")
```

**Zero Medtronic BLE UUIDs, zero model codes, zero pump vocabulary, zero alarm
codes.** The library is a *transport* implementation: it discovers services and
characteristics and shuttles bytes. The service/characteristic UUIDs it is told
to look for arrive as data (from the JAR, which encrypts its literals, or from
the pump), not as constants in this file. So the wire-protocol record's §5
conclusion — *"No Medtronic BLE UUID could be decoded"* — **survives the
recovery unchanged.** Recovering this library does not unblock the UUID question,
and a successor area must not be written as if it did.

## 6. `libSecureKeyBoxJava.dylib` is the white-box core, and it is *not* SAKE

Recovered, 6 502 032 B, **universal (x86_64 + arm64)**, exporting
`_JNI_OnLoad` / `_JNI_OnUnload` and **only 5 (x86_64) / 3 (arm64) exported
symbols** — the rest is reached through the JNI registration the on-load hook
performs, which is why the export table is nearly empty on a 6.5 MB file.

The `'sake|skb'` count of **124** is accurate as a *pattern* count but misleading
as a description: **all 124 are `skb`; `sake` occurs 0 times.** Composition:

```
_SKB_Callback_{AntiDebug,Jailbreak,Root}     — anti-tamper callbacks
_SKB_Get<64-hex>…                            — 12 mangled accessor symbols
SKB_DrbgSha / SKB_GetPublicKey / SKB_WrapData / SKB_CacheEngine
skb_cache_ / skb_key_flow_ / 15SkbJniException
```

`SKB_DrbgSha` is a **DRBG** and `SKB_GetPublicKey` a public-key accessor; the
`AntiDebug`/`Jailbreak`/`Root` callbacks are the tamper-response surface. What
this establishes is only that the white-box *engine* the wire-protocol record
called absent (§4, "not in these artefacts") is now present and is a real
cryptographic library with its own RNG and key handling. **It does not follow
that the white-box tables are recoverable**, and no claim is made that SKB is
broken — the position recorded in that §4 stands unchanged, including the
`not worth attacking, because it is unnecessary` verdict.

Note the asymmetry, which is worth a reader's attention: the SKB core is
**universal**, and the Medtronic BLE library is **x86_64-only**. The vendor
multi-arch'd the third-party cryptographic dependency and not their own
transport.

## 7. ⚠ The Apple Silicon defect is *not* "unrunnable regardless of Rosetta"

The recovery **confirms** two of the three parts of the correction circulated
with it, and **refutes the conclusion drawn from them**:

| claim | verdict |
|---|---|
| `libuploader.dylib` ships only at `DSS/lib/macos/x86_64/` | ✅ **true** — no arm64 directory is created by the installer; one slice in the file |
| `libSecureKeyBoxJava.dylib` is universal | ✅ **true** — x86_64 + arm64, measured per slice |
| "…therefore the uploader cannot run on Apple Silicon regardless of Rosetta/JRE" | ❌ **false as stated** |

Why the third does not follow. `uploader.NativeLoader` picks its path from the
**running JVM's** `os.arch`, not from the host's:

```java
String string3 = System.getProperty("os.arch").toLowerCase();
if (string3.matches("^(x86_64|amd64|ia32e|em64t|x64)$")) arch = "x86_64";
else if (string3.matches("^(arm64e?|aarch64)$"))              arch = "arm64";
String string3 = "lib/" + os + "/" + arch + "/" + string2;   // → lib/macos/x86_64/lib…dylib
```

A JVM running under Rosetta 2 is an **x86_64 process** and reports
`os.arch=x86_64`, so it resolves `lib/macos/x86_64/`, **which exists**. A
Rosetta-translated uploader would therefore load this dylib. What actually
happened on the install host is in the companion record and is a *different*
failure: `zsh: bad CPU type in executable: …/jre/bin/java` — the OS refusing to
translate because **Rosetta 2 was not installed** (`sysctl.proc_translated = 0`,
`oahd` not running). That is an environment gap, not an architecture mismatch in
the library.

**INFERRED, with its assumption stated:** that a translated JVM reports
`os.arch=x86_64` and can `dlopen` an x86_64-only dylib is standard Rosetta
behaviour, not something measured on this host (this is Linux; the library was
not executed). **The falsifiable test:** install Rosetta 2, run the bundled
`jre/bin/java` with the two jars on the classpath, and see whether
`BRILJNI` resolves a symbol. If it does, this record's reading is right; if it
fails with a load error, the "regardless of Rosetta" framing was right after all
and this section is the thing to correct.

**What the recovery *does* establish, and it is a stronger and permanent
statement than the environmental one:** there is **no arm64 build of the BLE
library at all**, so the uploader can never run on a *native* arm64 JVM. Rosetta
is a workaround for the missing JRE, and it would also paper over the missing
arm64 slice — but the vendor has no Apple-Silicon-native transport, on any
version of macOS, for as long as this packaging holds.

## 8. What this changes, and what it does not

**Closed by this pass**

- The `libuploader.dylib` blocker in the wire-protocol record §7 — the file is
  recovered, and its contents are now measured rather than assumed.
- `BRIL` as an unidentified token — it is a GAP/HCI scan state machine over
  CoreBluetooth, compiled from 17 named sources, with `StringDecryptor` and the
  HTTP layer *not* among them.
- The "one absent artefact" model of the remaining gap — the JAR's 1 370 natives
  are spread across at least three modules, of which this is one (378).

**Still blocked, and now blocked for a stated reason rather than a missing file**

1. **The HTTP layer** (`HttpClientCommunicator`, 67 natives) — not in this dylib,
   not in the JAR, location unknown.
2. **String decryption** (`StringDecryptor`, 443 natives) — same. This is what
   gates every device name, BLE UUID and user-visible literal in the JAR, so the
   device-vocabulary question is **exactly as open as it was**.
3. **A mitmproxy capture** — unchanged as the single highest-value artefact; it
   would settle URL paths, headers, `Content-Type`, the enum `.name()` strings
   and TLS pinning in one shot, and no amount of further static work substitutes
   for it.
4. **The SKB white-box tables** — present as an engine, still white-boxed.

**Not claimed**

- No claim that `uploader.Loader.l(int)` is a decryptor — INFERRED, §4.
- No claim that the uploader runs or does not run under Rosetta — INFERRED and
  falsifiable, §7.
- No claim that SKB is broken, or that its tables are recoverable.
- No Medtronic BLE UUID, model code, alarm code or device name.
- No claim about what `PCL F3` means.
