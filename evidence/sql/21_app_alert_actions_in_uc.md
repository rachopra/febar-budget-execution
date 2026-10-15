# App write-back round trip: alert actions (app -> Lakebase -> CDF -> UC Delta)

Executed 2026-10-15 14:26 UTC

```sql
SELECT _pg_change_type, _timestamp AS landed_in_uc, alert_id, alert_type, line_id, action, assignee, note, acted_by, acted_at
FROM rachopra_catalog.fe_bar.lb_app_alert_actions_history ORDER BY acted_at
```

**Result:**

| _pg_change_type | landed_in_uc | alert_id | alert_type | line_id | action | assignee | note | acted_by | acted_at |
|---|---|---|---|---|---|---|---|---|---|
| insert | 2026-10-15T13:38:00.098 | 47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456 | APPORTIONMENT_EXCEEDED | OCIO-PCI-01-FY2026 | Assigned | budget.analyst@dci.example.gov | Prepare apportionment reapportionment request before further obligations. | rahul.chopra@databricks.com | 2026-10-15T13:35:08.332Z |
| insert | 2026-10-15T14:08:30.318 | 47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456 | APPORTIONMENT_EXCEEDED | OCIO-PCI-01-FY2026 | Assigned | budget.analyst@dci.example.gov | Prepare apportionment reapportionment request before further obligations. | rahul.chopra@databricks.com | 2026-10-15T14:08:29.766Z |
| insert | 2026-10-15T14:10:00.033 | 47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456 | APPORTIONMENT_EXCEEDED | OCIO-PCI-01-FY2026 | Assigned | budget.analyst@dci.example.gov | Prepare apportionment reapportionment request before further obligations. | rahul.chopra@databricks.com | 2026-10-15T14:10:00.029Z |
| insert | 2026-10-15T14:25:06.775 | 47a557853016f120747c21a70798645b64d920b75d28424c53a0aaf38e122456 | APPORTIONMENT_EXCEEDED | OCIO-PCI-01-FY2026 | Assigned | budget.analyst@dci.example.gov | Prepare apportionment reapportionment request before further obligations. | rahul.chopra@databricks.com | 2026-10-15T14:25:06.769Z |
