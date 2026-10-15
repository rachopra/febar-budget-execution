"""Exercise the deployed Databricks App's API and record every request/response as Markdown.

Usage: python scripts/app_evidence.py [--profile P] [--app febar-budget-execution]
Writes evidence/app/README.md. Performs real write-backs (alert action, package submission,
quarterly sign-off) so the Lakebase -> Unity Catalog round trip can be verified afterwards.
"""

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


def cli_json(*args, profile):
    return json.loads(subprocess.run(["databricks", *args, "-p", profile, "-o", "json"], capture_output=True, text=True).stdout)


def shorten(obj, max_items=6, max_str=400):
    if isinstance(obj, list):
        out = [shorten(x, max_items, max_str) for x in obj[:max_items]]
        if len(obj) > max_items:
            out.append(f"... {len(obj) - max_items} more items")
        return out
    if isinstance(obj, dict):
        return {k: shorten(v, max_items, max_str) for k, v in obj.items()}
    if isinstance(obj, str) and len(obj) > max_str:
        return obj[:max_str] + "..."
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="fe-vm-rachopra-cyber-demo")
    ap.add_argument("--app", default="febar-budget-execution")
    ap.add_argument("--out", default="evidence/app")
    a = ap.parse_args()

    app = cli_json("apps", "get", a.app, profile=a.profile)
    url = app["url"].rstrip("/")
    token = cli_json("auth", "token", profile=a.profile)["access_token"]
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {token}"
    log = [f"# Databricks App API evidence: `{a.app}`", "",
           f"- URL: {url}",
           f"- App status: {app.get('app_status', {}).get('state')} / compute {app.get('compute_status', {}).get('state')}",
           f"- Active deployment: `{app.get('active_deployment', {}).get('deployment_id')}` "
           f"({app.get('active_deployment', {}).get('status', {}).get('state')})",
           f"- Resources: {', '.join(r['name'] + ' (' + next(k for k in r if k not in ('name', 'description')) + ')' for r in app.get('resources', []))}",
           f"- User API scopes (on-behalf-of-user): {', '.join(app.get('effective_user_api_scopes') or [])}",
           f"- Captured {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ""]

    def call(method, path, title, body=None, **params):
        t0 = time.perf_counter()
        r = s.request(method, f"{url}{path}", json=body, params=params or None, timeout=180)
        ms = (time.perf_counter() - t0) * 1000
        try:
            data = r.json()
        except ValueError:
            data = r.text[:500]
        req = f"{method} {path}" + (f"?{'&'.join(f'{k}={v}' for k, v in params.items())}" if params else "")
        log.extend([f"## {title}", "", f"`{req}` → **HTTP {r.status_code}** in {ms:.0f} ms", ""])
        if body is not None:
            log.extend(["Request body:", "```json", json.dumps(body, indent=1), "```"])
        log.extend(["Response:", "```json", json.dumps(shorten(data), indent=1, default=str)[:6000], "```", ""])
        print(f"{r.status_code} {req} ({ms:.0f} ms)")
        return data

    call("GET", "/api/health", "Health (Lakebase connectivity)")
    call("GET", "/api/me", "Signed-in user and office scope (from office_access_map)")
    call("GET", "/api/overview", "Budget execution dashboard KPIs, funding by office and appropriation")
    call("GET", "/api/burn", "Cumulative obligations vs plan (burn curve)")
    lines = call("GET", "/api/lines", "Unobligated balances approaching expiration, with ML forecast and AI headline", max_days=120)
    top = lines[0]["line_id"] if isinstance(lines, list) and lines else None
    if top:
        call("GET", f"/api/lines/{top}", f"Line detail for {top}: briefing, open PRs, alerts, package draft")
    call("GET", "/api/alerts/summary", "Risk alert summary")
    alerts = call("GET", "/api/alerts", "Critical alerts", severity="Critical")
    if isinstance(alerts, list) and alerts:
        call("POST", f"/api/alerts/{alerts[0]['alert_id']}/actions", "Write-back: acknowledge a critical alert",
             {"action": "Assigned", "assignee": "budget.analyst@dci.example.gov",
              "note": "Prepare apportionment reapportionment request before further obligations."})
    call("GET", "/api/procurement", "Procurement-cycle visibility: pipeline by stage, PALT, open PRs")
    if top:
        draft = call("POST", f"/api/packages/{top}/draft", f"On-demand AI procurement package draft for {top}")
        d = draft.get("draft", {}) if isinstance(draft, dict) else {}
        if d.get("title"):
            call("POST", f"/api/packages/{top}", "Write-back: submit the AI-drafted package to acquisition", {
                "title": d["title"], "acquisition_type": d.get("recommended_acquisition_type"),
                "contract_number": d.get("contract_number"), "amount": float(d.get("amount") or 0),
                "requirement_summary": d.get("requirement_summary"), "justification": d.get("justification"),
                "required_documents": d.get("required_documents") or [], "milestones": d.get("milestones") or []})
    q = call("GET", "/api/quarterly", "Quarterly budget-performance review: quarters, AI narratives, sign-offs")
    if isinstance(q, dict) and q.get("reviews"):
        office = q["reviews"][0]["office_code"]
        call("POST", f"/api/quarterly/{office}/signoff", f"Write-back: CFO sign-off for {office}",
             {"fiscal_year": 2026, "fiscal_quarter": 3, "decision": "Approved with conditions",
              "comment": "Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan."})
    call("POST", "/api/genie", "Ask Genie through the app (on behalf of the signed-in user)",
         {"question": "Which program offices are furthest behind their spend plan?"})

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_text("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
