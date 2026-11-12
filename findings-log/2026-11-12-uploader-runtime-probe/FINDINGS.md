# Running the uploader for real: Rosetta, the DCP guard, and what actually blocks the dump (2026-11-12)

**Evidence class: OBSERVED.** This pass ran the CareLink uploader's own JVM on
the operator's Mac, under Rosetta 2, and executed a probe against its classes.

**Requests issued by this pass: 0.** No vendor host was contacted.
**Cap: 0 of a 0 cap — no request was made.** **Delay:** the standing rule is ≥2 s
between requests to the same host; no vendor request was issued, so no spacing
applies and none is claimed. **Methods:** SSH to the operator's own host was used
for install inspection and to run locally-compiled probe classes. No `GET`,
`OPTIONS` or `POST` was sent to any Medtronic host.

---

## 1. Rosetta 2 installed, and the JRE runs

`softwareupdate --install-rosetta --agree-to-license` **succeeded without an
administrative password** — worth recording, because it was assumed to need one.

```
oahd: RUNNING
$ .../jre/bin/java -version
openjdk version "1.8.0_462"
OpenJDK Runtime Environment (Zulu 8.88.0.19-CA-macosx) (build 1.8.0_462-b08)
OpenJDK 64-Bit Server VM (Zulu 8.88.0.19-CA-macosx) (build 25.462-b08, mixed mode)
```

The JVM starts, and it loads both jars: `uploader.jar` and `lib/skb.jar`. **So the
x86_64 JRE defect recorded earlier is now closed as an environment gap — Rosetta
fixes it, exactly as the `NativeLoader` reading predicted.**

## 2. `uploader.Loader` needs `System.load`, not `System.loadLibrary`

A plain `Class.forName("uploader.Loader")` succeeds, but calling `Loader.l(int)`
throws:

```
java.lang.UnsatisfiedLinkError: uploader.Loader.l(I)V
```

Neither `-Djava.library.path=...` nor adding the directory to the classpath fixes
it, because `Loader` never calls `System.load` itself — it is a bare
`public static synchronized native void l(int)`.

**Loading the dylib explicitly does work:**

```java
System.load("/Library/Application Support/Medtronic/CareLink/Uploader/DSS/lib/macos/x86_64/libuploader.dylib");
// -> System.load OK
```

and that export resolves — `_Java_uploader_Loader_l` is at `0x780d30` in that
file, as recorded earlier.

**But `System.loadLibrary(<name>)` is a dead end, and the reason is circular:**
the one call site in the whole jar is

```java
// ConnectAdapterPage.java:321
System.loadLibrary(StringDecryptor.decryptString("\u146b"));
```

— the library **name is itself encrypted**, so decrypting it requires the library
to be loaded first. That call site cannot be the path by which the app works.

## 3. Three classes load; `StringDecryptor` does not — and here is exactly why

With the dylib loaded by absolute path, class-by-class:

| class | result |
|---|---|
| `com.medtronic.diabetes.solar.Solar` | **loads** |
| `com.medtronic.diabetes.solar.dataupload.api.impl.rest.HttpClientCommunicator` | **loads** |
| `com.medtronic.diabetes.solar.dataupload.api.DataUploadConstants` | **loads** |
| `com.medtronic.diabetes.solar.utils.StringDecryptor` | **fails** |

`StringDecryptor` resolves as a class and its **443 native declarations are
visible** (`decryptString` reports as `public static native`), but invoking it
throws, and the root cause is precise:

```
java.lang.ExceptionInInitializerError
  ROOT: java.lang.NullPointerException
    at com.medtronic.diabetes.solar.utils.StringDecryptor.$uploader$COI(Native Method)
    at com.medtronic.diabetes.solar.utils.StringDecryptor.<clinit>(StringDecryptor.java)
```

**`$uploader$COI()` is the DCP integrity hook** — the same synthetic native that
appears in `SecurityUtils`, `EncryptedString` and every `SecurityCallbacks`
holder. It is the first statement of the static initialiser, it runs **before**
`Loader.l(...)`, and it throws `NullPointerException` from native code unless the
runtime state it validates has been established.

That is the wall. It is not a missing library and not an architecture problem —
it is an **anti-tamper initialiser that expects the launcher's own startup
sequence**, and a bare `Class.forName` from a probe does not provide it.

## 4. What the run did yield

**`Solar.UPLOADER_URI_PATTERN` is a public static field and reads out:**

```
^([^:]+)://([^/]+)/([^/]+)(/([^/]*)(/([^/]+))?)?
```

That is the **URI template the uploader validates its server against** — a
`scheme://host/base` decomposition with optional path segments. It is the closest
thing recovered so far to a statement about what a valid uploader endpoint looks
like, and it is a regex, not a route: it constrains *shape*, not destination.

`Solar.EXPANDED` reads as `expanded`.

`DataUploadConstants` loads cleanly and exposes:

```
PATTERN_DATE_RFC3399 = yyyy-MM-dd'T'HH:mm:ss[.SSS]X
iIIiiiiiiIIIII(Object) -> String   // the Java-side XOR routine
```

The XOR routine uses `^0x50` / `^0x4F` alternating from the end of the string —
confirming the earlier static read. It has **zero call sites in the jar**, so it
decrypts nothing on its own.

## 5. The real path to a dump, and why it is harder than "run it"

`$uploader$COI` gating `<clinit>` means the decryptor cannot be reached by
instantiating the class from outside. The options, cheapest first:

1. **Launch the genuine app** (`CareLinkLauncher.app` → `Uploader.bundle`) so its
   own startup satisfies the guard, then attach. The launcher hardcodes
   `.../DSS/lib/macos/x86_64/libuploader.dylib` and runs a code-signature
   validation, so it does the whole sequence the probe cannot.
2. **Attach `lldb`** to that live process and break on `0x7af6b0` (the decoder)
   with the substitution table base at `0xdbe490`, or read `__bss` around it once
   the table is populated. `lldb` is present at `/usr/bin/lldb`.
3. Only then is the index→plaintext map available.

**What is now known to be unnecessary:** more static work on the desktop
`StringDecryptor`. The mechanism is understood; what is missing is a populated
runtime table, and that only exists inside a correctly-started process.

## 6. Debugging notes worth keeping

- **The JRE ships no `javac`.** Probe classes must be compiled elsewhere and
  copied in; `javac --release 8` on a JDK 17 produces class files the Java 8 JRE
  accepts.
- **`Class.forName` caches a failed initialiser.** A second attempt throws
  `NoClassDefFoundError: Could not initialize class ...` with no cause. Use
  `Class.forName(name, false, loader)` to resolve without initialising, then
  invoke, to see the true root exception.
- **SLF4J warns loudly** (`MedicalLoggerProvider could not be instantiated`) but
  is harmless — it falls back to a NOP logger. It is noise, not a fault.
- **`System.load` with an absolute path works; `-Djava.library.path` does not**,
  because nothing calls `System.loadLibrary` on the success path.

## 7. Not claimed

- Any decrypted string. None was obtained.
- That launching the real app satisfies `$uploader$COI` — **untested**, and it is
  the next thing to try.
- That `UPLOADER_URI_PATTERN` describes the production endpoint. It is a shape.
- That the uploader would complete a real upload. Only the JRE start and three
  class loads were exercised.
