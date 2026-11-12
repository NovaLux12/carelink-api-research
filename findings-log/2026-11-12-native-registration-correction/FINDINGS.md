# The uploader's native methods are registered at runtime — and my own advice was wrong twice (2026-11-12)

**Evidence class: OBSERVED** unless marked. This record corrects a
recommendation I made twice in this session, and it matters: acting on it would
have wasted a Rosetta install and a Java agent build that could not have worked.

**Requests issued by this pass: 0.** Static analysis plus one SSH session to a
host the operator had powered on, read-only. **Cap: 0 of a 0 cap — no request was
made to any vendor host.** **Delay:** the standing rule is ≥2 s between requests
to the same host; no vendor request was issued, so no spacing applies and none is
claimed. **Methods:** no `GET`, `OPTIONS` or `POST` was sent to any Medtronic
host. SSH was used only to list files and read headers.

---

## 1. ⚠ The correction: there is no dylib to run

I twice told the operator that the cheapest remaining move was to install
Rosetta 2 and run a Java agent calling `StringDecryptor.decryptString()` 442
times. **That would have failed.** The premise was that the 442 native methods
were implemented in `libuploader.dylib`, and they are not.

**Measured, against all four recovered dylibs:**

| library | `StringDecryptor` | `HttpClientCommunicator` | `solar/dataupload` |
|---|---|---|---|
| `libuploader.dylib` | **0** | **0** | **0** |
| `libSecureKeyBoxJava.dylib` | 0 | 0 | 0 |
| `libhidapi.dylib` | 0 | 0 | 0 |
| `libusb4java.dylib` | 0 | 0 | 0 |

And the install itself carries only four app-owned dylibs;
`libuploader.dylib` is the only Medtronic one. So **no artefact on the machine
implements those 442 methods** — a JVM would throw `UnsatisfiedLinkError` on the
first `decryptString` call, before any agent could read anything.

## 2. They are installed by a dispatcher, not by per-method symbols

Both `StringDecryptor` and `HttpClientCommunicator` have an `import uploader.Loader`
and exactly **one** call:

```java
// StringDecryptor, static initialiser
static {
    Loader.l(989279420);
    StringDecryptor.$uploader$COI();
}

// HttpClientCommunicator
Loader.l(-1036780515);
```

`StringDecryptor` declares **443** native methods and calls `Loader.l` **once**.
That asymmetry is the whole answer: `Loader.l` is not decrypting anything for one
method — it is **registering** the whole class's native table.

**The reverse-engineered evidence agrees.** `libuploader.dylib` exports:

```
_Java_uploader_Loader_l   at 0x780d30   (the only non-BRIL JNI export)
```

and **zero** occurrences of `JNI_OnLoad`, `RegisterNatives` or `JNI_OnUnload` as
strings. That combination — one exported `Loader_l`, no `RegisterNatives` string
— is the signature of a table-driven dispatcher that installs method bodies
itself, and `0x780d30` is exactly the address an earlier pass identified as the
entry to a 748 KB protected region with a flattened jump table.

**So the 1,370 native methods across 38 classes are installed at runtime by that
stub.** There is no symbol to link against and no file to hand to a JVM.

## 3. The jar-wide census is 12, not 429

| population | count |
|---|---|
| `Loader.l(<constant>)` call sites in `uploader.jar` | **12** |
| distinct constants | **12** |
| classes calling `Loader.l` | **12** |

The 429 figure in circulation belongs to the **Android app's** two packers
(`fblyyzyocs` 371 + `vdlbwnyfem` 25), not to the desktop uploader. Two different
mechanisms, two different counts, and they must not be quoted interchangeably.
**That is a second error I propagated** — I carried 429 across from the mobile
analysis into reasoning about the desktop client.

## 4. Why Rosetta would not have helped, on either count

Two independent reasons, and both are decisive:

1. **No implementation exists on the machine.** Rosetta makes an x86_64 binary
   *runnable*; it cannot conjure 442 method bodies that ship nowhere.
2. **`StringDecryptor` is not usable through `Loader.l` from outside.** A single
   `native void l(int)` whose argument is a per-class constant, with the real
   bodies installed by that call, means an agent cannot pass a `\uXXXX` index and
   get a string back — the public `decryptString` would only work once `Loader.l`
   had already run *and* the dispatcher had populated the table. Even then, the
   plaintext table it indexes lives in `__bss` and is built at runtime, as the
   earlier pass proved.

## 5. What this does not change

The earlier analysis of the decoder is unaffected and still stands: `decryptString`
takes a 16-bit **index**, not ciphertext (789 of 852 call sites pass a single
`\uXXXX`), the decoder at `0x7af6b0` is a 6-byte-state chained table cipher, and
its 64 KB substitution table is in `__bss` past EOF with 173 reads and zero
writes. **All of that remains true.** What is now dead is the idea that a live
process makes it easy — the difficulty was never only the cipher.

## 6. What would actually be needed

A runtime *dump* rather than a runtime *call*: attach to a **running uploader
process** and read the materialised table out of `__bss` once `Loader.l` has
executed and the dispatcher has populated it. That needs the uploader running,
which needs an x86_64 JVM (Rosetta), and it needs instrumenting the process —
`lldb` on `0x7af6b0` with the table base at `0xdbe490`, or a `Frida`-style read
of the mapped `__bss`.

**Order of operations, and it is the reverse of what I said before:**
1. Rosetta (`softwareupdate --install-rosetta`) — needed to *run* the client.
2. Launch the uploader so `Loader.l` executes.
3. Dump `__bss` around `0xdbe490` and the table at `0x84e6e0`.
4. *Then* the index→plaintext mapping is available.

Steps 2–4 are the work; step 1 was never the blocker on its own.

## 7. Not claimed

- That the uploader would run successfully even under Rosetta. Its own
  `InternetConnectionCheck` failed for a missing-Rosetta reason, but whether the
  rest of the client initialises cleanly is **unproven**.
- That the `__bss` dump succeeds. The table is built at runtime; whether it is
  ever fully populated before a decrypt call, and whether the memory is readable,
  are both untested.
- Any plaintext from the table.
