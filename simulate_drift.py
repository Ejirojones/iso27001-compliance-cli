"""
simulate_drift.py

Simulates configuration drift on a single, dedicated demo host, purely
to demonstrate the cron -> CLI -> dashboard pipeline reacting to a
genuine change, without touching the three fixed hosts (host-01,
host-02, host-03) used for the project's actual evaluation.

Important: this script only ever modifies data_demo/host-03.json,
never anything inside data/. The evaluation hosts remain fixed and
reproducible at all times; this demo host is a separate, clearly
labelled copy created purely for showing the automation working.

Each run has a small chance of flipping one random setting on the
demo host, mimicking a real setting silently changing between checks
(e.g. a firewall service being stopped, a backup starting to fail).

Run this before cli.py in the demo cycle:
    python3 simulate_drift.py
"""

import json
import random

DEMO_HOST_FILE = "data_demo/host-03.json"
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
    with open(DEMO_HOST_FILE) as f:
        return json.load(f)


def save_demo_host(data):
    with open(DEMO_HOST_FILE, "w") as f:
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
        print(f"Demo host updated: {DEMO_HOST_FILE}")
    else:
        print(f"Demo host unchanged: {DEMO_HOST_FILE}")


if __name__ == "__main__":
    main()