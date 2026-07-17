"""
generate_synthetic_hosts.py

Generates the three synthetic host input files (host-01, host-02, host-03)
used to test the CLI's five checks.

Design rationale:
- Timestamps are generated RELATIVE to the moment this script is run,
  not hardcoded to a fixed date. An earlier version of this project's
  synthetic data used fixed absolute dates, which was found to silently
  break time-sensitive checks (e.g. backup recency) as real time passed
  beyond the fixed date. Generating fresh, relative timestamps each run
  keeps the demonstration reliable indefinitely.
- Host profiles (fully compliant, fully non-compliant, mixed) match the
  three synthetic hosts already established and documented in the
  project's methodology (Section 5): host-01 passes all five controls,
  host-02 fails all five, host-03 is a realistic mix.
- Field names and structure match the real CIS Ubuntu 24.04 Benchmark
  settings sourced and documented in methodology Section 3.

Run this script before running the CLI, to (re)generate fresh input data:
    python3 generate_synthetic_hosts.py
"""

import json
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = "data"

WEAK_CIPHERS = "3des-cbc,aes128-cbc,aes256-cbc"
STRONG_CIPHERS = "chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes256-ctr"


def iso_now_minus(hours=0, days=0):
    """Returns an ISO timestamp relative to the current real time."""
    t = datetime.now(timezone.utc) - timedelta(hours=hours, days=days)
    return t.isoformat().replace("+00:00", "Z")


def build_host(hostname, profile):
    """profile is one of: 'compliant', 'non_compliant', 'mixed'"""

    if profile == "compliant":
        return {
            "hostname": hostname,
            "A.8.9": {
                "ufw_installed": True,
                "ufw_service_active": True,
                "ufw_incoming_default_deny": True,
                "min_password_length": 14,
                "future_dated_password_changes": False,
            },
            "A.8.13": {
                "last_backup_timestamp": iso_now_minus(hours=2),
                "backup_status": "success",
                "backup_tested": True,
            },
            "A.8.15": {
                "rsyslog_installed": True,
                "rsyslog_service_active": True,
            },
            "A.8.16": {
                "aide_installed": True,
                "dailyaidecheck_timer_enabled": True,
                "dailyaidecheck_timer_active": True,
            },
            "A.8.24": {
                "ciphers_config": STRONG_CIPHERS,
                "pqc_key_exchange_configured": True,
            },
        }

    if profile == "non_compliant":
        return {
            "hostname": hostname,
            "A.8.9": {
                "ufw_installed": False,
                "ufw_service_active": False,
                "ufw_incoming_default_deny": False,
                "min_password_length": 8,
                "future_dated_password_changes": True,
            },
            "A.8.13": {
                "last_backup_timestamp": iso_now_minus(days=20),
                "backup_status": "failed",
                "backup_tested": False,
            },
            "A.8.15": {
                "rsyslog_installed": False,
                "rsyslog_service_active": False,
            },
            "A.8.16": {
                "aide_installed": False,
                "dailyaidecheck_timer_enabled": False,
                "dailyaidecheck_timer_active": False,
            },
            "A.8.24": {
                "ciphers_config": WEAK_CIPHERS,
                "pqc_key_exchange_configured": False,
            },
        }

    if profile == "mixed":
        return {
            "hostname": hostname,
            "A.8.9": {
                "ufw_installed": True,
                "ufw_service_active": True,
                "ufw_incoming_default_deny": False,   # fails
                "min_password_length": 14,
                "future_dated_password_changes": True,  # fails
            },
            "A.8.13": {
                "last_backup_timestamp": iso_now_minus(hours=1),
                "backup_status": "success",
                "backup_tested": False,  # fails
            },
            "A.8.15": {
                "rsyslog_installed": True,
                "rsyslog_service_active": True,
            },
            "A.8.16": {
                "aide_installed": True,
                "dailyaidecheck_timer_enabled": True,
                "dailyaidecheck_timer_active": False,  # fails
            },
            "A.8.24": {
                "ciphers_config": STRONG_CIPHERS,
                "pqc_key_exchange_configured": True,
            },
        }

    raise ValueError(f"Unknown profile: {profile}")


def main():
    hosts = {
        "host-01": "compliant",
        "host-02": "non_compliant",
        "host-03": "mixed",
    }

    for hostname, profile in hosts.items():
        host_data = build_host(hostname, profile)
        path = f"{OUTPUT_DIR}/{hostname}.json"
        with open(path, "w") as f:
            json.dump(host_data, f, indent=2)
        print(f"Generated {path} ({profile})")


if __name__ == "__main__":
    main()