# libuploader.dylib — StringDecryptor recovery attempt

**Verdict: FAILED to recover plaintext, but the failure is fully diagnosed and the blocker is identified.**

I did not recover any decrypted device names, BLE UUIDs, or HTTP route/header strings from
`libuploader.dylib`. Below is a complete, falsifiable account of what I established, including
the disassembly of the actual decode routine and the precise reason static extraction cannot work.

---

## 1. The premise in the brief is wrong in one important way

The brief states: *"uploader.jar's HttpClientCommunicator has 67 `native` methods with no Code
attribute. Their bodies are in libuploader.dylib."*

**OBSERVED — this is not the case.** `libuploader.dylib` exports exactly 500 symbols:

| Category | Count |
|---|---|
| `_Java_com_medtronic_minimed_bril_BRILJNI_*` | 287 |
| `_Java_com_medtronic_minimed_gatts_GattStreamJNI_*` | 56 |
| `_Java_com_medtronic_minimed_sake_SakeJNI_*` | 34 |
| `_Java_uploader_Loader_l` | 1 |
| C++ / boost::asio mangled (`__Z*`) | 121 |
| `_boost_asio_detail_posix_thread_function` | 1 |

Command: `lief` export walk over `nativelibs/libuploader.dylib` (script `02_symbols.py`,
output `exports.txt`).

There is **no `_Java_com_medtronic_diabetes_solar_*` export of any kind**, and **no `JNI_OnLoad`
and no `RegisterNatives` string anywhere in the file** (all three are `0` occurrences under
`grep -a -c`). The same holds for `libSecureKeyBoxJava.dylib` — its only JNI exports are
`_JNI_OnLoad` and `_JNI_OnUnload` (5 exports x86_64, 3 arm64).

I also scanned `__DATA_CONST.__const` and `__DATA.__data` for `JNINativeMethod` triples
(`{const char* name, const char* sig, void* fn}` with name/sig pointing into `__cstring` and fn
into `__text`, 8-byte aligned): **0 hits** in libuploader and **0 hits** in libSecureKeyBoxJava
(script `10_jninatives.py` / `12_skb_natives.py`).

**INFERRED:** the 67 `HttpClientCommunicator` natives plus the 442 `StringDecryptor` natives are
not in either provided dylib. They are registered at runtime by a library that was **not in the
artefact set I was given** — most likely the DCP/zShield-protected Java-to-native bridge that the
`uploader.policy` file references, or a protected section that the installer writes but that is
absent from `mac-copy/`. `CareLinkUploader-install.txt` (OBSERVED) unpacks exactly 57 `.dylib`
files and the *only* app-owned one is `lib/macos/x86_64/libuploader.dylib`; the rest are the
bundled JRE, JavaFX, and four device drivers (`libusb4java`, `libSecureKeyBoxJava`, `libhidapi`,
plus VerioVue/FTDI USB drivers).

---

## 2. What StringDecryptor actually is (OBSERVED)

`com/medtronic/diabetes/solar/utils/StringDecryptor.class` (12,624 B) decompiles to a class with:

- `public static native String decryptString(String)` — 1 method
- `decryptString000` … `decryptString19B` (int) — 412 methods
- `decryptString10` … `decryptString19` (int,int) — 10 methods
- `decryptString1` (int,int,int) — 1 method
- `decryptString` (int,int,int,int) — 1 method
- `$uploader$COI()` — DCP integrity hook

Total 442 native methods. **The single-argument overload is not the one used in practice.**
Across 1,086 decompiled source files there are **852 `decryptString("…")` call sites**, and the
argument length histogram is (OBSERVED, `grep` over `decompiled/`):

| arg length | count |
|---|---|
| 1 char (`\uXXXX`) | 789 |
| 1 char (literal, e.g. `"["`, `"+"`) | 62 |
| 2 chars | 1 |

So the actual call convention is **`decryptString("\u1938")`** — a single 16-bit value that is a
**table index**, not a ciphertext blob. Confirmation that these are indices rather than data:

- The values are **sequential within semantic groups**. `SecurityCheckCode`'s 8 enum constants,
  declared in source order, use `\u1938, \u1939, … \u193f` — strictly consecutive.
  `AbstractAuthenticator`'s 5 map keys use `\u11e0, \u11e1, \u11e2, \u11e3, \u11e4` — consecutive.
- Range: **0x0001 … 0x199B (6555)** across 687 distinct values (script `13_idxrange.py`).
  Only 10.5% of the range is referenced.
- The `decryptStringNNN` / `decryptString(int…)` overloads are **never called from any Java
  source** (`grep` for `decryptString\d{3}\s*\(` over all 5,368 Procyon sources → 0 matches).

**This is the whiteCryption SecureKeyBox string-protection scheme**: literals are stripped at
build time, replaced by a 16-bit id, and the plaintext lives in an encrypted/lookup table inside
the native protector. It is not AES-over-blobs; there is no per-string ciphertext in the jar to
decrypt.

---

## 3. The decode routine, found and disassembled (OBSERVED)

`_Java_uploader_Loader_l` at **0x780d30** is the only non-BRIL JNI export, and its export range
is enormous: the next export is at 0x83bdc6, so **the "function" spans 766,102 bytes (748 KB)**.
That is not one function — it is the protected region, with the exported symbol as its entry
stub.

**Entry stub (0x780d30–0x780d72, 24 instructions, verbatim disassembly):**

```
push rbp; mov rbp,rsp; push r15/r14/r13/r12/rbx; sub rsp,0x28
mov qword [rbp-0x50], rdi
mov dword [rbp-0x3c], 0x74e0e1f8
mov dword [rbp-0x48], 0
mov eax, [rbp-0x48]
mov esi, [rip+0xc5834]
xor esi, 0xb
cmp esi, 0xd
jne 0x780d73          <-- integrity gate: if the check passes it just returns
... pop rbp; ret
0x780d73: mov ebx,0xf089e009 ; mov r8d,0x547483c6 ; mov r9d,0x6facf908
          lea r15,[rip+0x2a9] ; jmp 0x780da5
```

`0x780da5` is a **jump-table dispatcher**:

```
0x780da5: mov eax,[rip+0xc57e5]
0x780dab: add eax,esi
0x780dad: cmp eax,0xc
0x780db0: ja  0x780da0
0x780db2: movsxd rax,[r15+rax*4]
0x780db6: add rax,r15
0x780db9: jmp rax
```

The state variable `esi` is recomputed in almost every basic block by pairs of instructions of
the form `imul eax, r14d, 0x<prime>; shr eax, 0x11` (a constant-folded predicate) followed by
`and esi, 0xf` — i.e. the next state index is derived from arithmetic on opaque constants rather
than being a literal. This is textbook obfuscator control-flow flattening (OLLVM-lineage), and it
is what consumed the 748 KB.

**The actual string decoder is a separate, clean routine at 0x7af6b0.** It is not obfuscated.
Verbatim (first block):

```
0x7af6b0: push rbp ; mov rbp,rsp
0x7af6b4: mov eax, edi           ; arg1 = state/id
0x7af6b6: lea rdi,[rip+0x9f023]  ; -> key table, resolved base = 0x84e6e0
0x7af6bd: movzx r8d, byte [rsi]  ; src byte 0
0x7af6c1: movzx r9d, byte [rdx]  ; second src byte
0x7af6c5: shl r9, 8
0x7af6c9: or  r9, r8
0x7af6cc: movzx r10d, byte [rax+rdi]   ; KEY[id]
0x7af6d1: shl r10, 0xb               ; << 11
0x7af6d5: xor r10, r9
0x7af6d8: lea r8,[rip+0x60edb1]      ; -> substitution table, base 0xdbe490
0x7af6df: movzx r9d, byte [r8+r10]   ; SUB[(KEY[id]<<11) ^ src]
0x7af6e4: mov r10d, r9d
0x7af6e7: and r10b, 7
0x7af6eb: mov byte [rcx], r10b       ; dst byte = low 3 bits
0x7af6ee: and r9b, 0xf8              ; top 5 bits become feedback
0x7af6f2: xor r9b, byte [rsi+1]      ;   ... chained into next byte
```

It repeats this identically for offsets +1 … +5, so it is a **6-byte-state, byte-chained table
substitution cipher** — a small white-box cipher, feeding 5 bits of the previous output into the
next lookup.

There is a second, parallel decoder at **0x7af900** with the same shape but reading **u16**
entries at `[rax + rcx*2 + 0x8c000]`, `+0x4a000`, `+0x3a000`, `+0x5c000`, etc., and generic
loop versions at **0x7af3a0** and **0x7af430** (which loop `n` bytes with the same
`(table[idx]<<11) ^ (b0 | b1<<8)` construction).

**No AES, no XOR-key, no libSecureKeyBoxJava call is involved.** libuploader imports *no*
CommonCrypto or Security symbols at all (`_CCCrypt*`, `_SecKey*`, `_CCHmac*` → 0 hits). Its only
crypto-adjacent import is `_dlsym`.

---

## 4. Why the tables cannot be read statically (the blocker)

Segment layout (OBSERVED, `lief`):

```
__TEXT        va 0x000000-0xa88000   file_size 0xa88000
__DATA_CONST  va 0xa88000-0xa90000   file_size 0x8000
__DATA        va 0xa90000-0xe70000   file_size 0x60000   <-- only 384 KB of 3.9 MB is on disk
__LINKEDIT    va 0xe70000-0xea4000   file_size 0x33fb0
```

Every table the decoder touches, and its state in the file (script `35_final_tables.py`):

| Address | Segment | On disk? | Role |
|---|---|---|---|
| 0x84e6e0 (6556 B) | __TEXT | **FILE**, 6524/6556 nonzero | key/id table, indexed by the Java `\uXXXX` |
| 0x84ef50 (256 B) | __TEXT | **FILE**, 255/256 nonzero | 256-byte permutation of 0..255 |
| 0x850e50 (752 B) | __TEXT | **FILE** | values restricted to 0..7 |
| 0xa3cbb0 (256 B) | __TEXT | **FILE** | plain AES S-box (verified: `637c777bf26b6fc5…`) |
| **0xdbe490 (65536 B)** | **__DATA** | **ZERO-FILL — 0 nonzero** | **the substitution table the decoder reads** |
| 0xdde490 (65536 B) | __DATA | ZERO-FILL | second table (0x7af907 base) |
| 0xe6a490 (65536 B) | __DATA | ZERO-FILL | third table (0x7af90e +0x8c000) |

`0xdbe490` is **beyond the end of the file** (`file size = 11,681,712 = 0xb24b30`; `0xdbe490 >
0xb24b30`). The 64 KB substitution table is declared in `__bss` and **materialised at runtime**.

I confirmed by exhaustive scan (2,042,011 instructions disassembled across `__text`, script
`28_loader_extent.py`) that there **173 rip-relative references into that 64 KB window, all
inside the `Loader_l` protected range, and all are reads** — 0 write sites, and 0 references
from any of the 31 `__mod_init_func` constructors. So the table is filled either by code
reached only through the flattened dispatcher (which I did not symbolically execute), or by a
runtime-derived value (e.g. `dlsym`+`memcpy` from a region not present on disk).

**Decisive negative test:** if the 6556-byte table at 0x84e6e0 were a plaintext table keyed by
the Java constants, then `KEY[0x1938..0x193f]` should be the lengths of the 8
`SecurityCheckCode` enum names (declared in that exact order). It is not:

```
[0x1938] = 165    expected len("INTERNAL_ERROR")       = 14
[0x1939] = 107    expected len("LAUNCHER_TAMPERED")    = 17
[0x193a] = 222    expected len("JAVA_TAMPERED")        = 13
...
[0x11e0] = 225    expected len("requestingSite")       = 14
[0x11e1] =  86    expected len("requestingScheme")     = 16
```

No length interpretation matches, and the table is a permuted 256-value space, not lengths.

I also verified the reverse-engineering shortcuts all fail:

- **Plaintext search**, all five dylibs, for `MiniMed`, `Paradigm`, `Guardian`, `MMT-`,
  `requestingSite`, `700 Series`, `600 Series`, and the 8 enum names → **0 hits everywhere**.
- **Single-byte XOR** over the 7,680-byte high-entropy blocks: best key gives 38.7% printable
  (random is ~37%), so not XOR-obfuscated text.
- **UTF-16LE ASCII runs**: 1 distinct run in the whole file, not domain-related.
- **Encoded 128-bit BLE UUIDs** (raw `00001000800000805F9B34FB` suffix): **0 occurrences** in
  libuploader, libSecureKeyBoxJava and libjcocoa. The only UUID literal in the dylib is the
  standard base `00000000-0000-1000-8000-00805F9B34FB` at 0xa7aaea (a parser constant).
- **No `__cstring` HTTP strings at all**: the only `http` occurrences in the whole dylib are
  Apple CRL/OCSP URLs from the embedded code-signing certificate. So libuploader builds **no**
  HTTP requests — confirming the HTTP native methods are elsewhere.

---

## 5. What I did recover (OBSERVED plaintext from the dylib)

This is real and useful even though it is not the encrypted-string set.

**BLE stack error/state strings** (`__cstring`, all quoted with offset):
`E_BLE_LINK_ENCRYPTED` 0xa78bb5, `E_BLE_INSUFFICIENT_ENCRYPT` 0xa78c74,
`E_BLE_INSUFFICIENT_AUTHEN` 0xa78c5a, `E_BLE_INSUFFICIENT_KEY_SIZE` 0xa78c8f,
`E_BLE_GAP_BOND_REJECTED` 0xa78c30, `E_BLE_INVALID_MTU_SIZE` 0xa78be3,
`E_BLE_NOT_CONNECTED` 0xa78b7a, `E_BLE_PROCEDURE_COMPLETE` 0xa78bca,
`E_ERR_ATT_EXCHANGE_MTU_REQ/RSP` 0xa78008/0xa78023.

**BLE operation names**: `StartScanning` 0xa77a50, `SendBLEReset` 0xa77af0,
`SendReadCharacteristic` 0xa77b6f, `SendSignable` 0xa77b96,
`SendPairingRequestFromCentral` 0xa77bb4, `SendNextPacket` 0xa77cfd,
`BondCompleteConf` 0xa77d2a, `ExchangeMtuConf` 0xa77dfd, `HandlerPacketErrorRate` 0xa77d59,
`H_dvcBLE_Send` 0xa78f08, `Signable`/`RequireAuthentication` 0xa77fc9,
`RequireAuthorization` 0xa77fdf.

**Bond-record field names** 0xa7a09a–0xa7a0f9: `signCounter`, `resolvableAddress`, `encAuth`,
`authState`, `signAuth`, `authType` — these are the struct members of `BOND_STRUCT`.

**CB delegate method names** (`did…` family) 0xa7a568–0xa7a806: `didConnectCentral`,
`didDisconnectCentral`, `didSubscribeToCharacteristic`, `didUnsubscribeFromCharacteristic`,
`didUpdateValueForCharacteristic`, `didUpdateValueForDescriptor`, `didDiscoverDescriptors`,
`didDiscoverCharacteristicsForService`, `didDiscoverServices`, `didExchangeMtu`,
`didWriteValueForCharacteristic`, `didUpdateNotificationStateForCharacteristic`, `didReadRSSI`,
`didReadPacketErrorRate`.

**HCI command structs** from mangled symbols (proof of a real HCI implementation, not just a
GATT wrapper): `CMD_LE_READ_RSSI_STRUCT`, `CMD_HCI_EXT_PACKET_ERROR_RATE_STRUCT`,
`CMD_GAP_BOND_STRUCT`, `CMD_GAP_SIGNABLE_STRUCT`, `CMD_ATT_EXCHANGE_MTU_REQ_STRUCT`,
`CMD_GAP_AUTHENTICATE_STRUCT`, plus `BLE_STATE_MACHINE_STRUCT`, `BLE_REQ_RSP_NODE_STRUCT`,
`BLE_MSG_STRUCT`, `BOND_STRUCT`, `BLE_SERVICE_STRUCT_M`, `BLE_CHARACTERISTIC_STRUCT_M`,
`BLE_ATTRIBUTE_STRUCT_M`.

**Build provenance**: `<ci-home>/Jenkins/workspace/uploader_macos_pipeline/
build/dcp/src_analysis/scp_extra/bril/...` and the parallel `src_protected/...` tree (both
present) — confirming the DCP transform splits analysed vs protected sources.
Identity string `medtronic.carelink.uploader` 0xa80e18 and
`/medtronic/carelink/uploader/` 0xa80e34; code-signing subject
`Developer ID Application: MEDTRONIC MINIMED INC (K5YC96YT8M)` 0xb20340.

**AES S-box in the clear** at 0xa3cbb0, referenced from 0x82847b / 0x828b64 / 0x828c1a — all
inside `Loader_l`. It is used with `movdqu`/`pxor`/`pinsrb` sequences at 0x828462–0x828553,
i.e. a real AES round, but **it is not on the string-decryption path** (that uses the table
cipher at 0x7af6b0). No inverse S-box and no T-tables are present, so this is a compact
S-box-only AES, likely for SAKE/transport, not the string table.

---

## 6. Where the HTTP strings actually are (answered from plaintext, OBSERVED)

The 67 `HttpClientCommunicator` natives are not in libuploader, but the app's **base URL is in
plaintext** in `mac-copy/uploader.cfg`:

```
threadPriority=true
ble.base.url=http://blest.inrange.me:7095/api/dataupload/v1
http.connectionTimeout=10
http.socketTimeout=60
installation_language_code=en
```

`localhost:7095` localweb JSON files are also plaintext: `whitelist.json` (device list),
`configuration.json` (per-device serial/product regexes), `greylist.json`, `patientinfo.json`,
`metadata_token.json` (contains `"kind":"BLENGP_SECURE_SNAPSHOT_CONTROL_RESPONSE"` and a base64
`secureToken`).

`DataUploadConstants` in the jar contains a **Java-side XOR decoder** (OBSERVED, decompiled):
alternating `^0x50` / `^0x4F` applied from the end of the string backwards. It has **zero call
sites in the jar**, so it is dead code in this build — it cannot be used to recover the API
routes. The routes are almost certainly among the 442 `StringDecryptor` indices.

Device display names *are* available in plaintext, from resource bundles rather than the dylib:

```
ACC-7350.MEDTRONIC.BLE.PUMP_NAME      = MiniMed\u2122 700 Series
ACC-7350.MEDTRONIC.NGP.PUMP_NAME      = MiniMed\u2122 600 Series
ACC-7350.MEDTRONIC.PARADIGM.MMX23_DEVICE_NAME = Paradigm\u2122
ACC-7350.MEDTRONIC.PARADIGM.G3_DEVICE_NAME    = Guardian\u00ae Real Time
```

---

## 7. What would actually work next

Static extraction is blocked; the scheme needs either emulation to first-call or a live process.

1. **Emulate `Loader_l` with Unicorn, not the whole dylib.** I installed `unicorn 2.1.4` but did
   not complete this. The pain is the flattened dispatcher's jump table and the 3.9 MB of
   `__bss`; it is doable but is a multi-hour job, and the entry stub's integrity gate at
   0x780d5f must be satisfied first.
2. **Prefer the live-process route.** `StringDecryptor.decryptString("\uXXXX")` is a public
   static method. On a Mac with the uploader installed, attach a Java agent or use JNI to call it
   442× and dump the table. This needs **no** breaking of the white-box cipher at all — and the
   brief's own prior report already flagged "Path B: Drive JNI in-process as a black box" as the
   highest-leverage option.
3. **Recover the missing library.** The natives that are genuinely absent are the ones that
   matter. Get `DSS/lib/macos/x86_64/` in full (the installer creates that directory and only
   `libuploader.dylib` appears in the log), or whatever `uploader.policy`'s DCP bridge loads.

**Do not** expect AES key recovery to help: there is no per-string ciphertext in the jar to
decrypt, so even a perfect key would yield nothing.

---

## Files created

All under `.../uploader-jar/native-analysis/`:

- `exports.txt` — 500-symbol export dump with addresses
- `lub_strings.txt`, `skb_strings.txt` — `strings -a -t x` output
- `string_indices.json` — the 687 observed Java table indices
- `01_layout.py` … `37_http_plain.py` — 30 analysis scripts, one per hypothesis, listed in order
- `.venv/` — capstone 5.0.7, lief, unicorn 2.1.4

Key scripts: `07_crypto_scan.py` (S-box + entropy), `10_jninatives.py` (JNINativeMethod triple
scan), `21_xrefs2.py` (full-text xref), `24_decoder_tables.py` / `35_final_tables.py`
(file-vs-bss proof), `33_len_test.py` (the falsifying length test).
