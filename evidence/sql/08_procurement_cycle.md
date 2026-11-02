# Procurement-cycle visibility: PALT by acquisition type and open pipeline at risk

Executed 2026-11-02 18:12 UTC

```sql
SELECT acquisition_type,
       COUNT_IF(status = 'Awarded') AS awards, CAST(percentile_approx(palt_days, 0.5) AS INT) AS median_palt_days,
       COUNT_IF(is_open) AS open_prs, ROUND(SUM(CASE WHEN is_open THEN estimated_amount END) / 1e6, 1) AS open_value_m,
       COUNT_IF(at_risk_of_missing_expiration) AS open_prs_missing_expiration
FROM rachopra_catalog.fe_bar.gold_procurement_pipeline GROUP BY acquisition_type ORDER BY median_palt_days
```

**Result:**

| acquisition_type | awards | median_palt_days | open_prs | open_value_m | open_prs_missing_expiration |
|---|---|---|---|---|---|
| Option Exercise | 492 | 21 | 27 | 19.9 | 0 |
| Modification | 52 | 26 | 21 | 33.2 | 0 |
| New Award (Simplified) | 347 | 51 | 13 | 1.6 | 0 |
| Task Order | 1716 | 59 | 139 | 105.6 | 1 |
| Grant Award | 239 | 153 | 42 | 116.7 | 4 |
| New Award | 827 | 155 | 86 | 157.7 | 5 |
