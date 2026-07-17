"""
cli.py

Main entry point for the ISO 27001 compliance CLI tool.

Usage:
    python3 cli.py                         # run all five checks against all hosts
    python3 cli.py --control <control-id>  # run just one control, e.g. A.8.9,
                                            # A.8.13, A.8.15, A.8.16, or A.8.24
    python3 cli.py --scheduled             # marks this run as cron-triggered,
                                            # rather than manual (see methodology
                                            # Section 7f)

    --control and --scheduled can be combined, e.g.:
    python3 cli.py --control A.8.9 --scheduled

Design rationale:
- Supports both "run everything" and "run one specific control" modes,
  grounded directly in Prowler's and kube-bench's real, documented CLI
  behaviour (methodology Section 7c).
- Wraps observations and findings in a single run-level object carrying
  run_id, trigger_source, and timestamp, matching the real NIST OSCAL
  pattern of separating run-level metadata from individual records
  (methodology Section 7f).
- Uses argparse (Python's built-in library) rather than a third-party
  CLI framework, per the reasoning in methodology Section 7.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Make the checks/ folder importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "checks"))

from a8_9_configuration import ConfigurationCheck
from a8_13_backup import BackupCheck
from a8_15_logging import LoggingCheck
from a8_16_monitoring import MonitoringCheck
from a8_24_cryptography import CryptographyCheck

DATA_DIR = "data"
OUTPUT_DIR = "output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "results.json")

CONTROL_MAP = {
    "A.8.9": ConfigurationCheck,
    "A.8.13": BackupCheck,
    "A.8.15": LoggingCheck,
    "A.8.16": MonitoringCheck,
    "A.8.24": CryptographyCheck,
}


def discover_host_files():
    """Finds every host-*.json file in the data/ folder."""
    if not os.path.isdir(DATA_DIR):
        return []
    return sorted(
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.startswith("host-") and f.endswith(".json")
    )


def run(control_id=None, scheduled=False):
    """
    Runs either all five checks, or one specific control (if control_id
    is given), against every synthetic host found in data/.
    """
    if control_id:
        if control_id not in CONTROL_MAP:
            valid = ", ".join(CONTROL_MAP.keys())
            print(f"Error: unknown control '{control_id}'. Valid options: {valid}")
            sys.exit(1)
        checks_to_run = {control_id: CONTROL_MAP[control_id]}
    else:
        checks_to_run = CONTROL_MAP

    host_files = discover_host_files()
    if not host_files:
        print(f"No host files found in {DATA_DIR}/. "
              f"Run generate_synthetic_hosts.py first.")
        sys.exit(1)

    all_observations = []
    all_findings = []

    for host_file in host_files:
        with open(host_file) as f:
            host_data = json.load(f)

        for cid, CheckClass in checks_to_run.items():
            check = CheckClass()
            observations, finding = check.execute(host_data)
            all_observations.extend(o.to_dict() for o in observations)
            all_findings.append(finding.to_dict())

    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    result = {
        "run_id": run_id,
        "trigger_source": "scheduled" if scheduled else "manual",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "observations": all_observations,
        "findings": all_findings,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Run complete: {run_id} ({result['trigger_source']})")
    print(f"Hosts checked: {len(host_files)}")
    print(f"Controls checked: {len(checks_to_run)}")
    print(f"Findings: {len(all_findings)}")
    print(f"Results written to {OUTPUT_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="ISO 27001 continuous compliance CLI tool."
    )
    parser.add_argument(
        "--control",
        help="Run just one control instead of all five, e.g. A.8.9. "
             "If omitted, all five controls are run.",
        default=None,
    )
    parser.add_argument(
        "--scheduled",
        help="Mark this run as triggered by cron rather than manually.",
        action="store_true",
    )
    args = parser.parse_args()

    run(control_id=args.control, scheduled=args.scheduled)


if __name__ == "__main__":
    main()