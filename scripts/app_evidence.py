"""Exercise the deployed Databricks App's API and record every request/response as Markdown.

Usage: python scripts/app_evidence.py [--profile P] [--app febar-budget-execution]
Writes evidence/app/README.md. Performs real write-backs (year-end plan package, reprogramming request,
line note, alert board moves, quarterly sign-off) and exercises the controls (separation of duties,
same-account reprogramming), so the Lakebase -> Unity Catalog round trip can be verified afterwards.
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
    call("GET", "/api/me", "Signed-in user, office scope (from office_access_map) and approval rights")

    # ---- command center: the landing page
    call("GET", "/api/command-center", "Command center: year-end countdown, projected lapse vs actions in flight, "
         "acquisition windows, expiring-dollar composition, offices, top lines, work queue")
    call("GET", "/api/burn", "Cumulative obligations vs approved plan (burn curve)")
    call("GET", "/api/overview", "Budget execution KPIs, funding by office and appropriation")
    call("GET", "/api/search", "Global search (command palette)", q="grant")

    # ---- year-end plan: the recovery workflow
    plan = call("GET", "/api/plan", "Year-end plan: lines projected to lapse, validated AI package drafts, "
                "what is already in flight, and same-account reprogramming matches")
    lines = plan.get("lines", []) if isinstance(plan, dict) else []
    open_lines = [l for l in lines if l.get("draft_amount") and not l.get("draft_issues")
                  and float(l["packaged"]) == 0 and float(l["recovered"]) < float(l["projected_lapse_amount"]) - 1]
    target = open_lines[0] if open_lines else None
    if target:
        lid = target["line_id"]
        call("GET", f"/api/lines/{lid}", f"Line detail for {lid}: briefing, open PRs, alerts, package draft, reprogramming")
        call("POST", f"/api/packages/{lid}/draft", f"On-demand AI package redraft for {lid} (real-time model, validated)")
        room = float(target["projected_lapse_amount"]) - float(target["recovered"])
        call("POST", f"/api/packages/{lid}", f"Write-back: submit the validated batch AI package for {lid} as part of the year-end plan", {
            "title": target["draft_title"], "acquisition_type": target["draft_type"], "contract_number": target["draft_contract"],
            "amount": round(min(float(target["draft_amount"]), room), 2), "requirement_summary": target["draft_requirement_summary"],
            "justification": target["draft_justification"], "required_documents": target["draft_documents"] or [],
            "milestones": target["draft_milestones"] or [], "source": "Year-end plan - batch AI draft"})
        call("POST", f"/api/lines/{lid}/notes", f"Write-back: analyst note on {lid}",
             {"note": "Option exercise submitted from the year-end plan; program office to confirm the bona fide need memo by 7 Aug."})
        call("GET", f"/api/lines/{lid}/notes", f"Notes on {lid}")
    sugg = plan.get("suggestions", []) if isinstance(plan, dict) else []
    if sugg:
        sg = sugg[0]
        req = call("POST", "/api/reprogramming", f"Write-back: reprogramming request {sg['from_line_id']} -> {sg['to_line_id']} within {sg['tas']}", {
            "from_line_id": sg["from_line_id"], "to_line_id": sg["to_line_id"], "amount": sg["amount"],
            "justification": f"Year-end reprogramming within {sg['tas']}: {sg['from_ppa_name']} is projected to lapse; "
                             f"{sg['to_ppa_name']}: {sg['reason']}."})
        if isinstance(req, dict) and req.get("request_id"):
            call("POST", f"/api/reprogramming/{req['request_id']}/decision",
                 "Control: the requester tries to approve their own request (separation of duties, expect 403)",
                 {"decision": "Approved", "note": "self-approval attempt"})
        call("POST", "/api/reprogramming", "Control: a move between different appropriations is refused (expect 400)", {
            "from_line_id": sg["from_line_id"], "to_line_id": next((l["line_id"] for l in lines if l["tas"] != sg["tas"]), sg["to_line_id"]),
            "amount": 10000})
        call("GET", "/api/reprogramming", "Reprogramming requests in scope")

    # ---- alerts board
    call("GET", "/api/alerts/summary", "Risk alert summary")
    alerts = call("GET", "/api/alerts", "High-severity alerts (board cards)", severity="High")
    fresh = next((x for x in alerts if not x.get("last_action")), None) if isinstance(alerts, list) else None
    if fresh:
        aid = fresh["alert_id"]
        call("POST", f"/api/alerts/{aid}/actions", f"Write-back: board move Open -> Acknowledged ({fresh['alert_type']})",
             {"action": "Acknowledged"})
        call("POST", f"/api/alerts/{aid}/actions", "Write-back: board move Acknowledged -> Assigned",
             {"action": "Assigned", "assignee": "budget.analyst@dci.example.gov",
              "note": "Confirm obligation plan for the uncommitted balance before the option-exercise window closes."})
        call("GET", f"/api/alerts/{aid}/history", "Alert history (both moves)")

    # ---- procurement, quarterly review, Genie, activity
    call("GET", "/api/procurement", "Procurement-cycle visibility: pipeline by stage, PALT, open PRs with forecast award")
    call("GET", "/api/packages", "Packages submitted to acquisition and AI drafts")
    q = call("GET", "/api/quarterly", "Quarterly budget-performance review: quarters, AI narratives, sign-offs")
    if isinstance(q, dict) and q.get("reviews"):
        signed = {s["office_code"] for s in q.get("signoffs", []) if s["fiscal_year"] == 2026 and s["fiscal_quarter"] == 3}
        office = next((r["office_code"] for r in q["reviews"] if r["office_code"] not in signed), q["reviews"][0]["office_code"])
        call("POST", f"/api/quarterly/{office}/signoff", f"Write-back: CFO sign-off for {office}",
             {"fiscal_year": 2026, "fiscal_quarter": 3, "decision": "Approved with conditions",
              "comment": "Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan."})
    call("POST", "/api/genie", "Ask Genie through the app (on behalf of the signed-in user)",
         {"question": "What is the projected lapse by office?"})
    call("GET", "/api/activity", "Live activity feed after the write-backs", limit=12)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_text("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
