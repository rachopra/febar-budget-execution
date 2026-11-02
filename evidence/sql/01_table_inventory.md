# Every table and view in the schema, by medallion layer

Executed 2026-11-02 18:12 UTC

```sql
SELECT table_name, table_type, comment
FROM rachopra_catalog.information_schema.tables
WHERE table_schema = 'fe_bar' AND table_name NOT LIKE '\_\_%' AND table_name NOT LIKE 'event_log%'
ORDER BY CASE WHEN table_name LIKE 'bronze%' THEN 1 WHEN table_name LIKE 'silver%' THEN 2
              WHEN table_name LIKE 'gold%' THEN 3 ELSE 4 END, table_name
```

**Result:**

| table_name | table_type | comment |
|---|---|---|
| bronze_budget_authority | STREAMING_TABLE | Raw enacted budget authority and OMB apportionment by PPA and budget fiscal year. |
| bronze_invoices | STREAMING_TABLE | Raw invoice register extracts from the payment systems (IPP / PMS). Contains payee PII. |
| bronze_ppa_master | STREAMING_TABLE | Raw PPA / office / appropriation reference list from the budget office. |
| bronze_pr_events | STREAMING_TABLE | Raw procurement-request tracker change events (nested JSON, one event per status change or award action). |
| bronze_spend_plan_budget_office | STREAMING_TABLE | Raw spend-plan spreadsheets submitted on the budget-office template (whole dollars). |
| bronze_spend_plan_legacy | STREAMING_TABLE | Raw spend-plan spreadsheets submitted on the legacy office template (thousands of dollars). |
| silver_budget_lines | MATERIALIZED_VIEW | Budget lines (PPA x budget fiscal year) with enacted authority, OMB apportionment and period of availability. |
| silver_invoices | STREAMING_TABLE | Latest status of every invoice / grant drawdown (AUTO CDC on invoice_id). Payee TIN and bank details are masked. |
| silver_obligations | STREAMING_TABLE | Obligations recorded against each budget line: awards, option exercises, modifications and deobligations. Row-filtered by office. |
| silver_ppa | MATERIALIZED_VIEW | Conformed PPA reference: one row per Program/Project/Activity with owning office and appropriation. |
| silver_pr_events | STREAMING_TABLE | PR-tracker events, flattened, typed and de-duplicated (the export re-delivers some events). |
| silver_pr_status_history | STREAMING_TABLE | Full status history of every procurement request (AUTO CDC, SCD type 2) for procurement-cycle (PALT) analysis. |
| silver_procurement_requests | STREAMING_TABLE | Current state of every procurement request (AUTO CDC, SCD type 1). Row-filtered by office. |
| silver_spend_plan | STREAMING_TABLE | Every spend-plan revision from every office, normalised to whole dollars by PPA, object class and month. |
| silver_spend_plan_baseline | MATERIALIZED_VIEW | Baseline (approved operating) spend plan: the first revision each office submitted after full-year enactment. Execution is measured against this plan; later revisions re-forecast and true past months up to actuals. |
| silver_spend_plan_current | MATERIALIZED_VIEW | Current spend plan (re-forecast): the latest revision each office has submitted for each budget fiscal year. |
| gold_budget_execution | MATERIALIZED_VIEW | Budget execution by budget line (PPA x budget fiscal year) as of the reporting date: total budget, apportionment, baseline spend plan and latest re-forecast, commitments, obligations, expenditures, balances and rates. One row per line. |
| gold_execution_briefings | MANAGED | AI-generated weekly execution briefing per current budget line (ai_query over governed gold facts), with a numeric grounding check. |
| gold_financial_risk_alerts | MATERIALIZED_VIEW | Financial risk and variance alerts as of the reporting date: lapse risk, apportionment (Antideficiency Act) exposure, commitments exceeding available funds, burn-rate variance, stale spend plans, procurements that will miss fund expiration, stalled procurements, over-billing, duplicate and unmatched invoices, and Prompt Payment Act exposure. |
| gold_lapse_risk_forecast | MANAGED | Lapse-risk forecast for every current budget line as of the reporting date: predicted share and dollars expiring unobligated, risk tier and top drivers (model rachopra_catalog.fe_bar.lapse_risk_model@champion). |
| gold_monthly_execution | MATERIALIZED_VIEW | Monthly and cumulative planned (baseline operating plan) vs actual obligations and expenditures by budget line, through the reporting date. Use for burn-rate charts. |
| gold_office_execution_summary | MATERIALIZED_VIEW | Funding and execution rolled up by program office and budget fiscal year (current and expired lines). |
| gold_procurement_cycle_times | MATERIALIZED_VIEW | Procurement administrative lead time by stage: median and p80 days spent in each status by office and acquisition type, from the SCD2 status history. |
| gold_procurement_package_drafts | MANAGED | AI-initiated procurement request packages for lines forecast to lapse, validated against feasible PALT and active contracts. Pending program-office review. |
| gold_procurement_pipeline | MATERIALIZED_VIEW | Procurement-cycle visibility: every procurement request with milestone dates, days in current status, PALT, and for open requests a forecast award date (historical median PALT for the acquisition type) compared with fund expiration. |
| gold_quarterly_review | MATERIALIZED_VIEW | Quarterly budget-performance review for the current fiscal year: planned vs actual obligations and expenditures by office, PPA and fiscal quarter, with cumulative variance. |
| gold_quarterly_review_briefings | MANAGED | AI-drafted quarterly budget-performance review narrative per program office, grounded in gold_quarterly_review and current risk alerts. |
| genie_evaluation_runs | MANAGED | Log of benchmark questions asked of the Budget Execution Genie space: generated SQL, result sample and latency. |
| lb_app_alert_actions_history | MANAGED |  |
| lb_app_alert_actions_history_1 | MANAGED |  |
| lb_app_line_notes_history | MANAGED |  |
| lb_app_procurement_packages_history | MANAGED |  |
| lb_app_procurement_packages_history_1 | MANAGED |  |
| lb_app_reprogramming_requests_history | MANAGED |  |
| lb_app_review_signoffs_history | MANAGED |  |
| lb_app_review_signoffs_history_1 | MANAGED |  |
| lb_budget_execution | FOREIGN |  |
| lb_execution_briefings | FOREIGN |  |
| lb_financial_risk_alerts | FOREIGN |  |
| lb_lapse_risk_forecast | FOREIGN |  |
| lb_monthly_execution | FOREIGN |  |
| lb_office_access_map | FOREIGN |  |
| lb_office_execution_summary | FOREIGN |  |
| lb_procurement_package_drafts | FOREIGN |  |
| lb_procurement_pipeline | FOREIGN |  |
| lb_quarterly_review_briefings | FOREIGN |  |
| ml_lapse_training_set | MANAGED | Point-in-time lapse-risk training set: features as known at each checkpoint before expiration, label = share of budget authority unobligated at expiration. |
| mv_budget_execution | METRIC_VIEW | Governed budget-execution KPIs by office, PPA, appropriation and budget fiscal year. |
| office_access_map | MANAGED | Entitlements driving the office row filter and the payee-PII column mask. |
