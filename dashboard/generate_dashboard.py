"""
generate_dashboard.py

Reads output/results.json (produced by cli.py) and generates a static
HTML dashboard, matching the design finalised in the project's system
design phase.

Design rationale:
- Static, self-contained HTML, following the same pattern used by two
  real, established tools examined earlier in this project (OpenSCAP,
  Chef InSpec), which generate a report from a scan rather than run a
  live server (methodology Section 6).
- Auto-refresh uses a plain HTML meta tag, keeping the same
  self-contained approach (methodology Section 7a).
- Layout follows the wireframe design: header with run info, a summary
  bar, a per-host summary table, then one detail section per control,
  all shown in full rather than behind tabs or links.

Run this after cli.py has produced output/results.json:
    python3 dashboard/generate_dashboard.py
"""

import argparse
import json
import os
from datetime import datetime

REFRESH_INTERVAL_SECONDS = 300  # 5 minutes; adjust to taste

CONTROL_TITLES = {
    "A.8.9": "A.8.9 &middot; Configuration Management",
    "A.8.13": "A.8.13 &middot; Information Backup",
    "A.8.15": "A.8.15 &middot; Logging",
    "A.8.16": "A.8.16 &middot; Monitoring Activities",
    "A.8.24": "A.8.24 &middot; Use of Cryptography",
}


def load_results(results_file):
    if not os.path.exists(results_file):
        raise FileNotFoundError(
            f"{results_file} not found. Run cli.py first to generate results."
        )
    with open(results_file) as f:
        return json.load(f)


def finding_label(finding):
    """Turns a finding's status/reason into a plain label and a CSS class."""
    if finding["reason"] == "other":
        return "N/A", "na"
    if finding["status"] == "satisfied":
        return "Pass", "pass"
    return "Fail", "fail"


def build_summary(results):
    findings = results["findings"]
    total = len(findings)
    satisfied = sum(1 for f in findings if f["status"] == "satisfied")
    percent = round((satisfied / total) * 100) if total else 0
    hostnames = sorted(set(f["hostname"] for f in findings))
    return {
        "percent": percent,
        "satisfied": satisfied,
        "total": total,
        "host_count": len(hostnames),
        "hostnames": hostnames,
    }


def build_host_table_rows(results, hostnames, control_ids):
    findings_by_host_control = {
        (f["hostname"], f["control_id"]): f for f in results["findings"]
    }
    rows = []
    for hostname in hostnames:
        cells = []
        host_findings = [
            findings_by_host_control.get((hostname, cid)) for cid in control_ids
        ]
        for finding in host_findings:
            cells.append(finding_label(finding) if finding else ("-", ""))
        satisfied_count = sum(
            1 for f in host_findings if f and f["status"] == "satisfied"
        )
        if satisfied_count == len(control_ids):
            overall, overall_class = "Pass", "pass"
        elif satisfied_count == 0:
            overall, overall_class = "Fail", "fail"
        else:
            overall, overall_class = "Mixed", "mixed"
        rows.append((hostname, cells, overall, overall_class))
    return rows


def build_control_detail(results, control_id, hostnames):
    observations = [
        o for o in results["observations"] if o["control_id"] == control_id
    ]
    settings = []
    seen = set()
    for o in observations:
        if o["setting"] not in seen:
            settings.append(o["setting"])
            seen.add(o["setting"])

    values_by_host_setting = {
        (o["hostname"], o["setting"]): o["value"] for o in observations
    }

    rows = []
    for setting in settings:
        row = [setting]
        for hostname in hostnames:
            value = values_by_host_setting.get((hostname, setting), "-")
            row.append(str(value))
        rows.append(row)
    return rows


def render_html(results):
    summary = build_summary(results)
    control_ids = list(CONTROL_TITLES.keys())
    hostnames = summary["hostnames"]

    host_rows = build_host_table_rows(results, hostnames, control_ids)

    host_table_header = "".join(f"<th>{cid}</th>" for cid in control_ids)
    host_table_rows_html = ""
    for hostname, cells, overall, overall_class in host_rows:
        cells_html = "".join(
            f'<td class="{css_class}">{label}</td>' for label, css_class in cells
        )
        host_table_rows_html += (
            f"<tr><td>{hostname}</td>{cells_html}"
            f'<td class="{overall_class}"><strong>{overall}</strong></td></tr>\n'
        )

    control_sections_html = ""
    for control_id in control_ids:
        rows = build_control_detail(results, control_id, hostnames)
        header_html = "<th>Setting</th>" + "".join(f"<th>{h}</th>" for h in hostnames)
        rows_html = ""
        for row in rows:
            cells_html = "".join(f"<td>{cell}</td>" for cell in row)
            rows_html += f"<tr>{cells_html}</tr>\n"
        control_sections_html += f"""
        <h2>{CONTROL_TITLES[control_id]}</h2>
        <table>
          <tr>{header_html}</tr>
          {rows_html}
        </table>
        """

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="{REFRESH_INTERVAL_SECONDS}">
<title>ISO 27001 Compliance Dashboard</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 2rem; color: #222; }}
  h1 {{ margin-bottom: 0.2rem; }}
  .meta {{ color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }}
  .summary {{ display: flex; gap: 1rem; margin-bottom: 2rem; }}
  .summary div {{ border: 1px solid #ccc; border-radius: 6px; padding: 1rem; flex: 1; text-align: center; }}
  .summary .big {{ font-size: 1.6rem; font-weight: bold; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 2rem; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: center; font-size: 0.9rem; }}
  th {{ background: #f4f4f4; }}
  td:first-child, th:first-child {{ text-align: left; }}
  .pass {{ background: #e6f4ea; color: #1e7d34; font-weight: 600; }}
  .fail {{ background: #fbe9e7; color: #c62828; font-weight: 600; }}
  .mixed {{ background: #fff8e1; color: #a06800; font-weight: 600; }}
  .na {{ background: #eceff1; color: #607d8b; font-weight: 600; }}
</style>
</head>
<body>

<h1>ISO 27001 Compliance Dashboard</h1>
<p class="meta">
  Run: {results['run_id']} ({results['trigger_source']}) &middot;
  Generated: {generated_at} &middot;
  Auto-refreshes every {REFRESH_INTERVAL_SECONDS // 60} minutes
</p>

<div class="summary">
  <div><div class="big">{summary['percent']}%</div>Overall compliance</div>
  <div><div class="big">{summary['satisfied']} / {summary['total']}</div>Checks passing</div>
  <div><div class="big">{summary['host_count']}</div>Hosts checked</div>
</div>

<h2>Per-Host Summary</h2>
<table>
  <tr><th>Host</th>{host_table_header}<th>Overall</th></tr>
  {host_table_rows_html}
</table>

{control_sections_html}

</body>
</html>
"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate the compliance dashboard.")
    parser.add_argument(
        "--results", default=os.path.join("output", "results.json"),
        help="Path to the results JSON to read (default: output/results.json)",
    )
    parser.add_argument(
        "--output", default=os.path.join("dashboard", "dashboard.html"),
        help="Path to write the dashboard HTML to (default: dashboard/dashboard.html)",
    )
    args = parser.parse_args()

    results = load_results(args.results)
    html = render_html(results)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        f.write(html)
    print(f"Dashboard written to {args.output}")


if __name__ == "__main__":
    main()