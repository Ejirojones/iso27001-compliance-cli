"""
a8_15_logging.py

A.8.15 Logging check.

Settings sourced directly from the CIS Ubuntu Linux 24.04 LTS Benchmark
v2.0.0, Level 1 (Server & Workstation) profile:
- 6.1.2.1  Ensure rsyslog is installed
- 6.1.2.2  Ensure rsyslog service is enabled and active

Note: auditd (6.2.1.1, 6.2.1.2) was deliberately excluded, as it is a
Level 2 setting (see methodology Section 3), kept out for consistency
with this project's Level-1-only scope.
"""

from base_check import Check


class LoggingCheck(Check):
    control_id = "A.8.15"
    description = "Logging"

    def evaluate(self, host_data):
        control_data = host_data.get("A.8.15", {})

        rsyslog_installed = control_data.get("rsyslog_installed", False)
        rsyslog_service_active = control_data.get("rsyslog_service_active", False)

        observation_specs = [
            ("rsyslog_installed", rsyslog_installed),
            ("rsyslog_service_active", rsyslog_service_active),
        ]

        checks_pass = (
            rsyslog_installed is True
            and rsyslog_service_active is True
        )

        if checks_pass:
            return observation_specs, "satisfied", "pass"
        else:
            return observation_specs, "not-satisfied", "fail"