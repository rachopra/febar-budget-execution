# Genie Space

- Job task: `genie_space` (task run `19292932255085`)
- Result: **SUCCESS**, started 2026-11-02 18:12:56 UTC, ran 206s on serverless compute
- Notebook: `/Workspace/Users/rahul.chopra@databricks.com/.bundle/febar-budget-execution/dev/files/src/notebooks/06_genie_space`

# 06 · Genie: ask budget execution questions in plain English

Creates (or updates) the **Budget Execution - Ask the Data** Genie space over the governed gold tables, the metric
view, the lapse-risk forecast and the row-filtered procurement table, with a budget glossary, rules and trusted
SQL. Then asks the questions leadership actually asks through the Genie Conversation API and records each answer:
the generated SQL and its result.

```python
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
```

```python
TABLES = [
    "gold_budget_execution", "mv_budget_execution", "gold_monthly_execution", "gold_office_execution_summary",
    "gold_quarterly_review", "gold_financial_risk_alerts", "gold_procurement_pipeline",
    "gold_procurement_cycle_times", "gold_lapse_risk_forecast", "gold_execution_briefings",
    "silver_procurement_requests",
]
existing_tables = {r.tableName for r in spark.sql(f"SHOW TABLES IN {fq}").collect()}
# App write-backs streamed from Lakebase by the CDF config (present once the app has been used). A recreated
# CDF config writes a new `_1` table seeded with every row, so use the newest table of each stream.
def suffix(t):
    tail = t.rsplit("_", 1)[-1]
    return int(tail) if tail.isdigit() else 0

for stream in ["app_alert_actions", "app_procurement_packages", "app_review_signoffs",
               "app_reprogramming_requests", "app_line_notes"]:
    found = [t for t in existing_tables if t == f"lb_{stream}_history" or t.startswith(f"lb_{stream}_history_")]
    if found:
        TABLES.append(max(found, key=suffix))

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
- lb_app_*_history tables hold actions taken in the app (alert board moves, procurement package submissions,
  reprogramming requests and their approval, analyst notes on budget lines, quarterly sign-offs), streamed from
  Lakebase; _pg_change_type is insert/update. For the current status of a reprogramming request, use its latest row
  by _timestamp.

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
```

**Output:**

```text
Updated Genie space 01f1c89bee9a1ceb8ca7f0134bbea761
https://fevm-rachopra-cyber-demo.cloud.databricks.com/genie/rooms/01f1c89bee9a1ceb8ca7f0134bbea761
Tables:
  gold_budget_execution
  mv_budget_execution
  gold_monthly_execution
  gold_office_execution_summary
  gold_quarterly_review
  gold_financial_risk_alerts
  gold_procurement_pipeline
  gold_procurement_cycle_times
  gold_lapse_risk_forecast
  gold_execution_briefings
  silver_procurement_requests
  lb_app_alert_actions_history_1
  lb_app_procurement_packages_history_1
  lb_app_review_signoffs_history_1
  lb_app_reprogramming_requests_history
  lb_app_line_notes_history
```

## Ask the questions leadership asks

```python
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
```

**Output:**

```text
[COMPLETED] What is the agency's overall obligation rate and burn rate versus plan for current funds?  (20.9s, 1 rows)
[COMPLETED] Which program offices are furthest behind their spend plan?  (23.4s, 6 rows)
[COMPLETED] Which budget lines have more than $1M unobligated and expire in the next 90 days?  (16.6s, 26 rows)
[COMPLETED] What is the total projected lapse by office according to the lapse-risk forecast?  (16.6s, 6 rows)
[COMPLETED] Show the critical and high severity financial risk alerts with the amount at risk  (16.7s, 85 rows)
[COMPLETED] What is the median procurement administrative lead time by acquisition type?  (16.8s, 6 rows)
[COMPLETED] Which open procurement requests will miss their fund expiration date, and how much money is involved?  (20.8s, 10 rows)
[COMPLETED] How did the Office of Transportation Safety's obligations compare to plan by fiscal quarter this year?  (24.9s, 4 rows)
```

```python
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
```

**Output:**

```text
==============================================================================================================
Q: What is the agency's overall obligation rate and burn rate versus plan for current funds?
Genie: You want to see the obligation rate and burn rate compared to plan for current funds, broken down by each office in the agency.
Text: For **current funds**, the agency has obligated **$1,356.1M** out of **$2,147.0M**, for an overall obligation rate of **63.2%**. The burn rate versus plan for **current funds** is **91.3%**, which means obligations are running below plan based on the reported measure.
SQL:
SELECT MEASURE(`total_budget`) AS `total_budget`, MEASURE(`obligated_to_date`) AS `obligated_to_date`, 100 * MEASURE(`obligation_rate`) AS `obligation_rate_pct`, 100 * MEASURE(`burn_rate_vs_plan`) AS `burn_rate_vs_plan_pct`
FROM `rachopra_catalog`.`fe_bar`.`mv_budget_execution`
WHERE `fund_status` = 'Current'
GROUP BY ALL
 total_budget obligated_to_date obligation_rate_pct burn_rate_vs_plan_pct
2147031000.00     1356137416.88           63.163400             91.267800
==============================================================================================================
Q: Which program offices are furthest behind their spend plan?
Genie: You want to see a list of program offices that are currently furthest behind their planned spending, based on their burn rate compared to the plan.
Text: The program offices furthest behind their spend plan are **Office of Transportation Safety** and **Office of Workforce Development**, based on the lowest burn rate versus plan among current funds. Examples include:
- **Office of Transportation Safety (OTS):** **83.1%** of plan, with **$176.2M** obligated against **$212.1M** planned
- **Office of Workforce Development (OWD):** **91.4%** of plan, with **$95.0M** obligated against **$104.0M** planned
- **Office of Grid Modernization (OGM):** **91.7%** of plan, with **$309.5M** obligated against **$337.7M** planned
- **Office of the Chief Information Officer (OCIO):** **92.0%** of plan, with **$384.9M** obligated against **$418.5M** planned
- **Office of Water Systems (OWS):** **93.9%** of plan, with **$190.8M** obligated against **$203.2M** planned
Across all 6 offices shown, burn rate versus plan ranges from **83.1%** to **94.9%**, so every office in this result is currently below plan, with Transportation Safety the furthest behind.
SQL:
SELECT
  `office`,
  `office_code`,
  MEASURE(`total_budget`) AS `total_budget`,
  MEASURE(`planned_obligations_to_date`) AS `planned_obligations_to_date`,
  MEASURE(`obligated_to_date`) AS `obligated_to_date`,
  MEASURE(`burn_rate_vs_plan`) AS `burn_rate_vs_plan`
FROM `rachopra_catalog`.`fe_bar`.`mv_budget_execution`
WHERE `fund_status` ILIKE '%Current%'
  AND `office` IS NOT NULL
  AND `office_code` IS NOT NULL
GROUP BY ALL
HAVING `burn_rate_vs_plan` IS NOT NULL
ORDER BY `burn_rate_vs_plan` ASC
                                 office office_code total_budget planned_obligations_to_date obligated_to_date burn_rate_vs_plan
        Office of Transportation Safety         OTS 304063000.00                212135200.00      176219742.52          0.830695
        Office of Workforce Development         OWD 165619000.00                103978900.00       95013158.46          0.913773
           Office of Grid Modernization         OGM 492585000.00                337690850.79      309543024.69          0.916646
Office of the Chief Information Officer        OCIO 595446000.00                418523015.98      384930249.37          0.919735
                Office of Water Systems         OWS 297723000.00                203165213.16      190826633.76          0.939268
Office of Management and Administration         OMA 291595000.00                210395365.49      199604608.08          0.948712
==============================================================================================================
Q: Which budget lines have more than $1M unobligated and expire in the next 90 days?
Genie: You're looking for budget lines that have an unobligated balance greater than $1 million and are set to expire within the next 90 days. The results include details like the budget line ID, program name, office code and name, treasury account symbol, expiration date, days until expiration, unobligated and uncommitted balances, and the obligation rate, all filtered to only include currently available funds.
Text: Examples include:
- **OGM-GA-01-FY2026** — **State Energy Resilience Grants** (Office of Grid Modernization): **$41.0M** unobligated, expires in **61 days** on **2026-09-30**.
- **OWD-GA-01-FY2026** — **Infrastructure Workforce Grants** (Office of Workforce Development): **$38.7M** unobligated, expires in **61 days** on **2026-09-30**.
- **OWS-GA-01-FY2026** — **Tribal and Rural Water Grants** (Office of Water Systems): **$29.2M** unobligated, expires in **61 days** on **2026-09-30**.
- **OCIO-PCI-01-FY2024** — **Financial System Modernization** (Office of the Chief Information Officer): **$28.0M** unobligated, expires in **61 days** on **2026-09-30**.
- **OTS-GA-01-FY2026** — **Highway Safety Improvement Grants** (Office of Transportation Safety): **$17.6M** unobligated, expires in **61 days** on **2026-09-30**.
SQL:
SELECT
  `line_id`,
  `ppa_name`,
  `office_code`,
  `office_name`,
  `tas`,
  `expiration_date`,
  `days_to_expiration`,
  `unobligated_balance`,
  `uncommitted_balance`,
  `obligation_rate`
FROM `rachopra_catalog`.`fe_bar`.`gold_budget_execution`
WHERE `fund_status` = 'Current'
  AND `days_to_expiration` IS NOT NULL
  AND `days_to_expiration` <= 90
  AND `unobligated_balance` IS NOT NULL
  AND `unobligated_balance` > 1000000
ORDER BY `unobligated_balance` DESC
           line_id                          ppa_name office_code                             office_name                tas expiration_date days_to_expiration unobligated_balance uncommitted_balance obligation_rate
  OGM-GA-01-FY2026    State Energy Re
```

```python
(spark.createDataFrame(pd.DataFrame(answers).assign(space_id=space_id, asked_at=datetime.now(timezone.utc)))
 .write.mode("append").option("mergeSchema", "true").saveAsTable(f"{fq}.genie_evaluation_runs"))
spark.sql(f"COMMENT ON TABLE {fq}.genie_evaluation_runs IS 'Log of benchmark questions asked of the Budget Execution Genie space: generated SQL, result sample and latency.'")
display(spark.table(f"{fq}.genie_evaluation_runs").orderBy("asked_at", ascending=False).limit(len(QUESTIONS))
        .select("question", "status", "row_count", "seconds"))
```

**Output:**

| question | status | row_count | seconds |
|---|---|---|---|
| What is the agency's overall obligation rate and burn rate versus plan for current funds? | COMPLETED | 1 | 20.9 |
| Show the critical and high severity financial risk alerts with the amount at risk | COMPLETED | 85 | 16.7 |
| Which budget lines have more than $1M unobligated and expire in the next 90 days? | COMPLETED | 26 | 16.6 |
| What is the total projected lapse by office according to the lapse-risk forecast? | COMPLETED | 6 | 16.6 |
| What is the median procurement administrative lead time by acquisition type? | COMPLETED | 6 | 16.8 |
| Which program offices are furthest behind their spend plan? | COMPLETED | 6 | 23.4 |
| Which open procurement requests will miss their fund expiration date, and how much money is involved? | COMPLETED | 10 | 20.8 |
| How did the Office of Transportation Safety's obligations compare to plan by fiscal quarter this year? | COMPLETED | 4 | 24.9 |
