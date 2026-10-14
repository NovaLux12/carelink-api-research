#!/usr/bin/env python3
"""Area S4 — exhaustive request-shape recovery from the patient lazy-chunk corpus.

COUNTING RULE (AGENTS.md SS6 item 7 — "the counting rule lives in a script;
prose states the measured static count, nothing else"). Four decisions, each
stated because each one moves the number.

  D1. RECEIVER. A call site counts only when the receiver is `http`,
      `_httpClient` or `httpClient` — the injected Angular HttpClient bindings.
      The corpus holds 1,139 `.get(/.post(/.put(/.delete(` occurrences and 233 of
      them are HTTP. Everything else sharing those five method names is a
      collection lookup: `form.get` 161, `this.get` 37, `Vt.get` 27,
      `headers.get` 15, `cookieService.get` 14, `injector.get` 11, `map.get` 10,
      `cookieService.delete` 5, … Counting `.get(` without D1 is the
      AGENTS.md SS6 item-2 trap, and is how an earlier draft of this pass
      produced counts that were not reproducible under any stated rule.

  D2. FIRST ARGUMENT IS A LITERAL. The first argument must be a string, single-
      quoted, or template literal. Three forms occur and ALL THREE count:
        "/patient/users/me"                      leading slash
        "patient/logbookEntry"                   NO leading slash — the client
                                                posts it relative and an
                                                interceptor prefixes the base
        `patient/logbookEntry/${w}`              template, may interpolate
      A rule that requires the leading slash silently drops 45 pairs.
      A ternary in first-argument position contributes BOTH branches, labelled,
      because the client selects at runtime (`cond?"A":"B"`, 3 sites).

  D3. `${this.baseUrl}` IS RESOLVED ONLY WITHIN ITS OWN CHUNK, and only when
      that chunk contains exactly ONE `this.baseUrl="literal"` assignment.
      The guard is the whole point: `this.baseUrl` is an instance property and
      means different things in different builds (`"/patient/csr"` in a service
      vs a CMS media base `getBaseCmsUrl()` in the eager bundle), so a
      leaf-name map resolves it to whichever entry was indexed first and looks
      like agreement — AGENTS.md SS6 item 3. A call whose path is any other
      variable is reported UNRESOLVED and is never guessed.

  D4. SLOT NAMES ARE MINIFIER ARTEFACTS. `${t}/users` and `${o}/users` are the
      same template in different chunk builds. Slots are renumbered `{1}`, `{2}`,
      … by position. This is the rule docs/06 already states for its
      `/patient/csr` sweep; reusing it keeps ONE notion of "distinct shape" in
      this repository rather than two. The verbatim (un-normalised) literal is
      still emitted to pairs.tsv as `verbatim` so nothing is lost.

Outputs (under $S4_OUT): pairs.tsv, unresolved.tsv, resolved-constants.tsv,
counters.json. Zero vendor requests — pure string analysis over bytes on disk.

Usage:  S4_CORPUS=<dir> S4_OUT=<dir> python3 extract-call-sites.py
        (or pass the two directories as argv[1] and argv[2])
"""
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

CORPUS = os.environ.get("S4_CORPUS") or (sys.argv[1] if len(sys.argv) > 1 else "")
OUT = os.environ.get("S4_OUT") or (sys.argv[2] if len(sys.argv) > 2 else "")

RECEIVERS = r"(?:_?http(?:Client)?|HttpClient)"
METHODS = ("get", "post", "put", "delete", "patch")

# D1: receiver + method + opening paren. The argument text is then extracted by
# an exact quote-aware scanner rather than a regex, because a template literal
# may legitimately contain parentheses, e.g.
#     p?`/patient/m2m/sms/sendTestSms/${encodeURIComponent(A)}`:"..."
# and a naive "stop at the first (" cut truncates those and drops the site.
SITE = re.compile(r"\b" + RECEIVERS + r"\.(?P<m>" + "|".join(METHODS) + r")\(")

LIT_HEAD = re.compile(r"\s*(?P<q>[\"'\`])(?P<lit>[^`'\"]{1,200}?)(?P=q)")

TERNARY = re.compile(
    r"\?(?P<q1>[\"'\`])(?P<a1>[^\"'`]{1,200})(?P=q1)"
    r"\s*:\s*(?P<q2>[\"'\`])(?P<a2>[^\"'`]{1,200})(?P=q2)")

# compiled TS-enum / object-literal string assignment, e.g. a.NAME="literal"
CONST_DEF = re.compile(r'\.([A-Za-z_$][A-Za-z0-9_$]{1,40})="((?:[^"\\]|\\.){1,160})"')
BASE_ASSIGN = re.compile(r'this\.baseUrl="([^"]{1,200})"')
SLOT = re.compile(r"\$\{[^}]*\}")


def read_first_arg(text, open_paren_index):
    """Exact, quote- and depth-aware read of one call's first argument."""
    i = open_paren_index + 1
    depth = 0
    quote = None
    start = i
    n = len(text)
    while i < n:
        ch = text[i]
        if quote is not None:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        else:
            if ch in "\"'`":
                quote = ch
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                if depth == 0:
                    return text[start:i]
                depth -= 1
            elif ch == "," and depth == 0:
                return text[start:i]
        i += 1
    return text[start:min(i, start + 400)]


def normalize_slots(path):
    """D4: renumber `${…}` slots by position, not by name."""
    tags = ["{%d}" % (i + 1) for i, _ in enumerate(SLOT.findall(path))]
    return SLOT.sub(lambda _m: tags.pop(0), path)


def harvest(arg, consts):
    """D2: return [(path, branch, origin)] for this first argument."""
    tern = TERNARY.search(arg)
    if tern:
        return [(tern.group("a1"), "then-branch", "literal"),
                (tern.group("a2"), "else-branch", "literal")]
    head = LIT_HEAD.match(arg)
    if head:
        return [(head.group("lit"), "single", "literal")]
    # A dotted constant such as `T.S.PATIENT_REPORTS_SENSOR_HISTORY` resolves only
    # when its leaf name is defined exactly once in the corpus. `this.*` is
    # excluded on purpose — see D3 in the module docstring.
    a = arg.strip()
    if consts and re.match(r"^[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+$", a) \
            and not a.startswith("this."):
        vals = consts.get(a.split(".")[-1]) or set()
        if len(vals) == 1:
            return [(next(iter(vals)), "single", "const:" + a)]
    return []


def main():
    if not CORPUS or not os.path.isdir(CORPUS):
        sys.exit("usage: S4_CORPUS=<chunk-dir> S4_OUT=<out-dir> extract-call-sites.py")
    os.makedirs(OUT, exist_ok=True)
    files = sorted(f for f in os.listdir(CORPUS) if f.endswith(".b"))
    if not files:
        sys.exit("no chunk bodies in the corpus dir given")

    texts, manifest, consts = {}, [], defaultdict(set)
    for name in files:
        with open(os.path.join(CORPUS, name), "rb") as fh:
            blob = fh.read()
        manifest.append("%s  %s" % (hashlib.sha256(blob).hexdigest(), name))
        text = blob.decode("utf-8", "replace")
        texts[name] = text
        for m in CONST_DEF.finditer(text):
            consts[m.group(1)].add(m.group(2))

    pairs = defaultdict(lambda: {"chunks": set(), "verbatim": set()})
    sites_total = sites_literal = sites_resolved = sites_unresolved = 0
    unresolved_by_method = defaultdict(int)
    unresolved = []
    resolved_sites = []

    for name, text in texts.items():
        bases = BASE_ASSIGN.findall(text)
        chunk_base = bases[0] if len(bases) == 1 else None
        for m in SITE.finditer(text):
            sites_total += 1
            arg = read_first_arg(text, m.end() - 1)
            got = harvest(arg, consts)
            kind = "literal"
            # D3: LIT_HEAD captures a `${this.baseUrl}/suffix` template verbatim,
            # prefix included, so the base is substituted here.
            if got and chunk_base \
                    and all(p.startswith("${this.baseUrl}") for p, _, _ in got):
                got = [(chunk_base + p[len("${this.baseUrl}"):], b, "baseUrl")
                       for p, b, _ in got]
                kind = "baseUrl"
            if got:
                for path, branch, origin in got:
                    key = (m.group("m"), normalize_slots(path), branch)
                    pairs[key]["chunks"].add(name)
                    pairs[key]["verbatim"].add(path)
                if kind == "literal":
                    sites_literal += 1
                else:
                    sites_resolved += 1
                if got[0][2] != "literal":
                    resolved_sites.append(
                        {"chunk": name, "method": m.group("m"),
                         "first_arg": arg.strip()[:120],
                         "resolved_path": normalize_slots(got[0][0])})
            else:
                sites_unresolved += 1
                unresolved_by_method[m.group("m")] += 1
                if len(unresolved) < 60:
                    unresolved.append({"chunk": name, "method": m.group("m"),
                                       "first_arg": arg.strip()[:120]})

    rows = sorted(pairs.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    with open(os.path.join(OUT, "pairs.tsv"), "w") as fh:
        fh.write("method\tbranch\tnormalized_path\tn_chunks\tverbatim\n")
        for (meth, path, branch), info in rows:
            fh.write("%s\t%s\t%s\t%d\t%s\n" % (
                meth.upper(), branch, path, len(info["chunks"]),
                " | ".join(sorted(info["verbatim"]))))
    with open(os.path.join(OUT, "resolved-constants.tsv"), "w") as fh:
        fh.write("chunk\tmethod\tfirst_arg\tresolved_path\n")
        for r in sorted(resolved_sites, key=lambda x: (x["method"], x["chunk"])):
            fh.write("%s\t%s\t%s\t%s\n" % (r["chunk"], r["method"].upper(),
                                           r["first_arg"], r["resolved_path"]))
    with open(os.path.join(OUT, "unresolved.tsv"), "w") as fh:
        fh.write("chunk\tmethod\tfirst_arg_expression\n")
        for r in sorted(unresolved, key=lambda x: (x["method"], x["chunk"])):
            fh.write("%s\t%s\t%s\n" % (r["chunk"], r["method"], r["first_arg"]))

    by_method = defaultdict(int)
    for (meth, _p, _b) in pairs:
        by_method[meth] += 1

    counters = {
        "corpus_manifest_sha256": hashlib.sha256("\n".join(manifest).encode()).hexdigest(),
        "corpus_bytes": sum(os.path.getsize(os.path.join(CORPUS, f)) for f in files),
        "n_chunk_files": len(files),
        "http_call_sites_total": sites_total,
        "sites_with_literal_path": sites_literal,
        "sites_with_resolved_variable_path": sites_resolved,
        "sites_with_unresolved_variable_path": sites_unresolved,
        "unresolved_by_method": dict(unresolved_by_method),
        "distinct_pairs": len(pairs),
        "by_method": {m: by_method.get(m, 0) for m in METHODS},
        "by_method_sum": sum(by_method.get(m, 0) for m in METHODS),
        # Prose figures must be read from here, never hand-carried: an earlier
        # draft of this pass stated a leading-slash split that contradicted its
        # own committed pairs.tsv (AGENTS.md SS6 item 5).
        "pairs_with_leading_slash": sum(1 for k in pairs if k[1].startswith("/")),
        "pairs_without_leading_slash": sum(1 for k in pairs if not k[1].startswith("/")),
        "ternary_branch_rows": sum(1 for k in pairs if k[2] != "single"),
        "ternary_sites": sum(1 for k in pairs if k[2] != "single") // 2,
        "pairs_with_interpolation": sum(1 for k in pairs if "{" in k[1]),
        "pairs_without_interpolation": sum(1 for k in pairs if "{" not in k[1]),
        "csr_pairs": sum(1 for k in pairs if "patient/csr" in k[1]),
    }
    with open(os.path.join(OUT, "counters.json"), "w") as fh:
        json.dump(counters, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps(counters, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
