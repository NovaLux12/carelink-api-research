#!/usr/bin/env python3
"""Area K — prove that `resolve.py` can FAIL, by mutating its inputs and requiring a
non-zero exit from each. ZERO requests; works on copies, never on the captures.

WHY THIS EXISTS. `resolve.py` asserts that the pass's headline claim survives the
bytes. Its docstring claims it "cannot report a clean run over a body that no longer
supports the claim". **That claim was false and nobody could tell**, because the
script's own offset check was `re.search(pat, body[off-40 : off+120])` — a
NEIGHBOURHOOD match. Prepending one byte left every pattern still matching while
every printed offset and module span became wrong by one, and the script printed
"VERDICT: all assertions PASS".

This is the trap this same PR adds to `docs/09`: *a number that cannot fail is not
evidence, however small it is.* Reproduced inside the very script written to catch
bad bytes.

So the claim is no longer asserted — it is TESTED, here, and the test is committed so
the next person can re-run it rather than take it on trust.

Each mutant below is applied to a THROWAWAY COPY of the captures directory. The real
captures are never modified. A mutant passes only if `resolve.py` exits NON-ZERO and
names a failure; a mutant that still exits 0 is reported and the whole script exits
non-zero, because that means an assertion cannot fail.

Run: python3 resolve-mutants.py <captures-dir> <dir-holding-resolve.py>
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

CAPTURES = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
RESOLVE = os.path.join(HERE, "resolve.py")
CHUNK = "k-6746-c6795ff7e9ff468d-js.b"
MAIN = "k-main.b"


def mutate_prepend_one_byte(d):
    """THE blocker-1 mutant: prepend 'X'. Every offset shifts by 1."""
    p = os.path.join(d, CHUNK)
    b = open(p, "rb").read()
    open(p, "wb").write(b"X" + b)


def mutate_append_one_byte(d):
    """A CONTROL, not a mutant — see CONTROLS below."""
    p = os.path.join(d, CHUNK)
    b = open(p, "rb").read()
    open(p, "wb").write(b + b"X")


def mutate_drop_first_z2(d):
    """Break read 1: rename the alias so the chunk no longer reads the flags selector."""
    p = os.path.join(d, CHUNK)
    b = open(p, "rb").read()
    assert b.count(b"select(_.z2)") == 1
    open(p, "wb").write(b.replace(b"select(_.z2)", b"select(_.zX)"))


def mutate_drop_second_z2(d):
    p = os.path.join(d, CHUNK)
    b = open(p, "rb").read()
    assert b.count(b"select(F.z2)") == 1
    open(p, "wb").write(b.replace(b"select(F.z2)", b"select(F.zX)"))


def mutate_post_def_breaks(d):
    """Break the POST definition: reqUrl no longer destructured to b.

    LENGTH-PRESERVING (b -> x). An earlier version of this mutant used `reqXX`,
    which is one byte longer and therefore shifted every later offset — so the
    script reported a downstream A-offset failure instead of the A8 failure the
    mutation was meant to exercise. A mutant that fails for the wrong reason is a
    test that has stopped testing what it claims to."""
    p = os.path.join(d, CHUNK)
    b = open(p, "rb").read()
    open(p, "wb").write(b.replace(b"getPeriodicDataWithPost({reqUrl:b,",
                                 b"getPeriodicDataWithPost({reqUrl:x,", 1))


def mutate_post_call_breaks(d):
    """Decouple the POST call from the value: reqUrl: y -> reqUrl: q."""
    p = os.path.join(d, CHUNK)
    b = open(p, "rb").read()
    assert b.count(b"getPeriodicDataWithPost({reqUrl:y") == 1
    open(p, "wb").write(b.replace(b"getPeriodicDataWithPost({reqUrl:y",
                                 b"getPeriodicDataWithPost({reqUrl:q", 1))


def mutate_flow_breaks(d):
    """Break the unpack: E is no longer h.messageEndpoint. LENGTH-PRESERVING."""
    p = os.path.join(d, CHUNK)
    b = open(p, "rb").read()
    assert b.count(b",E=h.messageEndpoint;") == 1
    open(p, "wb").write(b.replace(b",E=h.messageEndpoint;", b",E=q.messageEndpoint;", 1))


def mutate_main_key_changed(d):
    """Change the dotted key in the main bundle. LENGTH-PRESERVING (s -> Z)."""
    p = os.path.join(d, MAIN)
    b = open(p, "rb").read()
    open(p, "wb").write(b.replace(b'"system.gc.gz.transition.flags"',
                                 b'"system.gc.gz.transition.flagZs"', 1))


def mutate_main_selector_unbound(d):
    """Repoint `be` at a different config key. LENGTH-PRESERVING (I -> Z)."""
    p = os.path.join(d, MAIN)
    b = open(p, "rb").read()
    open(p, "wb").write(b.replace(b"gt.guardianCumulusPeriodicAPI)",
                                 b"gt.guardianCumulusPeriodicAPZ)", 1))


def mutate_main_export_remapped(d):
    """`z2` no longer maps to `be`."""
    p = os.path.join(d, MAIN)
    b = open(p, "rb").read()
    assert b.count(b"z2:()=>be") == 1
    open(p, "wb").write(b.replace(b"z2:()=>be", b"z2:()=>q", 1))


def mutate_main_gains_a_z2_read(d):
    """Area V's negative reversed: the eager bundle now reads .z2 once.

    LENGTH-PRESERVING (a.b -> .z2, both 3 chars). This is a SYNTHETIC token, not
    real JavaScript — A9 counts the `\\.z2\\b` occurrences and nothing here parses JS.
    Labelled as synthetic so nobody later reads it as a claim about the bundle."""
    p = os.path.join(d, MAIN)
    b = open(p, "rb").read()
    open(p, "wb").write(b.replace(b"(0,e.UX)(a.b)", b"(0,e.UX)(.z2)", 1))


def mutate_chunk_gains_third_4265_import(d):
    """A third import of 4265 -> A1 (exactly twice) must fail. LENGTH-PRESERVING."""
    p = os.path.join(d, CHUNK)
    b = open(p, "rb").read()
    open(p, "wb").write(b.replace(b"F=o(4265),Q=o(68940)",
                                 b"F=o(4265),G=o(4265)x", 1))


def mutate_truncate_chunk(d):
    """Truncate below the POST definition."""
    p = os.path.join(d, CHUNK)
    b = open(p, "rb").read()
    open(p, "wb").write(b[:60000])


# Each must make resolve.py exit NON-ZERO.
MUTANTS = [
    ("prepend one byte (the blocker-1 mutant)", mutate_prepend_one_byte),
    ("read 1 no longer selects .z2", mutate_drop_first_z2),
    ("read 2 no longer selects .z2", mutate_drop_second_z2),
    ("POST definition: reqUrl not destructured to b", mutate_post_def_breaks),
    ("POST call: reqUrl decoupled from the value", mutate_post_call_breaks),
    ("flow: E no longer h.messageEndpoint", mutate_flow_breaks),
    ("main: dotted key renamed", mutate_main_key_changed),
    ("main: selector repointed at another key", mutate_main_selector_unbound),
    ("main: export table no longer maps z2 to be", mutate_main_export_remapped),
    ("main: eager bundle gains a .z2 read (A9)", mutate_main_gains_a_z2_read),
    ("chunk: a third import of module 4265 (A1)", mutate_chunk_gains_third_4265_import),
    ("chunk: truncated below the POST definition", mutate_truncate_chunk),
]

# Each must leave resolve.py exiting ZERO. A suite with no expected-to-PASS cases
# cannot tell a working assertion from an absent one, and every control then reads
# as a defect.
CONTROLS = [
    ("append one byte (shifts no cited offset)", mutate_append_one_byte),
]


def run(d):
    return subprocess.run([sys.executable, RESOLVE, d],
                          capture_output=True, text=True)


o = []
w = o.append
w("=" * 96)
w("RESOLVE.MUTANTS — each capture mutation MUST make resolve.py exit non-zero.")
w("Applied to throwaway copies; the real captures are never modified. ZERO requests.")
w("=" * 96)
w("")

base = run(CAPTURES)
w("BASELINE (unmutated captures): exit %d  %s"
  % (base.returncode, "PASS as required" if base.returncode == 0
     else "*** FAIL — the baseline itself is broken, every result below is void ***"))
w("")
if base.returncode != 0:
    w(base.stdout[-3000:])
    print("\n".join(o))
    raise SystemExit(2)

failed = []
for name, fn in MUTANTS:
    d = tempfile.mkdtemp(prefix="resolve-mutant-")
    try:
        for f in os.listdir(CAPTURES):
            src = os.path.join(CAPTURES, f)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(d, f))
        fn(d)
        r = run(d)
        caught = r.returncode != 0
        named = ""
        if caught:
            fails = re.findall(r"^\s+- (.+)$", r.stdout, re.M)
            named = fails[0][:88] if fails else "(no named failure line)"
        else:
            failed.append(name)
        w("%-4s exit %-3d %-52s %s"
          % ("ok" if caught else "MISS", r.returncode, name, named))
    finally:
        shutil.rmtree(d, ignore_errors=True)

w("")
w("-" * 96)
w("CONTROLS — each MUST leave resolve.py exiting zero. A suite with no")
w("expected-to-PASS case cannot tell a working assertion from an absent one.")
w("-" * 96)
control_bad = []
for name, fn in CONTROLS:
    d = tempfile.mkdtemp(prefix="resolve-control-")
    try:
        for f in os.listdir(CAPTURES):
            src = os.path.join(CAPTURES, f)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(d, f))
        fn(d)
        r = run(d)
        if r.returncode != 0:
            control_bad.append(name)
        w("%-4s exit %-3d %-52s %s"
          % ("ok" if r.returncode == 0 else "BAD", r.returncode, name,
             "" if r.returncode == 0
             else "*** a control that must pass did not — the suite is mis-specified ***"))
    finally:
        shutil.rmtree(d, ignore_errors=True)

w("")
w("=" * 96)
w("%d of %d mutants caught, %d of %d controls behaved."
  % (len(MUTANTS) - len(failed), len(MUTANTS),
     len(CONTROLS) - len(control_bad), len(CONTROLS)))
if failed:
    w("")
    w("MUTANTS THAT STILL PASS — each is an assertion that CANNOT FAIL:")
    for f in failed:
        w("  - %s" % f)
    w("")
    w("This is the blocker-1 defect reproduced. Fix the anchoring before trusting")
    w("any claim resting on resolve.py.")
else:
    w("Every mutation is caught. resolve.py's 'cannot report a clean run over a body")
    w("that no longer supports the claim' is TESTED here, not asserted.")
w("=" * 96)
print("\n".join(o))
sys.exit(1 if (failed or control_bad) else 0)