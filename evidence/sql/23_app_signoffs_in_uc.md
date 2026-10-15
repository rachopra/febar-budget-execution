# App write-back round trip: quarterly review sign-offs

Executed 2026-10-15 14:26 UTC

```sql
SELECT _pg_change_type, _timestamp AS landed_in_uc, office_code, fiscal_year, fiscal_quarter, decision, comment, signed_by, signed_at
FROM rachopra_catalog.fe_bar.lb_app_review_signoffs_history ORDER BY signed_at
```

**Result:**

| _pg_change_type | landed_in_uc | office_code | fiscal_year | fiscal_quarter | decision | comment | signed_by | signed_at |
|---|---|---|---|---|---|---|---|---|
| insert | 2026-10-15T13:38:03.289 | OCIO | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-10-15T13:35:08.792Z |
| insert | 2026-10-15T14:08:43.019 | OCIO | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-10-15T14:08:42.526Z |
| insert | 2026-10-15T14:10:20.155 | OCIO | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-10-15T14:10:19.668Z |
| insert | 2026-10-15T14:25:28.072 | OCIO | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-10-15T14:25:28.066Z |
