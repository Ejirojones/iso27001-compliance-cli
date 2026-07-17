"""
base_check.py

Shared base class for all ISO 27001 control checks.

Design rationale (see methodology Section 7d, 8):
- Follows the DRY principle (Hunt and Thomas, 1999): the repetitive work of
  building Observation and Finding records is written once here, not
  duplicated in each of the five subclasses.
- Structure (a shared base class with an execute() method, one subclass per
  control) is grounded directly in Prowler's real, documented check pattern.
- Observation/Finding split is grounded directly in the real NIST OSCAL
  Assessment Results schema.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone


class Observation:
    """Represents a single 'what was checked' record, matching the
    project's OSCAL-inspired schema."""

    def __init__(self, observation_id, hostname, control_id, description,
                 method, setting, value):
        self.observation_id = observation_id
        self.hostname = hostname
        self.control_id = control_id
        self.description = description
        self.method = method
        self.collected = datetime.now(timezone.utc).isoformat()
        self.setting = setting
        self.value = value

    def to_dict(self):
        return {
            "observation_id": self.observation_id,
            "hostname": self.hostname,
            "control_id": self.control_id,
            "description": self.description,
            "method": self.method,
            "collected": self.collected,
            "setting": self.setting,
            "value": self.value,
        }


class Finding:
    """Represents the pass/fail/not-applicable verdict for a control,
    referencing the observations it was based on."""

    def __init__(self, finding_id, hostname, control_id,
                 related_observation_ids, status, reason):
        self.finding_id = finding_id
        self.hostname = hostname
        self.control_id = control_id
        self.related_observation_ids = related_observation_ids
        self.status = status      # "satisfied" or "not-satisfied"
        self.reason = reason      # "pass", "fail", or "other" (not-applicable)

    def to_dict(self):
        return {
            "finding_id": self.finding_id,
            "hostname": self.hostname,
            "control_id": self.control_id,
            "related_observation_ids": self.related_observation_ids,
            "status": self.status,
            "reason": self.reason,
        }


class Check(ABC):
    """
    Abstract base class every control check inherits from.

    Subclasses must set control_id and description, and implement
    evaluate(), which contains ONLY the logic unique to that control.
    Everything repetitive (building Observation/Finding objects, IDs,
    timestamps) is handled here, once, per the DRY principle.
    """

    control_id = None
    description = None

    def __init__(self):
        if self.control_id is None:
            raise NotImplementedError(
                "Subclasses must set a control_id, e.g. 'A.8.9'"
            )

    @abstractmethod
    def evaluate(self, host_data):
        """
        Subclasses implement this method only.

        Must return a tuple: (observation_specs, status, reason)

        - observation_specs: a list of (setting_name, value) tuples,
          one per setting checked.
        - status: "satisfied" or "not-satisfied"
        - reason: "pass", "fail", or "other"
        """
        raise NotImplementedError

    def execute(self, host_data):
        """
        Shared logic (DRY): runs evaluate(), then builds the actual
        Observation and Finding objects from its result. Subclasses
        never need to touch this method.
        """
        hostname = host_data.get("hostname", "unknown-host")
        observation_specs, status, reason = self.evaluate(host_data)

        observations = []
        for index, (setting_name, value) in enumerate(observation_specs, start=1):
            obs_id = f"obs-{hostname}-{self.control_id}-{index}"
            observations.append(
                Observation(
                    observation_id=obs_id,
                    hostname=hostname,
                    control_id=self.control_id,
                    description=f"Checked {setting_name} for {self.control_id}",
                    method="TEST",
                    setting=setting_name,
                    value=value,
                )
            )

        finding = Finding(
            finding_id=f"find-{hostname}-{self.control_id}",
            hostname=hostname,
            control_id=self.control_id,
            related_observation_ids=[o.observation_id for o in observations],
            status=status,
            reason=reason,
        )

        return observations, finding