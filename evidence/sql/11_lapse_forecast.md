# ML lapse-risk forecast for current lines (model @champion)

Executed 2026-10-15 14:26 UTC

```sql
SELECT risk_tier, COUNT(*) AS lines, ROUND(SUM(total_budget) / 1e6, 1) AS budget_m,
       ROUND(SUM(projected_lapse_amount) / 1e6, 2) AS projected_lapse_m,
       ROUND(SUM(spend_plan_implied_lapse_rate * total_budget) / 1e6, 2) AS spend_plan_implied_lapse_m,
       MAX(model_version) AS model_version
FROM rachopra_catalog.fe_bar.gold_lapse_risk_forecast GROUP BY risk_tier ORDER BY projected_lapse_m DESC NULLS LAST
```

**Result:**

| risk_tier | lines | budget_m | projected_lapse_m | spend_plan_implied_lapse_m | model_version |
|---|---|---|---|---|---|
| Critical | 4 | 165.0 | 23.44 | 23.91 | 2 |
| High | 7 | 355.8 | 23.09 | 18.73 | 2 |
| Moderate | 14 | 478.6 | 17.37 | 22.98 | 2 |
| Low | 4 | 144.2 | 1.97 | 1.96 | 2 |
| Outside forecast window | 16 | 1003.3 |  | 51.96 | 2 |
