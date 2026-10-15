# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Govern: document, classify, define the KPIs once, prove the policies work
# MAGIC
# MAGIC * **Document** gold columns in Unity Catalog so analysts, Genie and the app share one definition of each figure.
# MAGIC * **Classify** with tags (domain, layer, source system, sensitivity, PII).
# MAGIC * **Metric view** `mv_budget_execution`: obligation rate, burn rate vs plan and the other KPIs, defined once in UC.
# MAGIC * **Prove** the row filter (office scoping) and column mask (payee PII) behave as designed.
# MAGIC * **Report** data-quality expectation results from the pipeline event log, and lineage.

# COMMAND ----------

dbutils.widgets.text("catalog", "rachopra_catalog")
dbutils.widgets.text("schema", "fe_bar")
dbutils.widgets.text("pipeline_id", "")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
pipeline_id = dbutils.widgets.get("pipeline_id")
fq = f"{catalog}.{schema}"
me = spark.sql("SELECT current_user()").first()[0]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Column documentation

# COMMAND ----------

COLUMN_DOCS = {
    "gold_budget_execution": {
        "line_id": "Budget line key: PPA code + budget fiscal year (e.g. OTS-GA-01-FY2026)",
        "budget_fiscal_year": "Budget fiscal year (BFY) the funds were appropriated for",
        "ppa_code": "Program, Project or Activity (PPA) code",
        "tas": "Treasury Account Symbol funding the line (agency-BFY[/EPOA]-main account)",
        "fund_type": "annual or multi-year funds",
        "expiration_date": "Last day the funds may be newly obligated (end of the period of availability)",
        "days_to_expiration": "Days from the reporting date until the funds expire",
        "fund_status": "Current (still available for new obligations) or Expired",
        "total_budget": "Enacted budget authority for the line ($)",
        "apportioned_to_date": "OMB-apportioned amount available through the current quarter ($)",
        "planned_obligations_to_date": "Obligations the approved baseline spend plan expected by the reporting date ($)",
        "reforecast_obligations_remaining": "Obligations still planned after the reporting date in the office's latest re-forecast ($)",
        "committed_not_obligated": "Funds certified on open procurement requests, not yet obligated ($)",
        "obligated_to_date": "Net obligations recorded through the reporting date, after deobligations ($)",
        "invoiced_to_date": "Invoices and grant drawdowns received against the line, excluding rejected ($)",
        "expended_to_date": "Payments disbursed against the line through the reporting date ($)",
        "unobligated_balance": "Remaining balance: total budget minus obligations ($)",
        "uncommitted_balance": "Total budget minus obligations minus open commitments ($)",
        "obligation_rate": "Obligated to date / total budget",
        "burn_rate_vs_plan": "Obligated to date / planned obligations to date (1.0 = on plan)",
        "expenditure_rate": "Expended to date / total budget",
        "execution_status": "On Plan, Behind Plan (<85% of plan), Ahead of Plan (>115%), No Plan, Expired",
        "spend_plan_age_days": "Days since the office last revised its spend plan",
    },
    "gold_financial_risk_alerts": {
        "alert_id": "Stable alert key (hash of alert type and entity)",
        "alert_type": "LAPSE_RISK, APPORTIONMENT_EXCEEDED, COMMITMENTS_EXCEED_AVAILABLE, BURN_RATE_VARIANCE, STALE_SPEND_PLAN, PROCUREMENT_WILL_MISS_EXPIRATION, STALLED_PROCUREMENT, INVOICE_EXCEEDS_OBLIGATION, POTENTIAL_DUPLICATE_INVOICE, UNMATCHED_INVOICE, PROMPT_PAY_RISK",
        "severity": "Critical, High or Medium",
        "entity_id": "The line, PR, obligation document or invoice the alert is about",
        "amount_at_risk": "Dollars exposed by the condition ($)",
        "detail": "Human-readable explanation of the alert",
    },
    "gold_procurement_pipeline": {
        "status": "Current PR status: Draft, Submitted, Funds Certified, In Solicitation, Under Evaluation, Awarded, Cancelled",
        "days_in_status": "Days the PR has been in its current status",
        "palt_days": "Procurement administrative lead time: submission to award (days)",
        "forecast_award_date": "Open PRs: submission date + historical median PALT for the acquisition type",
        "at_risk_of_missing_expiration": "Open PR whose forecast award date is after the funds expire",
    },
}


def run_ddl(statements):
    ok, failed = 0, []
    for s in statements:
        try:
            spark.sql(s)
            ok += 1
        except Exception as e:  # pipeline-owned objects may reject some ALTERs; report rather than hide
            failed.append((s[:90], str(e).splitlines()[0][:160]))
    return ok, failed


sql_str = lambda v: v.replace("\\", "\\\\").replace("'", "\\'")
stmts = [f"COMMENT ON COLUMN {fq}.{t}.{c} IS '{sql_str(d)}'" for t, cols in COLUMN_DOCS.items() for c, d in cols.items()]
ok, failed = run_ddl(stmts)
print(f"Column comments applied: {ok}/{len(stmts)}")
for f in failed[:5]:
    print("  FAILED:", f)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Classification tags

# COMMAND ----------

# Governed tag keys (account tag policies) are used with their allowed values: domain, layer,
# data_classification, contains_pii. The source tracker uses a free-form key.
TABLE_TAGS = {
    "bronze": {"layer": "bronze", "data_classification": "cui", "contains_pii": "true"},
    "silver": {"layer": "silver", "data_classification": "cui"},
    "gold": {"layer": "gold", "data_classification": "cui"},
}
SOURCE = {"spend_plan": "spend_plan_tracker", "pr_": "pr_tracker", "procurement": "pr_tracker",
          "obligation": "pr_tracker", "invoice": "invoice_register", "budget": "budget_formulation",
          "ppa": "budget_formulation"}
tables = [r.tableName for r in spark.sql(f"SHOW TABLES IN {fq}").collect() if not r.isTemporary]
stmts = []
for t in tables:
    layer = t.split("_")[0]
    if layer not in TABLE_TAGS:
        continue
    tags = {"domain": "finance", **TABLE_TAGS[layer]}
    src = next((v for k, v in SOURCE.items() if k in t), None)
    if src:
        tags["source_tracker"] = src
    if t == "silver_invoices":
        tags["contains_pii"] = "true"
    stmts.append(f"ALTER TABLE {fq}.{t} SET TAGS (" + ", ".join(f"'{k}' = '{v}'" for k, v in tags.items()) + ")")
for col, kind in [("vendor_tin", "tin"), ("remit_routing_number", "bank_routing"), ("remit_account_number", "bank_account")]:
    stmts.append(f"ALTER TABLE {fq}.silver_invoices ALTER COLUMN {col} SET TAGS ('payee_pii' = '{kind}')")
ok, failed = run_ddl(stmts)
print(f"Tag statements applied: {ok}/{len(stmts)}")
for f in failed[:5]:
    print("  FAILED:", f)

display(spark.sql(f"""
SELECT table_name, collect_list(concat(tag_name, '=', tag_value)) AS tags
FROM {catalog}.information_schema.table_tags WHERE schema_name = '{schema}'
GROUP BY table_name ORDER BY table_name
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Metric view: KPIs defined once

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {fq}.mv_budget_execution
WITH METRICS LANGUAGE YAML
COMMENT 'Governed budget-execution KPIs by office, PPA, appropriation and budget fiscal year.'
AS $$
version: 1.1
source: {fq}.gold_budget_execution
dimensions:
  - name: office
    expr: office_name
    comment: Program office that owns the PPA
  - name: office_code
    expr: office_code
  - name: ppa
    expr: ppa_name
    comment: Program, Project or Activity
  - name: ppa_code
    expr: ppa_code
  - name: appropriation
    expr: appropriation_name
  - name: budget_fiscal_year
    expr: budget_fiscal_year
  - name: fund_type
    expr: fund_type
  - name: fund_status
    expr: fund_status
    comment: Current or Expired
  - name: execution_status
    expr: execution_status
  - name: expiration_date
    expr: expiration_date
  - name: days_to_expiration
    expr: days_to_expiration
measures:
  - name: total_budget
    expr: SUM(total_budget)
    comment: Enacted budget authority
  - name: planned_obligations_to_date
    expr: SUM(planned_obligations_to_date)
  - name: committed_not_obligated
    expr: SUM(committed_not_obligated)
  - name: obligated_to_date
    expr: SUM(obligated_to_date)
  - name: expended_to_date
    expr: SUM(expended_to_date)
  - name: unobligated_balance
    expr: SUM(unobligated_balance)
    comment: Remaining balance (total budget minus obligations)
  - name: obligation_rate
    expr: SUM(obligated_to_date) / SUM(total_budget)
    comment: Share of budget authority obligated
  - name: burn_rate_vs_plan
    expr: SUM(obligated_to_date) / NULLIF(SUM(planned_obligations_to_date), 0)
    comment: Obligations as a share of the spend plan to date (1.0 = on plan)
  - name: expenditure_rate
    expr: SUM(expended_to_date) / SUM(total_budget)
  - name: budget_lines
    expr: COUNT(1)
$$
""")
display(spark.sql(f"""
SELECT office,
       ROUND(MEASURE(total_budget) / 1e6, 1) AS total_budget_m,
       ROUND(MEASURE(obligated_to_date) / 1e6, 1) AS obligated_m,
       ROUND(100 * MEASURE(obligation_rate), 1) AS obligation_rate_pct,
       ROUND(100 * MEASURE(burn_rate_vs_plan), 1) AS burn_vs_plan_pct,
       ROUND(MEASURE(unobligated_balance) / 1e6, 1) AS unobligated_m
FROM {fq}.mv_budget_execution
WHERE fund_status = 'Current'
GROUP BY office ORDER BY burn_vs_plan_pct
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Policies attached to tables

# COMMAND ----------

display(spark.sql(f"""
SELECT table_name, 'ROW FILTER' AS policy, filter_name AS function, target_columns AS on_columns
FROM {catalog}.information_schema.row_filters WHERE table_schema = '{schema}'
UNION ALL
SELECT table_name, 'COLUMN MASK', mask_name, column_name
FROM {catalog}.information_schema.column_masks WHERE table_schema = '{schema}'
ORDER BY table_name, policy
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Row filter: an agency-wide Budget Director vs. a program-office analyst
# MAGIC The same query is run twice. In between, this principal's entitlement is narrowed to OTS only, then restored.

# COMMAND ----------

def pr_counts():
    return spark.sql(f"""
        SELECT office_code, COUNT(*) AS procurement_requests, ROUND(SUM(estimated_amount)/1e6, 1) AS value_m
        FROM {fq}.silver_procurement_requests GROUP BY office_code ORDER BY office_code""").toPandas()


print("As Budget Director (office_code = ALL):")
display(pr_counts())
try:
    spark.sql(f"UPDATE {fq}.office_access_map SET office_code = 'OTS' WHERE principal = '{me}'")
    print("As OTS program analyst (office_code = OTS):")
    display(pr_counts())
finally:
    spark.sql(f"UPDATE {fq}.office_access_map SET office_code = 'ALL' WHERE principal = '{me}'")
print("Entitlement restored:", spark.sql(f"SELECT office_code FROM {fq}.office_access_map WHERE principal = '{me}'").first()[0])

# COMMAND ----------

# MAGIC %md
# MAGIC ### Column mask: payee TIN and bank details

# COMMAND ----------

def payees():
    return spark.sql(f"""SELECT invoice_id, vendor_name, vendor_tin, remit_routing_number, remit_account_number
                         FROM {fq}.silver_invoices ORDER BY invoice_id LIMIT 3""").toPandas()


print("Budget Director (can_view_payee_pii = false):")
display(payees())
try:
    spark.sql(f"UPDATE {fq}.office_access_map SET can_view_payee_pii = true WHERE principal = '{me}'")
    print("Disbursing Officer entitlement (can_view_payee_pii = true):")
    display(payees())
finally:
    spark.sql(f"UPDATE {fq}.office_access_map SET can_view_payee_pii = false WHERE principal = '{me}'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data quality: pipeline expectation results

# COMMAND ----------

if pipeline_id:
    display(spark.sql(f"""
    WITH latest AS (
      SELECT origin.update_id FROM event_log('{pipeline_id}')
      WHERE event_type = 'create_update' ORDER BY timestamp DESC LIMIT 1
    ),
    exp AS (
      SELECT explode(from_json(details:flow_progress:data_quality:expectations,
             'array<struct<name: string, dataset: string, passed_records: bigint, failed_records: bigint>>')) AS e
      FROM event_log('{pipeline_id}')
      WHERE event_type = 'flow_progress' AND origin.update_id IN (SELECT update_id FROM latest)
    )
    SELECT e.dataset, e.name AS expectation, SUM(e.passed_records) AS passed, SUM(e.failed_records) AS failed,
           ROUND(100 * SUM(e.failed_records) / NULLIF(SUM(e.passed_records) + SUM(e.failed_records), 0), 3) AS failed_pct
    FROM exp GROUP BY ALL ORDER BY failed DESC, dataset
    """))

# COMMAND ----------

if pipeline_id:
    display(spark.sql(f"""
    SELECT split(origin.flow_name, '\\.')[2] AS flow,
           SUM(details:flow_progress:metrics:num_output_rows::bigint) AS rows_written,
           SUM(details:flow_progress:data_quality:dropped_records::bigint) AS rows_dropped_by_expectations
    FROM event_log('{pipeline_id}')
    WHERE event_type = 'flow_progress' AND origin.flow_name LIKE '%.%.%'
      AND details:flow_progress:metrics:num_output_rows IS NOT NULL
      AND origin.update_id = (SELECT origin.update_id FROM event_log('{pipeline_id}')
                              WHERE event_type = 'create_update' ORDER BY timestamp DESC LIMIT 1)
    GROUP BY 1 ORDER BY 1
    """))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Bronze → silver reconciliation
# MAGIC Every raw record is either in silver, dropped by a named expectation, or removed as a duplicate delivery.

# COMMAND ----------

display(spark.sql(f"""
SELECT 'PR-tracker events' AS feed,
       (SELECT COUNT(*) FROM {fq}.bronze_pr_events) AS bronze_rows,
       (SELECT COUNT(DISTINCT event_id) FROM {fq}.bronze_pr_events) AS distinct_records,
       (SELECT COUNT(*) FROM {fq}.silver_pr_events) AS silver_rows
UNION ALL
SELECT 'Invoice register',
       (SELECT COUNT(*) FROM {fq}.bronze_invoices),
       (SELECT COUNT(DISTINCT invoice_id) FROM {fq}.bronze_invoices),
       (SELECT COUNT(*) FROM {fq}.silver_invoices)
UNION ALL
SELECT 'Spend plans (both templates)',
       (SELECT COUNT(*) FROM {fq}.bronze_spend_plan_budget_office) + (SELECT COUNT(*) FROM {fq}.bronze_spend_plan_legacy),
       NULL,
       (SELECT COUNT(*) FROM {fq}.silver_spend_plan)
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Lineage (Unity Catalog system tables)

# COMMAND ----------

try:
    display(spark.sql(f"""
    SELECT DISTINCT source_table_full_name AS upstream, target_table_full_name AS downstream
    FROM system.access.table_lineage
    WHERE target_table_full_name LIKE '{fq}.gold%' AND source_table_full_name LIKE '{fq}.%'
      AND event_date >= current_date() - INTERVAL 2 DAYS
    ORDER BY downstream, upstream
    """))
except Exception as e:
    print("Lineage system table not readable:", str(e).splitlines()[0])
