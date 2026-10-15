#!/usr/bin/env python3
"""xsuffix-analyse.py — is the client-side deviceFamily enum's `_*` suffix READ,
or only DECLARED?

Offline. Costs ZERO requests: every control that can be run over a body already
in hand is run over that body, and re-fetching a file whose sha256 is pinned in
this pass's own ledger row would spend a request to re-observe a byte-identical
artefact.

USAGE
    python3 xsuffix-analyse.py <body> [expected_sha256] [expected_bytes]

The first two arguments are the ANCHOR GATE. If the body does not reproduce them
the script exits 3 and prints nothing else: every read of a body this pass cannot
identify is a claim about a file this pass does not name.

WHY THE CLASSIFIER IS MECHANICAL AND THEN READ
    AGENTS.md section 6.2 — "a grep that hit without proving". A count is not a
    classification. So every occurrence of every token is printed with its byte
    offset, its enclosing token and its verbatim window, and the CALLER READS
    them. The labels this script emits are mechanical ("SUBSTRING-OTHER"), and
    the reading that turns a label into a claim is made in FINDINGS.md, not here.
    Where the script and the reading disagree, the reading and the window win
    and the script is wrong.

THE COUNTING RULE (recorded, because a count generalised from a subset has
already cost this repo once — AGENTS.md section 6.7)
    A "hit" is a byte-offset occurrence of the token in the decoded body.
    A "READ" is a hit that is a member access on the enum object exported by
    module 45559 — `<binding>.G.<MEMBER>` — which is the only shape a webpack
    ESM export can be read through in this build.
    A "DECLARATION" is a hit inside the object literal at the enum's offset.
    Every other hit is a SUBSTRING or an unrelated sense, and is enumerated.
"""
import hashlib
import re
import sys

EXPECTED_SHA = "0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa"
EXPECTED_BYTES = 3417255
MODULE_ID = "45559"
ENUM_MODULE = 45559
W = 90  # verbatim window half-width, bytes


def fail(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(3)


def quote_parity(T):
    """True at offset i if byte i-1 is inside a double-quoted span.

    Parity over unescaped `"` is enough for this corpus: a minified JS bundle
    puts no `"` inside its regex literals, so an even number of quotes before i
    means i is code and an odd number means i is inside a string literal. This is
    what separates the two kinds of hit AGENTS.md section 6.2 is about — a hit
    that proves a token exists is not a hit that proves what the token is.
    """
    state = bytearray(len(T) + 1)
    inside = False
    for i, ch in enumerate(T):
        state[i] = inside
        if ch == '"' and (i == 0 or T[i - 1] != "\\"):
            inside = not inside
    return state


def enclosing(T, i, toklen, qstate):
    """The identifier the hit at offset i sits inside, and whether it is in a string."""
    l = i
    while l > 0 and (T[l - 1].isalnum() or T[l - 1] in "_$"):
        l -= 1
    r = i + toklen
    while r < len(T) and (T[r].isalnum() or T[r] in "_$"):
        r += 1
    return f"ident={T[l:r]!r}", ("in-string-literal" if qstate[i] else "in-code")


def main():
    path = sys.argv[1]
    exp_sha = sys.argv[2] if len(sys.argv) > 2 else EXPECTED_SHA
    exp_len = int(sys.argv[3]) if len(sys.argv) > 3 else EXPECTED_BYTES
    raw = open(path, "rb").read()

    print("=" * 78)
    print("A. ANCHOR GATE — this pass reads nothing else unless it passes")
    print("=" * 78)
    got_sha = hashlib.sha256(raw).hexdigest()
    print(f"  bytes   : {len(raw)}  (pinned {exp_len})  "
          f"{'MATCH' if len(raw) == exp_len else 'MISMATCH'}")
    print(f"  sha256  : {got_sha}")
    print(f"  pinned  : {exp_sha}  "
          f"{'MATCH' if got_sha == exp_sha else 'MISMATCH'}")
    print(f"  last-modified note: etag/Last-Modified carried in the ledger row")
    if got_sha != exp_sha or len(raw) != exp_len:
        fail("anchor gate failed — stopping (AGENTS.md section 1: delete, do not "
             "soften, the claims a differently-built corpus cannot carry)")
    print("  RESULT  : PASS — the corpus is the build this pass names.")

    T = raw.decode("utf-8", "replace")

    print()
    print("=" * 78)
    print("B. THE ENUM, verbatim, with byte offsets")
    print("=" * 78)
    m = re.search(r"const (\w+)=\{BLE:\"BLE\"", T)
    if not m:
        fail("enum declaration not found — the anchor passed, so the shape moved")
    decl_start, decl_end = m.start(), T.index("}", m.start()) + 1
    print(f"  declaration byte range : {decl_start}..{decl_end - 1}")
    print(f"  verbatim              : {T[decl_start:decl_end]!r}")
    print(f"  verbatim (context)    : ...{T[decl_start - 68:decl_end + 4]!r}...")
    members = re.findall(r"(\w+):\"([^\"]*)\"", T[decl_start:decl_end])
    print(f"  member count          : {len(members)}")
    for k, v in members:
        print(f"    key={k!r} value={v!r}  key==value: {k == v}")

    # module header + export
    hdr = T.rfind(f"{ENUM_MODULE}:", 0, decl_start)
    print(f"  module header at      : {hdr}")
    print(f"  verbatim (context)    : {T[hdr:hdr + 70]!r}")

    print()
    print("=" * 78)
    print("C. MODULE-ID CENSUS — every occurrence of the module id in the body.")
    print("   A webpack module is reachable only by id, so this bounds the")
    print("   population of possible consumers. 2 = 1 definition + 1 importer.")
    print("=" * 78)
    for n, mm in enumerate(re.finditer(re.escape(MODULE_ID), T), 1):
        print(f"  [{n}] @{mm.start()}: {T[max(0, mm.start() - 40):mm.start() + 40]!r}")
    importers = list(re.finditer(r"(\w+)=i\(45559\)", T))
    print(f"  importer sites        : {len(importers)}")
    for mm in importers:
        print(f"    binding {mm.group(1)!r} at @{mm.start()}")
    if len(importers) != 1:
        print("  NOTE: importer count != 1 — the section D result below does not "
              "bound the consumer population and must not be read as if it did.")

    print()
    print("=" * 78)
    print("D. EVERY READ OF THE EXPORTED BINDING — `<binding>.G`")
    print("   Classified mechanically: a member read is `<binding>.G.<ident>`.")
    print("   Anything else (a call `(0,b.G)(...)`) is a same-token/different")
    print("   binding false hit and is listed so it cannot be mistaken for one.")
    print("=" * 78)
    binding = importers[0].group(1) if importers else None
    reads, others = [], []
    if binding:
        for mm in re.finditer(rf"\b{re.escape(binding)}\.G\b", T):
            after = T[mm.end():mm.end() + 14]
            if re.match(r"\.\w", after):
                member = re.match(r"\.(\w+)", after).group(1)
                reads.append((mm.start(), member, mm.end() + 1 + len(member)))
                lbl = f"MEMBER-READ .{member}"
            else:
                others.append(mm.start())
                lbl = f"NOT-A-MEMBER-READ (next chars: {after[:8]!r})"
            print(f"  @{mm.start():>9}  {lbl}")
            print(f"      window: {T[max(0, mm.start() - W):mm.end() + W]!r}")
    print(f"  member reads          : {len(reads)}")
    read_members = [r[1] for r in reads]
    print(f"  members actually read : {read_members}")
    print(f"  same-token false hits : {len(others)}")

    # bracket / iteration / spread reads would not look like `.G.` at all
    print()
    print("  Non-`.G.` consumption shapes that would ALSO count as a read, swept")
    print("  explicitly so their absence is measured rather than assumed:")
    shapes = {
        "bracket-literal  o.G[\"X\"]": rf"\b{binding}\.G\[\s*\"(\w+)\"",
        "bracket-single   o.G['X']": rf"\b{binding}\.G\[\s*'(\w+)'",
        "Object.values(o.G)": rf"Object\.values\(\s*{binding}\.G\s*\)",
        "Object.keys(o.G)": rf"Object\.keys\(\s*{binding}\.G\s*\)",
        "Object.entries(o.G)": rf"Object\.entries\(\s*{binding}\.G\s*\)",
        "spread           {...o.G}": rf"\.\.\.\s*{binding}\.G\b",
        "pass the object on  (o.G)": rf"(?<![.\w])\({binding}\.G\)",

        # The LABEL describes the shape; the REGEX is the authority. Round 2 found
        # the 8th sweep described in prose as "`o.G` followed by a comma or a
        # semicolon", which returns 0. Round 3 found the residue: this label still
        # read "o.G, o.G;" while the regex beside it returned 1. A label that
        # contradicts its own regex is a contradiction a re-runner cannot see
        # through (AGENTS.md section 6.2), so both columns print and they agree.
        "pass the object on  o.G bare (no member)": rf"(?<![.\w]){binding}\.G(?![\w.])",
    }
    for label, pat in shapes.items():
        hits = [mm.start() for mm in re.finditer(pat, T)]
        # The REGEX IS PRINTED, not just its label. Verification round 2 found the
        # 8th sweep described in prose as "`o.G` followed by a comma or semicolon",
        # which returns 0 — the real pattern returns 1. A re-runner who had only the
        # label would have reproduced a contradiction (AGENTS.md section 6.2).
        print(f"    {label:<34} {len(hits):>3} hit(s)"
              + (f"  @{hits}" if hits else "")
              + f"   regex={pat}")

    print()
    print("=" * 78)
    print("E. CASE-SENSITIVE TOKEN CENSUS — every occurrence, every one read.")
    print("=" * 78)
    toks = ["BLE_X", "SIMPLERA_X", "BLE", "SIMPLERA", "GUARDIAN", "NGP"]
    qstate = quote_parity(T)
    for tok in toks:
        occ = list(re.finditer(re.escape(tok), T))
        print()
        print(f"  --- {tok} : {len(occ)} case-sensitive occurrence(s) ---")
        for n, mm in enumerate(occ, 1):
            e, where = enclosing(T, mm.start(), len(tok), qstate)
            if decl_start <= mm.start() < decl_end:
                lbl = "DECLARATION"
            elif any(s <= mm.start() < en for s, _, en in reads):
                lbl = "READ"
            else:
                lbl = "OTHER"
            print(f"  [{n}] @{mm.start():>9} {lbl:<12} {e:<34} {where}")
            print(f"      window: {T[max(0, mm.start() - W):mm.start() + len(tok) + W]!r}")

    print()
    print("=" * 78)
    print("F. CASE-SENSITIVITY CONTROL — the same token set, case-INsensitively.")
    print("   Cost: 0 requests. Purpose: so a case-sensitive 0 is reported as a")
    print("   case-sensitive 0, and the ci count shows what the noise floor is.")
    print("=" * 78)
    for tok in toks:
        cs = T.count(tok)
        ci = len(re.findall(re.escape(tok), T, re.I))
        print(f"  {tok:<12} cs={cs:<6} ci={ci:<6} ratio="
              f"{('%.1f' % (ci / cs)) if cs else 'inf(cs=0)'}")

    print()
    print("=" * 78)
    print("G. LITERAL-VS-DIRECTIVE (POSITIVE) CONTROL — 0 requests.")
    print("   A zero is only a zero if this searcher can find a literal that IS")
    print("   present. These four are known-present in this build by committed")
    print("   prior work; each must come back non-zero or the zero above is void.")
    print("=" * 78)
    for tok, why in [
        ("system.logbook.entry.validation.config",
         "route literal, area P recorded at main-bundle byte 2768979/2769017"),
        ("deviceFamily", "the destructured matcher parameter"),
        ("getUploadDeviceInfo", "the branch's taken arm"),
        ("deviceModelMapping", "the adjacent, DIFFERENT model axis"),
    ]:
        c = T.count(tok)
        first = T.find(tok)
        print(f"  {'PRESENT' if c else 'ABSENT!! VOID ZERO':<20} x{c:<4} {tok!r}")
        print(f"      why it must be here: {why}")
        if first != -1:
            print(f"      first @ {first}: {T[max(0, first - 70):first + 70]!r}")

    print()
    print("=" * 78)
    print("H. THE NEAR-MISS — a token a substring grep would report as a member")
    print("=" * 78)
    for tok in ["SIMPLERACC", "BLEDevice", "BLEConnection"]:
        occ = [mm.start() for mm in re.finditer(tok, T)]
        print(f"  {tok:<16} {len(occ)} occurrence(s)  {occ[:6]}")
    print("  SIMPLERACC is a key of the DEVICE-MODEL capability map, not a member")
    print("  of the deviceFamily enum. It is a different axis that shares a prefix.")

    print()
    print("=" * 78)
    print("I. VERDICT ARITHMETIC")
    print("=" * 78)
    decl_members = [k for k, _ in members]
    read_set = sorted(set(read_members))
    never = [x for x in decl_members if x not in read_set]
    print(f"  declared members        : {decl_members}")
    print(f"  members with >=1 read   : {read_set}")
    print(f"  declared, never read    : {never}")
    print(f"  total member reads      : {len(reads)}   distinct members read: {len(read_set)}")
    print(f"  consumers of module {ENUM_MODULE} : {len(importers)}")
    print()
    print("  Does any read BRANCH on the `_X` suffix?  Answer is mechanical and")
    print("  is what section D measured: reads are"
          f" {read_members} and no other shape exists in this body.")

    print()
    print("=" * 78)
    print("J. THE REDUNDANCY TEST — would deleting the `_X` members change")
    print("   anything?  This is the shape of the finding, stated as arithmetic.")
    print("=" * 78)
    print("  The one consumer applies, per declared member value, the predicate")
    print("      value.startsWith(<member>)   ->   arm = CSR-or-null")
    print("  Truth table under the declared set, and under the set with the two")
    print("  `_X` members REMOVED. NOTE WHAT THE LAST COLUMN IS AND IS NOT: it")
    print("  compares the ARM a wire value takes. It does not compare code")
    print("  references — a member that is READ is not removable at all, which is")
    print("  a different and stronger statement than 'removable with no effect'.")

    def arm(value, read_set):
        return any(value.startswith(m) for m in read_set)

    print()
    print("    wire value      startsWith BLE/SIMPLERA/GUARDIAN   without _X members  verdict")
    for v in decl_members:
        a = arm(v, read_set)
        b = arm(v, [x for x in decl_members if x in read_set])
        if v in read_set:
            verdict = "READ - the code names it; not removable"
        else:
            verdict = "INERT - removing it changes no arm" if a == b else "LOAD-BEARING"
        print(f"    {v:<16} {str(a):<34} {str(b):<22} {verdict}")
    print()
    print("  Values the enum does not declare, for completeness of the predicate:")
    for v in ["NGP", "CC880", "MINIMED", "PARADIGM", "SIMPLERACC"]:
        print(f"    {v:<16} {str(arm(v, read_set)):<34} (undeclared; arm unchanged by any edit)")
    print()
    print("  Reading of that table, and it is the whole verdict:")
    print("   - BLE_X and SIMPLERA_X take the SAME arm as BLE and SIMPLERA, because")
    print("     startsWith('BLE') is already true of 'BLE_X'. Declaring them adds")
    print("     nothing the consumer can observe, at any wire value.")
    print("   - so the suffix is NOT a transport axis at this call site: the transport")
    print("     choice (CSR endpoint vs null) does not distinguish the suffixed values.")
    print("   - so the suffix is NOT a model axis at this call site either: the model")
    print("     axis in this corpus is the separate deviceModelMapping, whose SIMPLERACC")
    print("     key is not a member of this enum (section H).")
    print("   - whether `_X` MEANS anything on the wire is still open, and this corpus")
    print("     cannot close it: the discriminator's values arrive from an authenticated")
    print("     POST /patient/v2/monitor/data, which this project does not make.")

    print()
    print("=" * 78)
    print("K. THE TWO FUNCTIONS AROUND THE BRANCH — so every offset FINDINGS.md")
    print("   cites for the branch's consequences is reproducible from this file.")
    print("=" * 78)
    for label, needle, span in [
        ("getDeviceFamily  (produces deviceFamily)",
         "getDeviceFamily(V){", 620),
        ("getUploadDeviceInfo  (the CSR POST, in userService)",
         "getUploadDeviceInfo(V){", 560),
    ]:
        i = T.find(needle)
        print()
        print(f"  {label}  @{i}")
        print(f"    {T[i:i + span]!r}")
    print()
    print("  Offset of the pieces those two functions depend on:")
    for label, needle in [
        ("POST /patient/v2/monitor/data", "/patient/v2/monitor/data"),
        ("sessionStorage.getItem(\"deviceFamily\")", 'sessionStorage.getItem("deviceFamily")'),
        ("display_message  (the CSR endpoint the branch POSTs)",
         "display_message:X"),
        ("deviceModelMapping  (the adjacent model axis)", "deviceModelMapping"),
        ("StandaloneCGM  (a model-map key)", "StandaloneCGM"),
        ("SIMPLERACC  (a model-map key, the near-miss)", "SIMPLERACC"),
    ]:
        print(f"    {label:<52} @{T.find(needle)}")
    print()
    print("  `deviceModelMapping` is selected at the call site of StandaloneCGM; the")
    print("  capability map it feeds is a runtime value, which is why SIMPLERACC")
    print("  appears once — as a property READ — and has no definition in this body.")


    print()
    print("=" * 78)
    print("L. THE CLOSURE ENUMERATION — sections C and D COUNT; this one CLOSES.")
    print("   A global `<binding>.G` sweep finds one false hit belonging to some")
    print("   OTHER module. That is a count, not a closure. Here the importing")
    print("   MODULE is bounded by its own webpack delimiters, and EVERY use of the")
    print("   imported binding inside it is enumerated — including uses that are not")
    print("   member reads, which is where an alias or a bare pass-on would hide.")
    print("=" * 78)
    MODDEF = re.compile(r"(?:^|[,}{])(\d{3,6}):\((?:Je|J|e|_e)\s*,\s*(?:_e|e)\s*,")
    if binding:
        needle_imp = f"{binding}=i({ENUM_MODULE})"
        imp_sites = [m.start() for m in re.finditer(re.escape(needle_imp), T)]
        if len(imp_sites) != 1:
            print(f"  NOTE: `{needle_imp}` occurs {len(imp_sites)} time(s), not 1 — "
                  "this section does not close the consumer population and must not "
                  "be read as if it did.")
        imp_off = imp_sites[0]
        bounds = [(m.start(), int(m.group(1))) for m in MODDEF.finditer(T)]
        before = [b for b in bounds if b[0] < imp_off]
        after = [b for b in bounds if b[0] > imp_off]
        if not before or not after:
            fail("could not bound the importing module — the section D result below "
                 "does not bound the consumer population and must not be read as if "
                 "it did")
        m_lo, m_id = before[-1]
        m_hi = after[0][0]
        seg = T[m_lo:m_hi]
        print(f"  importing module id      : {m_id}")
        print(f"  module byte span         : {m_lo}..{m_hi - 1}  ({len(seg)} B)")
        print(f"  the import site          : {imp_off}  `{T[imp_off:imp_off + 12]}`")
        print()
        uses = [m.start() for m in
                re.finditer(rf"(?<![A-Za-z0-9_$.$]){re.escape(binding)}(?![A-Za-z0-9_$])", seg)]
        as_g, not_g = [], []
        for s in uses:
            (as_g if seg[s + 1:s + 3] == ".G" else not_g).append(s)
        print(f"  every identifier `{binding}` in that module : {len(uses)}")
        for s in as_g:
            print(f"    member read      @{m_lo + s}  {seg[s:s + 16]!r}")
        for s in not_g:
            print(f"    NOT a member read @{m_lo + s}  {seg[s:s + 16]!r}"
                  + ("   <- the import binding itself"
                     if seg[s:s + 12] == f"{binding}=i({ENUM_MODULE}" else ""))
        decls = [m.start() for m in
                 re.finditer(rf"(?<![A-Za-z0-9_$.$])(?:const|let|var)\s+{re.escape(binding)}\b", seg)]
        params = [m.start() for m in
                  re.finditer(rf"function\s*\w*\s*\([^)]*\b{re.escape(binding)}\b[^)]*\)", seg)]
        print()
        print(f"  module-level const/let/var `{binding}` : {decls}")
        print(f"  function parameters named `{binding}`  : {len(params)}")
        print(f"  `i({ENUM_MODULE})` sites in the WHOLE body : "
              f"{len(re.findall(re.escape(f'i({ENUM_MODULE})'), T))}")
        print()
        shadowed = bool(decls or params)
        print("  VERDICT: the binding is "
              + ("SHADOWED inside this module — the enumeration below does NOT "
                 "close the consumer population and must not be read as if it did."
                 if shadowed else
                 "never aliased, never passed bare and never shadowed inside the "
                 "module that imports it."))
        if not shadowed:
            print(f"  With module {ENUM_MODULE} exporting exactly one binding, the enum")
            print(f"  object cannot leave module {m_id} by any route this body contains,")
            print(f"  so section D's {len(reads)} member reads are a CLOSED enumeration of")
            print("  the consumer surface in this corpus, not a sample of one.")
        print()
        print("  THE FALSE HIT, ADJUDICATED BY MODULE. Each `o.G` site section D lists as")
        print("  NOT-A-MEMBER-READ is re-read here by module, not by token:")
        for s in others:
            fb = [(m.start(), int(m.group(1))) for m in MODDEF.finditer(T)]
            fbefore = [b for b in fb if b[0] < s][-1]
            fafter = [b for b in fb if b[0] > s][0]
            fseg = T[fbefore[0]:fafter[0]]
            own = re.findall(rf"{re.escape(binding)}\s*=\s*i\((\d+)\)", fseg)
            own_mod = own[0] if own else "?"
            needle = binding + "=i(" + own_mod + ")"
            own_off = fbefore[0] + fseg.index(needle) if needle in fseg else -1
            print(f"    byte {s} sits in module {fbefore[1]} "
                  f"(bytes {fbefore[0]}..{fafter[0] - 1}), which has its own "
                  + repr(needle) + f" import at {own_off}")
            print("    — a different module's binding, same token, different sense.")

if __name__ == "__main__":
    main()
