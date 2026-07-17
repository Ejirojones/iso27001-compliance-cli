"""
a8_13_backup.py

A.8.13 Information Backup check.

No settings for this control are grounded in the CIS Ubuntu benchmark
(confirmed absent via full-text search, see methodology Section 3).
This check's structure is therefore the project's own design, retained
on the strength of Montesino, Fenz and Baluja's (2012) automatability
precedent alone (methodology Section 2).

Backup recency threshold: NOT specified by ISO 27001 or the CIS
benchmark (both confirmed to leave this organisation-defined, see
methodology Section 3). The 48-hour threshold below is this project's
own stated policy assumption for its fictional synthetic hosts, not a
value drawn from any standard.
"""

from datetime import datetime, timezone, timedelta
from base_check import Check

BACKUP_RECENCY_THRESHOLD_HOURS = 48  # Project's own stated assumption


class BackupCheck(Check):
    control_id = "A.8.13"
    description = "Information Backup"

    def evaluate(self, host_data):
        control_data = host_data.get("A.8.13", {})

        last_backup_timestamp = control_data.get("last_backup_timestamp")
        backup_status = control_data.get("backup_status", "unknown")
        backup_tested = control_data.get("backup_tested", False)

        observation_specs = [
            ("last_backup_timestamp", last_backup_timestamp),
            ("backup_status", backup_status),
            ("backup_tested", backup_tested),
        ]

        backup_recent = False
        if last_backup_timestamp:
            try:
                backup_time = datetime.fromisoformat(
                    last_backup_timestamp.replace("Z", "+00:00")
                )
                age = datetime.now(timezone.utc) - backup_time
                backup_recent = age <= timedelta(hours=BACKUP_RECENCY_THRESHOLD_HOURS)
            except ValueError:
                backup_recent = False

        checks_pass = (
            backup_recent
            and backup_status == "success"
            and backup_tested is True
        )

        if checks_pass:
            return observation_specs, "satisfied", "pass"
        else:
            return observation_specs, "not-satisfied", "fail"