# App write-back round trip: quarterly review sign-offs

Executed 2026-11-02 18:12 UTC

```sql
SELECT 'lb_app_review_signoffs_history_1' AS uc_table, _pg_change_type, _timestamp AS landed_in_uc, office_code, fiscal_year, fiscal_quarter, decision, comment, signed_by, signed_at FROM rachopra_catalog.fe_bar.lb_app_review_signoffs_history_1
ORDER BY signed_at
```

**Result:**

| uc_table | _pg_change_type | landed_in_uc | office_code | fiscal_year | fiscal_quarter | decision | comment | signed_by | signed_at |
|---|---|---|---|---|---|---|---|---|---|
| lb_app_review_signoffs_history_1 | insert | 2026-11-02T18:02:39.800 | OCIO | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-10-15T13:35:08.792Z |
| lb_app_review_signoffs_history_1 | insert | 2026-11-02T18:02:39.800 | OCIO | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-10-15T14:08:42.526Z |
| lb_app_review_signoffs_history_1 | insert | 2026-11-02T18:02:39.800 | OCIO | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-10-15T14:10:19.668Z |
| lb_app_review_signoffs_history_1 | insert | 2026-11-02T18:02:39.800 | OCIO | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-10-15T14:25:28.066Z |
| lb_app_review_signoffs_history_1 | insert | 2026-11-02T18:04:24.961 | OGM | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-11-02T18:04:23.245Z |
| lb_app_review_signoffs_history_1 | insert | 2026-11-02T18:07:08.909 | OMA | 2026 | 3 | Approved with conditions | Approve Q3; submit Q4 obligation recovery plan for lines behind the approved spend plan. | rahul.chopra@databricks.com | 2026-11-02T18:07:08.901Z |
