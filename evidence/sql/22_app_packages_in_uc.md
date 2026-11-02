# App write-back round trip: procurement packages submitted to acquisition

Executed 2026-11-02 18:12 UTC

```sql
SELECT 'lb_app_procurement_packages_history_1' AS uc_table, _pg_change_type, _timestamp AS landed_in_uc, package_id, line_id, title, acquisition_type, contract_number, amount, status, source, model_endpoint, created_by, created_at FROM rachopra_catalog.fe_bar.lb_app_procurement_packages_history_1
ORDER BY created_at
```

**Result:**

| uc_table | _pg_change_type | landed_in_uc | package_id | line_id | title | acquisition_type | contract_number | amount | status | source | model_endpoint | created_by | created_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lb_app_procurement_packages_history_1 | insert | 2026-11-02T18:02:38.231 | REQ-OWD-GA-01-FY2026-01 | OWD-GA-01-FY2026 | Option Exercise on Contract DCI26C000954 (Cobalt Technologies Partners) to Obligate Projected-to-Lapse FY2026 Funds, Fund 999-2026-0600 (OWD-GA-01) | Option Exercise | DCI26C000954 | 7417000.00 | Submitted to Acquisition | App - on-demand AI draft | databricks-claude-sonnet-5-5 | rahul.chopra@databricks.com | 2026-10-15T14:10:19.547Z |
| lb_app_procurement_packages_history_1 | insert | 2026-11-02T18:02:38.231 | REQ-OWD-GA-01-FY2026-02 | OWD-GA-01-FY2026 | Option Exercise on Contract DCI26C000954 (Cobalt Technologies Partners) to Obligate Expiring FY2026 Funds, Fund 999-2026-0600 (OWD-GA-01) | Option Exercise | DCI26C000954 | 4200000.00 | Submitted to Acquisition | App - on-demand AI draft | databricks-claude-sonnet-5-5 | rahul.chopra@databricks.com | 2026-10-15T14:25:27.944Z |
| lb_app_procurement_packages_history_1 | insert | 2026-11-02T18:04:22.938 | REQ-OCIO-PCI-01-FY2024-01 | OCIO-PCI-01-FY2024 | FY2026 Financial System Modernization – Year-End IT Professional Services Modification (DCI26F001274) | Modification | DCI26F001274 | 1903840.14 | Submitted to Acquisition | Year-end plan - batch AI draft | databricks-claude-sonnet-5-5 | rahul.chopra@databricks.com | 2026-11-02T18:04:22.386Z |
| lb_app_procurement_packages_history_1 | insert | 2026-11-02T18:07:08.028 | REQ-OTS-PCI-01-FY2024-01 | OTS-PCI-01-FY2024 | Bridge Inspection Systems – Year-End Option Exercise (OTS-PCI-01) | Option Exercise | DCI25C000558 | 1039509.21 | Submitted to Acquisition | Year-end plan - batch AI draft | databricks-claude-sonnet-5-5 | rahul.chopra@databricks.com | 2026-11-02T18:07:08.023Z |
