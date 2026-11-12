# MiniMed Mobile 3.3.0 — the packer blocks most of it, but the graph vocabulary leaks (2026-11-12)

**Evidence class: OBSERVED** unless marked. Companion to
`2026-11-12-minimed-mobile-app/`, and it **corrects that record's optimism about
what is statically readable.**

**Requests issued by this pass: 0.** Static analysis of the extracted artefact
only. **Cap: 0 of a 0 cap — no request was made.** **Delay:** the standing rule is
≥2 s between requests to the same host; none was issued, so no spacing applies
and none is claimed. **Methods:** no `GET`, `OPTIONS` or `POST` was sent to any
host.

---

## 1. ⚠ Correction: the "readable" layers are mostly `native`

The parent record described `com.medtronic.securerepositories` as a readable
network layer whose shape could be documented. **That was too generous, and the
measurement is not close.**

```
$ find com/medtronic/securerepositories -name '*.java' | wc -l
33
$ grep -rl 'native ' --include=*.java com/medtronic/securerepositories | wc -l
24
```

**24 of 33 classes contain `native` methods**, and every one of the four
substantive classes I quoted — `NetworkSecureRepositoryImpl`,
`WebSocketCommunicator`, `NonceJob`, `AJob` — carries the packer's
`System.loadLibrary("vdlbwnyfem")` + `Loader.l(<constant>)` idiom. What is visible
is the **declaration**: method signatures, field names, constructor parameters.
What is **not** visible is any control flow, any string, any URL, and any message
body.

So the accurate statement is: **the `securerepositories` protocol is knowable as
an interface, not as an implementation.** A reader can learn that a WebSocket is
opened with a caller-supplied `Certificate` and that four message types exist;
they cannot learn what is sent over it.

## 2. The packer: two DCP engines and a 2.3 MB encrypted payload

| artefact | bytes | note |
|---|---|---|
| `libfblyyzyocs.so` | 3,675,584 | ELF aarch64, `.text` 2,877,524 B |
| `libvdlbwnyfem.so` | 1,297,336 | ELF aarch64 |
| `assets/fblyyzyocs.szip` | **2,356,173** | **entropy exactly 8.000**, 147,260/147,260 distinct 16-byte blocks |
| `assets/vdlbwnyfem.szip` | **12** | stub, not a payload |
| `assets/fblyyzyocs/0.odex` | **13** | stub, not code |

Each engine exports **exactly one** JNI symbol:

```
Java_fblyyzyocs_Loader_l
Java_vdlbwnyfem_Loader_l
```

and `libfblyyzyocs.so` imports `memfd_create`, `mmap` and `mprotect` — the
signature of decrypt-in-memory-then-load-from-an-anonymous-fd, with no plaintext
ever touching the filesystem.

The Java side is thin and identical in both packages:

```java
public final class Loader {
    public AFD afd;
    public AIS ais;
    public static native synchronized void l(int i6);
}
```

`AFD extends AssetFileDescriptor` and `AIS extends InputStream`, both with native
methods — these are the bridges that stream the packed asset.

**Call-site census** (`grep -rl 'fblyyzyocs.Loader'` over the decompiled tree):

| packer | classes calling `Loader` |
|---|---|
| `fblyyzyocs` | **371** |
| `vdlbwnyfem` | **25** |

The `int` argument at each call site is a per-class constant — `df/m2` passes
`-29403029`, `df/y2` `-1696404064`, `df/r2` `-1374854463`. That is an **address
constant**, not a class id: the values are dense/small hundreds of millions in
magnitude, which is a 32-bit obfuscated-index space rather than a table offset.

**Why the two payloads differ so much:** a 12-byte `szip` next to a 2.3 MB one
means the two engines are not symmetric. `fblyyzyocs` carries a real encrypted
payload; `vdlbwnyfem` most likely decrypts string/enum data that is already in the
APK elsewhere, or expects a payload the installer did not ship for this build.
**INFERRED** — only `fblyyzyocs` is evidenced as carrying bulk data.

## 3. What *is* readable: the graph vocabulary, and it is a wire vocabulary

`com.medtronic.graph` is plain Java with no packer dependency. Its meta-model
enums are deserialised by name — each has a `fromValue(String)` that looks the wire
string up in a `HashMap`, and `toString()` that returns it. **These are field
values on the wire**, not UI labels.

**`AbsentFeature`** — thirteen series names. The class name means "which feature is
absent from this graph payload", so these are the series identifiers the client
expects:

```
selectedPoint  sgs  events  microBoluses  autoCorrectionBoluses
basalRates  alertLimits  autoSuspends  autoMode  timeChanges
timeRange  maxAutoBasalRate  maxBolusAmount
```

**`BasalRateMetaDto$BasalType`** — `Regular`, `Temporary`, `Auto`.

**`EventMetaDto$Type`** — `meal`, `bg`, `timechange`, `bolus`.

**Why this matters more than it looks.** `sgs` is the Nightscout/CGM field name
for a sensor glucose value, and it appears here as a **wire string in Medtronic's
own production app**. The corpus has recorded `sgs` as a token with an unproven
carrier; this is a named, readable, shipped carrier for it. The same goes for
`autoCorrectionBoluses`, `microBoluses` and `autoSuspends`: those are the
SmartGuard behaviours the bridge is trying to publish, and here they are as
explicit series names.

**Caveat, stated because it limits the claim:** these are the **graph** model's
field names. The graph is populated from data the app already holds; nothing here
shows that the same names cross the network. Whether the upload payload reuses
them is **not established**. What *is* established is that Medtronic's client uses
`sgs`, `microBoluses`, `autoCorrectionBoluses`, `basalRates`, `autoSuspends` and
`autoMode` as its own identifiers for exactly the concepts the bridge models.

## 4. Two live subsystems are fully readable, and neither is pump upload

**`com.medtronic.applogs`** (48 classes) is a complete, un-packed uploader: RSA-OAEP
wrapped AES, 500 records per chunk, with `DispatchingClient` injected at runtime.
**`com.medtronic.teneo`** (107 classes) is the FOTA/enrolment PKI plane with eight
routes and a full request/response model set. Both are documented in
`2026-11-12-minimed-mobile-app/APP-UPLOAD-SURFACE.md`.

Neither carries pump therapy data.

## 5. What this changes

The mobile path is **not recoverable by static analysis alone.** The evidence:

1. The upload orchestrator — `minimed/bl/**`, `minimed/data/**`,
   `minimed/ngpsdk/**`, and `ui/menu/fb` (`SyncToCareLinkPresenter`) — is
   **referenced but not defined** in the DEX (160 classes).
2. The layer that would name the endpoints is **24-of-33 native**, with its
   implementation in a 3.7 MB packer.
3. The only bulk payload is **2.36 MB at entropy 8.000** with no disk-side key
   material located yet.

So a successor must either **defeat the DCP packer** or **run the app**. Reading
Java will not get there.

## 6. The one thing static analysis still owes

`libfblyyzyocs.so`'s `.data` is **184,152 B at entropy 7.316** with 5,987
high-entropy 32-byte windows — far above normal initialised data (entropy ~4–5),
which is where a key or an encrypted lookup table would sit. That is the next lead,
and it is a bounded disassembly job: find what `Loader_l` reads out of `.data`.

## 7. Not claimed

- Any endpoint, host or message body from the packed layer.
- That `vdlbwnyfem.szip`'s 12 bytes are a stub rather than a truncated asset —
  it may be a manifest for a payload not shipped in this build. **INFERRED.**
- That the graph field names cross the network.
- Any decryption of `fblyyzyocs.szip`.
