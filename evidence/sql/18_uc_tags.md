# Unity Catalog tags (governed tag policies: domain, layer, data_classification, contains_pii)

Executed 2026-10-15 14:26 UTC

```sql
SELECT table_name, array_join(sort_array(collect_list(concat(tag_name, '=', tag_value))), ', ') AS tags
FROM rachopra_catalog.information_schema.table_tags WHERE schema_name = 'fe_bar' GROUP BY table_name ORDER BY table_name
```

**Result:**

| table_name | tags |
|---|---|
| bronze_budget_authority | contains_pii=true, data_classification=cui, domain=finance, layer=bronze, source_tracker=budget_formulation |
| bronze_invoices | contains_pii=true, data_classification=cui, domain=finance, layer=bronze, source_tracker=invoice_register |
| bronze_ppa_master | contains_pii=true, data_classification=cui, domain=finance, layer=bronze, source_tracker=budget_formulation |
| bronze_pr_events | contains_pii=true, data_classification=cui, domain=finance, layer=bronze, source_tracker=pr_tracker |
| bronze_spend_plan_budget_office | contains_pii=true, data_classification=cui, domain=finance, layer=bronze, source_tracker=spend_plan_tracker |
| bronze_spend_plan_legacy | contains_pii=true, data_classification=cui, domain=finance, layer=bronze, source_tracker=spend_plan_tracker |
| gold_budget_execution | data_classification=cui, domain=finance, layer=gold, source_tracker=budget_formulation |
| gold_execution_briefings | data_classification=cui, domain=finance, layer=gold |
| gold_financial_risk_alerts | data_classification=cui, domain=finance, layer=gold |
| gold_lapse_risk_forecast | data_classification=cui, domain=finance, layer=gold |
| gold_monthly_execution | data_classification=cui, domain=finance, layer=gold |
| gold_office_execution_summary | data_classification=cui, domain=finance, layer=gold |
| gold_procurement_cycle_times | data_classification=cui, domain=finance, layer=gold, source_tracker=pr_tracker |
| gold_procurement_package_drafts | data_classification=cui, domain=finance, layer=gold, source_tracker=pr_tracker |
| gold_procurement_pipeline | data_classification=cui, domain=finance, layer=gold, source_tracker=pr_tracker |
| gold_quarterly_review | data_classification=cui, domain=finance, layer=gold |
| gold_quarterly_review_briefings | data_classification=cui, domain=finance, layer=gold |
| silver_budget_lines | data_classification=cui, domain=finance, layer=silver, source_tracker=budget_formulation |
| silver_invoices | contains_pii=true, data_classification=cui, domain=finance, layer=silver, source_tracker=invoice_register |
| silver_obligations | data_classification=cui, domain=finance, layer=silver, source_tracker=pr_tracker |
| silver_ppa | data_classification=cui, domain=finance, layer=silver, source_tracker=budget_formulation |
| silver_pr_events | data_classification=cui, domain=finance, layer=silver, source_tracker=pr_tracker |
| silver_pr_status_history | data_classification=cui, domain=finance, layer=silver, source_tracker=pr_tracker |
| silver_procurement_requests | data_classification=cui, domain=finance, layer=silver, source_tracker=pr_tracker |
| silver_spend_plan | data_classification=cui, domain=finance, layer=silver, source_tracker=spend_plan_tracker |
| silver_spend_plan_baseline | data_classification=cui, domain=finance, layer=silver, source_tracker=spend_plan_tracker |
| silver_spend_plan_current | data_classification=cui, domain=finance, layer=silver, source_tracker=spend_plan_tracker |
