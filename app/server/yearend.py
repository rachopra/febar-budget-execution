"""Year-end workspace API: command center, activity feed, search, the year-end lapse-recovery plan and
reprogramming requests. Reads come from Lakebase synced tables; writes go to the `workflow` schema."""

from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import db
from .routes import APPROVER_ROLES, AWARD_BUFFER_DAYS, S, User, current_user, scope

router = APIRouter(prefix="/api")

# Illustrative reprogramming notification threshold: the lesser of $500K or 10% of either PPA.
# Set these to the limits in the agency's appropriations act.
REPROGRAMMING_NOTIFY_AMOUNT = 500_000
REPROGRAMMING_NOTIFY_PCT = 0.10
MIN_SUGGESTION = 10_000
IN_FLIGHT = ("Pending", "Approved")


def f(v) -> float:
    return float(v or 0)


def scope_any(user: User, cols: list[str]) -> tuple[str, list]:
    """WHERE fragment matching rows where any of `cols` is one of the user's offices."""
    if user.offices is None:
        return "TRUE", []
    return "(" + " OR ".join(f"{c} = ANY(%s)" for c in cols) + ")", [user.offices] * len(cols)


def calendar() -> dict:
    as_of: date = db.query(f"SELECT MAX(as_of_date) AS d FROM {S}.lb_budget_execution")[0]["d"]
    fy = as_of.year + (1 if as_of.month >= 10 else 0)
    fy_start, fy_end = date(fy - 1, 10, 1), date(fy, 9, 30)
    quarter = (as_of.month + 2) % 12 // 3 + 1
    last_q = (fy, quarter - 1) if quarter > 1 else (fy - 1, 4)
    return {"as_of_date": as_of, "fiscal_year": fy, "fiscal_year_start": fy_start, "fiscal_year_end": fy_end,
            "must_award_by": fy_end - timedelta(days=AWARD_BUFFER_DAYS), "days_left": (fy_end - as_of).days,
            "fiscal_year_elapsed": round((as_of - fy_start).days / (fy_end - fy_start).days, 4),
            "fiscal_quarter": quarter, "last_completed_quarter": {"fiscal_year": last_q[0], "fiscal_quarter": last_q[1]}}


def recovery_by_line(where: str, params: list) -> dict[str, dict]:
    """Projected lapse per line and the part of it already covered by actions taken in the app
    (packages submitted to acquisition, reprogramming requests pending or approved)."""
    rows = db.query(f"""
        WITH pk AS (SELECT line_id, SUM(amount) AS amt, COUNT(*) AS n FROM workflow.app_procurement_packages GROUP BY 1),
             rp AS (SELECT from_line_id AS line_id, SUM(amount) AS amt, COUNT(*) AS n
                    FROM workflow.app_reprogramming_requests WHERE status = ANY(%s) GROUP BY 1)
        SELECT f.line_id, f.office_code, f.projected_lapse_amount AS lapse, COALESCE(pk.amt, 0) AS packaged, COALESCE(pk.n, 0) AS packages,
               COALESCE(rp.amt, 0) AS reprogrammed, COALESCE(rp.n, 0) AS reprogramming_requests
        FROM {S}.lb_lapse_risk_forecast f LEFT JOIN pk USING (line_id) LEFT JOIN rp USING (line_id)
        WHERE f.projected_lapse_amount > 0 AND {where}""", [list(IN_FLIGHT), *params])
    return {r["line_id"]: {**r, "recovered": min(f(r["lapse"]), f(r["packaged"]) + f(r["reprogrammed"]))} for r in rows}


def acquisition_windows(cal: dict, where: str, params: list) -> list[dict]:
    """For each acquisition type, the last day a request can be submitted and still award by the
    must-award-by date: conservative (p80 PALT) and typical (median PALT)."""
    palt = db.query(f"""SELECT acquisition_type, MAX(median_palt_days) AS median_palt_days, MAX(p80_palt_days) AS p80_palt_days
                        FROM {S}.lb_procurement_pipeline WHERE median_palt_days IS NOT NULL GROUP BY 1""")
    open_prs = {r["acquisition_type"]: r for r in db.query(f"""
        SELECT acquisition_type, COUNT(*) AS open_prs, SUM(estimated_amount) AS open_value,
               COUNT(*) FILTER (WHERE at_risk_of_missing_expiration) AS will_miss
        FROM {S}.lb_procurement_pipeline WHERE is_open AND expiration_date <= %s AND {where} GROUP BY 1""",
        [cal["fiscal_year_end"], *params])}
    as_of, award_by = cal["as_of_date"], cal["must_award_by"]
    out = []
    for p in sorted(palt, key=lambda p: p["median_palt_days"]):
        close_p80 = award_by - timedelta(days=int(p["p80_palt_days"]))
        close_median = award_by - timedelta(days=int(p["median_palt_days"]))
        status = "open" if as_of <= close_p80 else "closing" if as_of <= close_median else "closed"
        o = open_prs.get(p["acquisition_type"], {})
        out.append({"acquisition_type": p["acquisition_type"], "median_palt_days": p["median_palt_days"],
                    "p80_palt_days": p["p80_palt_days"], "last_submit_conservative": close_p80,
                    "last_submit_typical": close_median, "status": status,
                    "days_to_close": (close_median - as_of).days,
                    "open_prs": o.get("open_prs", 0), "open_value": f(o.get("open_value")), "will_miss": o.get("will_miss", 0)})
    return out


ALERT_STATUS = """LEFT JOIN LATERAL (SELECT action, assignee, acted_by, acted_at FROM workflow.app_alert_actions x
                                     WHERE x.alert_id = a.alert_id ORDER BY acted_at DESC LIMIT 1) act ON TRUE"""


@router.get("/command-center")
def command_center(office: str | None = None, user: User = Depends(current_user)):
    cal = calendar()
    where, params = scope(user, office)
    wb, pb = scope(user, office, "b.")
    fy_end = cal["fiscal_year_end"]

    e = db.query(f"""SELECT COUNT(*) AS lines, SUM(total_budget) AS budget, SUM(obligated_to_date) AS obligated,
                            SUM(committed_not_obligated) AS committed, SUM(requested_not_certified) AS requested,
                            SUM(unobligated_balance) AS unobligated, SUM(uncommitted_balance) AS uncommitted
                     FROM {S}.lb_budget_execution
                     WHERE fund_status = 'Current' AND expiration_date <= %s AND {where}""", [fy_end, *params])[0]
    budget, obligated, committed = f(e["budget"]), f(e["obligated"]), f(e["committed"])
    committed = min(committed, max(0.0, budget - obligated))
    requested = min(f(e["requested"]), max(0.0, budget - obligated - committed))
    expiring = {"lines": e["lines"], "total_budget": budget, "unobligated": f(e["unobligated"]),
                "uncommitted": f(e["uncommitted"]),
                "composition": [{"stage": "Obligated", "amount": obligated},
                                {"stage": "Committed (certified PRs)", "amount": committed},
                                {"stage": "Requested (draft / submitted PRs)", "amount": requested},
                                {"stage": "No action yet", "amount": max(0.0, budget - obligated - committed - requested)}]}

    tiers = db.query(f"""SELECT risk_tier, COUNT(*) AS lines, SUM(projected_lapse_amount) AS lapse,
                                SUM(projected_year_end_obligations) AS year_end_obligations, SUM(total_budget) AS budget
                         FROM {S}.lb_lapse_risk_forecast WHERE projected_lapse_amount IS NOT NULL AND {where}
                         GROUP BY 1""", params)
    order = {"Critical": 0, "High": 1, "Moderate": 2, "Low": 3}
    tiers.sort(key=lambda t: order.get(t["risk_tier"], 9))
    projected_lapse = sum(f(t["lapse"]) for t in tiers)
    rec = recovery_by_line(where, params)
    recovered = sum(r["recovered"] for r in rec.values())
    forecast = {"projected_lapse": projected_lapse, "lines": sum(t["lines"] for t in tiers),
                "high_risk_lines": sum(t["lines"] for t in tiers if t["risk_tier"] in ("Critical", "High")),
                "high_risk_lapse": sum(f(t["lapse"]) for t in tiers if t["risk_tier"] in ("Critical", "High")),
                "projected_year_end_obligations": sum(f(t["year_end_obligations"]) for t in tiers),
                "forecast_budget": sum(f(t["budget"]) for t in tiers),
                "by_tier": tiers,
                "recovery_in_flight": recovered,
                "packaged": sum(min(f(r["lapse"]), f(r["packaged"])) for r in rec.values()),
                "remaining_after_actions": max(0.0, projected_lapse - recovered)}

    offices = db.query(f"""
        SELECT b.office_code, MAX(b.office_name) AS office_name, SUM(b.total_budget) AS total_budget,
               SUM(b.obligated_to_date) AS obligated, SUM(b.planned_obligations_to_date) AS planned_to_date,
               SUM(b.obligated_to_date) / NULLIF(SUM(b.planned_obligations_to_date), 0) AS burn_rate_vs_plan,
               SUM(b.obligated_to_date) / NULLIF(SUM(b.total_budget), 0) AS obligation_rate,
               SUM(b.unobligated_balance) FILTER (WHERE b.expiration_date <= %s) AS unobligated_expiring,
               SUM(fc.projected_lapse_amount) AS projected_lapse
        FROM {S}.lb_budget_execution b LEFT JOIN {S}.lb_lapse_risk_forecast fc USING (line_id)
        WHERE b.fund_status = 'Current' AND {wb}
        GROUP BY b.office_code ORDER BY burn_rate_vs_plan""", [fy_end, *pb])
    wa, pa = scope(user, office, "a.")
    open_alerts = {r["office_code"]: r for r in db.query(f"""
        SELECT a.office_code, COUNT(*) FILTER (WHERE a.severity = 'Critical') AS critical,
               COUNT(*) FILTER (WHERE a.severity = 'High') AS high, COUNT(*) AS total
        FROM {S}.lb_financial_risk_alerts a {ALERT_STATUS}
        WHERE COALESCE(act.action, '') <> 'Resolved' AND {wa} GROUP BY 1""", pa)}
    for o in offices:
        a = open_alerts.get(o["office_code"], {})
        o.update(open_critical=a.get("critical", 0), open_high=a.get("high", 0), open_alerts=a.get("total", 0),
                 recovery_in_flight=sum(r["recovered"] for r in rec.values() if r["office_code"] == o["office_code"]))

    top = db.query(f"""
        SELECT fc.line_id, b.ppa_name, b.office_code, b.tas, b.days_to_expiration, b.total_budget, b.uncommitted_balance,
               b.burn_rate_vs_plan, fc.projected_lapse_amount, fc.predicted_lapse_rate, fc.risk_tier, fc.top_risk_drivers,
               d.amount AS draft_amount, d.recommended_acquisition_type AS draft_type
        FROM {S}.lb_lapse_risk_forecast fc JOIN {S}.lb_budget_execution b USING (line_id)
        LEFT JOIN LATERAL (SELECT amount, recommended_acquisition_type FROM {S}.lb_procurement_package_drafts x
                           WHERE x.line_id = fc.line_id ORDER BY amount DESC LIMIT 1) d ON TRUE
        WHERE fc.projected_lapse_amount > 0 AND {wb}
        ORDER BY fc.projected_lapse_amount DESC LIMIT 8""", pb)
    for t in top:
        r = rec.get(t["line_id"], {})
        t.update(recovered=r.get("recovered", 0.0), packages=r.get("packages", 0),
                 reprogramming_requests=r.get("reprogramming_requests", 0))

    lq = cal["last_completed_quarter"]
    wd, pd_ = scope(user, office, "d.")
    wq, pq = scope(user, office, "q.")
    wr, pr = scope_any(user, ["from_office_code", "to_office_code"])
    queue = db.query(f"""
        SELECT
          (SELECT COUNT(*) FROM {S}.lb_financial_risk_alerts a {ALERT_STATUS}
             WHERE a.severity IN ('Critical', 'High') AND act.action IS NULL AND {wa}) AS untriaged_alerts,
          (SELECT COUNT(*) FROM {S}.lb_procurement_package_drafts d
             WHERE NOT EXISTS (SELECT 1 FROM workflow.app_procurement_packages p WHERE p.line_id = d.line_id)
               AND {wd}) AS drafts_ready,
          (SELECT COUNT(*) FROM workflow.app_reprogramming_requests WHERE status = 'Pending' AND {wr}) AS reprogramming_pending,
          (SELECT COUNT(*) FROM {S}.lb_quarterly_review_briefings q
             WHERE NOT EXISTS (SELECT 1 FROM workflow.app_review_signoffs s WHERE s.office_code = q.office_code
                               AND s.fiscal_year = %s AND s.fiscal_quarter = %s)
               AND {wq}) AS reviews_pending
        """, [*pa, *pd_, *pr, lq["fiscal_year"], lq["fiscal_quarter"], *pq])[0]
    queue["reprogramming_suggestions"] = len(reprogramming_suggestions(user, office))

    return {"calendar": cal, "expiring": expiring, "forecast": forecast,
            "windows": acquisition_windows(cal, where, params), "offices": offices, "top_lines": top, "queue": queue}


@router.get("/activity")
def activity(limit: int = 30, user: User = Depends(current_user)):
    """Recent actions taken in the app, newest first (the same rows the CDF streams to Unity Catalog)."""
    w, p = scope(user, None)
    wr, pr = scope_any(user, ["from_office_code", "to_office_code"])
    return db.query(f"""
        SELECT * FROM (
          SELECT 'alert' AS kind, acted_at AS at, acted_by AS actor, office_code, line_id, lower(action) AS verb,
                 alert_type AS subject, assignee AS target, note AS detail, NULL::numeric AS amount
          FROM workflow.app_alert_actions WHERE {w}
          UNION ALL
          SELECT 'package', created_at, created_by, office_code, line_id, 'submitted package', package_id,
                 acquisition_type, title, amount
          FROM workflow.app_procurement_packages WHERE {w}
          UNION ALL
          SELECT 'signoff', signed_at, signed_by, office_code, NULL, lower(decision),
                 'FY' || fiscal_year || ' Q' || fiscal_quarter || ' review', NULL, comment, NULL
          FROM workflow.app_review_signoffs WHERE {w}
          UNION ALL
          SELECT 'reprogramming', requested_at, requested_by, from_office_code, from_line_id, 'requested reprogramming',
                 request_id, to_line_id, justification, amount
          FROM workflow.app_reprogramming_requests WHERE {wr}
          UNION ALL
          SELECT 'reprogramming', decided_at, decided_by, from_office_code, from_line_id, lower(status) || ' reprogramming',
                 request_id, to_line_id, decision_note, amount
          FROM workflow.app_reprogramming_requests WHERE decided_at IS NOT NULL AND {wr}
          UNION ALL
          SELECT 'note', created_at, author, office_code, line_id, 'added a note on', line_id, NULL, note, NULL
          FROM workflow.app_line_notes WHERE {w}
        ) x ORDER BY at DESC LIMIT %s""", [*p, *p, *p, *pr, *pr, *p, min(limit, 200)])


@router.get("/search")
def search(q: str, user: User = Depends(current_user)):
    like = f"%{q.strip()}%"
    w, p = scope(user, None)
    lines = db.query(f"""SELECT line_id, ppa_name, office_code, tas, days_to_expiration, unobligated_balance
                         FROM {S}.lb_budget_execution
                         WHERE fund_status = 'Current' AND (ppa_name ILIKE %s OR line_id ILIKE %s) AND {w}
                         ORDER BY total_budget DESC LIMIT 8""", [like, like, *p])
    prs = db.query(f"""SELECT pr_id, title, line_id, office_code, status, estimated_amount
                       FROM {S}.lb_procurement_pipeline WHERE (pr_id ILIKE %s OR title ILIKE %s) AND {w}
                       ORDER BY is_open DESC, estimated_amount DESC LIMIT 8""", [like, like, *p])
    return {"lines": lines, "prs": prs}


# ----------------------------------------------------------------------------------- year-end plan
def notification_required(amount: float, from_budget: float, to_budget: float) -> bool:
    return amount > min(REPROGRAMMING_NOTIFY_AMOUNT, REPROGRAMMING_NOTIFY_PCT * min(from_budget, to_budget))


def reprogramming_suggestions(user: User, office: str | None = None) -> list[dict]:
    """Match lines projected to lapse with lines short of funds in the same TAS. Moving funds between PPAs
    of one appropriation and period of availability is a reprogramming; across appropriations it would
    need transfer authority, so it is never suggested."""
    wb, pb = scope(user, None, "b.")
    rows = db.query(f"""
        WITH rp AS (SELECT line_id, SUM(out_amt) AS out_amt, SUM(in_amt) AS in_amt FROM (
                      SELECT from_line_id AS line_id, amount AS out_amt, 0 AS in_amt FROM workflow.app_reprogramming_requests WHERE status = ANY(%s)
                      UNION ALL
                      SELECT to_line_id, 0, amount FROM workflow.app_reprogramming_requests WHERE status = ANY(%s)) x GROUP BY 1),
             pk AS (SELECT line_id, SUM(amount) AS amt FROM workflow.app_procurement_packages GROUP BY 1)
        SELECT b.line_id, b.ppa_name, b.office_code, b.tas, b.total_budget, b.unobligated_balance, b.uncommitted_balance,
               b.committed_not_obligated, b.requested_not_certified, fc.projected_lapse_amount,
               COALESCE(rp.out_amt, 0) + COALESCE(pk.amt, 0) AS out_pending, COALESCE(rp.in_amt, 0) AS in_pending
        FROM {S}.lb_budget_execution b LEFT JOIN {S}.lb_lapse_risk_forecast fc USING (line_id)
        LEFT JOIN rp USING (line_id) LEFT JOIN pk USING (line_id)
        WHERE b.fund_status = 'Current' AND {wb}""", [list(IN_FLIGHT), list(IN_FLIGHT), *pb])
    donors, recipients = defaultdict(list), defaultdict(list)
    for r in rows:
        # funds already proposed for reprogramming or submitted as procurement packages are spoken for
        available = min(f(r["projected_lapse_amount"]), max(0.0, f(r["uncommitted_balance"]))) - f(r["out_pending"])
        if available >= MIN_SUGGESTION:
            donors[r["tas"]].append({**r, "available": available})
        shortfall_committed = f(r["committed_not_obligated"]) - f(r["unobligated_balance"]) - f(r["in_pending"])
        need = shortfall_committed + f(r["requested_not_certified"])
        if need >= MIN_SUGGESTION:
            recipients[r["tas"]].append({**r, "need": need, "overcommitted": max(0.0, shortfall_committed)})
    out = []
    for tas, rs in recipients.items():
        ds = sorted(donors.get(tas, []), key=lambda d: -d["available"])
        for rcv in sorted(rs, key=lambda x: (-x["overcommitted"], -x["need"])):
            need = rcv["need"]
            for d in ds:
                amount = min(need, d["available"]) // 1000 * 1000
                if amount < MIN_SUGGESTION or d["line_id"] == rcv["line_id"]:
                    continue
                if office and office not in (d["office_code"], rcv["office_code"]):
                    continue
                reason = (f"commitments exceed available funds by ${rcv['overcommitted']:,.0f}" if rcv["overcommitted"] > 0
                          else f"${rcv['need']:,.0f} of draft / submitted procurement requests exceed its uncommitted balance")
                out.append({"tas": tas, "amount": amount,
                            "from_line_id": d["line_id"], "from_ppa_name": d["ppa_name"], "from_office_code": d["office_code"],
                            "from_available": round(d["available"], 2),
                            "from_projected_lapse": f(d["projected_lapse_amount"]),
                            "to_line_id": rcv["line_id"], "to_ppa_name": rcv["ppa_name"], "to_office_code": rcv["office_code"],
                            "to_need": round(rcv["need"], 2), "reason": reason,
                            "notification_required": notification_required(amount, f(d["total_budget"]), f(rcv["total_budget"]))})
                d["available"] -= amount
                need -= amount
                if need < MIN_SUGGESTION:
                    break
    return sorted(out, key=lambda s: -s["amount"])


def list_reprogramming(user: User) -> list[dict]:
    wr, pr = scope_any(user, ["r.from_office_code", "r.to_office_code"])
    return db.query(f"""SELECT r.*, fb.ppa_name AS from_ppa_name, tb.ppa_name AS to_ppa_name
                        FROM workflow.app_reprogramming_requests r
                        LEFT JOIN {S}.lb_budget_execution fb ON fb.line_id = r.from_line_id
                        LEFT JOIN {S}.lb_budget_execution tb ON tb.line_id = r.to_line_id
                        WHERE {wr} ORDER BY r.requested_at DESC""", pr)


@router.get("/plan")
def plan(office: str | None = None, user: User = Depends(current_user)):
    """Every line projected to lapse, with the validated AI package draft and what is already in flight."""
    wb, pb = scope(user, office, "b.")
    lines = db.query(f"""
        SELECT b.line_id, b.ppa_name, b.office_code, b.office_name, b.tas, b.appropriation_name, b.expiration_date,
               b.days_to_expiration, b.total_budget, b.unobligated_balance, b.uncommitted_balance, b.burn_rate_vs_plan,
               fc.projected_lapse_amount, fc.predicted_lapse_rate, fc.risk_tier, fc.top_risk_drivers,
               d.package_id AS draft_id, d.title AS draft_title, d.recommended_acquisition_type AS draft_type,
               d.contract_number AS draft_contract, d.amount AS draft_amount, d.status AS draft_status,
               d.validation_issues AS draft_issues, d.requirement_summary AS draft_requirement_summary,
               d.justification AS draft_justification, d.required_documents AS draft_documents,
               d.milestones AS draft_milestones
        FROM {S}.lb_lapse_risk_forecast fc JOIN {S}.lb_budget_execution b USING (line_id)
        LEFT JOIN LATERAL (SELECT * FROM {S}.lb_procurement_package_drafts x WHERE x.line_id = fc.line_id
                           ORDER BY amount DESC LIMIT 1) d ON TRUE
        WHERE fc.projected_lapse_amount > 0 AND {wb}
        ORDER BY fc.projected_lapse_amount DESC""", pb)
    where, params = scope(user, office)
    rec = recovery_by_line(where, params)
    for line in lines:
        r = rec.get(line["line_id"], {})
        line.update(packaged=f(r.get("packaged")), reprogrammed=f(r.get("reprogrammed")), recovered=r.get("recovered", 0.0))
    return {"calendar": calendar(), "lines": lines, "suggestions": reprogramming_suggestions(user, office),
            "requests": list_reprogramming(user),
            "notification_threshold": {"amount": REPROGRAMMING_NOTIFY_AMOUNT, "pct": REPROGRAMMING_NOTIFY_PCT}}


class ReprogrammingRequest(BaseModel):
    from_line_id: str
    to_line_id: str
    amount: float = Field(gt=0)
    justification: str | None = None


@router.post("/reprogramming")
def request_reprogramming(body: ReprogrammingRequest, user: User = Depends(current_user)):
    if body.from_line_id == body.to_line_id:
        raise HTTPException(400, "Choose two different budget lines")
    wb, pb = scope(user, None, "b.")
    rows = {r["line_id"]: r for r in db.query(f"""
        SELECT b.line_id, b.office_code, b.tas, b.fund_status, b.total_budget, b.uncommitted_balance,
               (SELECT COALESCE(SUM(amount), 0) FROM workflow.app_reprogramming_requests r
                WHERE r.from_line_id = b.line_id AND r.status = ANY(%s))
             + (SELECT COALESCE(SUM(amount), 0) FROM workflow.app_procurement_packages p
                WHERE p.line_id = b.line_id) AS out_pending
        FROM {S}.lb_budget_execution b WHERE b.line_id = ANY(%s) AND {wb}""",
        [list(IN_FLIGHT), [body.from_line_id, body.to_line_id], *pb])}
    src, dst = rows.get(body.from_line_id), rows.get(body.to_line_id)
    if not src or not dst:
        raise HTTPException(404, "Both budget lines must exist and be in your office scope")
    if src["fund_status"] != "Current" or dst["fund_status"] != "Current":
        raise HTTPException(400, "Expired funds cannot be reprogrammed")
    if src["tas"] != dst["tas"]:
        raise HTTPException(400, f"{src['tas']} and {dst['tas']} are different accounts; moving funds between "
                                 "appropriations needs transfer authority, not a reprogramming")
    available = f(src["uncommitted_balance"]) - f(src["out_pending"])
    if body.amount > available + 0.005:
        raise HTTPException(400, f"Only ${max(available, 0):,.0f} on {body.from_line_id} is uncommitted and not already "
                                 "proposed for reprogramming or submitted as a procurement package")
    n = db.query("SELECT COUNT(*) AS n FROM workflow.app_reprogramming_requests")[0]["n"]
    return db.execute("""
        INSERT INTO workflow.app_reprogramming_requests
          (request_id, tas, from_line_id, from_office_code, to_line_id, to_office_code, amount, justification,
           notification_required, requested_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
        (f"RPG-{n + 1:04d}", src["tas"], body.from_line_id, src["office_code"], body.to_line_id, dst["office_code"],
         round(body.amount, 2), body.justification,
         notification_required(body.amount, f(src["total_budget"]), f(dst["total_budget"])), user.email))[0]


@router.get("/reprogramming")
def reprogramming(user: User = Depends(current_user)):
    return list_reprogramming(user)


class ReprogrammingDecision(BaseModel):
    decision: str = Field(pattern="^(Approved|Rejected|Withdrawn)$")
    note: str | None = None


@router.post("/reprogramming/{request_id}/decision")
def decide_reprogramming(request_id: str, body: ReprogrammingDecision, user: User = Depends(current_user)):
    wr, pr = scope_any(user, ["from_office_code", "to_office_code"])
    rows = db.query(f"SELECT * FROM workflow.app_reprogramming_requests WHERE request_id = %s AND {wr}", [request_id, *pr])
    if not rows:
        raise HTTPException(404, "Request not found or not in your office scope")
    r = rows[0]
    if r["status"] != "Pending":
        raise HTTPException(409, f"{request_id} is already {r['status'].lower()}")
    if body.decision == "Withdrawn":
        if r["requested_by"] != user.email:
            raise HTTPException(403, "Only the requester can withdraw a request")
    else:
        if user.role not in APPROVER_ROLES or user.offices is not None:
            raise HTTPException(403, "Only an agency-wide Budget Director can approve or reject reprogramming")
        if r["requested_by"] == user.email:
            raise HTTPException(403, "Separation of duties: a second Budget Director must decide on a request you made")
    return db.execute("""UPDATE workflow.app_reprogramming_requests
                         SET status = %s, decided_by = %s, decided_at = now(), decision_note = %s
                         WHERE request_id = %s RETURNING *""",
                      (body.decision, user.email, body.note, request_id))[0]
