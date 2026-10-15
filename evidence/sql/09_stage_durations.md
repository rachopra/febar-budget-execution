# Median days in each procurement stage (from the SCD2 status history)

Executed 2026-10-15 14:26 UTC

```sql
SELECT acquisition_type, stage, SUM(completed_stage_transitions) AS transitions, MAX(median_days_in_stage) AS median_days
FROM rachopra_catalog.fe_bar.gold_procurement_cycle_times GROUP BY ALL ORDER BY acquisition_type, median_days DESC
```

**Result:**

| acquisition_type | stage | transitions | median_days |
|---|---|---|---|
| Grant Award | In Solicitation | 329 | 81 |
| Grant Award | Under Evaluation | 288 | 67 |
| Grant Award | Draft | 330 | 9 |
| Grant Award | Funds Certified | 330 | 9 |
| Grant Award | Submitted | 330 | 7 |
| Modification | Funds Certified | 55 | 24 |
| Modification | Draft | 74 | 10 |
| Modification | Submitted | 69 | 7 |
| New Award | In Solicitation | 947 | 86 |
| New Award | Under Evaluation | 875 | 69 |
| New Award | Funds Certified | 958 | 10 |
| New Award | Draft | 959 | 8 |
| New Award | Submitted | 958 | 7 |
| New Award (Simplified) | In Solicitation | 361 | 40 |
| New Award (Simplified) | Draft | 371 | 9 |
| New Award (Simplified) | Submitted | 370 | 7 |
| New Award (Simplified) | Funds Certified | 370 | 7 |
| Option Exercise | Funds Certified | 510 | 19 |
| Option Exercise | Draft | 532 | 9 |
| Option Exercise | Submitted | 531 | 5 |
| Task Order | In Solicitation | 1790 | 48 |
| Task Order | Funds Certified | 1889 | 9 |
| Task Order | Draft | 1926 | 8 |
| Task Order | Submitted | 1914 | 6 |
