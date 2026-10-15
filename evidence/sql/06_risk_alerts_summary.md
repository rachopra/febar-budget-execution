# Financial risk and variance alerts by type and severity

Executed 2026-10-15 14:26 UTC

```sql
SELECT alert_type, severity, COUNT(*) AS alerts, ROUND(SUM(amount_at_risk) / 1e6, 2) AS amount_at_risk_m
FROM rachopra_catalog.fe_bar.gold_financial_risk_alerts GROUP BY ALL
ORDER BY CASE severity WHEN 'Critical' THEN 0 WHEN 'High' THEN 1 ELSE 2 END, amount_at_risk_m DESC
```

**Result:**

| alert_type | severity | alerts | amount_at_risk_m |
|---|---|---|---|
| APPORTIONMENT_EXCEEDED | Critical | 1 | 1.36 |
| BURN_RATE_VARIANCE | High | 7 | 47.67 |
| LAPSE_RISK | High | 5 | 33.25 |
| PROCUREMENT_WILL_MISS_EXPIRATION | High | 4 | 15.41 |
| COMMITMENTS_EXCEED_AVAILABLE | High | 4 | 7.01 |
| PROMPT_PAY_RISK | High | 29 | 5.39 |
| POTENTIAL_DUPLICATE_INVOICE | High | 20 | 3.72 |
| INVOICE_EXCEEDS_OBLIGATION | High | 15 | 3.54 |
| STALE_SPEND_PLAN | Medium | 8 | 127.84 |
| BURN_RATE_VARIANCE | Medium | 12 | 86.98 |
| LAPSE_RISK | Medium | 6 | 12.8 |
| PROCUREMENT_WILL_MISS_EXPIRATION | Medium | 6 | 4.17 |
| UNMATCHED_INVOICE | Medium | 12 | 0.93 |
| PROMPT_PAY_RISK | Medium | 7 | 0.85 |
