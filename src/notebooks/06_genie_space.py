# Databricks notebook source
# MAGIC %md
# MAGIC # 06 · Genie: ask budget execution questions in plain English
# MAGIC
# MAGIC Creates (or updates) the **Budget Execution - Ask the Data** Genie space over the governed gold tables, the metric
# MAGIC view, the lapse-risk forecast and the row-filtered procurement table, with a budget glossary, rules and trusted
# MAGIC SQL. Then asks the questions leadership actually asks through the Genie Conversation API and records each answer:
# MAGIC the generated SQL and its result.

# COMMAND ----------

dbutils.widgets.text("catalog", "rachopra_catalog")
dbutils.widgets.text("schema", "fe_bar")
dbutils.widgets.text("warehouse_id", "5aa6f979abb6e2d1")
dbutils.widgets.text("as_of_date", "2026-07-31")

import json
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
from databricks.sdk import WorkspaceClient

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
warehouse_id = dbutils.widgets.get("warehouse_id")
as_of = dbutils.widgets.get("as_of_date")
fq = f"{catalog}.{schema}"
TITLE = "Budget Execution - Ask the Data"
w = WorkspaceClient()
api = w.api_client

# COMMAND ----------

TABLES = [
    "gold_budget_execution", "mv_budget_execution", "gold_monthly_execution", "gold_office_execution_summary",
    "gold_quarterly_review", "gold_financial_risk_alerts", "gold_procurement_pipeline",
    "gold_procurement_cycle_times", "gold_lapse_risk_forecast", "gold_execution_briefings",
    "silver_procurement_requests",
]
existing_tables = {r.tableName for r in spark.sql(f"SHOW TABLES IN {fq}").collect()}
# App write-backs streamed from Lakebase by the CDF config (present once the app has been used)
for optional in ["lb_app_alert_actions_history", "lb_app_procurement_packages_history", "lb_app_review_signoffs_history"]:
    if optional in existing_tables:
        TABLES.append(optional)

INSTRUCTIONS = f"""
Context: budget execution data for a fictional federal civilian agency (synthetic). The reporting date is {as_of}.
The fiscal year runs October-September; fiscal quarter 1 is October-December. A budget line is one PPA (Program,
Project or Activity) funded for one budget fiscal year (line_id = ppa_code + '-FY' + budget_fiscal_year).

Definitions:
- Total budget = enacted budget authority (total_budget).
- Obligated = legally binding commitments recorded (obligated_to_date). Expended = payments disbursed (expended_to_date).
- Remaining / unobligated balance = total_budget - obligated_to_date. Uncommitted balance also subtracts open commitments.
- Obligation rate = obligated / total budget. Burn rate vs plan = obligated / planned obligations to date (1.0 = on plan).
- Funds that are not obligated by expiration_date lapse. "Expiring soon" means fund_status = 'Current' and days_to_expiration <= 90.
- PALT = procurement administrative lead time, submission to award (palt_days).
- lb_app_*_history tables hold actions taken in the app (alert assignments, package submissions, quarterly sign-offs),
  streamed from Lakebase; _pg_change_type is insert/update.

Rules:
- Unless the user asks about expired or prior-year funds, filter to fund_status = 'Current'.
- For KPIs aggregated by office, PPA, appropriation or fiscal year, prefer the metric view mv_budget_execution with MEASURE().
- For forecast or lapse questions use gold_lapse_risk_forecast (predicted_lapse_rate, projected_lapse_amount, risk_tier).
  Lines with risk_tier 'Outside forecast window' have no forecast yet.
- Show dollar amounts in millions with one decimal ($M) and rates as percentages with one decimal.
- For alerts, order by severity (Critical, High, Medium) and then amount_at_risk descending.
"""

EXAMPLES = [
    ("What is the obligation rate and burn rate versus plan by office for current funds?",
     f"""SELECT office, ROUND(MEASURE(total_budget) / 1e6, 1) AS total_budget_m,
       ROUND(MEASURE(obligated_to_date) / 1e6, 1) AS obligated_m,
       ROUND(100 * MEASURE(obligation_rate), 1) AS obligation_rate_pct,
       ROUND(100 * MEASURE(burn_rate_vs_plan), 1) AS burn_rate_vs_plan_pct
FROM {fq}.mv_budget_execution
WHERE fund_status = 'Current'
GROUP BY office
ORDER BY burn_rate_vs_plan_pct"""),
    ("Which unobligated balances expire in the next 90 days?",
     f"""SELECT line_id, ppa_name, office_code, tas, expiration_date, days_to_expiration,
       ROUND(unobligated_balance / 1e6, 1) AS unobligated_m, ROUND(uncommitted_balance / 1e6, 1) AS uncommitted_m,
       ROUND(100 * obligation_rate, 1) AS obligation_rate_pct
FROM {fq}.gold_budget_execution
WHERE fund_status = 'Current' AND days_to_expiration <= 90 AND unobligated_balance > 0
ORDER BY unobligated_balance DESC"""),
    ("What is the projected lapse by office?",
     f"""SELECT office_code, COUNT(*) AS lines_forecast, ROUND(SUM(projected_lapse_amount) / 1e6, 1) AS projected_lapse_m,
       COUNT_IF(risk_tier IN ('Critical', 'High')) AS high_risk_lines
FROM {fq}.gold_lapse_risk_forecast
WHERE risk_tier <> 'Outside forecast window'
GROUP BY office_code
ORDER BY projected_lapse_m DESC"""),
]

SAMPLE_QUESTIONS = [
    "What is the agency's obligation rate and burn rate vs plan for current funds?",
    "Which offices are furthest behind their spend plan?",
    "Which budget lines will lapse the most money at year end?",
    "Show the critical and high financial risk alerts",
    "Which open procurements will miss their fund expiration?",
]


def _id():
    return uuid.uuid4().hex


serialized = {
    "version": 2,
    "config": {"sample_questions": sorted([{"id": _id(), "question": [q]} for q in SAMPLE_QUESTIONS], key=lambda x: x["id"])},
    "data_sources": {"tables": sorted([{"identifier": f"{fq}.{t}"} for t in TABLES], key=lambda x: x["identifier"])},
    "instructions": {
        "text_instructions": [{"id": _id(), "content": [INSTRUCTIONS.strip()]}],
        "example_question_sqls": sorted([{"id": _id(), "question": [q], "sql": [s]} for q, s in EXAMPLES],
                                        key=lambda x: x["id"]),
    },
}
body = {"title": TITLE, "warehouse_id": warehouse_id, "serialized_space": json.dumps(serialized),
        "description": "Ask about budget execution, obligations vs plan, unobligated balances approaching expiration, "
                       "lapse forecasts, procurement pipeline and financial risk alerts (synthetic data)."}

spaces = api.do("GET", "/api/2.0/genie/spaces").get("spaces", [])
space_id = next((s["space_id"] for s in spaces if s.get("title") == TITLE), None)
if space_id:
    api.do("PATCH", f"/api/2.0/genie/spaces/{space_id}", body=body)
    print(f"Updated Genie space {space_id}")
else:
    space_id = api.do("POST", "/api/2.0/genie/spaces", body=body)["space_id"]
    print(f"Created Genie space {space_id}")
dbutils.jobs.taskValues.set("genie_space_id", space_id)
print(f"{w.config.host}/genie/rooms/{space_id}")
print("Tables:", *TABLES, sep="\n  ")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ask the questions leadership asks

# COMMAND ----------

QUESTIONS = [
    "What is the agency's overall obligation rate and burn rate versus plan for current funds?",
    "Which program offices are furthest behind their spend plan?",
    "Which budget lines have more than $1M unobligated and expire in the next 90 days?",
    "What is the total projected lapse by office according to the lapse-risk forecast?",
    "Show the critical and high severity financial risk alerts with the amount at risk",
    "What is the median procurement administrative lead time by acquisition type?",
    "Which open procurement requests will miss their fund expiration date, and how much money is involved?",
    "How did the Office of Transportation Safety's obligations compare to plan by fiscal quarter this year?",
]


def ask(question, timeout_s=240):
    start = api.do("POST", f"/api/2.0/genie/spaces/{space_id}/start-conversation", body={"content": question})
    conv, msg = start["conversation_id"], start["message_id"]
    t0 = time.time()
    while True:
        m = api.do("GET", f"/api/2.0/genie/spaces/{space_id}/conversations/{conv}/messages/{msg}")
        if m.get("status") in ("COMPLETED", "FAILED", "CANCELLED") or time.time() - t0 > timeout_s:
            break
        time.sleep(4)
    out = {"question": question, "status": m.get("status"), "sql": None, "description": None, "answer_text": None,
           "result_columns": None, "result_rows": None, "row_count": None, "seconds": round(time.time() - t0, 1)}
    for a in m.get("attachments") or []:
        if a.get("text"):
            out["answer_text"] = a["text"].get("content")
        if a.get("query"):
            out["sql"] = a["query"].get("query")
            out["description"] = a["query"].get("description")
            res = api.do("GET", f"/api/2.0/genie/spaces/{space_id}/conversations/{conv}/messages/{msg}"
                                f"/attachments/{a['attachment_id']}/query-result")
            sr = res.get("statement_response", {})
            cols = [c["name"] for c in sr.get("manifest", {}).get("schema", {}).get("columns", [])]
            rows = sr.get("result", {}).get("data_array", []) or []
            out.update(result_columns=json.dumps(cols), result_rows=json.dumps(rows[:25]),
                       row_count=sr.get("manifest", {}).get("total_row_count", len(rows)))
    return out


answers = []
for q in QUESTIONS:
    a = ask(q)
    answers.append(a)
    print(f"[{a['status']}] {q}  ({a['seconds']}s, {a['row_count']} rows)")

# COMMAND ----------

for a in answers:
    print("=" * 110)
    print("Q:", a["question"])
    if a["description"]:
        print("Genie:", a["description"])
    if a["answer_text"]:
        print("Text:", a["answer_text"])
    print("SQL:\n" + (a["sql"] or "(none)"))
    if a["result_columns"]:
        cols, rows = json.loads(a["result_columns"]), json.loads(a["result_rows"])
        print(pd.DataFrame(rows, columns=cols).head(12).to_string(index=False))

# COMMAND ----------

(spark.createDataFrame(pd.DataFrame(answers).assign(space_id=space_id, asked_at=datetime.now(timezone.utc)))
 .write.mode("append").option("mergeSchema", "true").saveAsTable(f"{fq}.genie_evaluation_runs"))
spark.sql(f"COMMENT ON TABLE {fq}.genie_evaluation_runs IS 'Log of benchmark questions asked of the Budget Execution Genie space: generated SQL, result sample and latency.'")
display(spark.table(f"{fq}.genie_evaluation_runs").orderBy("asked_at", ascending=False).limit(len(QUESTIONS))
        .select("question", "status", "row_count", "seconds"))
