# The packer identified: Zimperium zShield, and why static decryption is impossible (2026-11-12)

**Evidence class: OBSERVED** unless marked. Companion to
`2026-11-12-minimed-packer-engines/` and
`2026-11-12-minimed-packer-and-graph-vocab/`, which establish the two engines and
the call-site census. This record identifies **what the packer is**, states the
negative that closes the static route, and carries two corrections — one of them
to my own working.

**Requests issued by this pass: 0.** Static analysis of local artefacts plus
reading public prior art. **Cap: 0 of a 0 cap — no request was made.**
**Delay:** the standing rule is ≥2 s between requests to the same host; none was
issued, so no spacing applies and none is claimed. **Methods:** no `GET`,
`OPTIONS` or `POST` was sent to any host.

---

## 1. It is Zimperium zShield, not a bespoke Medtronic scheme — OBSERVED

The artefact triple matches the published signature exactly.

| artefact | this APK | zShield signature |
|---|---|---|
| `lib/<random>.so` ~3 MB, packed ELF | `libfblyyzyocs.so` 3,675,584 B | ~3 MB packed/encrypted ELF |
| `assets/<random>/0.odex` | **13 B** | truncated to 17–41 B |
| `assets/<random>.szip` | `fblyyzyocs.szip` 2,356,173 B | encrypted+compressed DEX bytecode |
| randomised library stem | `fblyyzyocs`, `vdlbwnyfem` | randomised per build |

Two public sources agree on that triple: the **AWAKE packer wiki**
(`awakewiki.org/packers/zshield`) and **enovella's zShield RE notes**. Both say
the stem between `lib` and `.so` is randomised per build, which is why the names
are meaningless.

**A useful consequence for identification, not for unpacking:** zShield is a
different product from **zKeyBox**, Zimperium's white-box crypto (which came from
their 2021 whiteCryption acquisition). The CareLink *desktop* uploader uses
`libSecureKeyBoxJava.dylib` — that is zKeyBox. The *mobile* app uses zShield.
**One vendor, two unrelated products**, and the two records in this repo should
not be read as describing the same protection.

## 2. The `.szip` is AES-shaped, and its key is not in the binary — OBSERVED

Payload measurement:

```
size      2,356,173 B  =  13 + 147,260 x 16
entropy   7.99992
blocks    147,260 of 147,260 distinct 16-byte blocks
```

That shape — a 13-byte header followed by an exact multiple of 16, every block
distinct — is what AES-CTR or AES-CBC with a per-build IV produces.

**A known-plaintext oracle was built and run** (`oracle2.c`, C with OpenSSL
AES-NI). For **every byte offset** in both engines it forms an AES-128 and an
AES-256 key from the bytes there and tests five conventions (CTR/iv=0,
CTR/iv=header, CBC/iv=0, CBC/iv=header, CBC-where-C[0:16]-is-the-IV) against an
**8-byte** plaintext check (`dex\n035\0`, `dey\n036\0`, `PK\x03\x04`,
`PK\x05\x06`, or gzip `1f 8b 08` with a sane FLG byte):

```
tested 29837148 keys x 5 conventions; hits=0
```

**149 million trials, zero hits.** About 20 seconds.

### The oracle is proven able to fail — and that matters more than the result

A positive control was run: an AES-256 key was planted at offset `0x100000` of a
copy of the binary, a fake DEX header was encrypted with it, and the oracle was
re-run. It found the key **at the exact offset** and recovered `6465780a30333500`
— `dex\n035\0`.

So the zero is a **real negative**, not a broken check. An earlier version using
only a 3-byte gzip magic reported six "hits", all of which were chance
occurrences of `1f 8b 08`; that is precisely why the final version requires eight
bytes and a positive control.

Also eliminated, each measured rather than assumed: hash-derived keys
(package / engine / asset path / header × SHA-256, SHA-1, MD5), deflate at every
bit offset, and any AES key schedule (a 176/240-byte ExpandKey replay at every
offset), with no AES S-box, no `AESE`/`PMULL`/`SHA256*` opcodes present.

## 3. ⚠ Two corrections

**3a. The lane's reasoning was weaker than its conclusion.** The negative was
partly justified on "`.text` is 1.2% encrypted on disk". Measured with
`capstone` and `skipdata=True` over the whole section:

```
libfblyyzyocs.so   719,381 instructions decoded, 0 undecodable (0.00%)
libvdlbwnyfem.so   249,027 instructions decoded, 0 undecodable (0.00%)
no 4 KiB block in either .text exceeds entropy 7.5
```

**The code is 100% plaintext ARM64.** There is no encrypted region. The 1.2%
figure was capstone's decode failures on ordinary code, not encryption.

This *strengthens* the conclusion rather than weakening it: because the code is
plaintext, a constant search over it is a **real** check, not a vacuous one.
Full working in [`XXTEA-CHECK.md`](XXTEA-CHECK.md).

**3b. I called a false positive, and it is worth recording as a method error.**
Mid-verification I saw `movk w9, #0x9e37` and `movk w11, #0x79b9` and announced
"found it — XXTEA is present". Wrong. Those pair with **different low halves**
(`#0x8951`, `#0x7b85`), reconstructing `0x9e378951` and `0x79b97b85`. Neither is
the XXTEA delta `0x9E3779B9`. Reconstructing every adjacent `movz`+`movk` pair on
the same register gives **zero** delta constructions in either binary.

**A half-word match is not a constant match.** The first scan also silently
examined only 7,771 of 719,381 instructions because `disasm()` without
`skipdata` halts at the first undecodable word — a truncation that would have
produced a confident negative from 1% of the file.

## 4. So this is a *different zShield configuration*

The public zShield write-up describes an **ELF self-decryption** stage using
XXTEA. That stage is **absent here**: the code is plaintext and there is no XXTEA
delta. This build is therefore **asset-only protection** — the native code is
readable (which is why §3a's disassembly works at all), and the protection is
concentrated in the encrypted `.szip`.

That is a **positive** for anyone working on this app: the native engines are
ordinary C++ that can be read and reasoned about. The wall is the asset cipher,
not the code.

## 5. What would actually open the payload

In cost order:

1. **Hook the asset path at runtime.** The four `mprotect` sites
   (`0x2fb5b0`, `0x2fb878`, `0x2fbab4`, `0x2fbc50`) and the single `__open_2` at
   `0x3089d4` are the places to breakpoint. Dumping the `.szip` read buffer after
   the engine has processed it is the shortest route, and it needs a rooted
   device or an emulator.
2. **Trace the 32-bit ARX keystream found at `0x3089b4`**, immediately before
   that `__open_2`: `c = T[i] ^ s ; s = c*T[i] + s (mod 2^32)` with a 15-bit key.
   The primitive is genuine; its table `T[]` is runtime-materialised, so the table
   is the thing to dump, not the key.
3. Reading Java will not get there. The orchestrator is 160 undefined classes and
   the naming layer is 24-of-33 `native`.

## 6. Not claimed

- Any plaintext from the `.szip`.
- That the cipher is AES. The shape is AES-like and an AES key is excluded from
  the binary; the algorithm itself is **not identified**.
- That zShield cannot be defeated — only that it cannot be defeated *statically
  from the APK*.
- That the 15-bit ARX primitive is the `.szip` cipher. It sits on the same code
  path; that is all that is established.
