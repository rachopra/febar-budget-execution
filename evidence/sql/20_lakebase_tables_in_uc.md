# Lakebase objects in Unity Catalog: synced serving tables and CDF write-back history

Executed 2026-10-15 14:26 UTC

```sql
SELECT table_name, table_type, created FROM rachopra_catalog.information_schema.tables
WHERE table_schema = 'fe_bar' AND table_name LIKE 'lb\_%' ORDER BY table_name
```

**Result:**

| table_name | table_type | created |
|---|---|---|
| lb_app_alert_actions_history | MANAGED | 2026-10-15T13:37:59.891Z |
| lb_app_procurement_packages_history | MANAGED | 2026-10-15T13:38:01.529Z |
| lb_app_review_signoffs_history | MANAGED | 2026-10-15T13:38:03.015Z |
| lb_budget_execution | FOREIGN | 2026-10-15T13:23:08.192Z |
| lb_execution_briefings | FOREIGN | 2026-10-15T13:24:00.868Z |
| lb_financial_risk_alerts | FOREIGN | 2026-10-15T13:23:35.612Z |
| lb_lapse_risk_forecast | FOREIGN | 2026-10-15T13:23:52.928Z |
| lb_monthly_execution | FOREIGN | 2026-10-15T13:23:16.903Z |
| lb_office_access_map | FOREIGN | 2026-10-15T13:24:26.628Z |
| lb_office_execution_summary | FOREIGN | 2026-10-15T13:23:26.684Z |
| lb_procurement_package_drafts | FOREIGN | 2026-10-15T13:24:19.838Z |
| lb_procurement_pipeline | FOREIGN | 2026-10-15T13:23:43.052Z |
| lb_quarterly_review_briefings | FOREIGN | 2026-10-15T13:24:11.829Z |
