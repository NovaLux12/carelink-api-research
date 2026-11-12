# SAKE on a live production artefact — protocol spec and two refutations (2026-11-12)

**Evidence class: OBSERVED** unless marked. Companion to
`2026-11-12-minimed-mobile-app/`, which records the artefact itself.

**Requests issued by this pass: 0.** Static analysis of a local binary plus
reading already-cloned public prior art. **Cap: 0 of a 0 cap — no request was
made.** **Delay:** the standing rule is ≥2 s between requests to the same host;
none was issued, so no spacing applies and none is claimed. **Methods:** no
`GET`, `OPTIONS` or `POST` was sent to any host.

The full specification is in [`SAKE-SPEC.md`](SAKE-SPEC.md) — 607 lines covering
all 163 JNI exports, every struct offset with its accessor vaddrs, the cipher
identification, and the key-database parser.

---

## 1. The headline is a refutation of this task's own premise

The brief for this pass assumed the published OpenMinimed key databases would be
found in the binary. **They are not, and the reason is structural.**

`libandroid-sake-lib.so` is a **protocol engine, not a key store**. It contains
the whole SAKE implementation — AES-128/192/256 key expansion, CTR, CMAC,
GF(2^128) doubling — plus a formal key-database *parser* with CRC32 validation,
and **no key material whatsoever**:

> Byte comparison against the published databases: **zero matches, full or
> partial.** Not in `base.apk`, not in the XAPK, not in any `.dex`, not in the
> arm64 library set. [OBSERVED]

Keys arrive at runtime in a `SAKE_KEY_DATABASE_S` buffer the app fills. So the
question "what are the keys" is not answerable from this artefact at all — it
moves to *who supplies them*, which is the app's packed layer (§4 here and in the
packer record).

## 2. What is confirmed, and it is a lot

Against `OpenMinimed/PythonSake` as prior art, the following are now
**structurally proven** rather than merely consistent:

| property | finding |
|---|---|
| cipher | **AES-128-CTR** with a 16-byte counter block — confirmed by six independent artefacts (S-box, inverse S-box, T-tables, key expansion, counter increment, nonce builder) |
| authentication | **CMAC-AES, truncated to a 2-byte tag** on the wire, with a sequence byte in the trailer |
| handshake message | **20 bytes**, hard-enforced |
| key database format | `[4-byte CRC][1-byte device type][1-byte count][n × 81 bytes]`, stride `0x51`, CRC over everything after the CRC field — matches prior art **byte for byte** |
| nonce construction | `(mode & 1) \| (counter << 1)` as 5-byte big-endian, 8-byte nonce, increment per message — the exact instruction sequence was recovered |
| `StaticKeys` | five 16-byte fields: `derivation_key`, `handshake_auth_key`, `permit_decrypt_key`, `permit_auth_key`, `handshake_payload` |

The handshake state structs were recovered field by field:
`SAKE_CLIENT_S` is **0x90 bytes**, `SAKE_SERVER_S` **0xC0** (the server carries an
extra 48-byte `temporarySecureLink`). Each field has a named setter and getter at
a known vaddr, which means the protocol can be stepped through without guessing.

## 3. A second key-agreement path: SRP, and it is live

**This corrects the analysis's own first pass**, and it is worth recording as a
method lesson.

The `srp` field in the handshake structs was first judged "dead weight — prior
art's protocol has no SRP". That was **wrong**. The binary contains a complete,
reachable **SRP** implementation:

- the **RFC 5054 1024-bit group prime N** at file offset `0x7df8`
- **g = 2** immediately after it
- a full **SHA-256** (K table at `0x7efc`, compression routine at `0x18b00`)
- a **bignum/modexp stack** (`0x18774` multiply, `0x18e1c`, `0x1920c`, `0x1ae90`,
  `0x1a5a8`)

SRP runs on the **`protocolVersion == 2`** path, reached from
`Sake_Client_Handshake` state 3 at `0x12c10`–`0x12c48`.

**Why the first pass missed it, in its own words:** *"I checked only big-endian
constant encodings, and the SHA-256 K table is stored little-endian. An
absence-of-constant check that can't fail is not evidence."* That is exactly the
failure mode this repository's method section warns about, caught in the act.

**Verified independently for this record:** the RFC 5054 N is at `0x7df8`, the
SHA-256 K table is at `0x7efc` in **little-endian**, and the AES S-box is at
`0x5bf8` with its inverse at `0x7cf8`. The spec's offsets are correct.

**So the app has two key-agreement paths**, one of which (`protocolVersion 2`,
SRP) uses a well-understood published algorithm rather than SAKE. Which path a
given pump negotiates is **not established**, but the existence of a
password-based SRP path in the client is significant: it implies the pump or the
server can authenticate with a credential rather than only a pre-shared key.

## 4. What this does and does not change

**Changes:** the SAKE implementation is now documented well enough to be
reimplemented — struct layouts, nonce construction, tag truncation and the
database format are all recovered. A community reimplementation no longer has to
reverse-engineer the library.

**Does not change:** the keys are still external. Two independent artefacts now
agree that no key material ships in the client — this binary, and the OpenMinimed
prior art, which obtains its databases from elsewhere. **So a working SAKE client
needs the key database supplied out-of-band, and how a device legitimately obtains
one is the next question, not a solved one.**

## 5. Not claimed

- Any key material. None was found and none is asserted.
- Which `protocolVersion` a 780G negotiates.
- That SRP is used for the server link rather than the pump link — the code path
  exists and is reachable; its peer is unproven.
- Any wire message body.
