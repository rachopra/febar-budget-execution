# App write-back round trip: alert actions (app -> Lakebase -> CDF -> UC Delta)

Executed 2026-11-02 18:12 UTC

```sql
SELECT 'lb_app_alert_actions_history_1' AS uc_table, _pg_change_type, _timestamp AS landed_in_uc, alert_id, alert_type, line_id, action, assignee, note, acted_by, acted_at FROM rachopra_catalog.fe_bar.lb_app_alert_actions_history_1
ORDER BY acted_at
```

**Result:**

| uc_table | _pg_change_type | landed_in_uc | alert_id | alert_type | line_id | action | assignee | note | acted_by | acted_at |
|---|---|---|---|---|---|---|---|---|---|---|
| lb_app_alert_actions_history_1 | insert | 2026-11-02T18:02:36.406 | 47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456 | APPORTIONMENT_EXCEEDED | OCIO-PCI-01-FY2026 | Assigned | budget.analyst@dci.example.gov | Prepare apportionment reapportionment request before further obligations. | rahul.chopra@databricks.com | 2026-10-15T13:35:08.332Z |
| lb_app_alert_actions_history_1 | insert | 2026-11-02T18:02:36.406 | 47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456 | APPORTIONMENT_EXCEEDED | OCIO-PCI-01-FY2026 | Assigned | budget.analyst@dci.example.gov | Prepare apportionment reapportionment request before further obligations. | rahul.chopra@databricks.com | 2026-10-15T14:08:29.766Z |
| lb_app_alert_actions_history_1 | insert | 2026-11-02T18:02:36.406 | 47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456 | APPORTIONMENT_EXCEEDED | OCIO-PCI-01-FY2026 | Assigned | budget.analyst@dci.example.gov | Prepare apportionment reapportionment request before further obligations. | rahul.chopra@databricks.com | 2026-10-15T14:10:00.029Z |
| lb_app_alert_actions_history_1 | insert | 2026-11-02T18:02:36.406 | 47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456 | APPORTIONMENT_EXCEEDED | OCIO-PCI-01-FY2026 | Assigned | budget.analyst@dci.example.gov | Prepare apportionment reapportionment request before further obligations. | rahul.chopra@databricks.com | 2026-10-15T14:25:06.769Z |
| lb_app_alert_actions_history_1 | insert | 2026-11-02T18:04:24.453 | 8915b868e77ef3bfc7350acfdb5e44900fa237d00b869a4c75f46b4df3750019 | LAPSE_RISK | OCIO-PCI-01-FY2024 | Acknowledged |  |  | rahul.chopra@databricks.com | 2026-11-02T18:04:22.871Z |
| lb_app_alert_actions_history_1 | insert | 2026-11-02T18:04:24.453 | 8915b868e77ef3bfc7350acfdb5e44900fa237d00b869a4c75f46b4df3750019 | LAPSE_RISK | OCIO-PCI-01-FY2024 | Assigned | budget.analyst@dci.example.gov | Confirm obligation plan for the uncommitted balance before the option-exercise window closes. | rahul.chopra@databricks.com | 2026-11-02T18:04:22.932Z |
| lb_app_alert_actions_history_1 | insert | 2026-11-02T18:07:08.482 | 0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09 | BURN_RATE_VARIANCE | OCIO-PCI-02-FY2026 | Acknowledged |  |  | rahul.chopra@databricks.com | 2026-11-02T18:07:08.475Z |
| lb_app_alert_actions_history_1 | insert | 2026-11-02T18:07:08.531 | 0dff95d8fd2266f732ee5e8b8cbc6e7aae95ac0adc3e1dd75e3b2a9aabd6df09 | BURN_RATE_VARIANCE | OCIO-PCI-02-FY2026 | Assigned | budget.analyst@dci.example.gov | Confirm obligation plan for the uncommitted balance before the option-exercise window closes. | rahul.chopra@databricks.com | 2026-11-02T18:07:08.526Z |
