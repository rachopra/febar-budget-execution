# App write-back round trip: procurement packages submitted to acquisition

Executed 2026-10-15 14:26 UTC

```sql
SELECT _pg_change_type, _timestamp AS landed_in_uc, package_id, line_id, title, acquisition_type, contract_number, amount,
       status, source, model_endpoint, created_by, created_at
FROM rachopra_catalog.fe_bar.lb_app_procurement_packages_history ORDER BY created_at
```

**Result:**

| _pg_change_type | landed_in_uc | package_id | line_id | title | acquisition_type | contract_number | amount | status | source | model_endpoint | created_by | created_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| insert | 2026-10-15T14:10:20.154 | REQ-OWD-GA-01-FY2026-01 | OWD-GA-01-FY2026 | Option Exercise on Contract DCI26C000954 (Cobalt Technologies Partners) to Obligate Projected-to-Lapse FY2026 Funds, Fund 999-2026-0600 (OWD-GA-01) | Option Exercise | DCI26C000954 | 7417000.00 | Submitted to Acquisition | App - on-demand AI draft | databricks-claude-sonnet-5-5 | rahul.chopra@databricks.com | 2026-10-15T14:10:19.547Z |
| insert | 2026-10-15T14:25:27.950 | REQ-OWD-GA-01-FY2026-02 | OWD-GA-01-FY2026 | Option Exercise on Contract DCI26C000954 (Cobalt Technologies Partners) to Obligate Expiring FY2026 Funds, Fund 999-2026-0600 (OWD-GA-01) | Option Exercise | DCI26C000954 | 4200000.00 | Submitted to Acquisition | App - on-demand AI draft | databricks-claude-sonnet-5-5 | rahul.chopra@databricks.com | 2026-10-15T14:25:27.944Z |
