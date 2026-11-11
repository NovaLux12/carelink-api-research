#!/usr/bin/env python3
"""Area AR — derive depth-1 `/hcp/<segment>/` subtree names from the build. ZERO requests.

WHY A BUNDLE AND NOT A GUESS. `AGENTS.md` §8 forbids wordlist fuzzing: a candidate
list must be derived from an observed naming convention with the reasoning recorded.
The convention here is structural, not lexical — every client route in the portal
build is a string literal beginning `hcp/`, so the set of **depth-1 segments** those
literals use IS the set of subtree names the build knows about. Grepping the build for
`hcp/<segment>/` and de-duplicating on `<segment>` therefore derives the candidate
subtree list rather than inventing it. No name below is typed by a human.

INPUT, AND ITS PROVENANCE. `main.js` is the clinic portal bundle
`/main.fb5f8cb7eb60c4d5.js` (3,397,615 B). It is NOT committed — `.loop/` is
gitignored — so this script cannot be re-run from a clean clone; the bundle's
byte count and sha256 are printed and must equal the values area AB pinned
(`findings-log/2026-11-10-area-ab-hcp-direct/probe.sh` records clinic
`2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba`, 3397615 B),
which is the check that this derivation ran against the build the repository pins.
THE BUNDLE WAS NOT RE-FETCHED FOR THIS PASS: it was already in this run's asset
cache (`.loop/aq-assets/main.js`), fetched by area AQ in the same run, and its
digest is verified here before any extraction. That is why AR's derivation costs
0 requests.

EXTRACTIONS, kept separate because they are different claims:

  * EAGER LITERALS — `["'`]` <optional space> `hcp/<seg>/...` in the eager bundle.
    The optional leading space is the recorded JS-API-SURFACE §2.1 quirk.
  * CALL-STYLE — the same string passed bare or via concatenation is NOT counted;
    a partial literal is a partial literal.

RANKING RULE, stated before the number is used. Segments already measured by AR's
parent areas are removed (see EXCLUDE). The remainder is ranked by
**distinct literal count under that segment, descending, then alphabetically**, and
the top N become the candidate list. The count is a proxy for "this subtree is
genuinely handled" — a segment with 50 route literals is a mount, a segment with 1
may be a leaf path that merely looks like a subtree. The proxy is INFERRED and is
declared as such in FINDINGS.md §4; the measurement it feeds is unaffected, because
every candidate is probed at two depths and the verdict is read from the response,
not from the proxy.

Usage: derive.py <bundle> <out-txt> <out-candidates> [n]
Exit:  0 = derivation completed (including a NEGATIVE: fewer than 3 subtrees survive)
       2 = the bundle is missing or its digest does not reproduce the pinned value
       3 = the derivation returned no third subtree at all (AR closes not-determinable)
"""
import hashlib
import re
import sys

PINNED_SHA = "2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba"
PINNED_BYTES = 3397615

# Already measured, by area and at which depth. Removing them is not cherry-picking:
# they are AR's *controls*, not its candidates, and re-probing them would re-answer a
# settled question (AL: 4 of 4 hosts; AQ: 4 of 4 hosts).
EXCLUDE = {
    "configuration": "measured — AR's CONTROL-2 reference (AL, AG, AK; 4 of 4 hosts, 405 + Allow)",
    "patients": "measured — area AQ this run (4 of 4 hosts, absent child 404)",
}
# Segments that are not subtree names but route fragments. NONE are removed on
# inspection: if the build writes `hcp/v2/`, then `/hcp/v2/` is the path a client
# calls and it is a legitimate candidate. Listed only if a name is removed.
NOT_A_SEGMENT = {}


def main():
    bundle_path, out_path, cand_path = sys.argv[1:4]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    body = open(bundle_path, "rb").read()
    digest = hashlib.sha256(body).hexdigest()
    text = body.decode("utf-8", "replace")

    out = []
    out.append(f"AR-DERIVE input: {bundle_path}")
    out.append(f"AR-DERIVE bundle: bytes={len(body)} sha256={digest}")
    out.append(f"AR-DERIVE pinned: bytes={PINNED_BYTES} sha256={PINNED_SHA} "
               f"reproduces={digest == PINNED_SHA and len(body) == PINNED_BYTES}")
    if digest != PINNED_SHA or len(body) != PINNED_BYTES:
        out.append("AR-DERIVE STOP: digest does not reproduce the pinned clinic build — "
                   "no recorded route table applies to this artefact. Do not derive from it.")
        text_out = "\n".join(out) + "\n"
        open(out_path, "w").write(text_out)
        print(text_out, end="")
        return 2

    # Every string literal whose value begins (after at most one space) at `hcp/`.
    LIT = re.compile(r"""["'`]\s*(/?hcp/[A-Za-z0-9._()/{}$+&=?%:,;!*~-]*)""")
    lits = LIT.findall(text)
    out.append(f"AR-DERIVE literal vocabulary: {len(lits)} string literals starting at `hcp/`")

    # Depth-1 segment, from a literal with at least one more `/`.
    seg_of = re.compile(r"^/?hcp/([A-Za-z0-9_-]+)/")
    per_seg = {}
    for lit in lits:
        m = seg_of.match(lit)
        if m:
            per_seg.setdefault(m.group(1), set()).add(lit.split("?", 1)[0].split("#", 1)[0])
    out.append(f"AR-DERIVE depth-1 segments in the build: {len(per_seg)}")
    out.append("")
    out.append("segment                          distinct_literals  status")
    for seg in sorted(per_seg, key=lambda s: (-len(per_seg[s]), s)):
        st = "EXCLUDED — " + EXCLUDE[seg] if seg in EXCLUDE else "candidate"
        out.append(f"/hcp/{seg + '/':<28} {len(per_seg[seg]):>17}  {st}")
    survivors = [s for s in per_seg if s not in EXCLUDE]
    survivors.sort(key=lambda s: (-len(per_seg[s]), s))
    out.append("")
    out.append(f"AR-DERIVE ranking rule: exclude {sorted(EXCLUDE)}; order by distinct literal "
               f"count desc, then alphabetical; take top {n}.")
    out.append(f"AR-DERIVE surviving subtrees: {len(survivors)}")
    if len(survivors) < 3:
        out.append("AR-DERIVE VERDICT: NEGATIVE — fewer than three subtrees survive the "
                   "exclusion. AR is NOT DETERMINABLE by derivation; no name was invented. "
                   "Close as not-determinable rather than fuzzing (AGENTS.md §8).")
        text_out = "\n".join(out) + "\n"
        open(out_path, "w").write(text_out)
        open(cand_path, "w").write("\n".join(survivors) + "\n")
        print(text_out, end="")
        return 3
    chosen = survivors[:n]
    for s in chosen:
        out.append(f"AR-DERIVE CANDIDATE /hcp/{s}/  literals={len(per_seg[s])}  "
                   f"first={sorted(per_seg[s])[0]}")
    out.append("AR-DERIVE VERDICT: PROCEED — a third subtree exists in the shipped build "
               "and its name was read, not guessed.")
    open(cand_path, "w").write("\n".join(chosen) + "\n")
    text_out = "\n".join(out) + "\n"
    open(out_path, "w").write(text_out)
    print(text_out, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
