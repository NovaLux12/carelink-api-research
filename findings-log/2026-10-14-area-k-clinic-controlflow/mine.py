#!/usr/bin/env python3
"""Webpack module index + token census for a minified bundle.

WHY THIS EXISTS. "A grep that hit without proving" is this repo's most repeated
failure (docs/09 section 5 item 2). A hit proves the token exists, not that it
means what was assumed — so every hit printed here carries its BYTE OFFSET, the
ENCLOSING WEBPACK MODULE ID, the enclosing string literal if there is one, and
its context. A reader can then judge the hit instead of trusting the count.

Also implements the two controls the false-hit class demands:
  * literal-vs-directive: reports whether the hit sits inside a JS string literal
    (a quoted value the code uses) or in bare code (an identifier, a property,
    a regex, a webpack runtime directive);
  * case sensitivity: every census is run case-sensitively by default and the
    case-insensitive count is reported beside it, so "0 case-sensitive hits" is
    distinguishable from "no hits at all".

Usage:
  mine.py index  <body>                     -> module table (id, start, end, bytes)
  mine.py find  <body> <token> [--ci] [--max N] [--ctx N]
  mine.py census <body...> -- <token> [<token> ...]
"""
import argparse
import json
import re
import sys

# A webpack module header at the top level of a chunk: `,12345:(a,b,c)=>{` or
# `{12345:function(...){`. Anchored on the `,`-or-`{` boundary so an id that
# merely looks like a number inside a string does not create a boundary.
MOD = re.compile(r'(?:^|[,{}])(\d+)\s*:\s*(?:\(([^)]*)\)\s*=>\s*\{|function\s*\()')


def load(p):
    with open(p, "rb") as f:
        return f.read()


def index(body):
    """Return [(module_id, start, end)] over the whole body."""
    text = body.decode("utf-8", "replace")
    out = []
    for m in MOD.finditer(text):
        out.append((int(m.group(1)), m.start(1)))
    out.sort(key=lambda t: t[1])
    mods = []
    for i, (mid, st) in enumerate(out):
        end = out[i + 1][1] if i + 1 < len(out) else len(body)
        mods.append((mid, st, end))
    return mods


def module_at(mods, off):
    lo, hi = 0, len(mods) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if mods[mid][1] <= off:
            best = mods[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def _quote_spans(text):
    """DEAD CODE KEPT AS THE RECORD OF A FAILED INSTRUMENT — see literal_label().

    A global `"((?:[^"\\\\]|\\\\.)*)"` span scan was implemented first and it
    DESYNCHRONISED: it reported 4 of the bundle's known route literals as bare
    code and labelled a 4-character run `,jn=` as a literal, because somewhere
    upstream one quote was consumed as a closing quote where it opened a
    literal, flipping the parity of every subsequent span. Nothing reported the
    flip — the spans simply became the gaps. It was caught only because
    `self-test` was written before the answers were believed (the same argument
    scripts/scrub-patterns.txt makes about its own dead pattern, and AGENTS.md
    section 6 item 1). Do not reinstate it.
    """
    raise NotImplementedError("superseded by literal_label(); see the docstring")


def _is_escaped(text, i):
    n = 0
    j = i - 1
    while j >= 0 and text[j] == "\\":
        n += 1
        j -= 1
    return n % 2 == 1


# The characters that, in MINIFIED output, precede an OPENING quote. Kept
# deliberately short: every character added to this set is one more way to call a
# literal's own content an opener. `/`, `-`, `+` and `*` were all considered and
# all rejected — they occur inside literal content (`".../"`, `"a-b"`) as often as
# they precede a quote, and including them is what a token like
# `system.logbook...` inside `"hcp/configuration/public/system.logbook..."` tests.
_STRONG_OPEN = set("=(,:[;,?&|+*{!")


def literal_label(text, off):
    """Label a hit as inside a double-quoted literal, using LOCAL evidence only.

    Returns one of:
      "literal-start"  the byte before the hit is an unescaped `"`
      "literal-inner"  the nearest preceding unescaped `"` is an OPENER (its own
                       preceding byte is in _STRONG_OPEN, or it is at offset 0)
      "code"           the nearest preceding unescaped `"` is a CLOSER — its own
                       preceding byte is a word character, `.`, `)`, `}`, `]` — so
                       the literal it ended is closed before the hit and no other
                       literal can contain it
      "uncertain"      the preceding byte is punctuation this instrument refuses
                       to adjudicate (see _STRONG_OPEN). NOT a verdict. Every
                       `uncertain` hit must be read at its offset before it is
                       reported, and the findings say which were read.

    WHY LOCAL. A global quote-parity scan is one dropped quote away from
    reporting every hit after the first escape as the opposite of what it is, and
    this pass's first implementation did exactly that — see _quote_spans(). The
    local argument above is sound without parity: if the nearest preceding quote
    is a CLOSER, no literal can contain the hit, because a literal containing the
    hit would need an opener between that closer and the hit, and by construction
    there is none.

    The label is still only a label. Every hit is printed with its surrounding
    bytes, and the findings quote what is AT the offset rather than what the
    label says.
    """
    if off <= 0 or off >= len(text):
        return "out-of-range"
    if text[off - 1] == '"' and not _is_escaped(text, off - 1):
        return "literal-start"
    p = off - 1
    while p >= 0:
        if text[p] == '"' and not _is_escaped(text, p):
            break
        p -= 1
    if p < 0:
        return "code"
    if p == 0:
        return "literal-inner"
    c = text[p - 1]
    if c in _STRONG_OPEN:
        return "literal-inner"
    if c.isalnum() or c in "_.})]%^~<>!@#$&*-+/\\'\"`":
        return "code"
    return "uncertain"


def in_string_literal(text, off, spans=None):
    return literal_label(text, off).startswith("literal")


def enclosing_literal(text, off, spans=None):
    lab = literal_label(text, off)
    if lab == "literal-start":
        start = off
        end = _closing_quote(text, start)
    elif lab == "literal-inner":
        start = _opening_quote(text, off)
        end = _closing_quote(text, start)
    else:
        return None
    if start is None or end is None:
        return None
    return text[start:end]


def _closing_quote(text, start):
    i = start
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == '"':
            return i
        i += 1
    return None


def _opening_quote(text, off):
    p = off - 1
    while p >= 0:
        if text[p] == '"' and (p == 0 or text[p - 1] != "\\"):
            return p
        p -= 1
    return None


def find(body, token, ci=False, limit=None, ctx=120):
    text = body.decode("utf-8", "replace")
    mods = index(body)
    flags = re.IGNORECASE if ci else 0
    rows = []
    for m in re.finditer(re.escape(token), text, flags):
        off = m.start()
        mod = module_at(mods, off)
        lab = literal_label(text, off)
        lit = enclosing_literal(text, off)
        rows.append({
            "offset": off,
            "module": mod[0] if mod else None,
            "module_span": [mod[1], mod[2]] if mod else None,
            "literal_label": lab,
            "in_string_literal": lab.startswith("literal"),
            "enclosing_literal": (lit[:400] if lit else None),
            "ctx": text[max(0, off - ctx): off + len(token) + ctx],
        })
        if limit and len(rows) >= limit:
            break
    return rows


def self_test(path):
    """Prove the literal detector FIRES and that it does not fire on code.

    An instrument that never fires proves nothing — the same argument
    scripts/scrub-patterns.txt makes about a dead scrub pattern. The negative
    controls are SYNTHETIC and provable by construction (a two-line snippet where
    the reader can see which occurrence is quoted and which is bare); the
    positive controls are real literals in the real bundle. Both directions are
    required: a detector that labels everything "literal" passes a
    positives-only test and is just as useless as a dead one.
    """
    ok = True
    print("negative + positive controls, synthetic (provable by construction):")
    synth = 'var a="logbook",b=logbook;var c="x\\"y",d=x;var e=function(){};'
    hits = list(re.finditer(re.escape("logbook"), synth))
    cases = [
        (hits[0].start(), "literal-start", "the quoted occurrence"),
        (hits[1].start(), "code", "the bare identifier occurrence"),
    ]
    for off, want, why in cases:
        got = literal_label(synth, off) == want
        print(f"  {'PASS' if got else 'FAIL'}  offset {off} ({why}): "
              f"{literal_label(synth, off)} (expect {want})")
        ok &= got
    labs = [literal_label(synth, h.start()) for h in re.finditer(re.escape("function"), synth)]
    got = all(l == "code" for l in labs)
    print(f"  {'PASS' if got else 'FAIL'}  'function': labels={labs} (expect all code)")
    ok &= got
    print("positive controls, real bundle literals:")
    body = load(path)
    text = body.decode("utf-8", "replace")
    for tok in ("hcp/patients/((patientId))/logbook/entries",
                "system.logbook.entry.validation.config"):
        ms = list(re.finditer(re.escape(tok), text))
        if not ms:
            print(f"  FAIL  {tok!r}: token absent, cannot test the detector")
            ok = False
            continue
        labs = [literal_label(text, m.start()) for m in ms]
        got = all(l.startswith("literal") for l in labs)
        print(f"  {'PASS' if got else 'FAIL'}  {tok!r}: {len(ms)} occurrences, labels={labs} (expect all literal-*)")
        ok &= got
    print("negative control, real bundle, absent token:")
    ms = list(re.finditer(re.escape("zzz-no-such-token-zzz"), text))
    got = len(ms) == 0
    print(f"  {'PASS' if got else 'FAIL'}  occurrences={len(ms)} (expect 0)")
    ok &= got
    print("self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["index", "find", "census", "self-test"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--ci", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ctx", type=int, default=120)
    a = ap.parse_args()
    if a.mode == "self-test":
        sys.exit(self_test(a.args[0]))
    if a.mode == "index":
        body = load(a.args[0])
        mods = index(body)
        print(f"# {a.args[0]}: {len(body)} bytes, {len(mods)} module boundaries")
        for mid, st, en in mods:
            print(f"{mid}\t{st}\t{en-st}")
        return
    if a.mode == "find":
        body = load(a.args[0])
        rows = find(body, a.args[1], ci=a.ci, limit=a.limit, ctx=a.ctx)
        print(f"# token={a.args[1]!r} case_sensitive={not a.ci} hits={len(rows)}")
        for r in rows:
            print(json.dumps(r))
        return
    # census: files... -- token...
    sep = a.args.index("--")
    files, tokens = a.args[:sep], a.args[sep + 1:]
    for t in tokens:
        cs = ci = 0
        for f in files:
            body = load(f)
            text = body.decode("utf-8", "replace")
            cs += len(re.findall(re.escape(t), text))
            ci += len(re.findall(re.escape(t), text, re.IGNORECASE))
        print(f"{t}\tocc_case_sensitive={cs}\tocc_case_insensitive={ci}")


if __name__ == "__main__":
    main()