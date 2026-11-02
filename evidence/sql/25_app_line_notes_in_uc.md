# App write-back round trip: analyst notes on budget lines

Executed 2026-11-02 18:12 UTC

```sql
SELECT 'lb_app_line_notes_history' AS uc_table, _pg_change_type, _timestamp AS landed_in_uc, note_id, line_id, office_code, note, author, created_at FROM rachopra_catalog.fe_bar.lb_app_line_notes_history
ORDER BY created_at
```

**Result:**

| uc_table | _pg_change_type | landed_in_uc | note_id | line_id | office_code | note | author | created_at |
|---|---|---|---|---|---|---|---|---|
| lb_app_line_notes_history | insert | 2026-11-02T18:04:23.422 | 1 | OCIO-PCI-01-FY2024 | OCIO | Option exercise submitted from the year-end plan; program office to confirm the bona fide need memo by 7 Aug. | rahul.chopra@databricks.com | 2026-11-02T18:04:22.444Z |
| lb_app_line_notes_history | insert | 2026-11-02T18:07:08.086 | 2 | OTS-PCI-01-FY2024 | OTS | Option exercise submitted from the year-end plan; program office to confirm the bona fide need memo by 7 Aug. | rahul.chopra@databricks.com | 2026-11-02T18:07:08.081Z |
