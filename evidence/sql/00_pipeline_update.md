# Spark Declarative Pipeline: latest update lifecycle

Executed 2026-11-02 18:12 UTC

```sql
SELECT timestamp, message FROM event_log('2a2a20f2-5cb5-4aa8-99db-6e9c0bca6ebe')
WHERE event_type = 'update_progress'
  AND origin.update_id = (SELECT origin.update_id FROM event_log('2a2a20f2-5cb5-4aa8-99db-6e9c0bca6ebe') WHERE event_type = 'create_update' ORDER BY timestamp DESC LIMIT 1)
ORDER BY timestamp
```

**Result:**

| timestamp | message |
|---|---|
| 2026-10-15T13:48:07.731Z | Update be0d76 is WAITING_FOR_RESOURCES. |
| 2026-10-15T13:48:19.112Z | Update be0d76 is INITIALIZING. |
| 2026-10-15T13:49:17.643Z | Update be0d76 is RESETTING. |
| 2026-10-15T13:49:21.732Z | Update be0d76 is SETTING_UP_TABLES. |
| 2026-10-15T13:49:38.519Z | Update be0d76 is RUNNING. |
| 2026-10-15T13:50:44.429Z | Update be0d76 is COMPLETED. |
