# Unity Catalog row filters and column masks on pipeline tables

Executed 2026-11-02 18:12 UTC

```sql
SELECT table_name, 'ROW FILTER' AS policy, filter_name AS function, target_columns AS columns
FROM rachopra_catalog.information_schema.row_filters WHERE table_schema = 'fe_bar'
UNION ALL
SELECT table_name, 'COLUMN MASK', mask_name, column_name
FROM rachopra_catalog.information_schema.column_masks WHERE table_schema = 'fe_bar'
```

**Result:**

| table_name | policy | function | columns |
|---|---|---|---|
| silver_obligations | ROW FILTER | rachopra_catalog.fe_bar.office_row_filter | office_code |
| silver_procurement_requests | ROW FILTER | rachopra_catalog.fe_bar.office_row_filter | office_code |
| silver_pr_status_history | ROW FILTER | rachopra_catalog.fe_bar.office_row_filter | office_code |
| silver_invoices | COLUMN MASK | rachopra_catalog.fe_bar.mask_payee_pii | remit_account_number |
| silver_invoices | COLUMN MASK | rachopra_catalog.fe_bar.mask_payee_pii | remit_routing_number |
| silver_invoices | COLUMN MASK | rachopra_catalog.fe_bar.mask_payee_pii | vendor_tin |
