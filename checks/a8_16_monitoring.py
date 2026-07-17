"""
a8_16_monitoring.py

A.8.16 Monitoring Activities check.

Settings sourced directly from the CIS Ubuntu Linux 24.04 LTS Benchmark
v2.0.0, Level 1 (Server & Workstation) profile:
- 6.3.1  Ensure AIDE is installed
- 6.3.2  Ensure filesystem integrity is regularly checked
  (dailyaidecheck.timer enabled and active)

Important limitation (see methodology Section 3,):
AIDE is a file integrity checking tool, not a SIEM-style live monitoring
system. It is the closest real, CIS-grounded setting available for this
control, but is a narrower, adjacent substitute for the broader
"system monitoring" concept described in Montesino, Fenz and Baluja
(2012), not an exact equivalent.
"""

from base_check import Check


class MonitoringCheck(Check):
    control_id = "A.8.16"
    description = "Monitoring Activities"

    def evaluate(self, host_data):
        control_data = host_data.get("A.8.16", {})

        aide_installed = control_data.get("aide_installed", False)
        dailyaidecheck_timer_enabled = control_data.get("dailyaidecheck_timer_enabled", False)
        dailyaidecheck_timer_active = control_data.get("dailyaidecheck_timer_active", False)

        observation_specs = [
            ("aide_installed", aide_installed),
            ("dailyaidecheck_timer_enabled", dailyaidecheck_timer_enabled),
            ("dailyaidecheck_timer_active", dailyaidecheck_timer_active),
        ]

        checks_pass = (
            aide_installed is True
            and dailyaidecheck_timer_enabled is True
            and dailyaidecheck_timer_active is True
        )

        if checks_pass:
            return observation_specs, "satisfied", "pass"
        else:
            return observation_specs, "not-satisfied", "fail"