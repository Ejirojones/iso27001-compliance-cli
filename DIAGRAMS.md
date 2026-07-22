# System Diagrams

---

## 1. Architecture

Shows the main pieces of the system and how they connect.

```mermaid
flowchart TB
    Cron["cron<br/>(daily, 2am)"]
    Refresh["refresh_hosts.py"]
    Drift["simulate_drift.py"]
    Data["data/<br/>host-01, host-02, host-03"]
    CLI["cli.py"]
    Base["Check base class"]
    C1["ConfigurationCheck"]
    C2["BackupCheck"]
    C3["LoggingCheck"]
    C4["MonitoringCheck"]
    C5["CryptographyCheck"]
    Results["output/results.json"]
    DashGen["dashboard/generate_dashboard.py"]
    Dashboard["dashboard/dashboard.html"]
    Viewer["Person viewing it"]

    Cron --> Refresh --> Drift --> CLI
    CLI --> Data
    CLI --> Base
    Base --> C1 & C2 & C3 & C4 & C5
    CLI --> Results
    Cron --> DashGen
    DashGen --> Results
    DashGen --> Dashboard
    Viewer --> Dashboard
    Dashboard -.auto-refresh.-> Dashboard
```

---

## 2. Sequence (one full cycle)

Shows the order things happen in, step by step, during one automatic run.

```mermaid
sequenceDiagram
    participant Cron
    participant Refresh as refresh_hosts.py
    participant Drift as simulate_drift.py
    participant CLI as cli.py
    participant Check as Check subclass
    participant Results as results.json
    participant DashGen as generate_dashboard.py
    participant Dashboard as dashboard.html
    participant Viewer

    Cron->>Refresh: run
    Refresh->>Refresh: reset host-01/02, refresh host-03 timestamp only
    Cron->>Drift: run
    Drift->>Drift: maybe change one setting on host-03
    Cron->>CLI: run --scheduled
    loop for each of the 5 controls, each host
        CLI->>Check: execute(host_data)
        Check-->>CLI: observations + finding
    end
    CLI->>Results: write
    Cron->>DashGen: run
    DashGen->>Results: read
    DashGen->>Dashboard: write updated HTML
    Viewer->>Dashboard: open in browser
    Dashboard->>Dashboard: auto-refresh timer
```

---

## 3. Class diagram

Shows how the code itself is structured, one shared base, five checks built on it.

```mermaid
classDiagram
    class Check {
        -control_id: str
        -description: str
        +execute(host_data: dict) Observation[], Finding
    }
    class ConfigurationCheck {
        -ufw_installed: bool
        -min_password_length: int
    }
    class BackupCheck {
        -backup_status: str
        -backup_tested: bool
    }
    class LoggingCheck {
        -rsyslog_installed: bool
    }
    class MonitoringCheck {
        -aide_installed: bool
    }
    class CryptographyCheck {
        -ciphers_config: str
        -pqc_key_exchange_configured: bool
    }
    Check <|-- ConfigurationCheck
    Check <|-- BackupCheck
    Check <|-- LoggingCheck
    Check <|-- MonitoringCheck
    Check <|-- CryptographyCheck
    class Observation {
        +observation_id: str
        +hostname: str
        +control_id: str
    }
    class Finding {
        +finding_id: str
        +status: str
        +reason: str
    }
    Check ..> Observation : creates
    Check ..> Finding : creates
    Finding "1" --> "1..*" Observation : references
```

---

## 4. Activity diagram (decision logic)

Shows the actual decisions the CLI makes while running, not just the order of events.

```mermaid
flowchart TD
    Start([Start]) --> Q1{--control flag given?}
    Q1 -- yes --> One[Run only that one control]
    Q1 -- no --> All[Run all five controls]
    One --> Read[Read host data]
    All --> Read
    Read --> Q2{Does this control apply<br/>to this host?}
    Q2 -- no, e.g. no SSH --> NA[Mark as Not Applicable]
    Q2 -- yes --> Eval[Check settings against<br/>required values]
    Eval --> Q3{All settings correct?}
    Q3 -- yes --> Pass[Mark as Pass]
    Q3 -- no --> Fail[Mark as Fail]
    NA --> Record[Record observation + finding]
    Pass --> Record
    Fail --> Record
    Record --> Q4{More controls or<br/>hosts left?}
    Q4 -- yes --> Read
    Q4 -- no --> Write[Write results.json]
    Write --> Dash[Trigger dashboard generation]
    Dash --> End([End])
```