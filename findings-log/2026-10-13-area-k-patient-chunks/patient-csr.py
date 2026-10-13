#!/usr/bin/env python3
"""Area K — the `/patient/csr` census, with the counting rule stated and re-derived.

ZERO requests; reads only bodies already captured.

WHY THIS EXISTS. The first version of this pass reported "12 endpoint literals across
7 chunks". That number was a subset of what its own source table (`tables.txt` section
T3) already listed: chunk `5750.d7bef840102da905.js` carries FOUR `/patient/csr`
offsets — [775, 855, 985, 1076] — and the route table named one of them. No counting
rule was recorded anywhere, which is `AGENTS.md` section 6 item 7, and a prose figure
that is not re-derived from its own table is item 5. The error was conservative — it
under-counted a positive — but a number that does not come from a rule is not a
measurement.

THE COUNTING RULE, in full:

  1. CORPUS. The 211 real chunks: a body answering 200 + application/javascript
     (210 `SWEEP-*` rows + 1 `FOLLOWUP` row). Ledger rows that are not a chunk are
     excluded, and the count is asserted against the committed list.
  2. UNIT. One **endpoint shape** = one distinct (HTTP method, path template) pair.
     A path template is either
       (a) an inline literal beginning `/patient/csr`, or
       (b) the chunk's `this.baseUrl` value concatenated with the template suffix of
           a `this.http.<verb>(\`${this.baseUrl}…\`)` call.
     `{…}` marks a RUNTIME template substitution (a minified parameter), and is part
     of the template, not a separate value.
  3. DEDUPLICATION. Counted ONCE per distinct (method, template) pair across the
     WHOLE corpus. Three chunks carry a byte-identical safety/notice service; that
     is one shape seen three times, not three shapes.
  4. EXCLUSION, and this is the decision that actually moves the number: a
     `this.http.<verb>(x)` call whose first argument is a BARE IDENTIFIER is EXCLUDED,
     because the URL is supplied by the caller and is not a path this corpus fixes.
     In the safety/notice service that excludes exactly two calls —
     `downloadFromUrl(t)` and `uploadToS3(t)` — which take an absolute URL. Counting
     them would have inflated the figure by two. **A bare `this.baseUrl` is NOT
     excluded**: it resolves to the base itself and is a shape in its own right.
  5. TERNARIES count as BOTH branches. `cond?\`/a\`:"/b"` yields two templates.
     Collapsing a ternary to one branch under-counts; the 5750 chunk's two ternaries
     are the whole reason the first "12" was short.
  6. VERBS are taken from the call site, never from the service name. `GET` and
     `POST` on the same path are two shapes.
  7. A runtime slot's NAME is a MINIFIER ARTEFACT and is canonicalised away. The
     same logical slot is `{t}` in one chunk, `{o}` in the next and `{c}` in the
     third, so template slots are renumbered `{1}`, `{2}`, … by order of appearance.
     **Position is the shape; the name is not.** Without this the three
     safety/notice chunks fail to deduplicate against each other and the count
     triples.
  8. SCOPE. Only paths under `/patient/csr`. A neighbouring `/patient/consents`,
     `/patient/users/me/consents/answers` in the same chunk is a different namespace
     and is listed as out-of-scope rather than counted or called "excluded".

Prints the rule, the per-chunk raw evidence, the resolved shapes, and the total.
Exits non-zero if the corpus count disagrees with the committed list, so it cannot
report a clean census over the wrong rows.
"""
import json
import os
import re
import sys
from collections import OrderedDict

BODIES = sys.argv[1]
LEDGER = sys.argv[2]
LIST = sys.argv[3]

rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
rows.sort(key=lambda r: r["seq"])
listed = [l.strip() for l in open(LIST) if l.strip() and not l.startswith("#")]


def is_real_chunk(r):
    return r["http_status"] == "200" and r["content_type"] == "application/javascript"


corpus = [r for r in rows
          if r["role"].startswith(("SWEEP-", "FOLLOWUP")) and is_real_chunk(r)]
if len(corpus) != len(listed):
    print("FATAL: counting rule yields %d real chunks but the committed list has %d. "
          "Do not read any figure below." % (len(corpus), len(listed)), file=sys.stderr)
    raise SystemExit(2)

o = []
w = o.append
w("=" * 100)
w("/patient/csr CENSUS — counting rule applied, figures re-derived, ZERO requests")
w("=" * 100)
w("")
w("rule 1 corpus       : %d real chunks = 200 + application/javascript"
  % len(corpus))
w("                     (asserted against %d committed list entries)" % len(listed))
w("rule 2 unit         : one endpoint shape = (HTTP method, path template)")
w("rule 3 dedup        : once per distinct (method, template) across the corpus")
w("rule 4 exclusion    : a call whose first argument is a BARE IDENTIFIER is")
w("                     excluded — the URL comes from the caller, not this corpus")
w("rule 5 verbs        : from the call site, not the service name")
w("")

# --- collect ------------------------------------------------------------------
# shape key -> {chunks, offsets, verb, template, how}
shapes = OrderedDict()
excluded = []
per_chunk_literals = OrderedDict()

def canon(tmpl):
    """Rule 7: renumber runtime slots by POSITION. The slot NAME is a minifier
    artefact -- the same logical slot is {t}, {o} or {c} in three builds of the same
    safety/notice service -- so dedupe on position or the three chunks never meet."""
    n = [0]

    def sub(_m):
        n[0] += 1
        return "{%d}" % n[0]

    return re.sub(r"\$\{[^}]*\}", sub, tmpl)


def iter_calls(s):
    """Yield (VERB, first-argument-text) for every this.http.<verb>(...) call.

    A character-class regex cannot do this. The first version of this script used
    `[^,;)]{0,400}` and it silently truncated at the FIRST `)` inside a template
    substitution -- `${encodeURIComponent(a)}` -- which dropped chunk 5750 entirely
    from the census. A dropped chunk is the exact failure this pass was corrected
    for, so the extractor scans properly: it tracks backtick/single/double quoting,
    `${` nesting and paren depth, and stops at the top-level comma or the call's
    own closing paren.
    """
    for m in re.finditer(r"this\.http\.(get|post|put|delete|patch)\(", s):
        i = m.end()
        depth, q, tmpl, start, n = 1, None, 0, i, len(s)
        while i < n:
            c = s[i]
            if q == "`" and c == "$" and i + 1 < n and s[i + 1] == "{":
                tmpl, i = tmpl + 1, i + 2
                continue
            if tmpl and c == "}":
                tmpl, i = tmpl - 1, i + 1
                continue
            if not tmpl:
                if q:
                    if c == q:
                        q = None
                elif c in "`\'":
                    q = c
                elif c in "([{":
                    depth += 1
                elif c in ")]}":
                    depth -= 1
                    if depth == 0:
                        break
                elif c == "," and depth == 1:
                    break
            i += 1
        yield m.start(), m.group(1).upper(), s[start:i].strip()


def resolve(arg, base):
    """Resolve one call's first argument to a list of path templates.

    Returns (templates, note). note is None on success. Handles a bare identifier
    (out of scope), a bare this.baseUrl (the base itself -- a shape in its own
    right), a template literal over this.baseUrl, a quoted literal, and a ternary of
    any two of those (rule 5: BOTH branches)."""
    arg = arg.strip()
    tern = re.match(r"^[A-Za-z0-9_$.]+\?(.*?):(.*?),?$", arg, re.S)
    if tern and ("`" in tern.group(1) or '"' in tern.group(1)):
        acc = []
        for branch in (tern.group(1), tern.group(2)):
            b = branch.strip().rstrip(",").strip()
            t, note = resolve(b, base)
            if t:
                acc.extend(t)
            else:
                return None, note
        return acc, None
    if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*(\.[A-Za-z0-9_$]+)*", arg):
        if arg == "this.baseUrl":
            return ([base] if base else None), None
        return None, "bare identifier -- URL supplied by the caller (rule 4)"
    m = re.match("^[`\'\"](.*)[`\'\"]$", arg, re.S)
    if not m:
        return None, "unrecognised argument form"
    lit = m.group(1)
    m2 = re.match(r"^\$\{this\.baseUrl\}(.*)$", lit)
    if m2:
        if not base:
            return None, "template over this.baseUrl but no this.baseUrl here"
        return [base + m2.group(1)], None
    if "patient/csr" in lit:
        return [lit], None
    return None, "out of scope -- not a /patient/csr path (rule 8)"


out_of_scope = []
for r in corpus:
    p = os.path.join(BODIES, r["host_tag"] + ".b")
    if not os.path.exists(p):
        print("FATAL: body missing for %s" % r["host_tag"], file=sys.stderr)
        raise SystemExit(2)
    s = open(p, "rb").read().decode("utf-8", errors="replace")
    if "/patient/csr" not in s:
        continue
    base = None
    mb = re.search(r'this\.baseUrl\s*=\s*"(/patient/csr[^"]*)"', s)
    if mb:
        base = mb.group(1)

    # rules 4-7: every this.http.<verb>(arg) call
    for moff, verb, arg in iter_calls(s):
        tmpls, note = resolve(arg, base)
        if not tmpls:
            if note and note.startswith("out of scope"):
                out_of_scope.append((r["path"], moff, verb, arg[:60], note))
            else:
                excluded.append((r["path"], moff, verb, arg[:60]))
            continue
        for raw in tmpls:
            key = (verb, canon(raw))
            if key not in shapes:
                shapes[key] = {"chunks": [], "offsets": [], "verb": verb,
                               "template": key[1]}
            shapes[key]["chunks"].append(r["path"])
            shapes[key]["offsets"].append("%s@%d" % (r["path"].rsplit("/", 1)[-1][:12], moff))

    lits = [(m.start(), m.group(0)) for m in re.finditer(r"/patient/csr[A-Za-z0-9/_\-{}$.]*", s)]
    if lits:
        per_chunk_literals[r["path"]] = (base, lits)

# --- report -------------------------------------------------------------------
w("-" * 100)
w("RAW EVIDENCE — every `/patient/csr` literal in the corpus, with its byte offset")
w("-" * 100)
total_lits = 0
for path, (base, lits) in per_chunk_literals.items():
    w("%-36s baseUrl=%s" % (path.rsplit("/", 1)[-1], repr(base)))
    for off, lit in lits:
        w("      @%-7d %r" % (off, lit))
    total_lits += len(lits)
    w("")
w("TOTAL raw `/patient/csr` literals: %d across %d chunks"
  % (total_lits, len(per_chunk_literals)))
w("")

w("-" * 100)
w("EXCLUDED BY RULE 4 — bare-identifier arguments, URL supplied by the caller")
w("-" * 100)
for path, off, verb, arg in excluded:
    w("  %-36s @%-7d %-6s arg=%r" % (path.rsplit("/", 1)[-1], off, verb, arg))
w("TOTAL excluded: %d" % len(excluded))
w("")

w("-" * 100)
w("RESOLVED ENDPOINT SHAPES — one row per (method, template), deduplicated")
w("-" * 100)
w("%-7s %-62s %-6s %s" % ("method", "path template", "seen in", "call sites"))
for (verb, tmpl), d in sorted(shapes.items(), key=lambda kv: (kv[0][1], kv[0][0])):
    w("%-7s %-62s %-6d %s" % (verb, tmpl, len(d["chunks"]),
                              ", ".join(d["offsets"][:4]) + (" …" if len(d["offsets"]) > 4 else "")))
w("")

n_shapes = len(shapes)
n_templates = len({t for _, t in shapes})
w("=" * 100)
w("THE FIGURES, FROM THE RULE")
w("  distinct path templates        : %d" % n_templates)
w("  distinct method x path shapes  : %d" % n_shapes)
w("  raw `/patient/csr` literals    : %d in %d chunks  (literals, not shapes —" % (total_lits, len(per_chunk_literals)))
w("                                     two of them are the same path in two branches")
w("                                    of a ternary)")
w("  excluded bare-identifier calls : %d" % len(excluded))
w("=" * 100)
w("")
w("WITHDRAWN: the '12 endpoint literals across 7 chunks' figure published in the first")
w("version of this pass. It was a subset of this pass's own tables.txt section T3 —")
w("chunk 5750 carries four literals and the route table named one — and no counting")
w("rule existed to produce it. The rule above yields %d shapes / %d templates." % (n_shapes, n_templates))
print("\n".join(o))