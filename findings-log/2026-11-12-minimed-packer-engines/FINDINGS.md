# MiniMed Mobile 3.3.0 — the packer: two DCP engines, the encrypted payload, and the `Loader.l` census (2026-11-12)

**Evidence class: OBSERVED** — byte-level static analysis of the base APK and its
two protector libraries, all local. Nothing here is inferred from a class name or
a string hit alone; every count below carries the command that produced it and
its counting rule, because AGENTS.md §6 item 7 dates from a count generalised
from a subset.

Companion records: `findings-log/2026-11-12-minimed-mobile-app/` (the artefact,
the SAKE layer and the upload-surface question) and
`findings-log/2026-11-12-uploader-native-libraries/` (the desktop dylibs, and the
`Loader.l(int)` dispatcher *hypothesis* this record tests — without resolving
it — on the Android side).

<!-- cap-counts: ledger-rows -->
**Requests issued by this pass: 0.** All work is local file analysis — `zipfile`,
`grep`, `strings`, and LIEF 1.0 in a local virtualenv. **Cap: 0 of a 0 cap — no
request was made. Delay:** none applies: the standing ≥2 s rule was not engaged,
because nothing was requested, and no spacing is claimed. **Methods:** no `GET`,
no `OPTIONS` and no `POST` was sent to any host. The artefact was already on
disk; no download was repeated and no credential was used.

**Tooling.** `python3` `zipfile` + `Counter` (Shannon entropy, per-byte), `grep
-rl`/`grep -rho` with `LC_ALL=C` (byte collation, so `sort`/`comm` agree),
`strings -a`, and LIEF `1.0.0-d05b3499b` from the analysis virtualenv for the ELF
symbol and section tables. Paths below are relative to the local analysis
directory and are written as `<workdir>`; no machine path is reproduced.

**Artefact identity.** `base.apk`, **21,294,359 B**, sha256 prefix
`f6ac266116bb4965`; package `com.medtronic.diabetes.minimedmobile.eu` 3.3.0
(1091), the same APK the companion record describes. Extracted with
`jadx-1.5.3-all.jar`; the decompiled tree holds **7,488** `.java` files.

---

## 1. ⚠ First, a correction: the `securerepositories` layer is *not* statically readable

The companion record — `APP-UPLOAD-SURFACE.md` §2.1, headed **"The
`securerepositories` layer is native, not Java"** — introduces
`NetworkSecureRepositoryImpl` as a class whose behaviour is JNI and then goes on
to describe the layer's transport, its message model and its certificate
handling as if those were read from Java bodies. It describes
`WebSocketCommunicator`'s methods (`connect`, `closeConnection`, `addListener`,
`removeListener`, `sendStringMessage`, `sendByteStringMessage`) without saying
that **every one of them is a `native` declaration with no body**. Same for
`Message` (`equals`, `hashCode`, `toString`, `getData`, `getType`) and
`MessageType` (`valueOf`, `values`, `getType`).

Measured over the package:

```
$ grep -rl 'native ' --include='*.java' \
    <workdir>/out/sources/com/medtronic/securerepositories | wc -l
24
$ find <workdir>/out/sources/com/medtronic/securerepositories -name '*.java' | wc -l
33
$ grep -rhoE '\bnative\b' --include='*.java' \
    <workdir>/out/sources/com/medtronic/securerepositories | wc -l
159
$ comm -12 <(grep -rl 'native ' --include='*.java' … | sort) \
           <(grep -rlE '(fblyyzyocs|vdlbwnyfem)\.Loader' … | sort) | wc -l
24
```

**Counting rule** (stated before the number): one unit is one `.java` file under
`com/medtronic/securerepositories/`; "carries native methods" means the literal
token `native ` occurs in it, verified three ways — the bare token, the word
boundary `\bnative\b`, and `native ` followed by a type or comment — all three
return **24**, so the figure does not depend on one regex's quirks. The
intersection with files that reference a packer `Loader` is also **24**, i.e.
**every** native-carrying file in the package is a packed class. The 9 files
without natives are the interfaces, the listener/error DTOs, `R`,
`SecureRepositoryLogger`, `StorageSecureRepository` and `NetworkRepositoryFactory`.

**The plain statement: the earlier characterisation was too generous.** This is
not a layer where a native shim sits behind readable Java. **24 of 33 files —
159 native declarations — have their bodies in the packer**, and 18 of those 24
route their own construction through a native call codec (`$vdlbwnyfem$B…(…)`
returning an `Object[]`, which `$vdlbwnyfem$E…(this, arr)` then applies to the
instance) — so for those classes even *field initialisation* is not in Java.
What survives is the *shape*: the interfaces, the field names, the
`@SerializedName` annotations, the `Certificate` constructor parameter. What does
not survive is any statement of what the code does. Any future sentence about
this layer must be worded as *"the signature says"*, never as *"the code does"*.

The **9** files with no native token are the two interfaces
(`NetworkSecureRepository`, `StorageSecureRepository`), the two listener DTOs
(`RepositoryListener`, `WebSocketEventListener`), the two job-result DTOs
(`JobListenerError`, `JobListenerSuccess`), `R`, `SecureRepositoryLogger`, and
`NetworkRepositoryFactory` — a 14-line final class whose entire content is a
static initialiser (`System.loadLibrary("vdlbwnyfem"); Loader.l(1620344445);`)
and a private constructor. So the companion record's point that
`createNetworkSecureRepository()` has no caller in the DEX holds for **both**
factories and by a wider margin than it states: `NetworkRepositoryFactory` does
not even declare the method, and `SecureRepositoryFactory` declares it `native`
at `:36` and constructs nothing in Java either.

**One claim in that record is provably wrong and is corrected here** (in this
section, because it belongs with the libraries): its §6 states `libfblyyzyocs.so`
"is 95 % `.data` (3.49 MB of 3.68 MB at 7.66 bits/byte)". Measured, it is not:

| reading | size | % of file | entropy |
|---|---:|---:|---:|
| `.text` (the largest section) | 2,877,524 | 78.3 % | 7.063 |
| `.data` | 184,152 | **5.0 %** | 7.316 |
| whole file | 3,675,584 | 100 % | **6.950** |

No section is 3.49 MB, no section reaches 7.66 bits/byte (the highest is `.data`
at 7.316), and the whole-file entropy is 6.950 — a *normal* unstripped C++
library. So both halves of that sentence are wrong, and the conclusion drawn
from it — "a second copy of encrypted payload inside the library" — is
**unsupported**. The payload copy that *is* measured is `assets/fblyyzyocs.szip`
(§3, entropy 7.99992). This matters beyond bookkeeping: the earlier reading made
the engine look like a random blob and therefore un-analysable, when in fact
78 % of it is ordinary machine code.

## 2. Two DCP engines, one JNI export each

| library | bytes | sha256 (16) | arch | exported syms | `Java_` exports |
|---|---:|---|---|---:|---|
| `libfblyyzyocs.so` | **3,675,584** | `53650cbd212d6116` | AArch64 | 298 | **1** — `Java_fblyyzyocs_Loader_l` |
| `libvdlbwnyfem.so` | **1,297,336** | `5d3c7b9557a779d9` | AArch64 | 301 | **1** — `Java_vdlbwnyfem_Loader_l` |

Both are `ELF 64-bit` AArch64 shared objects, and both are **unstripped**: 298 and
301 exported symbols respectively, almost all C++ RTTI/vtable/`std::` symbols
from `libc++`. That matters — the export table is not empty on a multi-megabyte
library, which means the *engine* is ordinary C++ and only its *asset format* is
proprietary. It is a genuinely tractable static target.

The protector is named in the symbol data, identically in both files: 11 `__dcp`
occurrences each, and the same nine asset classes —

```
DCPAsset  DCPBlobAsset  DCPBufferAsset  DCPConstAsset  DCPDeflatedAsset
DCPObfuscatedAsset  DCPException
DCPAndroidAssetImpl<…>  DCPAndroidAssetNakedImpl<…>
```

Neither library contains a single Medtronic-shaped string:

```
$ strings -a libs/libfblyyzyocs.so  | grep -icE 'medtronic|minimed|carelink|sake'   -> 0
$ strings -a libs/libvdlbwnyfem.so  | grep -icE 'medtronic|minimed|carelink|sake'   -> 0
```

So the JNI binding is exactly one entry point per library, named for the package,
and **the class/asset work happens entirely inside the engine** — consistent with
the `Loader` class in each package being a 9-line stub holding two fields
(`AFD afd`, `AIS ais`) and one `public static native synchronized void l(int)`.

**Naming trap, recorded because it cost a command.** The on-disk library is
`libfblyyzyocs.so`, whose stem (`lib` and `.so` removed) is **byte-identical to
the Java package** `fblyyzyocs` and to the asset directory `assets/fblyyzyocs/` —
all three are `f-b-l-y-y-z-y-o-c-s`. The spelling that appears in some notes,
`libfblyyocs.so`, drops the `zy` and **names no file in the tree**:

```
$ find <workdir> -name 'libfblyyocs.so'   -> nothing
$ find <workdir> -name 'lib*ocs.so'       -> libs/libfblyyzyocs.so
                                             native/libfblyyzyocs.so
```

A `find` on the short spelling returns empty and reads exactly as "the library is
absent" — the AGENTS.md §6 item 6 shape, a failed lookup read as a negative
result. Recorded here so the next pass does not re-derive it as a missing
artefact.

## 3. The payloads: one 2.36 MB ciphertext, two stubs

Read straight out of `base.apk` with `zipfile`, entropy over the whole byte
population (Shannon, base-2, per byte):

| entry | bytes | entropy (bits/B) | distinct 16-B blocks | leading bytes |
|---|---:|---:|---:|---|
| `assets/fblyyzyocs.szip` | **2,356,173** | **7.99992** | 147,260 of 147,260 | `212f23a4490f81cb` |
| `assets/vdlbwnyfem.szip` | **12** | 3.585 | — | `c01ea7c4d3f5e4da` |
| `assets/fblyyzyocs/0.odex` | **13** | 3.547 | — | `4ca1012e0197ba6d` |

The 2.36 MB blob is at entropy 7.99992, which rounds to **8.000** — full byte
entropy, and every one of the 147,260 aligned 16-byte blocks is distinct, so
there is no ECB-mode repetition to exploit and no recognisable container magic at
offset 0. It is ciphertext or a stream-cipher output; it is not a compressed DEX
(`dex`/`PK`/zstd/lz4/gzip all absent at offset 0).

The other two are **stubs**: 12 and 13 bytes, entropy ~3.5, downstream of nothing
— the same lengths and the same leading bytes the companion record tabulates in
its §2.3 decoy list, where the 13-byte `.cer`, 13-byte `msso_config.json` and
13-byte `analyticsMappings.json` also sit. **Two of the packer's three named
payload slots are placeholders.** Only the `fblyyzyocs` engine actually ships an
encrypted asset; the `vdlbwnyfem` slot holds a 12-byte marker, so whatever that
engine decrypts it either carries internally or fetches — it is not in `assets/`.

**Lengths reconcile with the caller, which is the useful part:** 2,356,173 B is
plausible for the ~160 missing `com/medtronic` classes the companion record
counts as referenced-but-not-defined (a DEX of that order is a few MB
uncompressed, and ciphertext over a compressed stream lands here). That is a
**consistency check, not a proof** — the payload could equally be resources plus
code, and nothing in this pass decrypts a byte of it.

## 4. In-memory decryption: `memfd_create` in one engine, not the other

Undefined-symbol import lists, read from the ELF symbol table with LIEF (63 and
62 undefined symbols respectively — the full list is short enough to read by eye,
which is why the negatives below are trustworthy):

| import | `libfblyyzyocs.so` | `libvdlbwnyfem.so` |
|---|:--:|:--:|
| `memfd_create` | **yes** | **no** |
| `mmap` | yes | yes |
| `mprotect` | yes | yes |
| `munmap` | yes | yes |
| `dl_iterate_phdr` | yes | yes |
| `syscall` | yes | yes |
| `open` | no (`__open_2`, `dup`, `lseek`) | **yes**, plus `unlink`, `atoi` |
| `fexecve` | no | no |

**The mechanism is measured, and it is a two-step:** a file descriptor is created
in memory (`memfd_create`), the decrypted image is mapped over it (`mmap`), and
the mapping is then made executable (`mprotect`) — with `dl_iterate_phdr` present
to walk the loaded-object list and `syscall` present for the direct-numbered
calls a protector uses to avoid a libc wrapper it cannot rely on. That is the
standard in-memory code-loading shape, and requiring no `fexecve` is consistent
with the mapped image being parsed as a DEX/ELF by the runtime rather than
executed as a process.

**This corrects a claim carried into this pass:** it is *not* true that **each**
engine imports `memfd_create`. `libfblyyzyocs.so` does; `libvdlbwnyfem.so` does
not — it uses ordinary `open` + `unlink` (create-then-`unlink`, the classic
anonymous-file idiom on Android), and it holds the only `atoi` in either file,
which points at argument/flag parsing on that path. The two engines are therefore
**not the same build with different keys**: they implement different
asset-delivery strategies. The honest statement is *both decrypt in memory and
map executable pages — one via `memfd_create`, one via an unlinked file* — and the
weaker "both use `memfd_create`" is refuted by the symbol table.

Note what is **absent from both**: no crypto library import at all — no
`libcrypto`, no `EVP_*`, no `AES_*`, no `SSL_*` in either undefined-symbol list.
The cipher is **statically compiled into the engine**, so there is no
key-schedule symbol to hook from a library boundary and the algorithm must be
recovered from code. The two differ in logging, too: `libvdlbwnyfem.so` imports
`__android_log_print`, while `libfblyyzyocs.so` does not and uses
`syslog`/`openlog` instead — a small but real sign that these are two builds from
different toolchain settings, not one library compiled twice.

## 5. `Loader.l(int)`: 371 and 25 classes, 429 call sites, 429 distinct constants

```
$ cd <workdir>/out
$ grep -rl 'fblyyzyocs\.Loader' sources | wc -l     -> 371
$ grep -rl 'vdlbwnyfem\.Loader' sources | wc -l     ->  25
$ comm -12 <(grep -rl 'fblyyzyocs\.Loader' sources | sort) \
           <(grep -rl 'vdlbwnyfem\.Loader' sources | sort) | wc -l   -> 0
$ grep -rho 'Loader\.l([-0-9]*)' sources | wc -l     -> 429
$ grep -rho 'Loader\.l([-0-9]*)' sources | sort -u | wc -l  -> 429
```

**Counting rule:** one unit is one `.java` file that contains the literal
`<package>.Loader` import/reference; the two populations are disjoint (the
intersection is **0** — no class calls both engines), and together they are
**396**, which is exactly the population of files containing a `Loader.l(` call.
So every `Loader` reference in the tree is a call site, and the split between the
two engines is **371 : 25**.

**The constant is per class, not per file, and that is measured, not assumed:**
429 call sites across 396 files, **429 distinct integer arguments, zero
collisions anywhere in the tree**. 21 files hold more than one distinct value,
and inspecting them shows why — the extra calls live in nested and anonymous
classes, each with its own static initialiser:

```java
// internal/sequencejobs/network/SJob.java — three initialisers, three constants
class AnonymousClass1 extends TimerTask {
    static { System.loadLibrary("vdlbwnyfem"); Loader.l(1022940273); }
    public native void run();
}
static /* synthetic */ class AnonymousClass2 {
    static { System.loadLibrary("vdlbwnyfem"); Loader.l(1898213561); $vdlbwnyfem$COI(); }
}
static { System.loadLibrary("vdlbwnyfem"); Loader.l(-430685118); $vdlbwnyfem$COI(); }
```

**What the uniqueness does and does not prove.** It rules out an index into a
small set — a sequential `0, 1, 2 …` counter, a per-file index (which would give
**396** distinct values, not 429), or a hash of the class *name* over a
low-entropy bucket — because all three would collide within 429 sites. It does
**not** rule out a random or per-build identifier: in a 32-bit space, 429 draws
are expected to collide with probability ~2×10⁻⁵, so zero collisions is the
*ordinary* outcome for a random key and carries almost no information. **The
positive claim is therefore narrower than "a table key": each initialiser is
passed a distinct, per-class value, sized and shaped like an identifier rather
than an index, and the value is not derivable from the class name or its order.**
Whether the engine treats it as a decryption key, a table slot, or a CRC seed is
inside the engine and is not measured here (§7).

**Two mechanical details that constrain the recovery:** the initialiser always
calls `System.loadLibrary(<engine>)` *immediately before* `Loader.l(<int>)` — the
engine is loaded by the same class that needs its entry point, so there is no
global load order to reconstruct. And `Loader.l` is declared
`native synchronized`, so concurrent initialisers serialise inside the engine
rather than racing in Java. Both are read off the declarations, not inferred.

## 6. What this means, and it is a firm negative

The mobile upload path is **not recoverable by static analysis of this APK.** The
chain of reasoning is short and each link is measured above:

1. The upload orchestration lives in ~160 `com/medtronic` classes that are
   referenced by the DEX and **not defined** in it (companion record, §4), so the
   class bodies are absent from the shipped plaintext.
2. The classes that *are* present in the packed layers are present only as
   initialisers, native declarations and field names — **24 of 33**
   `securerepositories` files carry native bodies (§1), including every method of
   `WebSocketCommunicator`, `Message`, `MessageType` and
   `NetworkSecureRepositoryImpl`. So even the retained classes state no behaviour.
3. Recovering either requires defeating the engine: a 2.36 MB ciphertext at
   entropy 8.000 (§3), a cipher statically linked with no library-boundary symbol
   (§4), and a per-class identifier supplied to the single JNI entry point —
   429 distinct values, one per class initialiser (§5) — whose meaning is inside
   the same code that consumes it.

**Therefore: the packer must be defeated, or the app must be run.** There is no
third route that consists of reading more files. Concretely, the two options are

- **run it** — hook the single JNI entry point. `Loader.l` is declared
  `native synchronized`, one export per engine, symbol names known
  (`Java_fblyyzyocs_Loader_l`, `Java_vdlbwnyfem_Loader_l`), and both are
  **unstripped**, so a Frida `Interceptor.attach` on the export needs no address
  arithmetic. Hooking it yields the plaintext class bytes it installs, and the
  429-constant census above gives a de-duplication key for the dump.
  This requires a rooted device or an emulator;
- **defeat the engine statically** — decompile `libvdlbwnyfem.so` first, not
  `libfblyyzyocs.so`: 1.30 MB against 3.68 MB, 62 imports, and its payload slot
  is empty (§3), so its assets must be internal or fetched and its logic is not
  sharing space with a 2.36 MB blob. This is the tractable static target and it is
  the same problem as the desktop uploader's `StringDecryptor`.

**What this does not change:** the companion record's §7 conclusion stands — the
mobile app does not use the desktop uploader's `/api/uploader/v1/*` surface, and
the `securerepositories` WebSocket layer's demonstrated DEX consumer is still the
local-database key store, not a data upload. This record makes that negative
*stronger*, not weaker: the reason the upload leg cannot be named is no longer
"the strings are encrypted" but "the classes are absent and the classes that
remain have native bodies". **Recovering an upload endpoint from this artefact
requires executing code, full stop.**

## 7. Not claimed

- **No byte of the 2.36 MB payload was decrypted.** Its *size* and *entropy* are
  measured; its *contents* are unknown, including whether it holds the 160
  missing classes, resources, or both.
- **No claim about the cipher or key schedule.** The absence of a crypto import
  proves the cipher is statically linked, not which cipher it is.
- **No claim that `Loader.l(int)` decrypts anything.** What is measured is that
  it is the only JNI export, that it is called once per class initialiser with a
  value distinct across 429 sites, and that the engine maps executable pages. The
  step from "per-class identifier" to "decrypts that class" is **INFERRED**, and
  its assumption is that a loader is handed a key for the thing it loads rather
  than a global table — which a table keyed by class would satisfy equally.
- **No claim that `libvdlbwnyfem.so` carries its payload internally.** Its
  `assets/` slot is a 12-byte stub; where its data comes from is open.
- **No claim of a shared codebase between the two engines.** Same protector
  family (`__dcp`, identical asset class names), *different* delivery mechanism
  (§4) — that is the measured position.
- **No Medtronic hostname, BLE UUID, model code or alarm code.** As before, and
  for the reason above rather than a weaker one.
- **Nothing about `assets/msso_config.json` or the `.cer` beyond the byte
  counts already recorded** — both are 12/13-byte placeholders, not configs.

## 8. Corrections carried forward

Two, both stated in full above rather than left implicit:

1. **`APP-UPLOAD-SURFACE.md` §2.1's "native, not Java" heading understates its
   own finding, and the prose under it reads as if Java bodies had been
   inspected.** They had not: 24 of 33 files, 159 native declarations, every
   `WebSocketCommunicator` method bodiless. The earlier "readable" framing of
   this layer was too generous (§1).
2. **That record's §6 `.data` figure is wrong** — 184,152 B / 5.0 %, not 3.49 MB
   / 95 % — and the "second copy of encrypted payload inside the library" reading
   built on it is unsupported (§1). The payload copy that exists is in `assets/`.

Both are corrected here rather than edited in place: `findings-log/` is
append-only (AGENTS.md §3), and the retraction history is the evidence.

