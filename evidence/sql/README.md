# SQL evidence

Queries executed on SQL warehouse `5aa6f979abb6e2d1` at 2026-10-15 14:26 UTC.

| Evidence | What it shows | Rows |
|---|---|---|
| [00_pipeline_expectations](00_pipeline_expectations.md) | Spark Declarative Pipeline: data-quality expectation results (latest update) | 20 |
| [00_pipeline_update](00_pipeline_update.md) | Spark Declarative Pipeline: latest update lifecycle | 6 |
| [01_table_inventory](01_table_inventory.md) | Every table and view in the schema, by medallion layer | 44 |
| [02_row_counts](02_row_counts.md) | Row counts through the medallion layers | 19 |
| [03_agency_kpis](03_agency_kpis.md) | Budget execution dashboard KPIs (current funds) via the UC metric view | 1 |
| [04_funding_by_office](04_funding_by_office.md) | Funding by program office (current funds) | 6 |
| [05_expiring_balances](05_expiring_balances.md) | Unobligated balances approaching deadlines (expire within 90 days) | 29 |
| [06_risk_alerts_summary](06_risk_alerts_summary.md) | Financial risk and variance alerts by type and severity | 14 |
| [07_risk_alert_examples](07_risk_alert_examples.md) | Highest-exposure alert of each type | 10 |
| [08_procurement_cycle](08_procurement_cycle.md) | Procurement-cycle visibility: PALT by acquisition type and open pipeline at risk | 6 |
| [09_stage_durations](09_stage_durations.md) | Median days in each procurement stage (from the SCD2 status history) | 24 |
| [10_quarterly_review](10_quarterly_review.md) | FY2026 quarterly budget-performance review: obligations vs plan by office and quarter | 24 |
| [11_lapse_forecast](11_lapse_forecast.md) | ML lapse-risk forecast for current lines (model @champion) | 5 |
| [12_lapse_forecast_top_lines](12_lapse_forecast_top_lines.md) | Top projected lapses with model-explained drivers | 12 |
| [13_ai_briefings](13_ai_briefings.md) | GenAI execution briefings (ai_query) with grounding check | 8 |
| [14_ai_grounding](14_ai_grounding.md) | Grounding check pass rate for all AI outputs | 3 |
| [15_ai_quarterly_reviews](15_ai_quarterly_reviews.md) | GenAI quarterly budget-performance review narratives | 6 |
| [16_ai_procurement_packages](16_ai_procurement_packages.md) | Automated procurement package initiation (AI drafts, validated) | 26 |
| [17_uc_policies](17_uc_policies.md) | Unity Catalog row filters and column masks on pipeline tables | 6 |
| [18_uc_tags](18_uc_tags.md) | Unity Catalog tags (governed tag policies: domain, layer, data_classification, contains_pii) | 27 |
| [19_uc_column_docs](19_uc_column_docs.md) | Unity Catalog column documentation on gold_budget_execution | 22 |
| [20_lakebase_tables_in_uc](20_lakebase_tables_in_uc.md) | Lakebase objects in Unity Catalog: synced serving tables and CDF write-back history | 13 |
| [21_app_alert_actions_in_uc](21_app_alert_actions_in_uc.md) | App write-back round trip: alert actions (app -> Lakebase -> CDF -> UC Delta) | 4 |
| [22_app_packages_in_uc](22_app_packages_in_uc.md) | App write-back round trip: procurement packages submitted to acquisition | 2 |
| [23_app_signoffs_in_uc](23_app_signoffs_in_uc.md) | App write-back round trip: quarterly review sign-offs | 4 |
