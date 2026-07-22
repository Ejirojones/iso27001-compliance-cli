"""
simulate_drift.py

Randomly changes one setting on host-03, to simulate a real machine
drifting out of compliance over time. Only ever touches host-03,
host-01 and host-02 stay untouched.

Since host-03 already starts from a mixed state and only one thing
changes at a time, it'll usually still show a realistic mixed
pass/fail result, just not always exactly the same one.

Run this before cli.py.
"""

import json
import random

HOST_FILE = "data/host-03.json"
DRIFT_PROBABILITY = 0.5  # 50% chance something changes on a given run

# Settings that can be flipped, and what "drifted" looks like for each
DRIFTABLE_SETTINGS = [
    ("A.8.9", "ufw_service_active"),
    ("A.8.9", "ufw_incoming_default_deny"),
    ("A.8.13", "backup_status", ["success", "failed"]),
    ("A.8.13", "backup_tested"),
    ("A.8.15", "rsyslog_service_active"),
    ("A.8.16", "dailyaidecheck_timer_active"),
    ("A.8.24", "pqc_key_exchange_configured"),
]


def load_demo_host():
    with open(HOST_FILE) as f:
        return json.load(f)


def save_demo_host(data):
    with open(HOST_FILE, "w") as f:
        json.dump(data, f, indent=2)


def apply_random_drift(data):
    if random.random() > DRIFT_PROBABILITY:
        print("No drift this run.")
        return data, None

    choice = random.choice(DRIFTABLE_SETTINGS)
    control_id, setting = choice[0], choice[1]

    if len(choice) == 3:  # multi-value setting, e.g. backup_status
        options = choice[2]
        current = data[control_id].get(setting)
        new_value = random.choice([v for v in options if v != current])
    else:  # boolean setting: just flip it
        current = data[control_id].get(setting, True)
        new_value = not current

    data[control_id][setting] = new_value
    print(f"Drift applied: {control_id}.{setting} changed to {new_value}")
    return data, (control_id, setting, new_value)


def main():
    data = load_demo_host()
    data, change = apply_random_drift(data)
    save_demo_host(data)
    if change:
        print(f"Demo host updated: {HOST_FILE}")
    else:
        print(f"Demo host unchanged: {HOST_FILE}")


if __name__ == "__main__":
    main()