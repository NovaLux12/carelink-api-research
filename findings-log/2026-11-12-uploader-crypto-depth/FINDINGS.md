# Uploader crypto depth — the string decryptor and SKB, analysed (2026-11-12)

**Evidence class: OBSERVED** unless marked. Companion to
`2026-11-12-uploader-native-libraries/`, which records the recovery of the
libraries themselves. This record carries the two deep analyses that the
recovery made possible, and the corrections they force.

Two supporting documents sit beside this one and should be read as part of it:

- [`STRINGDECRYPTOR-ANALYSIS.md`](STRINGDECRYPTOR-ANALYSIS.md) — the full
  disassembly of the decoder, the index-range measurement, and the proof that
  static extraction cannot work
- [`SKB-CHARACTERISATION.md`](SKB-CHARACTERISATION.md) — the Secure Key Box
  binary, its white-box technique, and a complete call-site graph of what the
  uploader uses it for

**Requests issued by this pass: 0.** Everything is static analysis of local
artefacts. **Cap: 0 of a 0 cap — no request was made.** **Delay:** the standing
rule is ≥2 s between requests to the same host; no request was issued, so no
spacing applies and none is claimed. **Methods:** no `GET`, `OPTIONS` or `POST`
was sent to any host, and no credential was used.

**Tooling:** `strings`, hand-rolled Mach-O readers (no Mach-O binutils on this
host — `nm` and `objdump` reject the format), CFR 0.152 under OpenJDK 17, and
`capstone` / `lief` / `unicorn` for the disassembly work.

---

## 1. `StringDecryptor` is an index lookup, not ciphertext

This is the finding that reframes the problem, and it invalidates the obvious
approach.

`decryptString` does **not** take ciphertext. It takes a **16-bit table index**.
Across 852 call sites:

| argument shape | call sites |
|---|---|
| a single `\uXXXX` | **789** |
| a single literal character | 62 |
| two characters | 1 |

The indices are **sequential within semantic groups**, which is the proof they
are not data: `SecurityCheckCode`'s eight enum constants, declared in source
order, use `\u1938, \u1939, … \u193f` consecutively; `AbstractAuthenticator`'s
five map keys use `\u11e0 … \u11e4`. The range is **0x0001–0x199B (6555)** across
687 distinct values, so only 10.5% of the table space is referenced.

The `decryptString000` … `decryptString19B` overloads (412 of them) are **never
called from any Java source**.

**Consequence:** there is no per-string ciphertext in the JAR to decrypt. Even a
perfect key would yield nothing. This is a whiteCryption Secure Key Box
string-protection scheme: literals are stripped at build time, replaced by an id,
and the plaintext lives in a table inside the native protector.

## 2. The decoder, disassembled

`_Java_uploader_Loader_l` at `0x780d30` is the only non-BRIL JNI export, and the
gap to the next export runs 766,102 bytes (748 KB) — not one function, but the
whole protected region entered through one stub. The entry stub carries an
**integrity gate**: it compares a constant-derivable value against `0xd` and
simply returns if the check passes.

The real cipher is clean and **not** obfuscated, at `0x7af6b0`:

```
0x7af6b4  mov   eax, edi              ; arg1 = id
0x7af6b6  lea   rdi, [rip+0x9f023]    ; -> key table, base 0x84e6e0
0x7af6bd  movzx r8d, byte [rsi]       ; src byte 0
0x7af6c1  movzx r9d, byte [rdx]       ; src byte 1
0x7af6c5  shl   r9, 8
0x7af6c9  or    r9, r8                ; = src0 | src1<<8
0x7af6cc  movzx r10d, byte [rax+rdi]  ; KEY[id]
0x7af6d1  shl   r10, 0xb              ; << 11
0x7af6d5  xor   r10, r9
0x7af6d8  lea   r8, [rip+0x60edb1]    ; -> substitution table, base 0xdbe490
0x7af6df  movzx r9d, byte [r8+r10]    ; SUB[(KEY[id]<<11) ^ src]
0x7af6e7  and   r10b, 7               ; dst byte = low 3 bits
0x7af6ee  and   r9b, 0xf8             ; top 5 bits...
0x7af6f2  xor   r9b, byte [rsi+1]     ; ...chained into the next byte
```

So: a **6-byte-state, byte-chained table substitution cipher**, with 5 bits of
each output feeding the next lookup. There is a second parallel decoder at
`0x7af900` reading u16 entries, and generic loop forms at `0x7af3a0`/`0x7af430`.

**No AES, no XOR key, no SKB call on this path.** `libuploader.dylib` imports no
CommonCrypto or Security symbols at all (`_CCCrypt*`, `_SecKey*`, `_CCHmac*` are
all absent); its only crypto-adjacent import is `_dlsym`.

## 3. Why static extraction cannot work — proven, not assumed

The tables the decoder reads:

| address | segment | on disk? | role |
|---|---|---|---|
| `0x84e6e0` (6556 B) | `__TEXT` | **yes**, 6524/6556 nonzero | key table, indexed by the Java id |
| `0x84ef50` (256 B) | `__TEXT` | **yes**, a true permutation of 0..255 | byte substitution |
| `0x850e50` (752 B) | `__TEXT` | yes | values restricted to 0..7 |
| `0xa3cbb0` (256 B) | `__TEXT` | yes | plaintext AES S-box |
| **`0xdbe490` (65536 B)** | **`__DATA`** | **NO — zero-fill** | **the table the decoder actually reads** |
| `0xdde490`, `0xe6a490` (65536 B each) | `__DATA` | no — zero-fill | second and third tables |

`0xdbe490` is **past the end of the file** (file size `0xb24b30`). The 64 KB
substitution table is declared in `__bss` and materialised at runtime. An
exhaustive scan disassembled 2,042,011 instructions across `__text` and found
**173 rip-relative references into that window, all reads, zero writes**, and
none from any of the 31 `__mod_init_func` constructors.

**The falsifying test was run and passed.** If the key table were plaintext
string lengths, `KEY[0x1938]` should be `len("INTERNAL_ERROR")` = 14. Measured:

```
KEY[0x1938..0x193f] = 165 107 222 243 70 208 134 171
```

No length reading matches, and the table is a 256-value permutation, not a set of
lengths. So the table is **not** a plaintext lookup and the decoder cannot be
run backwards from the file.

**Verified independently for this record:** the S-box at `0xa3cbb0` matches the
standard Rijndael table byte-for-byte, and the permutation at `0x84ef50` is a
genuine 256-element permutation. The measurements in this section were re-run
from the file, not taken from the analysis document.

## 4. What the failure is worth

This is a **negative that closes a line of enquiry**, and it is more useful than
a partial guess would have been:

- Any plan to "decrypt the strings with AES" is dead: there is no ciphertext.
- Any plan to "brute-force the XOR key" is dead: the best single-byte XOR over
  the high-entropy blocks gives 38.7% printable against a 37% random baseline.
- Plaintext search for `MiniMed`, `Paradigm`, `Guardian`, `MMT-`, the eight enum
  names: **0 hits across all five dylibs**.
- Encoded 128-bit BLE UUID suffixes: **0 occurrences**, so the "all device names
  and BLE UUIDs" claim is unsupported by this artefact.

**What is not dead, and is cheap:** `StringDecryptor.decryptString` is a
**public static method**. In a live process it can be called 442 times and the
table dumped, with no breaking of any cipher. That needs the uploader running,
which needs Rosetta 2 on this host.

## 5. SKB: real white-box, modest scale, narrow purpose

The white-box technique is **present but lightweight**:

- **73 encoded T-boxes** (74,752 B) with four permutation lanes and genuine AES
  DDT (max = 4), in 16-table clusters; three tables show the lane1==lane2
  signature of a real white-box construction.
- **264 pure GF(2)-affine mixing bijections** among 385 permutation tables
  (the other 121 are nonlinear).
- **But** a plaintext AES S-box sits at `0x2c5f70` inside an ordinary T-table
  cluster, and **no block matches classic `Te0..Te3`**.
- About 75 KB of encoded tables is one to two orders of magnitude below a
  Chow-scale white-box. Encoded, yes; heavyweight, no.

**Verified independently for this record:** the plaintext S-box occurs twice in
the dylib, and the classic `Te0` table does **not** occur — consistent with
"encoded T-boxes, plaintext S-box". No attack was attempted and **no claim of
weakness is made**.

The binary ships a persistent per-device key cache
(`skb_cache_<guid><guid>.kc`, with `diversification_guid` and a default of
`123456789`), and anti-tamper callbacks: `SKB_Callback_AntiDebug`,
`SKB_Callback_Jailbreak`, `SKB_Callback_Root`.

## 6. What SKB actually protects: two things, neither of them pump data

A complete call-site walk of all 8,972 `uploader.jar` classes found **exactly two
consumers**:

1. **The CareLink password**, wrapped as SKB `SecureData`, persisted as
   `getEncryptedValue()` in `Preferences` with an IV derived from the machine
   UUID, plaintext existing only inside a native `access()` callback. This is the
   strongest and clearest use, and it is a genuine **credential-at-rest**
   control.
2. **The diagnostic log at rest** — gzip plus **ordinary AES-128-CBC** via
   `Engine.createCipher`, with a key supplied by the *server* through
   `ControlCodes."encryptionKey"`. The white-box protects the key, not the
   algorithm.

A third, optional use — the REST auth token — is gated by `isEncryptedToken()`
and is **off** in `LocalCommunicator`.

**Explicitly not protected:** the uploaded medical payload
(`UploadDeviceAction` → `sendSnapshot(byte[])` takes a raw array; its only
`SecurityUtils` reference is `getSecureRandom()`), and the SAKE link keys, which
are the 34 `SakeJNI` natives in `libuploader.dylib` with zero SKB overlap.

**Verdict: SKB does not gate pump data.** It gates the credential. Pump data
travelled the BLE/SAKE path, which ships un-white-boxed. The accurate sentence
is: **SKB protects the CareLink password and log confidentiality; pump data is
reachable through the SAKE path regardless of SKB.**

## 7. Corrections this record carries

**⚠ `sake` does not appear in `libSecureKeyBoxJava.dylib` at all.** An earlier
count of "124 `sake|skb` references" was a *pattern* count and is misleading as a
description: measured, `sake` occurs **0** times and `SKB` 100 times. The dylib
is the SKB engine only. Anyone reading the earlier figure as evidence that SKB
implements SAKE would be wrong.

**⚠ A third native library is still missing.** `SecurityUtils`' nine crypto
methods are `native`, and `libuploader.dylib` does **not** implement them — its
378 `Java_*` exports are all `bril`/`gatts`/`sake`. So the SKB Java path is not
executable from the recovered artefacts either. The uploader's 1,370 native
methods across 38 classes are served by at least three modules, and two remain
unlocated.

## 8. Not claimed

- No plaintext string, device name or BLE UUID from the protected table.
- No claim that SKB is broken — nor that it is safe. Its cryptographic strength
  is **unanswered**, not answered negatively.
- No `__text` disassembly of `libSecureKeyBoxJava.dylib` (no capable tool was
  installed on this host); the SKB reading is from export tables, section maps,
  table census and the Java side.
- Nothing about what the third native module contains.
