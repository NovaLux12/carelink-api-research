# XXTEA check — verification of the lane's claim, and a correction to my own

**Purpose:** the public zShield research (enovella's gist, AWAKE wiki) says
zShield self-decrypts the ELF body with **XXTEA**. The lane reported XXTEA
absent. That is the exact "absence check that can't fail" trap, so it was re-run
properly.

## Method

`capstone` with `skipdata=True` over the whole of `.text` for both engines, then
reconstructing every adjacent `mov`/`movz` + `movk` pair on the **same
register** to recover full 32-bit immediates, and testing for the XXTEA delta
`0x9E3779B9` (and its complement `0x61C88647`).

The first attempt used `md.disasm(data, base)` **without** `skipdata`, which
halted at the first undecodable word and decoded only **7,771 of 719,381**
instructions. That is a silent truncation — the scan would have reported a
negative having examined 1% of the file.

## Result — OBSERVED

```
=== libfblyyzyocs.so
  total slots=719,381  real insns=719,381  undecodable=0 (0.00%)
  XXTEA delta constructions: 0
  instructions naming 0x9e37 or 0x79b9: 3
    0x000b4ef4 movk w9,  #0x9e37, lsl #16
    0x0019c494 movk w11, #0x79b9, lsl #16
    0x00265104 mov   w8,  #0x9e37

=== libvdlbwnyfem.so
  total slots=249,027  real insns=249,027  undecodable=0 (0.00%)
  XXTEA delta constructions: 0
  instructions naming 0x9e37 or 0x79b9: 1
    0x000be760 movk w12, #0x79b9, lsl #16
```

## Two corrections, and the second is to my own working

**1. The lane's conclusion is right; its reasoning was not.** It justified the
negative partly on `.text` being "1.2% encrypted on disk". Measured: **`.text`
is 100% decodable — 0 undecodable words out of 719,381**. There is no encrypted
region. The 1.2% figure was capstone's decode failures on plaintext code, not
encryption, and no 4 KiB block in either `.text` exceeds entropy 7.5.

That matters because if the code *had* been encrypted, searching it for the
delta would have been the vacuous check. It wasn't — the code is plaintext, so
the delta search is a **real** negative. The conclusion is stronger than the
lane argued.

**2. I called a false positive.** Mid-check I saw `movk w9, #0x9e37` and
`movk w11, #0x79b9` and reported "found it". Wrong: those are two *separate*
constants in two *separate* functions, each pairing with a different low half
(`#0x8951` and `#0x7b85`), reconstructing `0x9e378951` and `0x79b97b85` — neither
is the delta. Reconstructing the pairs properly gives **zero** delta
constructions. A half-word match is not a constant match.

## What this establishes

**This build does not use an XXTEA outer layer**, and its native code is
plaintext. So zShield's documented ELF self-decryption is not present here — this
is a **different zShield configuration** (asset-only protection) rather than the
one in the public write-up.

Combined with the payload measurement — 2,356,173 B, entropy 7.99992, all
147,260 16-byte blocks distinct — the asset encryption is a **separate cipher
whose key is not in either binary**, and the 29.8M-candidate known-plaintext
oracle (with a working positive control) rules out a statically stored AES key.

**Static decryption of the `.szip` from the APK is not possible.** The packer
must be run, or the app must be instrumented at runtime.
