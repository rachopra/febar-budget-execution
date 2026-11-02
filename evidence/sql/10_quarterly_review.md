# FY2026 quarterly budget-performance review: obligations vs plan by office and quarter

Executed 2026-11-02 18:12 UTC

```sql
SELECT office_code, fiscal_quarter, ROUND(SUM(planned_obligations) / 1e6, 1) AS planned_m,
       ROUND(SUM(actual_obligations) / 1e6, 1) AS actual_m,
       ROUND(100 * SUM(actual_obligations) / NULLIF(SUM(planned_obligations), 0), 0) AS attainment_pct
FROM rachopra_catalog.fe_bar.gold_quarterly_review GROUP BY ALL ORDER BY office_code, fiscal_quarter
```

**Result:**

| office_code | fiscal_quarter | planned_m | actual_m | attainment_pct |
|---|---|---|---|---|
| OCIO | 1 | 25.0 | 29.1 | 117 |
| OCIO | 2 | 52.6 | 48.8 | 93 |
| OCIO | 3 | 73.7 | 63.4 | 86 |
| OCIO | 4 | 92.0 | 26.8 | 29 |
| OGM | 1 | 23.4 | 10.8 | 46 |
| OGM | 2 | 48.8 | 74.7 | 153 |
| OGM | 3 | 77.5 | 51.9 | 67 |
| OGM | 4 | 116.1 | 38.4 | 33 |
| OMA | 1 | 24.8 | 16.7 | 67 |
| OMA | 2 | 40.7 | 52.4 | 129 |
| OMA | 3 | 52.3 | 45.7 | 87 |
| OMA | 4 | 65.5 | 26.8 | 41 |
| OTS | 1 | 17.8 | 9.4 | 53 |
| OTS | 2 | 33.1 | 25.5 | 77 |
| OTS | 3 | 47.4 | 36.1 | 76 |
| OTS | 4 | 64.3 | 20.7 | 32 |
| OWD | 1 | 7.9 | 3.5 | 44 |
| OWD | 2 | 18.7 | 25.9 | 139 |
| OWD | 3 | 38.3 | 35.4 | 92 |
| OWD | 4 | 71.2 | 8.6 | 12 |
| OWS | 1 | 14.7 | 12.1 | 83 |
| OWS | 2 | 30.3 | 44.5 | 147 |
| OWS | 3 | 48.1 | 33.8 | 70 |
| OWS | 4 | 72.0 | 15.9 | 22 |
