# App write-back round trip: reprogramming requests within a TAS (with approval state)

Executed 2026-11-02 18:12 UTC

```sql
SELECT 'lb_app_reprogramming_requests_history' AS uc_table, _pg_change_type, _timestamp AS landed_in_uc, request_id, tas, from_line_id, to_line_id, amount, notification_required, status, requested_by, requested_at, decided_by, decided_at FROM rachopra_catalog.fe_bar.lb_app_reprogramming_requests_history
ORDER BY requested_at, landed_in_uc
```

**Result:**

| uc_table | _pg_change_type | landed_in_uc | request_id | tas | from_line_id | to_line_id | amount | notification_required | status | requested_by | requested_at | decided_by | decided_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lb_app_reprogramming_requests_history | insert | 2026-11-02T18:04:23.864 | RPG-0001 | 999-2026-0100 | OTS-OS-02-FY2026 | OWS-OS-02-FY2026 | 920000.00 | true | Pending | rahul.chopra@databricks.com | 2026-11-02T18:04:22.562Z |  |  |
| lb_app_reprogramming_requests_history | insert | 2026-11-02T18:07:08.188 | RPG-0002 | 999-2026-0600 | OWS-GA-01-FY2026 | OGM-GA-01-FY2026 | 433000.00 | false | Pending | rahul.chopra@databricks.com | 2026-11-02T18:07:08.183Z |  |  |
