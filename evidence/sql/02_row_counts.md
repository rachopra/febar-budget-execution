# Row counts through the medallion layers

Executed 2026-10-15 14:26 UTC

```sql
SELECT 'bronze_pr_events' AS table_name, COUNT(*) AS rows FROM rachopra_catalog.fe_bar.bronze_pr_events UNION ALL
SELECT 'silver_pr_events', COUNT(*) FROM rachopra_catalog.fe_bar.silver_pr_events UNION ALL
SELECT 'silver_procurement_requests', COUNT(*) FROM rachopra_catalog.fe_bar.silver_procurement_requests UNION ALL
SELECT 'silver_pr_status_history', COUNT(*) FROM rachopra_catalog.fe_bar.silver_pr_status_history UNION ALL
SELECT 'silver_obligations', COUNT(*) FROM rachopra_catalog.fe_bar.silver_obligations UNION ALL
SELECT 'bronze_invoices', COUNT(*) FROM rachopra_catalog.fe_bar.bronze_invoices UNION ALL
SELECT 'silver_invoices', COUNT(*) FROM rachopra_catalog.fe_bar.silver_invoices UNION ALL
SELECT 'bronze_spend_plan_budget_office', COUNT(*) FROM rachopra_catalog.fe_bar.bronze_spend_plan_budget_office UNION ALL
SELECT 'bronze_spend_plan_legacy', COUNT(*) FROM rachopra_catalog.fe_bar.bronze_spend_plan_legacy UNION ALL
SELECT 'silver_spend_plan', COUNT(*) FROM rachopra_catalog.fe_bar.silver_spend_plan UNION ALL
SELECT 'silver_spend_plan_current', COUNT(*) FROM rachopra_catalog.fe_bar.silver_spend_plan_current UNION ALL
SELECT 'silver_budget_lines', COUNT(*) FROM rachopra_catalog.fe_bar.silver_budget_lines UNION ALL
SELECT 'gold_budget_execution', COUNT(*) FROM rachopra_catalog.fe_bar.gold_budget_execution UNION ALL
SELECT 'gold_monthly_execution', COUNT(*) FROM rachopra_catalog.fe_bar.gold_monthly_execution UNION ALL
SELECT 'gold_procurement_pipeline', COUNT(*) FROM rachopra_catalog.fe_bar.gold_procurement_pipeline UNION ALL
SELECT 'gold_financial_risk_alerts', COUNT(*) FROM rachopra_catalog.fe_bar.gold_financial_risk_alerts UNION ALL
SELECT 'gold_lapse_risk_forecast', COUNT(*) FROM rachopra_catalog.fe_bar.gold_lapse_risk_forecast UNION ALL
SELECT 'gold_execution_briefings', COUNT(*) FROM rachopra_catalog.fe_bar.gold_execution_briefings UNION ALL
SELECT 'gold_procurement_package_drafts', COUNT(*) FROM rachopra_catalog.fe_bar.gold_procurement_package_drafts
```

**Result:**

| table_name | rows |
|---|---|
| silver_procurement_requests | 4211 |
| silver_pr_status_history | 21277 |
| silver_obligations | 3839 |
| silver_invoices | 19736 |
| bronze_pr_events | 21534 |
| silver_pr_events | 21443 |
| bronze_invoices | 19736 |
| bronze_spend_plan_budget_office | 43152 |
| bronze_spend_plan_legacy | 7092 |
| silver_spend_plan | 50244 |
| silver_spend_plan_current | 7584 |
| silver_budget_lines | 116 |
| gold_budget_execution | 116 |
| gold_monthly_execution | 3067 |
| gold_procurement_pipeline | 4211 |
| gold_financial_risk_alerts | 136 |
| gold_lapse_risk_forecast | 45 |
| gold_execution_briefings | 29 |
| gold_procurement_package_drafts | 26 |
