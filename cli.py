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
    python3 cli.py --data-dir data_demo --output output/demo_results.json
                                            # point the CLI at a different data
                                            # folder and output location, used
                                            # for the isolated drift demo

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
- --data-dir and --output default to the project's real data/ and
  output/results.json, so the main evaluation pipeline behaves exactly
  as before; these flags exist solely to let a separate, isolated demo
  pipeline reuse the same checking logic without touching the real
  evaluation hosts.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "checks"))

from a8_9_configuration import ConfigurationCheck
from a8_13_backup import BackupCheck
from a8_15_logging import LoggingCheck
from a8_16_monitoring import MonitoringCheck
from a8_24_cryptography import CryptographyCheck

CONTROL_MAP = {
    "A.8.9": ConfigurationCheck, "A.8.13": BackupCheck, "A.8.15": LoggingCheck,
    "A.8.16": MonitoringCheck, "A.8.24": CryptographyCheck,
}


def discover_host_files(data_dir):
    if not os.path.isdir(data_dir):
        return []
    return sorted(
        os.path.join(data_dir, f) for f in os.listdir(data_dir)
        if f.startswith("host-") and f.endswith(".json")
    )


def run(control_id=None, scheduled=False, data_dir="data", output_file=None):
    if output_file is None:
        output_file = os.path.join("output", "results.json")

    if control_id:
        if control_id not in CONTROL_MAP:
            print(f"Error: unknown control '{control_id}'.")
            sys.exit(1)
        checks_to_run = {control_id: CONTROL_MAP[control_id]}
    else:
        checks_to_run = CONTROL_MAP

    host_files = discover_host_files(data_dir)
    if not host_files:
        print(f"No host files found in {data_dir}/.")
        sys.exit(1)

    all_observations, all_findings = [], []
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
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Run complete: {run_id} ({result['trigger_source']}) -> {output_file}")


def main():
    parser = argparse.ArgumentParser(description="ISO 27001 compliance CLI tool.")
    parser.add_argument("--control", default=None)
    parser.add_argument("--scheduled", action="store_true")
    parser.add_argument(
        "--data-dir", default="data",
        help="Folder to read host files from (default: data)",
    )
    parser.add_argument(
        "--output", default=None,
        help="Where to write results (default: output/results.json)",
    )
    args = parser.parse_args()
    run(control_id=args.control, scheduled=args.scheduled,
        data_dir=args.data_dir, output_file=args.output)


if __name__ == "__main__":
    main()