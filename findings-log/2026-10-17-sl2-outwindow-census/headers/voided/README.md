# voided/ — capture files from invocations that produced NO ledger row.
#
# 2026-10-17, the first run of this pass: the queue file carried a header line
# (`role\tcrawl\tpath\toutname`), probe.sh had no guard for a non-path line, and
# three curl invocations were built against the literal path "path". All three
# died at DNS resolution -- `curl: (6) Could not resolve host:
# index.commoncrawl.orgpath` -- so NO request reached the network and none carries
# a status. A fourth invocation was killed when its parent shell exited.
#
# probe.sh now REFUSES any queue line whose path does not start with `/CC-MAIN-`,
# writing it to run.log.refused instead of sending it. The files are kept, not
# deleted: the retraction history is the evidence (AGENTS.md section 3).
