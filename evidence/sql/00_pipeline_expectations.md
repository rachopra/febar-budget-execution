# Spark Declarative Pipeline: data-quality expectation results (latest update)

Executed 2026-11-02 18:12 UTC

```sql
WITH latest AS (SELECT origin.update_id FROM event_log('2a2a20f2-5cb5-4aa8-99db-6e9c0bca6ebe') WHERE event_type = 'create_update' ORDER BY timestamp DESC LIMIT 1),
exp AS (SELECT explode(from_json(details:flow_progress:data_quality:expectations,
          'array<struct<name: string, dataset: string, passed_records: bigint, failed_records: bigint>>')) AS e
        FROM event_log('2a2a20f2-5cb5-4aa8-99db-6e9c0bca6ebe') WHERE event_type = 'flow_progress' AND origin.update_id IN (SELECT update_id FROM latest))
SELECT split(e.dataset, '\\.')[size(split(e.dataset, '\\.')) - 1] AS dataset, e.name AS expectation,
       SUM(e.passed_records) AS passed, SUM(e.failed_records) AS failed
FROM exp GROUP BY ALL ORDER BY failed DESC, dataset
```

**Result:**

| dataset | expectation | passed | failed |
|---|---|---|---|
| invoices_clean | well_formed_contract_number | 19724 | 12 |
| silver_pr_events | has_pr_id | 21443 | 6 |
| invoices_clean | positive_invoice_amount | 19736 | 0 |
| invoices_clean | has_invoice_id | 19736 | 0 |
| silver_budget_lines | positive_enacted_amount | 116 | 0 |
| silver_budget_lines | apportionment_within_enacted | 116 | 0 |
| silver_obligations | nonzero_obligation | 3839 | 0 |
| silver_obligations | has_obligation_document | 3839 | 0 |
| silver_ppa | valid_ppa_code | 29 | 0 |
| silver_pr_events | known_status | 21449 | 0 |
| silver_pr_events | valid_ppa_code | 21449 | 0 |
| silver_pr_events | has_event_ts | 21449 | 0 |
| spend_plan_from_budget_office_template | valid_ppa_code | 43152 | 0 |
| spend_plan_from_budget_office_template | valid_planned_obligations | 43152 | 0 |
| spend_plan_from_budget_office_template | valid_plan_month | 43152 | 0 |
| spend_plan_from_budget_office_template | valid_revision | 43152 | 0 |
| spend_plan_from_legacy_template | valid_ppa_code | 7092 | 0 |
| spend_plan_from_legacy_template | valid_plan_month | 7092 | 0 |
| spend_plan_from_legacy_template | valid_planned_obligations | 7092 | 0 |
| spend_plan_from_legacy_template | valid_revision | 7092 | 0 |
