# Genie Space

- Job task: `genie_space` (task run `123694528472583`)
- Result: **SUCCESS**, started 2026-10-15 14:20:27 UTC, ran 199s on serverless compute
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
  lb_app_alert_actions_history
  lb_app_procurement_packages_history
  lb_app_review_signoffs_history
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
[COMPLETED] What is the agency's overall obligation rate and burn rate versus plan for current funds?  (33.1s, 1 rows)
[COMPLETED] Which program offices are furthest behind their spend plan?  (20.7s, 6 rows)
[COMPLETED] Which budget lines have more than $1M unobligated and expire in the next 90 days?  (20.7s, 26 rows)
[COMPLETED] What is the total projected lapse by office according to the lapse-risk forecast?  (16.7s, 6 rows)
[COMPLETED] Show the critical and high severity financial risk alerts with the amount at risk  (20.7s, 85 rows)
[COMPLETED] What is the median procurement administrative lead time by acquisition type?  (16.6s, 6 rows)
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
Genie: You want to see the obligation rate and burn rate compared to plan for current funds, broken down by each office.
Text: For **current funds**, the agency has **$1,356.1M** obligated out of **$2,147.0M** in total budget, for an overall obligation rate of **63.2%**. The burn rate versus plan is **91.3%**, which means current funds are running below plan overall.
SQL:
SELECT MEASURE(`total_budget`) AS `total_budget`, MEASURE(`obligated_to_date`) AS `obligated_to_date`, 100 * MEASURE(`obligation_rate`) AS `obligation_rate_pct`, 100 * MEASURE(`burn_rate_vs_plan`) AS `burn_rate_vs_plan_pct`
FROM `rachopra_catalog`.`fe_bar`.`mv_budget_execution`
WHERE `fund_status` = 'Current'
GROUP BY ALL
 total_budget obligated_to_date obligation_rate_pct burn_rate_vs_plan_pct
2147031000.00     1356137416.88           63.163400             91.267800
==============================================================================================================
Q: Which program offices are furthest behind their spend plan?
Genie: You want to see the obligation rate and how the actual spending compares to the planned spending for each program office with current funds.
Text: The program offices furthest behind plan are the ones with the **lowest burn rate versus plan** among current funds. Some of the offices furthest behind are:
- **Office of Transportation Safety** — **83.1%** of plan, with **$176.2M** obligated versus **$212.1M** planned
- **Office of Workforce Development** — **91.4%** of plan, with **$95.0M** obligated versus **$104.0M** planned
- **Office of Grid Modernization** — **91.7%** of plan, with **$309.5M** obligated versus **$337.7M** planned
- **Office of the Chief Information Officer** — **92.0%** of plan, with **$384.9M** obligated versus **$418.5M** planned
- **Office of Water Systems** — **93.9%** of plan, with **$190.8M** obligated versus **$203.2M** planned
Across all **6** offices shown, burn rate versus plan ranges from **83.1%** to **94.9%**, so **Office of Transportation Safety** is the clearest laggard.
SQL:
SELECT
  `office`,
  ROUND(MEASURE(`burn_rate_vs_plan`), 3) AS `burn_rate_vs_plan`,
  ROUND(try_divide(MEASURE(`obligated_to_date`),1e6), 1) AS `obligated_m`,
  ROUND(try_divide(MEASURE(`planned_obligations_to_date`),1e6), 1) AS `planned_obligations_m`,
  ROUND(try_divide(MEASURE(`total_budget`),1e6), 1) AS `total_budget_m`,
  ROUND(try_divide(MEASURE(`unobligated_balance`),1e6), 1) AS `unobligated_m`
FROM `rachopra_catalog`.`fe_bar`.`mv_budget_execution`
WHERE `fund_status` = 'Current'
  AND `office` IS NOT NULL
GROUP BY ALL
ORDER BY `burn_rate_vs_plan` ASC
                                 office burn_rate_vs_plan obligated_m planned_obligations_m total_budget_m unobligated_m
        Office of Transportation Safety             0.831       176.2                 212.1          304.1         127.8
        Office of Workforce Development             0.914        95.0                 104.0          165.6          70.6
           Office of Grid Modernization             0.917       309.5                 337.7          492.6         183.0
Office of the Chief Information Officer             0.920       384.9                 418.5          595.4         210.5
                Office of Water Systems             0.939       190.8                 203.2          297.7         106.9
Office of Management and Administration             0.949       199.6                 210.4          291.6          92.0
==============================================================================================================
Q: Which budget lines have more than $1M unobligated and expire in the next 90 days?
Genie: You want to see budget lines that currently have more than $1 million unobligated balance and will expire within the next 90 days.
Text: There are **26** current budget lines with more than **$1.0M** unobligated and expiring within the next **90 days**; all shown here expire on **2026-09-30** in **61 days**. Examples include:
- **State Energy Resilience Grants** (OGM-GA-01-FY2026): **$41.0M** unobligated, **49.8%** obligated
- **Infrastructure Workforce Grants** (OWD-GA-01-FY2026): **$38.7M** unobligated, **41.2%** obligated
- **Tribal and Rural Water Grants** (OWS-GA-01-FY2026): **$29.2M** unobligated, **39.0%** obligated
- **Financial System Modernization** (OCIO-PCI-01-FY2024): **$28.0M** unobligated, **72.6%** obligated
- **Highway Safety Improvement Grants** (OTS-GA-01-FY2026): **$17.6M** unobligated, **16.7%** obligated

Across these 26 lines, unobligated balances range from **$1.5M** to **$41.0M**, with the largest balances concentrated in several grant-funded lines.
SQL:
SELECT line_id, ppa_name, office_code, tas, expiration_date, days_to_expiration,
       ROUND(try_divide(unobligated_balance,1e6), 1) AS unobligated_m, ROUND(try_divide(uncommitted_balance,1e6), 1) AS uncommitted_m,
       ROUND(100 * obligation_rate, 1) AS obligation_rate_pct
FROM rachopra_catalog.fe_bar.gold_budget_execution
WHERE fund_status = 'Current' AND days_to_expiration <= 90 AND unobligated_balance > 1000000
ORDER BY unobligated_balance DESC
           line_id                          ppa_name office_code                tas expiration_date days_to_expiration unobligated_m uncommitted_m obligation_rate_pct
  OGM-GA-01-FY2026    State Energy Resilience Grants         OGM      999-2026-0600      2026-09-30                 61          41.0          -4.3                49.8
  OWD-GA-01-FY2026   Infrastructure Workforce Grants         OWD      999-2026-0600      2026-09-30                 61          38.7           5.3                41.2
  OWS-GA-01-FY2026     Tribal and Rural Water Grants         OWS      999-2026-0600      2026-09-30                 61          29.2           0.4                39.0
OCIO-PCI-0
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
| What is the agency's overall obligation rate and burn rate versus plan for current funds? | COMPLETED | 1 | 33.1 |
| Show the critical and high severity financial risk alerts with the amount at risk | COMPLETED | 85 | 20.7 |
| Which budget lines have more than $1M unobligated and expire in the next 90 days? | COMPLETED | 26 | 20.7 |
| What is the total projected lapse by office according to the lapse-risk forecast? | COMPLETED | 6 | 16.7 |
| What is the median procurement administrative lead time by acquisition type? | COMPLETED | 6 | 16.6 |
| Which program offices are furthest behind their spend plan? | COMPLETED | 6 | 20.7 |
| Which open procurement requests will miss their fund expiration date, and how much money is involved? | COMPLETED | 10 | 20.8 |
| How did the Office of Transportation Safety's obligations compare to plan by fiscal quarter this year? | COMPLETED | 4 | 24.9 |
