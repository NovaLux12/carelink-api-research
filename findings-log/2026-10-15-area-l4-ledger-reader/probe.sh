#!/bin/sh
# probe.sh — the record of what was sent by 2026-10-15-area-l4-ledger-reader.
#
# NOTHING WAS SENT. This pass had a cap of 0 requests and used 0. There is no
# curl here to run, and adding one would be the scope drift the claim warned
# about ("if the work seems to need a request, that is the finding that the
# scope drifted — stop and record it as the successor instead").
#
# The work is done by read-area-l.py, which reads files under findings-log/ and
# writes nothing outside its own directory. The commands below are the ones that
# were actually run, in order; each is a local read.
#
#   python3 read-area-l.py population    # count the population, before reading it
#   python3 read-area-l.py schemas       # the schema figures, under rules K1-K3
#   python3 read-area-l.py manifest      # write manifest.tsv, precedence order
#   python3 read-area-l.py census        # the census, compared cell by cell
#   python3 read-area-l.py self-test     # the controls, exercised
#
# Network egress: none. No vendor host, no archive host, no Common Crawl API.
# Nothing here can be made to send a request by editing an argument.

set -eu
echo "0 of a 0 cap — this pass sends no requests. See run.log for what was run."
python3 read-area-l.py population
python3 read-area-l.py schemas
python3 read-area-l.py manifest
python3 read-area-l.py census
python3 read-area-l.py self-test