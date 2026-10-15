# Budget execution dashboard KPIs (current funds) via the UC metric view

Executed 2026-10-15 14:26 UTC

```sql
SELECT ROUND(MEASURE(total_budget) / 1e6, 1) AS total_budget_m,
       ROUND(MEASURE(planned_obligations_to_date) / 1e6, 1) AS planned_to_date_m,
       ROUND(MEASURE(obligated_to_date) / 1e6, 1) AS obligated_m,
       ROUND(MEASURE(expended_to_date) / 1e6, 1) AS expended_m,
       ROUND(MEASURE(unobligated_balance) / 1e6, 1) AS remaining_balance_m,
       ROUND(100 * MEASURE(obligation_rate), 1) AS obligation_rate_pct,
       ROUND(100 * MEASURE(burn_rate_vs_plan), 1) AS burn_rate_vs_plan_pct,
       MEASURE(budget_lines) AS budget_lines
FROM rachopra_catalog.fe_bar.mv_budget_execution WHERE fund_status = 'Current'
```

**Result:**

| total_budget_m | planned_to_date_m | obligated_m | expended_m | remaining_balance_m | obligation_rate_pct | burn_rate_vs_plan_pct | budget_lines |
|---|---|---|---|---|---|---|---|
| 2147.0 | 1485.9 | 1356.1 | 758.2 | 790.9 | 63.2 | 91.3 | 45 |
