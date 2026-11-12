# libandroid-sake-lib.so — API & Protocol Specification

**Target:** `libandroid-sake-lib.so (from the MiniMed Mobile 3.14 APK payload)`
**SHA-256:** `3899462439a627eb84265877607b5d32426dda74604134b57c64018cfb5f405f`
**Size:** 129,184 B · ELF64 ARM aarch64 · shared object · stripped · Android API 30 · NDK r28c (clang 19.0.1, LLD 19.0.1)
**BuildID:** `a0457de95a2b957e515386a897c1d449ba74f9c9`

All offsets below are **file offsets** unless marked `vaddr`. Evidence tags:
**[OBS]** = observed by me in this binary (offset given) · **[PUB]** = prior art · **[INF]** = inference.

---

## 1. Executive summary

| Question | Answer | Basis |
|---|---|---|
| Are the published OpenMinimed key DBs in this binary? | **No.** Zero matches, full or partial. | [OBS] |
| Are they anywhere in the APK/XAPK? | **No.** Not in `base.apk`, `minimed.eu.xapk`, any `.dex`, or the arm64 lib set. | [OBS] |
| Is the cipher AES-128-CTR? | **Yes, confirmed** — AES-CTR with a 16-byte counter block, plus truncated CMAC-AES tags. | [OBS] |
| Is CMAC verification truncated to 2 bytes? | **Yes** — 2-byte tag on the wire, sequence byte in the trailer. | [OBS] |
| Handshake message size | **20 bytes**, hard-enforced. | [OBS] |
| Where do the keys live? | **Supplied at runtime** through `SAKE_KEY_DATABASE_S` (a byte buffer the app fills); the library parses and CRC-checks it but never embeds one. | [OBS]/[INF] |

The security-relevant finding: this library is a **protocol engine, not a key store**. It contains the entire SAKE implementation — AES-128/192/256 key expansion, CTR, CMAC, GF(2^128) doubling — plus a formal key-database parser with CRC32 validation, but **no key material whatsoever**. Any device that talks SAKE through this build must be handed its static keys from outside the `.so`.

---

## 2. Prior art, quoted

From **OpenMinimed/PythonSake** (README, [PUB], cloned 2026-11-12):

> "This is a re-implementation of the SAKE cryptographic library in Python. Original PoC code was provided to the project by @planiitis from https://github.com/planiitis/medtronic-bt-decrypt"

`pysake/seqcrypt.py` documents the native library directly:

> "Native library model (libandroid-sake-lib_v210.so):
>   - Single 64-bit counter per SAKE_SECURE_LINK_S, +1 per msg
>   - CTR nonce encodes: (mode & 1) | (counter << 1) as 5-byte big-endian
>   - Wire trailer byte: counter & 0xFF
>   - mode=0 for client, mode=1 for server"

**That description is confirmed correct against this build** — see §7.4, which recovers the exact instruction sequence that builds that nonce.

`pysake/keys.py` defines the key-database wire format:

> "Layout: [4-byte CRC][1-byte local_device_type][1-byte n][n * (1-byte dev_type + 80-byte StaticKeys)]
> CRC is computed over bytes after the CRC field (i.e. from local_device_type onwards)."

`StaticKeys` = five 16-byte fields: `derivation_key`, `handshake_auth_key`, `permit_decrypt_key`, `permit_auth_key`, `handshake_payload`.

**This format is confirmed byte-for-byte against this binary** — see §6.1, which recovers the same numbers (4-byte CRC, 1-byte device type, 1-byte count, 81 bytes/entry, 0x51 stride) from the disassembly.

---

## 3. Complete export table — 163 `SakeJNI` exports

`readelf --dyn-syms` reports **184** defined `FUNC GLOBAL DEFAULT` symbols; **163** are `Java_com_medtronic_minimed_sake_SakeJNI_*` and **21** are libc PLT imports. There are **no other exported functions** — the entire public surface is the JNI binding.

Symbols are C++ mangled with `_1` = `_`. Addresses are `vaddr` (base 0); `.text` is `vaddr 0x10794 / file 0xc794`.

### 3.1 Glue, error enum, and message containers — phase 0 (utility)

| vaddr | size | demangled |
|---|---|---|
| `0x0107f4` | 316 | `cdata` |
| `0x010930` | 136 | `memmove` |
| `0x0109b8` | 12 | `new_p_uint8_t` |
| `0x0109c4` | 8 | `delete_p_uint8_t` |
| `0x0109cc` | 8 | `p_uint8_t_getitem` |
| `0x0109d4` | 8 | `p_uint8_t_setitem` |
| `0x0109dc` | 8 | `p_uint8_t_cast` |
| `0x0109e4` | 8 | `p_uint8_t_frompointer` |
| `0x0109ec` | 316 | `cdata_uint8_t` |
| `0x010b28` | 8 | `AsVoidPtr` |
| `0x010b30` | 8 | `E_SAKE_HANDSHAKE_ERROR_INVALID_get` → **0** |
| `0x010b38` | 8 | `E_SAKE_HANDSHAKE_NO_ERROR_get` → **1** |
| `0x010b40` | 8 | `E_SAKE_HANDSHAKE_ERROR_LAST_get` → **0x17 (23)** |
| `0x010b48` | 28 | `Sake_HandshakeError_IsValid` (1..23) |
| `0x010b64` | 68 | `Sake_HandshakeError_ToString` |
| `0x010ba8` | 136 | `Sake_HandshakeError_FromString` |

`cdata`/`cdata_uint8_t` at 316 B each are **ctypes-generated CPython bindings** — this library is driven from Java via a Python layer (Chaquopy) rather than hand-written JNI. That is why every accessor takes `(env, thiz, ptr, ...)` and moves `x4→x2`.

### 3.2 SAKE_SECURE_MESSAGE_S — post-handshake encrypt/decrypt

| vaddr | size | demangled |
|---|---|---|
| `0x010c30` | 8 | `MIN_SAKE_SECURE_MESSAGE_BYTE_COUNT_get` → **3** |
| `0x010c38` | 8 | `MAX_SAKE_SECURE_MESSAGE_BYTE_COUNT_get` → **0x40 (64)** |
| `0x010c40` | 60 | `SAKE_SECURE_MESSAGE_S_pBytes_set` |
| `0x010c7c` | 8 | `SAKE_SECURE_MESSAGE_S_pBytes_get` |
| `0x010c84` | 12 | `SAKE_SECURE_MESSAGE_S_byteCount_set` (off `0x40`) |
| `0x010c90` | 8 | `SAKE_SECURE_MESSAGE_S_byteCount_get` (off `0x40`) |
| `0x010c98` | 12 | `new_SAKE_SECURE_MESSAGE_S` |
| `0x010ca4` | 8 | `delete_SAKE_SECURE_MESSAGE_S` |
| `0x010cac` | 32 | `Sake_SecureMessage_GetSequenceNumber` |
| `0x010ccc` | 44 | `Sake_SecureMessage_EncryptAndSign` |
| `0x010cf8` | 40 | `Sake_SecureMessage_DecryptAndAuthenticate` |

### 3.3 SAKE_USER_MESSAGE_S — plaintext payload

| vaddr | size | demangled |
|---|---|---|
| `0x010d20` | 8 | `MAX_SAKE_USER_MESSAGE_BYTE_COUNT_get` → **0x3d (61)** |
| `0x010d28` | 72 | `SAKE_USER_MESSAGE_S_pBytes_set` |
| `0x010d70` | 8 | `SAKE_USER_MESSAGE_S_pBytes_get` |
| `0x010d78` | 12 | `SAKE_USER_MESSAGE_S_byteCount_set` (off `0x40`) |
| `0x010d84` | 8 | `SAKE_USER_MESSAGE_S_byteCount_get` (off `0x40`) |
| `0x010d8c` | 12 | `new_SAKE_USER_MESSAGE_S` |
| `0x010d98` | 8 | `delete_SAKE_USER_MESSAGE_S` |

### 3.4 SAKE_KEY_DATABASE_S — key store (setup phase)

| vaddr | size | demangled | value |
|---|---|---|---|
| `0x010da0` | 8 | `SAKE_KEY_DATABASE_CRC_BYTE_COUNT_get` | **4** |
| `0x010da8` | 8 | `SAKE_KEY_DATABASE_DEVICE_TYPE_BYTE_COUNT_get` | **1** |
| `0x010db0` | 8 | `SAKE_KEY_DATABASE_REMOTE_DEVICE_COUNT_BYTE_COUNT_get` | **1** |
| `0x010db8` | 8 | `SAKE_KEY_DATABASE_HEADER_BYTE_COUNT_get` | **6** |
| `0x010dc0` | 8 | `SAKE_KEY_DATABASE_REMOTE_DEVICE_KEY_COUNT_get` | **4** |
| `0x010dc8` | 12 | `SAKE_KEY_DATABASE_S_pBytes_set` | |
| `0x010dd4` | 8 | `SAKE_KEY_DATABASE_S_pBytes_get` | |
| `0x010ddc` | 12 | `SAKE_KEY_DATABASE_S_byteCapacity_set` | |
| `0x010de8` | 8 | `SAKE_KEY_DATABASE_S_byteCapacity_get` | |
| `0x010df0` | 12 | `new_SAKE_KEY_DATABASE_S` | |
| `0x010dfc` | 8 | `delete_SAKE_KEY_DATABASE_S` | |
| `0x010e04` | 36 | `Sake_KeyDatabase_Open` | impl `0x14180` |
| `0x010e28` | 48 | `Sake_KeyDatabase_GetLocalDeviceType` | impl `0x1425c` |
| `0x010e58` | 160 | `Sake_KeyDatabase_HasRemoteDeviceType` | impl `0x14278` |
| `0x010ef8` | 156 | `Sake_KeyDatabase_GetRemoteDeviceKeyByType` | impl `0x142f4` |
| `0x010f94` | 168 | `Sake_KeyDatabase_Create` | impl `0x14374` |
| `0x01103c` | 164 | `Sake_KeyDatabase_AddRemoteDeviceKey` | impl `0x14408` |
| `0x0110e0` | 8 | `Sake_KeyDatabase_Clear` | |
| `0x0110e8` | 8 | `Sake_KeyDatabase_GetSizeInBytes` | impl `0x14560` |

### 3.5 SAKE_PASSKEY_S and SAKE_PERMIT_S — pairing credential / authorization token

| vaddr | size | demangled | value |
|---|---|---|---|
| `0x0110f0` | 8 | `SAKE_PASSKEY_BYTE_CAPACITY_get` | **0x10 (16)** |
| `0x0110f8` | 132 | `SAKE_PASSKEY_S_pBytes_set` | |
| `0x01117c` | 8 | `SAKE_PASSKEY_S_pBytes_get` | |
| `0x011184` | 12 | `SAKE_PASSKEY_S_byteCount_set` (off `0x10`) | |
| `0x011190` | 8 | `SAKE_PASSKEY_S_byteCount_get` (off `0x10`) | |
| `0x011198` | 12 | `new_SAKE_PASSKEY_S` | |
| `0x0111a4` | 8 | `delete_SAKE_PASSKEY_S` | |
| `0x0111ac` | 32 | `Sake_Passkey_FromInteger` | impl `0x14570` |
| `0x0111cc` | 8 | `SAKE_PERMIT_PROPRIETARY_BYTE_COUNT_get` | **0xa (10)** |
| `0x0111d4` | 160 | `SAKE_PERMIT_S_version_set` | |
| `0x011274` | 40 | `SAKE_PERMIT_S_version_get` | |
| `0x01129c` | 160 | `SAKE_PERMIT_S_deviceType_set` | |
| `0x01133c` | 40 | `SAKE_PERMIT_S_deviceType_get` | |
| `0x011364` | 84 | `SAKE_PERMIT_S_pProprietaryBytes_set` | |
| `0x0113b8` | 8 | `SAKE_PERMIT_S_pProprietaryBytes_get` | |
| `0x0113c0` | 12 | `new_SAKE_PERMIT_S` | |
| `0x0113cc` | 8 | `delete_SAKE_PERMIT_S` | |
| `0x0113d4` | 228 | `Sake_Permit_Init` | |
| `0x0114b8` | 40 | `Sake_Permit_EncryptAndSign` | impl `0x145c8` |
| `0x0114e0` | 40 | `Sake_Permit_DecryptAndAuthenticate` | impl `0x14690` |

`SAKE_PERMIT_S` is **20 bytes** — `Permit_Init` at `0x11404` allocates exactly `#0x14` and stores `q0` (16 B) + `w8` (4 B) at `[x0]` / `[x0,#0x10]`. [OBS]

### 3.6 Handshake scratch memory

| vaddr | size | demangled |
|---|---|---|
| `0x011508` | 172 | `SAKE_CLIENT_MEMORY_S_transcript_set` |
| `0x0115b4` | 56 | `SAKE_CLIENT_MEMORY_S_transcript_get` |
| `0x0115ec` | 172 | `SAKE_CLIENT_MEMORY_S_srp_set` |
| `0x011698` | 56 | `SAKE_CLIENT_MEMORY_S_srp_get` |
| `0x0116d0` | 28 | `SAKE_CLIENT_MEMORY_S_passkey_set` |
| `0x0116ec` | 8 | `SAKE_CLIENT_MEMORY_S_passkey_get` |
| `0x0116f4` | 12 | `new_SAKE_CLIENT_MEMORY_S` |
| `0x011700` | 8 | `delete_SAKE_CLIENT_MEMORY_S` |
| `0x011ea8` | 172 | `SAKE_SERVER_MEMORY_S_transcript_set` |
| `0x011f54` | 56 | `SAKE_SERVER_MEMORY_S_transcript_get` |
| `0x011f8c` | 172 | `SAKE_SERVER_MEMORY_S_srp_set` |
| `0x012038` | 56 | `SAKE_SERVER_MEMORY_S_srp_get` |
| `0x012070` | 24 | `SAKE_SERVER_MEMORY_S_passkey_set` |
| `0x012088` | 8 | `SAKE_SERVER_MEMORY_S_passkey_get` |
| `0x012090` | 12 | `new_SAKE_SERVER_MEMORY_S` |
| `0x01209c` | 8 | `delete_SAKE_SERVER_MEMORY_S` |

`transcript` copies **0xF8 = 248 bytes**; `srp` copies **0x368 = 872 bytes** (server) / **0x370 = 880** (client). [OBS]

> **The `srp` field is live, not vestigial.** My first pass concluded otherwise and was **wrong** — corrected here. This build contains a complete, reachable SRP implementation (§6.7): the RFC 5054 1024-bit group (N at `0x7df8`, g=2 at `0x7e78`), a full SHA-256 (K table at `0x7efc`, compression at `0x18b00`), and a bignum/modexp stack (`0x18774` mul, `0x18e1c`, `0x1920c` init, `0x1ae90`, `0x1a5a8`). SRP runs on the **`protocolVersion == 2`** path, which is reached from `Sake_Client_Handshake` state 3 at `0x12c10`–`0x12c48`.

What tripped me up: I checked only big-endian constant encodings, and the SHA-256 K table is stored little-endian. An absence-of-constant check that can't fail is not evidence — noted, and the finding reversed.

### 3.7 SAKE_CLIENT_S — handshake state (client side)

Recovered offsets from the generated accessors; struct is **0x90 bytes**.

| field | offset | width | vaddr (set / get) |
|---|---|---|---|
| `currentState` | `0x00` | u32 | `0x011708` / `0x0117a8` |
| `protocolVersion` | `0x04` | u32 | `0x0117d0` / `0x011870` |
| `clientChallenge` | `0x08` | 8 B | `0x011898` / `0x011938` |
| `serverChallenge` | `0x10` | 8 B | `0x011960` / `0x011a00` |
| `clientInitializationVector` | `0x18` | u32 (4 B) | `0x011a28` / `0x011ac8` |
| `serverInitializationVector` | `0x1c` | u32 (4 B) | `0x011af0` / `0x011b90` |
| *(inline key database)* | `0x20` | — | see `keyDatabase_set` `0x011ca0` |
| `serverPermit` | `0x30` | 20 B (`q0`@0x20 + `w8`@0x30) | `0x011bb8` / `0x011bd0` |
| `serverDeviceType` | `0x34` | u32 | `0x011bd8` / `0x011c78` |
| *(inline keyDatabase mirror)* | `0x38` | 0x30 | |
| `secureLink` | `0x48` | 48 B (`q0,q1,q2`) | `0x011cb8` / `0x011d64` |
| `isSecureLinkEstablished` | `0x78` | u8 | `0x011d9c` / `0x011db0` |
| `pMemory` | `0x80` | ptr | `0x011db8` / `0x011dc4` |
| `lastError` | `0x88` | u32 | `0x011dcc` / `0x011dd8` |

### 3.8 SAKE_SERVER_S — handshake state (server side)

Struct is **0xC0 bytes**; 0x30 larger than the client (extra `temporarySecureLink`).

| field | offset | width | vaddr (set / get) |
|---|---|---|---|
| `currentState` | `0x00` | u32 | `0x0120a4` / `0x012144` |
| `protocolVersion` | `0x04` | u32 | `0x01216c` / `0x01220c` |
| `clientChallenge` | `0x08` | 8 B | `0x012234` / `0x0122d4` |
| `serverChallenge` | `0x10` | 8 B | `0x0122fc` / `0x01239c` |
| `clientInitializationVector` | `0x18` | u32 | `0x0123c4` / `0x012464` |
| `serverInitializationVector` | `0x1c` | u32 | `0x01248c` / `0x01252c` |
| `clientPermit` | `0x30` | 20 B | `0x012554` / `0x01256c` |
| `clientDeviceType` | `0x34` | u32 | `0x012574` / `0x012614` |
| `temporarySecureLink` | `0x38` | 48 B | `0x01263c` / `0x0126e8` |
| `secureLink` | `0x78` | 48 B | `0x012738` / `0x0127e4` |
| `isSecureLinkEstablished` | `0xa8` | u8 | `0x01281c` / `0x012830` |
| `pMemory` | `0xb0` | ptr | `0x012838` / `0x012844` |
| `lastError` | `0xb8` | u32 | `0x01284c` / `0x012858` |

### 3.9 The operational API — 16 functions that matter

**Client (0x90-byte object):**

| vaddr | size | function | body |
|---|---|---|---|
| `0x011df4` | 32 | `Sake_Client_Init` | `0x129cc` |
| `0x011e14` | 8 | `Sake_Client_Destroy` | `0x12a04` |
| `0x011e1c` | 36 | `Sake_Client_SetPasskey` | `0x12a24` |
| `0x011e40` | 16 | `Sake_Client_Handshake` | `0x12fc4` |
| `0x011e50` | 36 | `Sake_Client_SecureForSending` | `0x13210` |
| `0x011e74` | 36 | `Sake_Client_UnsecureAfterReceiving` | `0x1322c` |
| `0x011e98` | 8 | `Sake_Client_GetServerPermit` | `0x13248` |
| `0x011ea0` | 8 | `Sake_Client_GetLastError` | `0x13260` |

**Server (0xC0-byte object):**

| vaddr | size | function | body |
|---|---|---|---|
| `0x012874` | 32 | `Sake_Server_Init` | |
| `0x012894` | 8 | `Sake_Server_Destroy` | |
| `0x01289c` | 36 | `Sake_Server_SetPasskey` | |
| `0x0128c0` | 16 | `Sake_Server_Handshake` | `0x14dc4` |
| `0x0128d0` | 36 | `Sake_Server_SecureForSending` | |
| `0x0128f4` | 36 | `Sake_Server_UnsecureAfterReceiving` | |
| `0x012918` | 8 | `Sake_Server_GetClientPermit` | |
| `0x012920` | 8 | `Sake_Server_GetLastError` | |

Plus `new_SAKE_CLIENT_S` `0x011de0` / `delete_SAKE_CLIENT_S` `0x011dec`, `new_SAKE_SERVER_S` `0x012860` / `delete_SAKE_SERVER_S` `0x01286c` — **163 total**, fully enumerated above.

---

## 4. Protocol phase grouping

| Phase | Exports | Purpose |
|---|---|---|
| **0. Setup / key provisioning** | `Sake_KeyDatabase_*` (8), `Sake_Passkey_FromInteger`, `SAKE_KEY_DATABASE_*` consts (5) | Load and validate the static-key blob; build the pairing passkey |
| **1. Handshake (key agreement)** | `Sake_Client_Init/Handshake/SetPasskey/GetServerPermit`, `Sake_Server_Init/Handshake/SetPasskey/GetClientPermit`, `SAKE_*_MEMORY_S_*` (16) | 6-message challenge/response exchanging 8-byte challenges, 4-byte IVs, device types |
| **2. Permit (authorization)** | `Sake_Permit_Init`, `Sake_Permit_EncryptAndSign`, `Sake_Permit_DecryptAndAuthenticate`, `SAKE_PERMIT_S_*` (9) | 16-byte AES-ECB-encrypted + CMAC-signed device authorization token |
| **3. Secure session** | `Sake_SecureMessage_EncryptAndSign`, `..._DecryptAndAuthenticate`, `..._GetSequenceNumber`, `SAKE_SECURE_MESSAGE_S_*`, `Sake_{Client,Server}_SecureForSending`, `..._UnsecureAfterReceiving` | Per-message AES-CTR + truncated CMAC |
| **4. Utility / reflection** | `cdata*`, `p_uint8_t_*`, `AsVoidPtr`, `memmove`, `new_*`/`delete_*`, `Sake_HandshakeError_*`, all `*_get`/`*_set` accessors | ctypes plumbing and Java-visible field access |

Note the asymmetry that reveals the design intent: **the client can `GetServerPermit`, the server can `GetClientPermit`** — permits travel in *both* directions. The pump authorizes the phone as much as the phone authorizes the pump.

---

## 5. Key database: presence determination

### 5.1 The published databases

From `PythonSake/pysake/constants.py` [PUB]:

| Name | hex (87 B) | local dev | remote dev |
|---|---|---|---|
| `KEYDB_G4_CGM` | `5fe5928308010230f0b50d…efef2c43b326` | 8 = PrimaryDisplay | 2 = GlucoseSensor |
| `KEYDB_PUMP_EXTRACTED` | `f75995e70401011bc1bf7c…d66dc1895c` | 4 = MobileApplication | 1 = InsulinPump |
| `KEYDB_PUMP_HARDCODED` | `c2cdfdd1040101fce36ed6…eebe30e4ba` | 4 = MobileApplication | 1 = InsulinPump |

I verified all three are self-consistent: `len == 6 + 81*n` holds, and the stored 4-byte big-endian CRC32 equals `zlib.crc32(payload)` in every case. [OBS]

### 5.2 Byte comparison — result: NO MATCH

I searched for each database in five forms: the full 87-byte blob, the 75-byte body (skipping CRC + header), and each of the five 16-byte static keys individually. **Every search returned zero hits.**

Searched against: the `.so` itself (all 129,184 bytes), the 87-byte full blob, 75-byte body, and all 5 × 16-byte subkeys — across `libs/libandroid-sake-lib.so`, `native/libandroid-sake-lib.so`, `base.apk` (21.3 MB), `minimed.eu.xapk` (36.1 MB), and `jadx.zip` (116.6 MB). **Zero matches everywhere.** [OBS]

For scale: `KEYDB_G4_CGM`'s derivation key begins `30f0b50df613f2e4…`; that 16-byte string does not occur at any offset in the binary. A 16-byte random value has a ~2⁻¹²⁸ chance of coincidental absence, so this is a definitive negative, not a sampling artifact.

### 5.3 Why they are absent — the library is a parser, not a store

`Sake_KeyDatabase_Open` (impl `0x14180`) takes a **caller-supplied buffer** and validates it:

```
0x141a8  cmp  x2, #6              ; reject if length < header
0x141c0  ldrb w0, [x20, #4]!      ; local_device_type
0x141c4  bl   0x14170             ; -> (v-1) < 8, i.e. device type 1..8
0x141cc  ldrb w8, [x19, #5]       ; n remote devices
0x141d0  mov  w9, #0x51           ; 81 bytes per entry
0x141d8  umull x8, w8, w9         ; n * 81
0x141dc  add  x9, x8, #6          ; 6 + n*81
0x141e0  cmp  x9, x21             ; must fit the buffer
0x14200  add  x2, x8, #2          ; CRC covers bytes [4 .. 6+n*81)
0x1420c  bl   0x22874             ; CRC32
0x14210  ldr  w8, [x19]
0x14214  rev  w8, w8              ; big-endian compare
0x14218  cmp  w0, w8
```

Every constant here — `#6`, `#0x51`, `#4`, `#5`, device-type range 1–8, big-endian CRC32 — **matches the prior-art format exactly**. [OBS] `Sake_KeyDatabase_GetSizeInBytes` (`0x14560`) is literally `6 + n*81`:

```
0x14560  mov  w8, #0x51
0x14564  mov  w9, #6
0x14568  madd w0, w0, w8, w9
```

The CRC32 is the standard reflected polynomial `0xEDB88320`; its 256-entry little-endian table sits at **file offset `0x807c`**, and the loop at `0x22874` begins with `mvn w8, w0` (the classic `crc = ~crc` pre-conditioning). [OBS]

**Conclusion:** the binary contains the *schema* for the keys and not the keys. The app must supply the 87-byte blob to `Sake_KeyDatabase_Open` at runtime — most plausibly provisioned during account setup / pairing and held in the encrypted SQLCipher database (`libsqlcipher.so`, 5.18 MB, ships in the same APK split). [INF] That is a statement about where the keys are *not*; I have not found where they *are*.

Two supporting observations:
1. The only file I/O in the library is `/dev/urandom` (3 direct `adr` references at `0x21584`, `0x21a8c`, `0x228c8`) — no key-file path strings, no `assets/` names, no `.key`/`.keydb` literals. [OBS]
2. The EU build's `base.apk` dex contains **no** `SakeJNI` reference at all, and no `com/medtronic/minimed/sake` package. The JNI class must ship in a code-split or dynamically loaded dex. [OBS] This is a **build-variant difference**, not evidence about keys.

---

## 6. Cipher identification — AES-128-CTR confirmed

### 6.1 Structural evidence

| Observation | Offset | Meaning |
|---|---|---|
| Standard Rijndael S-box | `0x5bf8` | AES encrypt |
| **Inverse** S-box | `0x7cf8` | AES decrypt — so ECB decrypt exists (permit path) |
| 4 × 256-word T-tables | `0x5cf8`, `0x60f8`, `0x64f8`, `0x68f8` | Table-driven AES round |
| CRC32 table (reflected) | `0x807c` | Key-DB integrity |
| 5 S-box `adr` sites | `0x15564`, `0x1563c`, `0x15774`, `0x15974`, `0x15df4` | The AES core, all in `.text 0x15000–0x15E00` |
| Key expansion with 10/12/14 rounds | `0x154a0` | `cmp w2,#0x80→10`, `#0xc0→12`, `#0x100→14` |

`0x154a0` is `aes_setkey_enc` in all but name: it accepts 128/192/256-bit keys, selects `Nr` = 10/12/14, stores `Nr` at `[x0]`, the round-key pointer at `[x0,#8]`, and copies key words into a **0x110-byte** context (cleared by `0x15458`, which writes 9 × 16 B `stp q0,q0`). `0x158cc` is the matching `aes_setkey_dec`. [OBS]

The `adr x9,#0x5bd0` at `0x15558` plus S-box at `0x5bf8` confirms the round-constant array sits immediately before the S-box — textbook table-driven AES layout.

### 6.2 CMAC identification — the GF(2^128) doubling is present

The distinguishing signature of CMAC subkey generation is the conditional `Rb` XOR: shift the 128-bit block left one bit, and if the shifted-out MSB was 1, XOR the low byte with `0x87`. Both constants appear at **`0x16ac8` (`#0x1b`)** and **`0x16ad8` (`#0x87`)** inside the CMAC core at `0x169a0`, alongside a second pair at `0x16b40`/`0x16b48` for the `L`-derivation copy. [OBS]

That is unambiguous CMAC-AES per **RFC 4493** — it cannot be HMAC (no `0x36`/`0x5c` pad runs anywhere) nor GMAC (no carry-less multiply instructions). The core at `0x169a0` loads the cipher at `[x0]`, subkey at `[x0,#0x48]`, and `mac_len` from `[x9,#0x20]`.

### 6.3 CTR identification — 16-byte block with big-endian increment

The stream primitive at **`0x163dc`** is:

```
0x163f8  ldr  x26, [x2]          ; stream position 0..15
0x16424  ldrb w8, [x21], #1      ; next plaintext byte
0x16428  ldrb w9, [x22, x26]     ; keystream[pos]
0x16430  eor  w8, w9, w8         ; XOR
0x16438  and  x26, x9, #0xf      ; pos = (pos+1) & 15
0x16448  bl   0x15b24            ; AES encrypt the counter block
0x16458  mov  w8, #0x10          ; 16-byte counter
0x1645c  ldrb w9, [x27, w8]      ; byte[i]
0x16460  add  w9, w9, #1         ; ++byte
0x16464  strb w9, [x27, w8]
0x16468  subs w8, w8, #1         ; walk i downward
0x1646c  tbz  w9, #8, done       ; stop unless carry out
0x16470  b.hi 0x1645c            ; propagate carry
```

This is **AES-CTR with a full 16-byte big-endian counter** (increments from byte 15 downward, carrying). It is *not* GCM (no GHASH), *not* CCM (no separate CBC-MAC length encoding), and *not* a 12-byte-nonce construction — the whole block is the counter. [OBS]

### 6.4 The nonce construction — prior art confirmed exactly

`Sake_Client_SecureForSending` (impl `0x13c38`) builds the counter block:

```
0x13c68  ldr  x8, [x0, #8]       ; 64-bit msg counter
0x13c6c  lsr  x9, x8, #0x28      ; reject counter >= 2^40
0x13c74  lsr  x9, x8, #0x1f      ; byte0 = counter>>31
0x13c78  lsr  x10, x8, #0x17     ; byte1 = counter>>23
0x13c7c  ldr  d2, [x0, #0x28]    ; 8-byte session nonce
0x13c90  lsr  x9, x8, #0xf       ; byte2 = counter>>15
0x13c98  lsr  x10, x8, #7        ; byte3 = counter>>7
0x13ca0  ldr  w9, [x0]           ; mode (0=client, 1=server)
0x13cb0  cset w9, ne
0x13cb8  orr  w9, w9, w8, lsl #1 ; byte4 = (counter<<1) | mode
0x13cc4  ext  v0.16b, v0.16b, v2.16b, #0xb
0x13cd0  tbl  v0.16b, {v0,v1}, v2
0x13cdc  str  q0, [sp]           ; 16-byte counter block
0x13ce0  bl   0x13ea8            ; EncryptAndSign
0x13cec  ldr  x9, [x20, #8]
0x13cf0  add  x9, x9, #1         ; ++counter, only on success
```

The 16-byte counter block is `[5-byte BE ((counter<<1)|mode)] || [8-byte nonce] || [3 zero bytes]`.

This is **exactly** the prior-art claim — *"CTR nonce encodes: (mode & 1) | (counter << 1) as 5-byte big-endian"*, *"single 64-bit counter per SAKE_SECURE_LINK_S, +1 per msg"*, *"mode=0 for client, mode=1 for server"*. Independently derived from disassembly, it matches. [OBS] confirms [PUB].

**`SAKE_SECURE_LINK_S` layout (48 bytes):**

| offset | field |
|---|---|
| `0x00` | `mode` (u32): 0 = client, 1 = server |
| `0x08` | `counter` (u64), `+1` per message, capped below 2^40 |
| `0x10` | reserved |
| `0x18` | AES session key (16 B) |
| `0x28` | session nonce (8 B) |

### 6.5 Key derivation

`0x138f0` derives the session key: it gathers client challenge (`[x22]`), server challenge (`[x21]` via `ldr q0`) and an 8-byte nonce, assembles 32 bytes at `[sp,#0x10]` (`stp x8,x9` + `str q0`), then calls `0x150ec` (the CTR/ECB wrapper) with `w2 = #0x20` (32 bytes). [OBS] This matches the prior-art `AES-ECB(derivation_key, server_key_material || client_key_material)` producing a 32-byte output, of which 16 bytes become the AES key and 8 the nonce.

### 6.6 Verdict

**AES-128-CTR with truncated CMAC-AES authentication is CONFIRMED** — not merely consistent with prior art but structurally proven by six independent artefacts (S-box, inverse S-box, T-tables, 10/12/14-round key schedule, `0x87`/`0x1b` CMAC doubling, 16-byte BE counter increment).

However, the library is **generic over AES-128/192/256** (§6.1). SAKE's compiled-in key sizes select 128-bit at runtime; the cipher-name strings `"AES-128-CTR"` (`0x566f`), `"AES-192-CTR"` (`0x59df`), `"AES-256-CTR"` (`0x52a5`), `"AES-128-ECB"` (`0x55f4`), `"AES-192-ECB"` (`0x5299`), `"AES-256-ECB"` (`0x52d6`) appear in `.rodata` as algorithm-descriptor names in the table at `0x26c20`–`0x26d88`. Calling it "AES-128" describes the SAKE configuration, not a limitation of the primitive. [OBS]

### 6.7 SRP — a second, version-gated key-agreement path (corrected finding)

The binary contains a full **SRP-6a** implementation, contrary to my initial read and to prior art's coverage. Components, all `[OBS]`:

| Component | Offset | Evidence |
|---|---|---|
| RFC 5054 1024-bit N | `0x7df8` (128 B) | byte-exact match to the published RFC 5054 group |
| g = 2 | `0x7e78` (1 B = `0x02`) | passed as `adr x3,#0x7e78` with `mov w4,#1` — g length is 1 byte |
| g = 2 (alt, LE u32) | `0x7ef8` | `02000000`, immediately before the K table |
| SHA-256 K table (64 words) | `0x7efc` | all 64 values, little-endian; xref at `0x18b00` |
| SHA-256 compression | `0x18b00` | full round: `ror #6/#11/#25` (Σ1), `ror #2/#13/#22` (Σ0), `bic`+`orr` (Ch/Maj) |
| SRP core | `0x17020` | calls `0x18e1c`, `0x170ec`, `0x191ec` |
| SRP client init | `0x1730c` | `adr x1,#0x7df8` (N), `adr x3,#0x7e78` (g), `mov w2,#0x80`, `mov w4,#1`, `mov w6,#0x10` |
| Bignum/modexp | `0x18774`, `0x18e1c`, `0x1920c`, `0x1ae90`, `0x1a5a8` | mul + Montgomery-style reduction; 256≤bits≤1024 guard at `0x192a0`/`0x192b0` |

The `mov w6,#0x10` and the `#0x200`/`#0x400` bounds checks at `0x192a0`/`0x192b4` confirm a 1024-bit modulus with 256-bit-minimum inputs — SRP-6a over the 1024-bit group, i.e. the classic RFC 5054 configuration.

**When it runs:** only when `protocolVersion == 2`. The gate is explicit and appears 11 times across the client and server state machines:

```
0x12c10  ldr  w8, [x20, #4]        ; SAKE_CLIENT_S.protocolVersion
0x12c14  cmp  w8, #2
0x12c18  b.ne 0x12cac              ; pv != 2  ->  return state 5 (skip SRP)
0x12c1c  ldr  x0, [x20, #0x80]     ; pMEmory
0x12c24  bl   0x14118              ; verify peer's SRP message
0x12c3c  ldr  x8, [x20, #0x80]
0x12c40  add  x0, x8, #0x98        ; client SRP state
0x12c44  add  x1, x8, #0x408       ; server SRP state
0x12c48  bl   0x17020              ; SRP-6a shared-secret computation
0x12c50  mov  w0, #4               ; -> state 4
```

`protocolVersion == 1` takes the CTR/CMAC-only path documented by prior art; `== 2` additionally performs an SRP-6a exchange before the permit step. The SRP state lives inside `SAKE_CLIENT_MEMORY_S` at `+0x98`, server side at `+0x408`, which is why the client `memory` blob is 0x370 bytes and the server's 0x368.

**Correction to §3.6 and §8:** errors 21 ("The password authenticated key exchange could not be completed") and 23 ("The messages exchanged between the client and server could not be hashed") are **not** legacy — they are the live SRP-path and SHA-256-path failures for protocol version 2. The `srp` struct member is actively used.

**Prior art gap:** `PythonSake` implements only the `protocolVersion == 1` flow. It does not model SRP, does not contain the RFC 5054 group, and its `check_len`/state stages skip this branch entirely. **A pump or app negotiating protocol version 2 cannot be driven by the published PythonSake implementation** — this is a real functional gap in the prior art, not a documentation omission.

---

## 7. Message constants

| Constant | Value | Symbol / offset | Basis |
|---|---|---|---|
| Handshake message size | **20 bytes**, enforced | `0x132bc: cmp x10,#0x14; b.ne` in `check_len` `0x1328c` | [OBS] |
| Challenge | **8 bytes** | `clientChallenge` getter allocates `#8` @ `0x11948` | [OBS] |
| Initialization vector | **4 bytes** per side | IV getter allocates `#4` @ `0x11ad8` | [OBS] |
| Session nonce | **8 bytes** | `ldr d2,[x0,#0x28]` @ `0x13c7c` | [OBS] |
| AES key | **16 bytes** | key @ `[SecureLink+0x18]`, CTR block size `#0x10` | [OBS] |
| CTR counter block | **16 bytes** | `mov w8,#0x10` @ `0x16458` | [OBS] |
| CMAC handshake tag | **8 bytes** (`mac_len=8`) | `cmac8` path `0x13828` | [OBS] |
| **Wire tag** | **2 bytes** | `ldrh w9,[sp]` → `sturh w9,[x8,#-2]` @ `0x13f70`/`0x13f84` | [OBS] |
| Wire sequence byte | **1 byte**, `counter & 0xFF` | `sturb w23,[x8,#-3]` @ `0x13f78` | [OBS] |
| Min secure message | **3 bytes** | `MIN_SAKE_SECURE_MESSAGE_BYTE_COUNT` = 3 | [OBS] |
| Max secure message | **64 bytes** | `MAX_..._BYTE_COUNT` = 0x40 | [OBS] |
| Max user (plaintext) | **61 bytes** | `MAX_SAKE_USER_MESSAGE_BYTE_COUNT` = 0x3d | [OBS] |
| Permit | **20 bytes** | `Permit_Init` allocates `#0x14` @ `0x11404` | [OBS] |
| Permit plaintext core | **12 bytes** | `mov w2,#0xc` @ `0x146f4` (ver, devtype, flags) | [OBS] |
| Permit proprietary area | **10 bytes** | `SAKE_PERMIT_PROPRIETARY_BYTE_COUNT` = 0xa | [OBS] |
| Passkey | **16 bytes** max | `SAKE_PASSKEY_BYTE_CAPACITY` = 0x10 | [OBS] |
| Static keys per device | **5 × 16 = 80 bytes** | `SAKE_KEY_DATABASE_REMOTE_DEVICE_KEY_COUNT` = 4 (+type byte = 81) | [OBS] |
| Key-DB header | **6 bytes** | `HEADER_BYTE_COUNT` = 6 | [OBS] |
| Key-DB entry | **81 bytes** | `#0x51` @ `0x141d0` | [OBS] |
| Device types | **1..8** | `cmp w8,#8; cset lo` @ `0x14174` | [OBS] |
| Protocol versions | enumerated | `SAKE_PROTOCOL_VERSION_E` (null-deref guard @ `0x5767`) | [OBS] |
| RNG source | `/dev/urandom` | 3 `adr` refs @ `0x21584`, `0x21a8c`, `0x228c8` | [OBS] |

### 7.1 Wire format of a secure message

```
  +---------------------------+--------+--------+
  | AES-CTR ciphertext        | seq B  | tag 2B |
  | (1..61 bytes)             | (1 B)  | (2 B) |
  +---------------------------+--------+--------+
  total = plaintext_len + 3,  min 3, max 64
```

From `0x13f6c`–`0x13f84`: buffer length is set to `ciphertext_len + 3` (`add x9,x8,#3` @ `0x13ef4`), then the sequence byte is written at `[-3]` and the 2-byte tag at `[-2]`. Only **2 bytes of the 16-byte CMAC** are transmitted — a 65,536-fold reduction in authentication strength versus full CMAC. [OBS]

`Sake_SecureMessage_GetSequenceNumber` (`0x13e6c`) reads `[msg+len-3]` and additionally enforces `len-3 <= 0x3d`, i.e. 3..64. [OBS]

### 7.2 Handshake message field maps

The six messages are all 20 bytes. Field positions below are **[PUB]** from `pysake/session.py`, consistent with the 20-byte enforcement and the 8/8/4/4 split I measured **[OBS]**:

| # | Dir | Layout |
|---|---|---|
| 0 | S→C | `[0]` server device type, `[1]`=1, rest padding |
| 1 | C→S | `[0:8]` client key material, `[8]` client device type, `[9:13]` client nonce |
| 2 | S→C | `[0:8]` CMAC8 tag, `[8:16]` server key material, `[16:20]` server nonce |
| 3 | C→S | `[0:8]` CMAC8 tag, `[8:20]` filler |
| 4 | S→C | AES-CTR encrypted permit (20 B ciphertext + 3 B trailer = 23 B on air) |
| 5 | C→S | AES-CTR encrypted permit (20 B ciphertext + 3 B trailer = 23 B on air) |

Messages 4 and 5 carry `SAKE_PERMIT_S` (20 bytes) inside a secure message, so they are 23 bytes on the wire while still passing the 20-byte `check_len` after decryption. [OBS]/[INF]

### 7.3 Device types

From `device_types.py` [PUB], and confirmed as the 1..8 range enforced at `0x14170`: `1`=InsulinPump, `2`=GlucoseSensor, `3`=BloodGlucoseMeter, `4`=MobileApplication/SecondaryDisplay, `5`=CareLinkUploadApplication, `6`=FirmwareUpdateApplication, `7`=DiagnosticApplication, `8`=PrimaryDisplay. [OBS] The bounds check `(v-1) < 8` proves the enum is exactly 8 wide.

### 7.4 Handshake state machine

Client `currentState` at `[+0x00]`; dispatch at `0x12ff8` (`cmp w8,#5 / #2 / #3 / #4`) with `lastError` at `[+0x88]`. Terminal states are 6 (success) and 0xA (failure) — see `0x130a8`–`0x130bc`, where `w0==6` and `w0==0xa` are handled specially and everything else returns via `cset/ne`. [OBS]

---

## 8. Error enum — 23 values, strings recovered

`Sake_HandshakeError_ToString` (`0x12938`) indexes a 23-entry pointer table at **`0x26b58`** for input 1..23, returning `"The handshake error is invalid"` (`0x5413`) otherwise. [OBS]

| # | String | rodata |
|---|---|---|
| 1 | No error has occurred | `0x5696` |
| 2 | The handshake interface was misused | `0x592c` |
| 3 | The synchronization message is invalid | `0x5456` |
| 4 | The challenge could not be generated | `0x52b1` |
| 5 | The challenge is invalid | `0x56ac` |
| 6 | The synchronization response could not be generated | `0x5639` |
| 7 | The synchronization response is invalid | `0x579b` |
| 8 | The remote device type is not supported | `0x55cc` |
| 9 | The challenge response of the remote device is invalid | `0x5331` |
| 10 | The challenge response could not be generated | `0x5950` |
| 11 | The challenge response could not be randomized | `0x5579` |
| 12 | The session key could not be derived | `0x57e4` |
| 13 | The session key could not be randomized | `0x5809` |
| 14 | The session key could not be used to receive the permit | `0x597e` |
| 15 | The permit could not be secured for sending | `0x54a6` |
| 16 | The permit could not be padded for sending | `0x5901` |
| 17 | The permit received is not padded | `0x56c5` |
| 18 | The permit received is invalid | `0x52e2` |
| 19 | The permit received is issued to a different device type | `0x5831` |
| 20 | The remote device used a protocol version that does not match | `0x54d2` |
| 21 | The password authenticated key exchange could not be completed | `0x5895` |
| 22 | The passkey exchanged between the devices is invalid | `0x56e7` |
| 23 | The messages exchanged between the client and server could not be hashed | `0x5250` |

`E_SAKE_HANDSHAKE_NO_ERROR` = **1** and `E_SAKE_HANDSHAKE_ERROR_INVALID` = **0** — note the enum is 1-based, so "no error" is truthy and "invalid" is falsy. `IsValid` is `(v-1) < 23` i.e. `1..23`. [OBS]

Errors 21 and 23 are the **live protocol-version-2 SRP/SHA-256 failure paths** — see §6.7. (An earlier draft of this document called them legacy; that was wrong.)

---

## 9. Import surface — all 21 are libc

```
__cxa_atexit  __cxa_finalize  __memcpy_chk  __open_2  __read_chk
__register_atfork  __stack_chk_fail  calloc  close  fclose  fgetc
fopen  free  malloc  memcmp  memcpy  memmove  memset  read
realloc  strcmp
```

**No crypto library is linked.** AES, CMAC, CRC32, SHA-256, and the SRP bignum stack are all self-contained in `.text`. Combined with the total absence of vendor strings (`mbed`, `openssl`, `Entrust`, `nCipher`, `Botan`, `wolfSSL`, `libsodium`, `tinycrypt` — all zero hits), the entire crypto stack is **Medtronic's own or an unattributed statically-linked third-party core**. Note `/dev/random` (`0x59ed`) and `AES-192-*`/`AES-256-*` strings are present but unreferenced by code — they belong to the generic crypto layer's full API surface, of which SAKE uses a subset. [OBS]

The presence of `fopen`/`fgetc`/`fclose` (callers at `0x228d4`/`0x228e8` only) is **not** key loading — those three are the `fopen`-based RNG fallback path adjacent to the `/dev/urandom` reads, and the sole `__read_chk` caller is at `0x1a3dc` (hashing-adjacent). `Sake_KeyDatabase_Open` takes a memory pointer, never a path (§5.3). [OBS]

---

## 10. Findings summary

**Confirmed [OBS]:**
1. **163 SakeJNI exports**, fully enumerated with addresses, sizes, and role groupings (§3, §4). The operational API is 16 functions; 74 are field accessors; 84 are JNI/ctypes glue and container management.
2. **The published OpenMinimed key databases are NOT in this build.** Zero matches for all three, in full, body-only, and per-key form, across the `.so` and the entire APK/XAPK/jadx bundle. This is a definitive negative.
3. **AES-128-CTR + truncated CMAC-AES confirmed structurally** from six independent artefacts, not inferred from prior art.
4. **Prior art's nonce construction is exactly right** — `(mode & 1) | (counter << 1)` as 5-byte BE, 8-byte nonce, 3 zero bytes, single +1-per-message counter.
5. **Prior art's key-DB format is exactly right** — 4-byte BE CRC32, 6-byte header, 81-byte entries, device types 1–8.
6. **Only 2 of 16 CMAC bytes are transmitted** (§7.1) — the single most security-relevant number here, and it is not in the prior art's prose.
7. **A full SRP-6a implementation exists and is reachable** (§6.7) on the `protocolVersion == 2` path: RFC 5054 1024-bit group at `0x7df8`, g=2 at `0x7e78`, complete SHA-256 (K table `0x7efc`, compression `0x18b00`), and a bignum/modexp stack. This is **absent from and unmodelled by** the published PythonSake prior art, which covers only protocol version 1. Errors 21/23 are live SRP-path failures, not legacy strings.

**Retracted mid-analysis:** I initially reported "no hash and no bignum code, SRP is vestigial." That was **wrong** — I had searched only big-endian encodings for the SHA-256 constants, and the K table is stored little-endian. §3.6, §6.7 and §8 carry the correction inline.

**This build is a protocol engine, not a key store [OBS]/[INF]:** it ships the complete SAKE state machine, cipher stack, formal key-DB schema, and CRC validator, but zero key bytes. Keys arrive via `Sake_KeyDatabase_Open(buf,len)` from outside. **I did not locate where they actually live** — the leading hypothesis is app-level provisioning into the SQLCipher store, and confirming that is out of scope for static analysis of this `.so`.

**Not established:** the 20-byte handshake field maps in §7.2 are prior art consistent with my measured sizes, not independently byte-verified against live traffic. The `SAKE_PROTOCOL_VERSION_E` and `SAKE_PERMIT_VERSION_E` enumerated values were not recovered (only their null-deref guards). Which AES width SAKE actually selects at runtime is inferred from prior art's 128-bit claim, not from a traced call.

---

### Artefacts written
- This specification: `libandroid-sake-lib.spec.md`
- Prior-art clone: `cache/scratch/pysake_prior/` (OpenMinimed/PythonSake @ main)
