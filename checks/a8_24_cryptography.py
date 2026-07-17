"""
a8_24_cryptography.py

A.8.24 Use of Cryptography check.

Settings sourced directly from the CIS Ubuntu Linux 24.04 LTS Benchmark
v2.0.0, Level 1 (Server & Workstation) profile:
- 5.1.6   Ensure sshd Ciphers are configured
          (weak ciphers: 3des-cbc, aes128-cbc, aes256-cbc, blowfish,
          cast128, arcfour variants, rijndael-cbc must be excluded)
- 5.1.23  Ensure sshd post-quantum cryptography key exchange is configured

Weak/strong cipher names cross-referenced against the OpenSSH manual
(man7.org), not just the CIS document alone (see methodology Section 3).

This is the ONLY one of the five controls with a genuine "not applicable"
case (methodology Section 6a): a host that does not run SSH at all has
nothing for this check to evaluate. A missing "A.8.24" section, or an
explicit ssh_enabled: false flag, is treated as not-applicable rather
than a failure, using OSCAL's "other" reason value. Not-applicable is
mapped to status "satisfied" here, since a control that genuinely does
not apply should not count as a failure.
"""

from base_check import Check

WEAK_CIPHERS = {
    "3des-cbc", "blowfish", "cast128",
    "aes128-cbc", "aes192-cbc", "aes256-cbc",
    "arcfour", "arcfour128", "arcfour256",
    "rijndael-cbc@lysator.liu.se",
}


class CryptographyCheck(Check):
    control_id = "A.8.24"
    description = "Use of Cryptography"

    def evaluate(self, host_data):
        control_data = host_data.get("A.8.24")

        # Not-applicable case: no A.8.24 section at all, or explicitly
        # flagged as not running SSH.
        if control_data is None or control_data.get("ssh_enabled") is False:
            observation_specs = [("ssh_enabled", False)]
            return observation_specs, "satisfied", "other"

        ciphers_config = control_data.get("ciphers_config", "")
        pqc_key_exchange_configured = control_data.get("pqc_key_exchange_configured", False)

        configured_ciphers = {c.strip() for c in ciphers_config.split(",") if c.strip()}
        weak_ciphers_detected = bool(configured_ciphers & WEAK_CIPHERS)

        observation_specs = [
            ("ciphers_config", ciphers_config),
            ("weak_ciphers_detected", weak_ciphers_detected),
            ("pqc_key_exchange_configured", pqc_key_exchange_configured),
        ]

        checks_pass = (
            weak_ciphers_detected is False
            and pqc_key_exchange_configured is True
        )

        if checks_pass:
            return observation_specs, "satisfied", "pass"
        else:
            return observation_specs, "not-satisfied", "fail"