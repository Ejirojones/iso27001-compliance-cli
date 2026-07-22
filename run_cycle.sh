#!/bin/bash
#
# What this does, in order:
# 1. Refreshes the test data. host-01 and host-02 get fully reset to
#    their normal clean/broken state with a fresh timestamp. host-03
#    only gets its timestamp refreshed, everything else about it stays
#    as it currently is, so any drift from before isn't lost.
# 2. Maybe changes one setting on host-03, to simulate something
#    breaking on a real machine over time.
# 3. Actually runs the five checks. This checks all three machines,
#    host-01 and host-02 included, every single time.
# 4. Rebuilds the dashboard so it shows whatever just happened.
#
# This is the one file cron runs automatically.

cd /home/ejiro/iso27001-compliance-cli || exit 1

python3 refresh_hosts.py
python3 simulate_drift.py
python3 cli.py --scheduled
python3 dashboard/generate_dashboard.py