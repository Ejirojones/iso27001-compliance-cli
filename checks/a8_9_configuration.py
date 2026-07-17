"""
a8_9_configuration.py

A.8.9 Configuration Management check.

Settings and thresholds sourced directly from the CIS Ubuntu Linux 24.04
LTS Benchmark v2.0.0, Level 1 (Server & Workstation) profile:
- 4.1.1  Ensure ufw is installed
- 4.1.2  Ensure ufw service is configured (enabled and active)
- 4.1.3  Ensure ufw incoming default is configured (deny/reject)
- 5.3.3.2.2  Ensure password length is configured (minimum 14 characters)
- 5.4.1.6  Ensure last password change date is in the past
  (no future-dated password changes)

A host fails this control if ANY of the five settings does not meet
the CIS Level 1 requirement.
"""

from base_check import Check

MIN_PASSWORD_LENGTH = 14  # CIS 5.3.3.2.2, Level 1


class ConfigurationCheck(Check):
    control_id = "A.8.9"
    description = "Configuration Management"

    def evaluate(self, host_data):
        control_data = host_data.get("A.8.9", {})

        ufw_installed = control_data.get("ufw_installed", False)
        ufw_service_active = control_data.get("ufw_service_active", False)
        ufw_incoming_default_deny = control_data.get("ufw_incoming_default_deny", False)
        min_password_length = control_data.get("min_password_length", 0)
        future_dated_password_changes = control_data.get("future_dated_password_changes", True)

        observation_specs = [
            ("ufw_installed", ufw_installed),
            ("ufw_service_active", ufw_service_active),
            ("ufw_incoming_default_deny", ufw_incoming_default_deny),
            ("min_password_length", min_password_length),
            ("future_dated_password_changes", future_dated_password_changes),
        ]

        checks_pass = (
            ufw_installed is True
            and ufw_service_active is True
            and ufw_incoming_default_deny is True
            and min_password_length >= MIN_PASSWORD_LENGTH
            and future_dated_password_changes is False
        )

        if checks_pass:
            return observation_specs, "satisfied", "pass"
        else:
            return observation_specs, "not-satisfied", "fail"