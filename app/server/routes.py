"""REST API for the Budget Execution app. Reads come from Lakebase synced tables; writes go to the
`workflow` schema in Lakebase (which a CDF config streams back to Unity Catalog)."""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from . import ai, db
from .config import DEFAULT_OFFICE_SCOPE, LOCAL_USER, PG_SCHEMA, SERVING_ENDPOINT, workspace

router = APIRouter(prefix="/api")
S = PG_SCHEMA
AWARD_BUFFER_DAYS = 14  # award at least two weeks before the funds expire
APPROVER_ROLES = {"Budget Director"}


# ----------------------------------------------------------------------------------- identity
class User(BaseModel):
    email: str
    role: str
    offices: list[str] | None  # None = agency-wide
    token: str | None = Field(default=None, exclude=True)


def current_user(request: Request) -> User:
    email = request.headers.get("x-forwarded-email") or LOCAL_USER or workspace().current_user.me().user_name
    rows = db.query(f"SELECT office_code, budget_role FROM {S}.lb_office_access_map WHERE principal = %s", (email,))
    if rows:
        offices = None if any(r["office_code"] == "ALL" for r in rows) else sorted(r["office_code"] for r in rows)
        role = rows[0]["budget_role"]
    elif DEFAULT_OFFICE_SCOPE == "ALL":
        offices, role = None, "Viewer (demo default)"
    else:
        offices, role = [], "No access"
    return User(email=email, role=role, offices=offices, token=request.headers.get("x-forwarded-access-token"))


def scope(user: User, office: str | None, alias: str = "") -> tuple[str, list]:
    """WHERE fragment restricting rows to the user's offices (and an optional office filter)."""
    col = f"{alias}office_code"
    clauses, params = [], []
    if user.offices is not None:
        clauses.append(f"{col} = ANY(%s)")
        params.append(user.offices)
    if office:
        clauses.append(f"{col} = %s")
        params.append(office)
    return (" AND ".join(clauses) or "TRUE"), params


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user.model_dump() | {"genie_on_behalf_of_user": bool(user.token),
                                "can_approve_reprogramming": user.role in APPROVER_ROLES and user.offices is None}


@router.get("/filters")
def filters(user: User = Depends(current_user)):
    where, params = scope(user, None)
    offices = db.query(f"SELECT DISTINCT office_code, office_name FROM {S}.lb_budget_execution WHERE {where} ORDER BY 1", params)
    asof = db.query(f"SELECT MAX(as_of_date) AS as_of FROM {S}.lb_budget_execution")[0]["as_of"]
    return {"offices": offices, "as_of_date": asof}


# ----------------------------------------------------------------------------------- dashboard
KPI_SQL = """
SELECT COUNT(*) AS budget_lines,
       SUM(total_budget) AS total_budget,
       SUM(planned_obligations_to_date) AS planned_obligations_to_date,
       SUM(committed_not_obligated) AS committed_not_obligated,
       SUM(obligated_to_date) AS obligated_to_date,
       SUM(expended_to_date) AS expended_to_date,
       SUM(unobligated_balance) AS unobligated_balance,
       SUM(obligated_to_date) / NULLIF(SUM(total_budget), 0) AS obligation_rate,
       SUM(obligated_to_date) / NULLIF(SUM(planned_obligations_to_date), 0) AS burn_rate_vs_plan,
       SUM(expended_to_date) / NULLIF(SUM(total_budget), 0) AS expenditure_rate,
       SUM(CASE WHEN days_to_expiration <= 90 THEN unobligated_balance ELSE 0 END) AS unobligated_expiring_90d
FROM {S}.lb_budget_execution WHERE fund_status = 'Current' AND {where}
"""


@router.get("/overview")
def overview(office: str | None = None, user: User = Depends(current_user)):
    where, params = scope(user, office)
    kpis = db.query(KPI_SQL.format(S=S, where=where), params)[0]
    lapse = db.query(f"""SELECT SUM(projected_lapse_amount) AS projected_lapse,
                                COUNT(*) FILTER (WHERE risk_tier IN ('Critical','High')) AS high_risk_lines
                         FROM {S}.lb_lapse_risk_forecast WHERE {where}""", params)[0]
    by_office = db.query(f"""
        SELECT office_code, office_name, SUM(total_budget) AS total_budget, SUM(obligated_to_date) AS obligated,
               SUM(expended_to_date) AS expended, SUM(unobligated_balance) AS unobligated,
               SUM(obligated_to_date) / NULLIF(SUM(total_budget), 0) AS obligation_rate,
               SUM(obligated_to_date) / NULLIF(SUM(planned_obligations_to_date), 0) AS burn_rate_vs_plan
        FROM {S}.lb_budget_execution WHERE fund_status = 'Current' AND {where}
        GROUP BY 1, 2 ORDER BY burn_rate_vs_plan""", params)
    by_appropriation = db.query(f"""
        SELECT appropriation_name, fund_type, SUM(total_budget) AS total_budget, SUM(obligated_to_date) AS obligated,
               SUM(unobligated_balance) AS unobligated,
               SUM(obligated_to_date) / NULLIF(SUM(total_budget), 0) AS obligation_rate
        FROM {S}.lb_budget_execution WHERE fund_status = 'Current' AND {where}
        GROUP BY 1, 2 ORDER BY 3 DESC""", params)
    return {"kpis": kpis | lapse, "by_office": by_office, "by_appropriation": by_appropriation}


@router.get("/burn")
def burn(office: str | None = None, line_id: str | None = None, user: User = Depends(current_user)):
    """Cumulative planned vs actual obligations for funds expiring at the end of the current fiscal year."""
    where, params = scope(user, office, "m.")
    line_clause = "m.line_id = %s" if line_id else "b.days_to_expiration BETWEEN 0 AND 366"
    if line_id:
        params.append(line_id)
    rows = db.query(f"""
        SELECT m.month,
               SUM(m.planned_obligations) AS planned_obligations, SUM(m.actual_obligations) AS actual_obligations,
               SUM(m.planned_expenditures) AS planned_expenditures, SUM(m.actual_expenditures) AS actual_expenditures,
               bool_and(m.is_actualized) AS is_actualized
        FROM {S}.lb_monthly_execution m JOIN {S}.lb_budget_execution b USING (line_id)
        WHERE b.fund_status = 'Current' AND {line_clause} AND {where}
          AND m.month >= (SELECT MIN(make_date(budget_fiscal_year - 1, 10, 1)) FROM {S}.lb_budget_execution b2
                          WHERE b2.line_id = ANY(ARRAY(SELECT line_id FROM {S}.lb_budget_execution b3
                                                       WHERE b3.fund_status = 'Current' AND b3.days_to_expiration <= 366)))
        GROUP BY m.month ORDER BY m.month""", params)
    cum = {"planned_obligations": 0, "actual_obligations": 0, "planned_expenditures": 0, "actual_expenditures": 0}
    out = []
    for r in rows:
        for k in cum:
            cum[k] += float(r[k] or 0)
        out.append({"month": r["month"], "is_actualized": r["is_actualized"],
                    **{f"cumulative_{k}": round(v, 2) for k, v in cum.items()}})
    return out


@router.get("/lines")
def lines(office: str | None = None, max_days: int = 400, user: User = Depends(current_user)):
    where, params = scope(user, office, "b.")
    params.append(max_days)
    return db.query(f"""
        SELECT b.line_id, b.ppa_code, b.ppa_name, b.office_code, b.tas, b.fund_type, b.budget_fiscal_year,
               b.expiration_date, b.days_to_expiration, b.total_budget, b.planned_obligations_to_date,
               b.obligated_to_date, b.committed_not_obligated, b.expended_to_date, b.unobligated_balance,
               b.uncommitted_balance, b.obligation_rate, b.burn_rate_vs_plan, b.execution_status,
               f.predicted_lapse_rate, f.projected_lapse_amount, f.risk_tier, f.top_risk_drivers,
               e.headline AS briefing_headline
        FROM {S}.lb_budget_execution b
        LEFT JOIN {S}.lb_lapse_risk_forecast f USING (line_id)
        LEFT JOIN {S}.lb_execution_briefings e USING (line_id)
        WHERE b.fund_status = 'Current' AND {where} AND b.days_to_expiration <= %s
        ORDER BY f.projected_lapse_amount DESC NULLS LAST, b.uncommitted_balance DESC""", params)


@router.get("/lines/{line_id}")
def line_detail(line_id: str, user: User = Depends(current_user)):
    where, params = scope(user, None, "b.")
    rows = db.query(f"""SELECT b.*, f.predicted_lapse_rate, f.projected_lapse_amount, f.risk_tier,
                               f.top_risk_drivers, f.spend_plan_implied_lapse_rate, f.model_version
                        FROM {S}.lb_budget_execution b LEFT JOIN {S}.lb_lapse_risk_forecast f USING (line_id)
                        WHERE b.line_id = %s AND {where}""", [line_id, *params])
    if not rows:
        raise HTTPException(404, "Line not found or not in your office scope")
    return {
        "line": rows[0],
        "briefing": next(iter(db.query(f"SELECT headline, summary, recommended_actions, grounding_passed, model_endpoint FROM {S}.lb_execution_briefings WHERE line_id = %s", (line_id,))), None),
        "open_procurements": db.query(f"""SELECT pr_id, title, acquisition_type, contract_vehicle, estimated_amount, status,
                                                 days_in_status, forecast_award_date, at_risk_of_missing_expiration
                                          FROM {S}.lb_procurement_pipeline WHERE line_id = %s AND is_open
                                          ORDER BY estimated_amount DESC""", (line_id,)),
        "alerts": db.query(f"SELECT alert_id, alert_type, severity, amount_at_risk, detail FROM {S}.lb_financial_risk_alerts WHERE line_id = %s ORDER BY amount_at_risk DESC", (line_id,)),
        "package_draft": next(iter(db.query(f"SELECT * FROM {S}.lb_procurement_package_drafts WHERE line_id = %s", (line_id,))), None),
        "submitted_packages": db.query("SELECT * FROM workflow.app_procurement_packages WHERE line_id = %s ORDER BY created_at DESC", (line_id,)),
        "reprogramming": db.query("""SELECT * FROM workflow.app_reprogramming_requests
                                     WHERE %s IN (from_line_id, to_line_id) ORDER BY requested_at DESC""", (line_id,)),
    }


class Note(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


@router.get("/lines/{line_id}/notes")
def line_notes(line_id: str, user: User = Depends(current_user)):
    where, params = scope(user, None)
    return db.query(f"SELECT * FROM workflow.app_line_notes WHERE line_id = %s AND {where} ORDER BY created_at DESC",
                    [line_id, *params])


@router.post("/lines/{line_id}/notes")
def add_line_note(line_id: str, body: Note, user: User = Depends(current_user)):
    where, params = scope(user, None)
    line = db.query(f"SELECT office_code FROM {S}.lb_budget_execution WHERE line_id = %s AND {where}", [line_id, *params])
    if not line:
        raise HTTPException(404, "Line not found or not in your office scope")
    return db.execute("""INSERT INTO workflow.app_line_notes (line_id, office_code, note, author)
                         VALUES (%s, %s, %s, %s) RETURNING *""",
                      (line_id, line[0]["office_code"], body.note.strip(), user.email))[0]


# ----------------------------------------------------------------------------------- alerts
@router.get("/alerts")
def alerts(office: str | None = None, severity: str | None = None, alert_type: str | None = None,
           user: User = Depends(current_user)):
    where, params = scope(user, office, "a.")
    extra = ""
    if severity:
        extra += " AND a.severity = %s"
        params.append(severity)
    if alert_type:
        extra += " AND a.alert_type = %s"
        params.append(alert_type)
    return db.query(f"""
        SELECT a.alert_id, a.alert_type, a.severity, a.line_id, a.office_code, a.ppa_code, a.entity_id,
               a.amount_at_risk, a.detail, act.action AS last_action, act.assignee, act.acted_by, act.acted_at
        FROM {S}.lb_financial_risk_alerts a
        LEFT JOIN LATERAL (SELECT action, assignee, acted_by, acted_at FROM workflow.app_alert_actions x
                           WHERE x.alert_id = a.alert_id ORDER BY acted_at DESC LIMIT 1) act ON TRUE
        WHERE {where} {extra}
        ORDER BY CASE a.severity WHEN 'Critical' THEN 0 WHEN 'High' THEN 1 ELSE 2 END, a.amount_at_risk DESC
        LIMIT 500""", params)


@router.get("/alerts/summary")
def alert_summary(office: str | None = None, user: User = Depends(current_user)):
    where, params = scope(user, office)
    return db.query(f"""SELECT alert_type, severity, COUNT(*) AS alerts, SUM(amount_at_risk) AS amount_at_risk
                        FROM {S}.lb_financial_risk_alerts WHERE {where} GROUP BY 1, 2 ORDER BY 4 DESC""", params)


@router.get("/alerts/{alert_id}/history")
def alert_history(alert_id: str, user: User = Depends(current_user)):
    where, params = scope(user, None)
    return db.query(f"SELECT * FROM workflow.app_alert_actions WHERE alert_id = %s AND {where} ORDER BY acted_at DESC",
                    [alert_id, *params])


class AlertAction(BaseModel):
    action: str = Field(pattern="^(Acknowledged|Assigned|Escalated|Resolved)$")
    assignee: str | None = None
    note: str | None = None


@router.post("/alerts/{alert_id}/actions")
def act_on_alert(alert_id: str, body: AlertAction, user: User = Depends(current_user)):
    where, params = scope(user, None)
    alert = db.query(f"SELECT alert_type, line_id, office_code FROM {S}.lb_financial_risk_alerts WHERE alert_id = %s AND {where}",
                     [alert_id, *params])
    if not alert:
        raise HTTPException(404, "Alert not found or not in your office scope")
    a = alert[0]
    return db.execute("""INSERT INTO workflow.app_alert_actions
                         (alert_id, alert_type, line_id, office_code, action, assignee, note, acted_by)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                      (alert_id, a["alert_type"], a["line_id"], a["office_code"], body.action, body.assignee,
                       body.note, user.email))[0]


# ----------------------------------------------------------------------------------- procurement
@router.get("/procurement")
def procurement(office: str | None = None, user: User = Depends(current_user)):
    where, params = scope(user, office)
    open_prs = db.query(f"""
        SELECT pr_id, line_id, ppa_name, office_code, title, acquisition_type, contract_vehicle, estimated_amount,
               status, days_in_status, age_days, forecast_award_date, expiration_date, at_risk_of_missing_expiration,
               COALESCE(submitted_at, drafted_at) AS started_at, median_palt_days
        FROM {S}.lb_procurement_pipeline WHERE is_open AND {where}
        ORDER BY at_risk_of_missing_expiration DESC, expiration_date, estimated_amount DESC LIMIT 300""", params)
    by_stage = db.query(f"""SELECT status, COUNT(*) AS prs, SUM(estimated_amount) AS value
                            FROM {S}.lb_procurement_pipeline WHERE is_open AND {where} GROUP BY 1""", params)
    palt = db.query(f"""SELECT acquisition_type, COUNT(*) AS awards,
                               percentile_cont(0.5) WITHIN GROUP (ORDER BY palt_days) AS median_palt_days,
                               percentile_cont(0.8) WITHIN GROUP (ORDER BY palt_days) AS p80_palt_days
                        FROM {S}.lb_procurement_pipeline WHERE status = 'Awarded' AND {where}
                        GROUP BY 1 ORDER BY 3""", params)
    return {"open": open_prs, "by_stage": by_stage, "palt": palt}


def _package_facts(line_id: str, user: User) -> dict:
    where, params = scope(user, None, "b.")
    rows = db.query(f"""SELECT b.*, f.projected_lapse_amount, f.top_risk_drivers FROM {S}.lb_budget_execution b
                        JOIN {S}.lb_lapse_risk_forecast f USING (line_id) WHERE b.line_id = %s AND {where}""",
                    [line_id, *params])
    if not rows:
        raise HTTPException(404, "Line not found or not in your office scope")
    r = rows[0]
    as_of = r["as_of_date"]
    must_award_by = r["expiration_date"] - timedelta(days=AWARD_BUFFER_DAYS)
    days_left = (must_award_by - as_of).days
    palt = db.query(f"""SELECT acquisition_type,
                               percentile_cont(0.5) WITHIN GROUP (ORDER BY palt_days) AS median_palt_days,
                               percentile_cont(0.8) WITHIN GROUP (ORDER BY palt_days) AS p80_palt_days
                        FROM {S}.lb_procurement_pipeline WHERE status = 'Awarded'
                          AND acquisition_type IN ('Option Exercise', 'Modification', 'Task Order') GROUP BY 1""")
    contracts = db.query(f"""SELECT contract_number, MAX(vendor_name) AS vendor, MAX(object_class) AS object_class,
                                    SUM(award_amount) AS obligated_to_date
                             FROM {S}.lb_procurement_pipeline
                             WHERE ppa_code = %s AND status = 'Awarded' AND object_class LIKE '25.%%'
                               AND contract_number IS NOT NULL AND awarded_at >= %s
                             GROUP BY 1 ORDER BY 4 DESC LIMIT 3""", (r["ppa_code"], as_of - timedelta(days=330)))
    gap = float(r["projected_lapse_amount"] or r["uncommitted_balance"] or 0)
    return {
        "ppa": f"{r['ppa_name']} ({r['ppa_code']})", "fund": r["tas"], "expires_on": str(r["expiration_date"]),
        "must_award_by": str(must_award_by), "days_until_must_award": days_left,
        "projected_lapse_amount": round(gap, 2), "recommended_package_amount": round(0.8 * gap, -3),
        "feasible_acquisition_types": [{"type": p["acquisition_type"], "median_palt_days": int(p["median_palt_days"]),
                                        "p80_palt_days": int(p["p80_palt_days"])}
                                       for p in palt if p["p80_palt_days"] <= days_left],
        "active_service_contracts_on_line": [{**c, "obligated_to_date": float(c["obligated_to_date"])} for c in contracts],
        "risk_drivers": list(r["top_risk_drivers"] or []),
        "_office_code": r["office_code"],
    }


@router.post("/packages/{line_id}/draft")
def generate_package(line_id: str, user: User = Depends(current_user)):
    facts = _package_facts(line_id, user)
    office = facts.pop("_office_code")
    draft = ai.draft_package(facts)
    issues = []
    types = {a["type"] for a in facts["feasible_acquisition_types"]}
    if draft.get("recommended_acquisition_type") not in types:
        issues.append("acquisition type cannot award before expiration")
    contracts = {c["contract_number"] for c in facts["active_service_contracts_on_line"]}
    if draft.get("contract_number") and draft["contract_number"] not in contracts:
        issues.append("contract number not found on this line")
    if float(draft.get("amount") or 0) > facts["projected_lapse_amount"] * 1.01:
        issues.append("amount exceeds projected lapse")
    contract = next((c for c in facts["active_service_contracts_on_line"]
                     if c["contract_number"] == draft.get("contract_number")), None)
    if contract and float(draft.get("amount") or 0) > contract["obligated_to_date"]:
        issues.append("amount exceeds the contract's obligated value; confirm priced option value and bona fide need")
    return {"line_id": line_id, "office_code": office, "facts": facts, "draft": draft,
            "validation_issues": issues, "model_endpoint": SERVING_ENDPOINT}


class PackageSubmit(BaseModel):
    title: str
    acquisition_type: str | None = None
    contract_number: str | None = None
    amount: float
    requirement_summary: str | None = None
    justification: str | None = None
    required_documents: list[str] = []
    milestones: list[str] = []
    source: str = "App - on-demand AI draft"


@router.post("/packages/{line_id}")
def submit_package(line_id: str, body: PackageSubmit, user: User = Depends(current_user)):
    where, params = scope(user, None)
    line = db.query(f"SELECT office_code FROM {S}.lb_budget_execution WHERE line_id = %s AND {where}", [line_id, *params])
    if not line:
        raise HTTPException(404, "Line not found or not in your office scope")
    n = db.query("SELECT COUNT(*) AS n FROM workflow.app_procurement_packages WHERE line_id = %s", (line_id,))[0]["n"]
    return db.execute("""
        INSERT INTO workflow.app_procurement_packages
          (package_id, line_id, office_code, title, acquisition_type, contract_number, amount, requirement_summary,
           justification, required_documents, milestones, source, model_endpoint, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
        (f"REQ-{line_id}-{n + 1:02d}", line_id, line[0]["office_code"], body.title, body.acquisition_type,
         body.contract_number or None, body.amount, body.requirement_summary, body.justification,
         json.dumps(body.required_documents), json.dumps(body.milestones), body.source, SERVING_ENDPOINT,
         user.email))[0]


@router.get("/packages")
def packages(user: User = Depends(current_user)):
    where, params = scope(user, None)
    return {
        "submitted": db.query(f"SELECT * FROM workflow.app_procurement_packages WHERE {where} ORDER BY created_at DESC", params),
        "ai_drafts": db.query(f"""SELECT package_id, line_id, office_code, ppa_code, title, recommended_acquisition_type,
                                         contract_number, amount, requirement_summary, status, validation_issues
                                  FROM {S}.lb_procurement_package_drafts WHERE {where} ORDER BY amount DESC""", params),
    }


# ----------------------------------------------------------------------------------- quarterly review
@router.get("/quarterly")
def quarterly(user: User = Depends(current_user)):
    where, params = scope(user, None, "m.")
    quarters = db.query(f"""
        SELECT m.office_code, m.fiscal_quarter, SUM(m.planned_obligations) AS planned_obligations,
               SUM(m.actual_obligations) AS actual_obligations, SUM(m.actual_expenditures) AS actual_expenditures
        FROM {S}.lb_monthly_execution m
        WHERE m.activity_fiscal_year = (SELECT EXTRACT(YEAR FROM MAX(as_of_date))::int
                                          + CASE WHEN EXTRACT(MONTH FROM MAX(as_of_date)) >= 10 THEN 1 ELSE 0 END
                                        FROM {S}.lb_budget_execution)
          AND {where}
        GROUP BY 1, 2 ORDER BY 1, 2""", params)
    w2, p2 = scope(user, None)
    reviews = db.query(f"""SELECT office_code, performance_summary, key_risks, decisions_requested, grounding_passed
                           FROM {S}.lb_quarterly_review_briefings WHERE {w2} ORDER BY office_code""", p2)
    signoffs = db.query(f"SELECT * FROM workflow.app_review_signoffs WHERE {w2} ORDER BY signed_at DESC", p2)
    return {"quarters": quarters, "reviews": reviews, "signoffs": signoffs}


class Signoff(BaseModel):
    fiscal_year: int
    fiscal_quarter: int
    decision: str = Field(pattern="^(Approved|Approved with conditions|Returned)$")
    comment: str | None = None


@router.post("/quarterly/{office_code}/signoff")
def signoff(office_code: str, body: Signoff, user: User = Depends(current_user)):
    if user.offices is not None and office_code not in user.offices:
        raise HTTPException(403, "Office not in your scope")
    return db.execute("""INSERT INTO workflow.app_review_signoffs (office_code, fiscal_year, fiscal_quarter, decision, comment, signed_by)
                         VALUES (%s, %s, %s, %s, %s, %s) RETURNING *""",
                      (office_code, body.fiscal_year, body.fiscal_quarter, body.decision, body.comment, user.email))[0]


# ----------------------------------------------------------------------------------- genie
class Question(BaseModel):
    question: str
    conversation_id: str | None = None


@router.post("/genie")
def genie(body: Question, user: User = Depends(current_user)):
    return ai.ask_genie(body.question, body.conversation_id, user.token)


@router.get("/health")
def health():
    db.query("SELECT 1 AS ok")
    return {"status": "ok", "today": str(date.today())}
