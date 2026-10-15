# Funding by program office (current funds)

Executed 2026-10-15 14:26 UTC

```sql
SELECT office, ROUND(MEASURE(total_budget) / 1e6, 1) AS budget_m, ROUND(MEASURE(obligated_to_date) / 1e6, 1) AS obligated_m,
       ROUND(MEASURE(expended_to_date) / 1e6, 1) AS expended_m, ROUND(MEASURE(unobligated_balance) / 1e6, 1) AS remaining_m,
       ROUND(100 * MEASURE(obligation_rate), 1) AS obligation_rate_pct, ROUND(100 * MEASURE(burn_rate_vs_plan), 1) AS burn_vs_plan_pct
FROM rachopra_catalog.fe_bar.mv_budget_execution WHERE fund_status = 'Current' GROUP BY office ORDER BY burn_vs_plan_pct
```

**Result:**

| office | budget_m | obligated_m | expended_m | remaining_m | obligation_rate_pct | burn_vs_plan_pct |
|---|---|---|---|---|---|---|
| Office of Transportation Safety | 304.1 | 176.2 | 103.9 | 127.8 | 58.0 | 83.1 |
| Office of Workforce Development | 165.6 | 95.0 | 23.9 | 70.6 | 57.4 | 91.4 |
| Office of Grid Modernization | 492.6 | 309.5 | 153.5 | 183.0 | 62.8 | 91.7 |
| Office of the Chief Information Officer | 595.4 | 384.9 | 269.0 | 210.5 | 64.6 | 92.0 |
| Office of Water Systems | 297.7 | 190.8 | 104.6 | 106.9 | 64.1 | 93.9 |
| Office of Management and Administration | 291.6 | 199.6 | 103.3 | 92.0 | 68.5 | 94.9 |
