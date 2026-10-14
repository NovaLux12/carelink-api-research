#!/usr/bin/env bash
# Assemble the two corpus directories that S4's extractor is run over, then RUN
# S4's extractor — the patient pass's own committed script, unmodified — over
# each. Zero requests; pure local file organisation.
#
# WHY TWO DIRECTORIES. The patient corpus S4 counted was 215 files: 211 lazy
# chunks + main + runtime + the f.u name-variant of chunk 2076 + one HTTP error
# page. The clinic corpus has no separate name-variant body, because the 225
# entries were already requested under the names f.u emits (so `common.<hash>.js`
# is one of the 225, and the id form `2076.<hash>.js` was measured separately as
# control C5 and does not exist). So:
#
#   A  chunks-only   225 lazy chunks — the cleanest like-for-like against the
#                    211 lazy chunks the patient side contributes
#   B  full          225 chunks + main + runtime + 1 control body — the closest
#                    structural analogue to S4's 215
#
# B is reported separately and never silently merged into A. The two differ by
# whatever the eager bundle contributes, and that difference is a result.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC=${TMPBODIES:?set TMPBODIES to the directory the sweep wrote bodies into}
OUTROOT=${OUTROOT:-$SRC/corpus}
LEDGER="$HERE/results.jsonl"
rm -rf "$OUTROOT/chunks-only" "$OUTROOT/full"
mkdir -p "$OUTROOT/chunks-only" "$OUTROOT/full"

python3 - "$LEDGER" "$SRC" "$OUTROOT" <<'PY'
import json, os, shutil, sys
ledger, src, outroot = sys.argv[1], sys.argv[2], sys.argv[3]
rows = [json.loads(l) for l in open(ledger) if l.strip()]
# map emitted filename -> body file, using the seq- prefix the sweep wrote
by_seq = {}
for r in rows:
    tag = r["emitted"].replace("/", "_")
    cand = os.path.join(src, f"{r['seq']}-{tag}.b")
    if os.path.exists(cand):
        by_seq[r["seq"]] = (r, cand)
    else:  # the uppercase-extension control keeps its case in the tag already
        alt = os.path.join(src, f"{r['seq']}-{tag}.b")
        if os.path.exists(alt):
            by_seq[r["seq"]] = (r, alt)

n_chunks = n_main = n_runtime = n_ctl = 0
for seq, (r, path) in sorted(by_seq.items()):
    role = str(r.get("role", ""))
    name = r["emitted"] + ".b"
    if role.startswith("SWEEP"):
        for d in ("chunks-only", "full"):
            shutil.copy(path, os.path.join(outroot, d, name))
        n_chunks += 1
    elif role.startswith("C2"):                       # the eager main bundle
        shutil.copy(path, os.path.join(outroot, "full", name)); n_main += 1
    elif role.startswith("C4"):                       # the runtime
        shutil.copy(path, os.path.join(outroot, "full", name)); n_runtime += 1
    elif role.startswith("C1"):                           # ONE control body, the
        # certainly-absent name — the structural analogue of S4's 196-byte HTML
        # 404 page. C3 is the same SPA shell under a different name and is NOT
        # included: S4's corpus carried one error page, not two, and including
        # both would make the file counts incomparable for no analytical gain.
        # C5 and C6 are excluded too — C5 is the id-form of chunk 2076, which does
        # not exist as a body (it IS the SPA shell), and S4's analogue for the
        # name-substitution was the real `common.<hash>.js` body, which here is
        # already one of the 225 because the clinic list was f.u-correct.
        shutil.copy(path, os.path.join(outroot, "full", name.replace(".", "_", 1))); n_ctl += 1
    else:
        print("  UNCLASSIFIED role, not copied:", role, r["emitted"])
print(f"corpus A (chunks-only): {n_chunks} lazy chunks")
print(f"corpus B (full):        {n_chunks} chunks + {n_main} main + {n_runtime} runtime + {n_ctl} control")
PY

for d in chunks-only full; do
  echo "=== S4 extractor over corpus '$d' ==="
  S4_CORPUS="$OUTROOT/$d" S4_OUT="$HERE/s4-$d" \
    python3 "$HERE/../2026-10-14-area-s4-lazy-chunk-control-flow/extract-call-sites.py"
  echo
done