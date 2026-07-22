"""
refresh_hosts.py

Keeps the three test machines up to date without wiping out drift.

host-01 and host-02 should always look the same (fully compliant and
fully non-compliant), so these get completely regenerated every time,
with a fresh timestamp, same as before.

host-03 is different. Since I'm letting it drift on purpose, I can't
just regenerate it from scratch each time, that would wipe out
whatever changed. So for host-03, I only update the backup timestamp
and leave everything else exactly as it currently is.

Run this before simulate_drift.py.
"""

import json
import os
from datetime import datetime, timezone, timedelta

DATA_DIR = "data"
WEAK_CIPHERS = "3des-cbc,aes128-cbc,aes256-cbc"
STRONG_CIPHERS = "chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes256-ctr"


def iso_now_minus(hours=0, days=0):
    t = datetime.now(timezone.utc) - timedelta(hours=hours, days=days)
    return t.isoformat().replace("+00:00", "Z")


def build_fresh_host(hostname, profile):
    if profile == "compliant":
        return {
            "hostname": hostname,
            "A.8.9": {"ufw_installed": True, "ufw_service_active": True,
                      "ufw_incoming_default_deny": True, "min_password_length": 14,
                      "future_dated_password_changes": False},
            "A.8.13": {"last_backup_timestamp": iso_now_minus(hours=2),
                       "backup_status": "success", "backup_tested": True},
            "A.8.15": {"rsyslog_installed": True, "rsyslog_service_active": True},
            "A.8.16": {"aide_installed": True, "dailyaidecheck_timer_enabled": True,
                       "dailyaidecheck_timer_active": True},
            "A.8.24": {"ciphers_config": STRONG_CIPHERS, "pqc_key_exchange_configured": True},
        }
    if profile == "non_compliant":
        return {
            "hostname": hostname,
            "A.8.9": {"ufw_installed": False, "ufw_service_active": False,
                      "ufw_incoming_default_deny": False, "min_password_length": 8,
                      "future_dated_password_changes": True},
            "A.8.13": {"last_backup_timestamp": iso_now_minus(days=20),
                       "backup_status": "failed", "backup_tested": False},
            "A.8.15": {"rsyslog_installed": False, "rsyslog_service_active": False},
            "A.8.16": {"aide_installed": False, "dailyaidecheck_timer_enabled": False,
                       "dailyaidecheck_timer_active": False},
            "A.8.24": {"ciphers_config": WEAK_CIPHERS, "pqc_key_exchange_configured": False},
        }
    raise ValueError(f"Unknown profile: {profile}")


def build_initial_host03():
    """The starting mixed baseline for host-03, used only if host-03.json
    doesn't exist yet (first run)."""
    return {
        "hostname": "host-03",
        "A.8.9": {"ufw_installed": True, "ufw_service_active": True,
                  "ufw_incoming_default_deny": False, "min_password_length": 14,
                  "future_dated_password_changes": True},
        "A.8.13": {"last_backup_timestamp": iso_now_minus(hours=1),
                   "backup_status": "success", "backup_tested": False},
        "A.8.15": {"rsyslog_installed": True, "rsyslog_service_active": True},
        "A.8.16": {"aide_installed": True, "dailyaidecheck_timer_enabled": True,
                   "dailyaidecheck_timer_active": False},
        "A.8.24": {"ciphers_config": STRONG_CIPHERS, "pqc_key_exchange_configured": True},
    }


def refresh_host01_and_02():
    for hostname, profile in [("host-01", "compliant"), ("host-02", "non_compliant")]:
        data = build_fresh_host(hostname, profile)
        path = os.path.join(DATA_DIR, f"{hostname}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Refreshed {path} ({profile}, fresh timestamp)")


def refresh_host03_timestamp_only():
    path = os.path.join(DATA_DIR, "host-03.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    else:
        data = build_initial_host03()
        print(f"host-03.json did not exist, created initial mixed baseline")

    # Only touch the timestamp, leave every other setting (drifted or not) alone
    data["A.8.13"]["last_backup_timestamp"] = iso_now_minus(hours=1)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Refreshed {path} (timestamp only, drift state preserved)")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    refresh_host01_and_02()
    refresh_host03_timestamp_only()


if __name__ == "__main__":
    main()