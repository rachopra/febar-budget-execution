"""Run named evidence queries on a SQL warehouse and write each query + result to Markdown.

Usage: python scripts/sql_evidence.py [--profile P] [--warehouse ID] [--pipeline-id ID]
Writes evidence/sql/<name>.md and evidence/sql/README.md.
"""

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

FQ = "rachopra_catalog.fe_bar"


def queries(pipeline_id: str) -> dict[str, tuple[str, str]]:
    q = {
        "01_table_inventory": ("Every table and view in the schema, by medallion layer", f"""
SELECT table_name, table_type, comment
FROM rachopra_catalog.information_schema.tables
WHERE table_schema = 'fe_bar' AND table_name NOT LIKE '\\_\\_%' AND table_name NOT LIKE 'event_log%'
ORDER BY CASE WHEN table_name LIKE 'bronze%' THEN 1 WHEN table_name LIKE 'silver%' THEN 2
              WHEN table_name LIKE 'gold%' THEN 3 ELSE 4 END, table_name"""),
        "02_row_counts": ("Row counts through the medallion layers", f"""
SELECT 'bronze_pr_events' AS table_name, COUNT(*) AS rows FROM {FQ}.bronze_pr_events UNION ALL
SELECT 'silver_pr_events', COUNT(*) FROM {FQ}.silver_pr_events UNION ALL
SELECT 'silver_procurement_requests', COUNT(*) FROM {FQ}.silver_procurement_requests UNION ALL
SELECT 'silver_pr_status_history', COUNT(*) FROM {FQ}.silver_pr_status_history UNION ALL
SELECT 'silver_obligations', COUNT(*) FROM {FQ}.silver_obligations UNION ALL
SELECT 'bronze_invoices', COUNT(*) FROM {FQ}.bronze_invoices UNION ALL
SELECT 'silver_invoices', COUNT(*) FROM {FQ}.silver_invoices UNION ALL
SELECT 'bronze_spend_plan_budget_office', COUNT(*) FROM {FQ}.bronze_spend_plan_budget_office UNION ALL
SELECT 'bronze_spend_plan_legacy', COUNT(*) FROM {FQ}.bronze_spend_plan_legacy UNION ALL
SELECT 'silver_spend_plan', COUNT(*) FROM {FQ}.silver_spend_plan UNION ALL
SELECT 'silver_spend_plan_current', COUNT(*) FROM {FQ}.silver_spend_plan_current UNION ALL
SELECT 'silver_budget_lines', COUNT(*) FROM {FQ}.silver_budget_lines UNION ALL
SELECT 'gold_budget_execution', COUNT(*) FROM {FQ}.gold_budget_execution UNION ALL
SELECT 'gold_monthly_execution', COUNT(*) FROM {FQ}.gold_monthly_execution UNION ALL
SELECT 'gold_procurement_pipeline', COUNT(*) FROM {FQ}.gold_procurement_pipeline UNION ALL
SELECT 'gold_financial_risk_alerts', COUNT(*) FROM {FQ}.gold_financial_risk_alerts UNION ALL
SELECT 'gold_lapse_risk_forecast', COUNT(*) FROM {FQ}.gold_lapse_risk_forecast UNION ALL
SELECT 'gold_execution_briefings', COUNT(*) FROM {FQ}.gold_execution_briefings UNION ALL
SELECT 'gold_procurement_package_drafts', COUNT(*) FROM {FQ}.gold_procurement_package_drafts"""),
        "03_agency_kpis": ("Budget execution dashboard KPIs (current funds) via the UC metric view", f"""
SELECT ROUND(MEASURE(total_budget) / 1e6, 1) AS total_budget_m,
       ROUND(MEASURE(planned_obligations_to_date) / 1e6, 1) AS planned_to_date_m,
       ROUND(MEASURE(obligated_to_date) / 1e6, 1) AS obligated_m,
       ROUND(MEASURE(expended_to_date) / 1e6, 1) AS expended_m,
       ROUND(MEASURE(unobligated_balance) / 1e6, 1) AS remaining_balance_m,
       ROUND(100 * MEASURE(obligation_rate), 1) AS obligation_rate_pct,
       ROUND(100 * MEASURE(burn_rate_vs_plan), 1) AS burn_rate_vs_plan_pct,
       MEASURE(budget_lines) AS budget_lines
FROM {FQ}.mv_budget_execution WHERE fund_status = 'Current'"""),
        "04_funding_by_office": ("Funding by program office (current funds)", f"""
SELECT office, ROUND(MEASURE(total_budget) / 1e6, 1) AS budget_m, ROUND(MEASURE(obligated_to_date) / 1e6, 1) AS obligated_m,
       ROUND(MEASURE(expended_to_date) / 1e6, 1) AS expended_m, ROUND(MEASURE(unobligated_balance) / 1e6, 1) AS remaining_m,
       ROUND(100 * MEASURE(obligation_rate), 1) AS obligation_rate_pct, ROUND(100 * MEASURE(burn_rate_vs_plan), 1) AS burn_vs_plan_pct
FROM {FQ}.mv_budget_execution WHERE fund_status = 'Current' GROUP BY office ORDER BY burn_vs_plan_pct"""),
        "05_expiring_balances": ("Unobligated balances approaching deadlines (expire within 90 days)", f"""
SELECT b.line_id, b.ppa_name, b.tas, b.days_to_expiration, ROUND(b.total_budget / 1e6, 2) AS budget_m,
       ROUND(100 * b.obligation_rate, 1) AS obligated_pct, ROUND(b.uncommitted_balance / 1e6, 2) AS uncommitted_m,
       ROUND(100 * b.burn_rate_vs_plan, 0) AS vs_plan_pct, f.risk_tier, ROUND(f.projected_lapse_amount / 1e6, 2) AS projected_lapse_m
FROM {FQ}.gold_budget_execution b LEFT JOIN {FQ}.gold_lapse_risk_forecast f USING (line_id)
WHERE b.fund_status = 'Current' AND b.days_to_expiration <= 90
ORDER BY f.projected_lapse_amount DESC NULLS LAST"""),
        "06_risk_alerts_summary": ("Financial risk and variance alerts by type and severity", f"""
SELECT alert_type, severity, COUNT(*) AS alerts, ROUND(SUM(amount_at_risk) / 1e6, 2) AS amount_at_risk_m
FROM {FQ}.gold_financial_risk_alerts GROUP BY ALL
ORDER BY CASE severity WHEN 'Critical' THEN 0 WHEN 'High' THEN 1 ELSE 2 END, amount_at_risk_m DESC"""),
        "07_risk_alert_examples": ("Highest-exposure alert of each type", f"""
SELECT alert_type, severity, entity_id, ROUND(amount_at_risk / 1e6, 2) AS amount_at_risk_m, detail
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY alert_type ORDER BY amount_at_risk DESC) AS rn
      FROM {FQ}.gold_financial_risk_alerts) WHERE rn = 1 ORDER BY amount_at_risk_m DESC"""),
        "08_procurement_cycle": ("Procurement-cycle visibility: PALT by acquisition type and open pipeline at risk", f"""
SELECT acquisition_type,
       COUNT_IF(status = 'Awarded') AS awards, CAST(percentile_approx(palt_days, 0.5) AS INT) AS median_palt_days,
       COUNT_IF(is_open) AS open_prs, ROUND(SUM(CASE WHEN is_open THEN estimated_amount END) / 1e6, 1) AS open_value_m,
       COUNT_IF(at_risk_of_missing_expiration) AS open_prs_missing_expiration
FROM {FQ}.gold_procurement_pipeline GROUP BY acquisition_type ORDER BY median_palt_days"""),
        "09_stage_durations": ("Median days in each procurement stage (from the SCD2 status history)", f"""
SELECT acquisition_type, stage, SUM(completed_stage_transitions) AS transitions, MAX(median_days_in_stage) AS median_days
FROM {FQ}.gold_procurement_cycle_times GROUP BY ALL ORDER BY acquisition_type, median_days DESC"""),
        "10_quarterly_review": ("FY2026 quarterly budget-performance review: obligations vs plan by office and quarter", f"""
SELECT office_code, fiscal_quarter, ROUND(SUM(planned_obligations) / 1e6, 1) AS planned_m,
       ROUND(SUM(actual_obligations) / 1e6, 1) AS actual_m,
       ROUND(100 * SUM(actual_obligations) / NULLIF(SUM(planned_obligations), 0), 0) AS attainment_pct
FROM {FQ}.gold_quarterly_review GROUP BY ALL ORDER BY office_code, fiscal_quarter"""),
        "11_lapse_forecast": ("ML lapse-risk forecast for current lines (model @champion)", f"""
SELECT risk_tier, COUNT(*) AS lines, ROUND(SUM(total_budget) / 1e6, 1) AS budget_m,
       ROUND(SUM(projected_lapse_amount) / 1e6, 2) AS projected_lapse_m,
       ROUND(SUM(spend_plan_implied_lapse_rate * total_budget) / 1e6, 2) AS spend_plan_implied_lapse_m,
       MAX(model_version) AS model_version
FROM {FQ}.gold_lapse_risk_forecast GROUP BY risk_tier ORDER BY projected_lapse_m DESC NULLS LAST"""),
        "12_lapse_forecast_top_lines": ("Top projected lapses with model-explained drivers", f"""
SELECT line_id, ppa_name, days_to_expiration, ROUND(100 * obligation_rate, 1) AS obligated_pct,
       ROUND(100 * predicted_lapse_rate, 1) AS predicted_lapse_pct, ROUND(projected_lapse_amount / 1e6, 2) AS projected_lapse_m,
       risk_tier, array_join(top_risk_drivers, '; ') AS drivers
FROM {FQ}.gold_lapse_risk_forecast WHERE predicted_lapse_rate IS NOT NULL
ORDER BY projected_lapse_amount DESC LIMIT 12"""),
        "13_ai_briefings": ("GenAI execution briefings (ai_query) with grounding check", f"""
SELECT b.line_id, f.risk_tier, b.headline, b.summary, array_join(b.recommended_actions, ' | ') AS recommended_actions,
       b.grounding_passed, b.model_endpoint
FROM {FQ}.gold_execution_briefings b JOIN {FQ}.gold_lapse_risk_forecast f USING (line_id)
ORDER BY f.projected_lapse_amount DESC LIMIT 8"""),
        "14_ai_grounding": ("Grounding check pass rate for all AI outputs", f"""
SELECT 'execution briefings' AS output, COUNT(*) AS generated, COUNT_IF(grounding_passed) AS grounded,
       ROUND(100 * COUNT_IF(grounding_passed) / COUNT(*), 1) AS pass_pct FROM {FQ}.gold_execution_briefings
UNION ALL
SELECT 'quarterly review narratives', COUNT(*), COUNT_IF(grounding_passed), ROUND(100 * COUNT_IF(grounding_passed) / COUNT(*), 1)
FROM {FQ}.gold_quarterly_review_briefings
UNION ALL
SELECT 'procurement package drafts', COUNT(*), COUNT_IF(size(validation_issues) = 0),
       ROUND(100 * COUNT_IF(size(validation_issues) = 0) / COUNT(*), 1) FROM {FQ}.gold_procurement_package_drafts"""),
        "15_ai_quarterly_reviews": ("GenAI quarterly budget-performance review narratives", f"""
SELECT office_code, performance_summary, array_join(key_risks, ' | ') AS key_risks,
       array_join(decisions_requested, ' | ') AS decisions_requested, grounding_passed
FROM {FQ}.gold_quarterly_review_briefings ORDER BY office_code"""),
        "16_ai_procurement_packages": ("Automated procurement package initiation (AI drafts, validated)", f"""
SELECT package_id, title, recommended_acquisition_type, contract_number, ROUND(amount / 1e6, 2) AS amount_m,
       requirement_summary, array_join(milestones, ' | ') AS milestones, status, array_join(validation_issues, '; ') AS issues
FROM {FQ}.gold_procurement_package_drafts ORDER BY amount DESC"""),
        "17_uc_policies": ("Unity Catalog row filters and column masks on pipeline tables", f"""
SELECT table_name, 'ROW FILTER' AS policy, filter_name AS function, target_columns AS columns
FROM rachopra_catalog.information_schema.row_filters WHERE table_schema = 'fe_bar'
UNION ALL
SELECT table_name, 'COLUMN MASK', mask_name, column_name
FROM rachopra_catalog.information_schema.column_masks WHERE table_schema = 'fe_bar'"""),
        "18_uc_tags": ("Unity Catalog tags (governed tag policies: domain, layer, data_classification, contains_pii)", f"""
SELECT table_name, array_join(sort_array(collect_list(concat(tag_name, '=', tag_value))), ', ') AS tags
FROM rachopra_catalog.information_schema.table_tags WHERE schema_name = 'fe_bar' GROUP BY table_name ORDER BY table_name"""),
        "19_uc_column_docs": ("Unity Catalog column documentation on gold_budget_execution", f"""
SELECT column_name, data_type, comment FROM rachopra_catalog.information_schema.columns
WHERE table_schema = 'fe_bar' AND table_name = 'gold_budget_execution' AND comment IS NOT NULL ORDER BY ordinal_position"""),
        "20_lakebase_tables_in_uc": ("Lakebase objects in Unity Catalog: synced serving tables and CDF write-back history", f"""
SELECT table_name, table_type, created FROM rachopra_catalog.information_schema.tables
WHERE table_schema = 'fe_bar' AND table_name LIKE 'lb\\_%' ORDER BY table_name"""),
        "21_app_alert_actions_in_uc": ("App write-back round trip: alert actions (app -> Lakebase -> CDF -> UC Delta)", f"""
SELECT _pg_change_type, _timestamp AS landed_in_uc, alert_id, alert_type, line_id, action, assignee, note, acted_by, acted_at
FROM {FQ}.lb_app_alert_actions_history ORDER BY acted_at"""),
        "22_app_packages_in_uc": ("App write-back round trip: procurement packages submitted to acquisition", f"""
SELECT _pg_change_type, _timestamp AS landed_in_uc, package_id, line_id, title, acquisition_type, contract_number, amount,
       status, source, model_endpoint, created_by, created_at
FROM {FQ}.lb_app_procurement_packages_history ORDER BY created_at"""),
        "23_app_signoffs_in_uc": ("App write-back round trip: quarterly review sign-offs", f"""
SELECT _pg_change_type, _timestamp AS landed_in_uc, office_code, fiscal_year, fiscal_quarter, decision, comment, signed_by, signed_at
FROM {FQ}.lb_app_review_signoffs_history ORDER BY signed_at"""),
    }
    if pipeline_id:
        q["00_pipeline_expectations"] = ("Spark Declarative Pipeline: data-quality expectation results (latest update)", f"""
WITH latest AS (SELECT origin.update_id FROM event_log('{pipeline_id}') WHERE event_type = 'create_update' ORDER BY timestamp DESC LIMIT 1),
exp AS (SELECT explode(from_json(details:flow_progress:data_quality:expectations,
          'array<struct<name: string, dataset: string, passed_records: bigint, failed_records: bigint>>')) AS e
        FROM event_log('{pipeline_id}') WHERE event_type = 'flow_progress' AND origin.update_id IN (SELECT update_id FROM latest))
SELECT split(e.dataset, '\\\\.')[size(split(e.dataset, '\\\\.')) - 1] AS dataset, e.name AS expectation,
       SUM(e.passed_records) AS passed, SUM(e.failed_records) AS failed
FROM exp GROUP BY ALL ORDER BY failed DESC, dataset""")
        q["00_pipeline_update"] = ("Spark Declarative Pipeline: latest update lifecycle", f"""
SELECT timestamp, message FROM event_log('{pipeline_id}')
WHERE event_type = 'update_progress'
  AND origin.update_id = (SELECT origin.update_id FROM event_log('{pipeline_id}') WHERE event_type = 'create_update' ORDER BY timestamp DESC LIMIT 1)
ORDER BY timestamp""")
    return q


def run(stmt, profile, warehouse):
    body = {"statement": stmt, "warehouse_id": warehouse, "wait_timeout": "50s", "on_wait_timeout": "CONTINUE",
            "format": "JSON_ARRAY", "disposition": "INLINE"}
    call = lambda *a: json.loads(subprocess.run(["databricks", "api", *a, "-p", profile], capture_output=True, text=True).stdout)
    r = call("post", "/api/2.0/sql/statements", "--json", json.dumps(body))
    while r.get("status", {}).get("state") in ("PENDING", "RUNNING"):
        time.sleep(3)
        r = call("get", f"/api/2.0/sql/statements/{r['statement_id']}")
    if r.get("status", {}).get("state") != "SUCCEEDED":
        return None, r.get("status", {}).get("error", {}).get("message", "failed")
    return [c["name"] for c in r["manifest"]["schema"]["columns"]], r.get("result", {}).get("data_array") or []


def md(cols, rows):
    esc = lambda v: "" if v is None else str(v).replace("|", "\\|").replace("\n", " ")
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(esc(v) for v in r) + " |" for r in rows[:60]]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="fe-vm-rachopra-cyber-demo")
    ap.add_argument("--warehouse", default="5aa6f979abb6e2d1")
    ap.add_argument("--pipeline-id", default="")
    ap.add_argument("--out", default="evidence/sql")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    index = ["# SQL evidence", "", f"Queries executed on SQL warehouse `{a.warehouse}` at {stamp}.", "",
             "| Evidence | What it shows | Rows |", "|---|---|---|"]
    for name, (title, sql) in sorted(queries(a.pipeline_id).items()):
        cols, rows = run(sql, a.profile, a.warehouse)
        body = md(cols, rows) if cols else f"**Query failed:** {rows}"
        (out / f"{name}.md").write_text(f"# {title}\n\nExecuted {stamp}\n\n```sql\n{sql.strip()}\n```\n\n**Result:**\n\n{body}\n")
        index.append(f"| [{name}]({name}.md) | {title} | {len(rows) if cols else 'ERROR'} |")
        print(f"{name}: {len(rows) if cols else 'ERROR ' + str(rows)[:200]}")
    (out / "README.md").write_text("\n".join(index) + "\n")


if __name__ == "__main__":
    main()
